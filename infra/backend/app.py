from __future__ import annotations

import base64
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from mangum import Mangum
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from excel_reader import search_workbook
from oauth_dcr import (
    RegistrationError,
    authorization_server_metadata,
    register_public_client,
)

BUCKET = os.environ["BUCKET_NAME"]
SOURCES = {
    "depo": os.environ["DEPOT_KEY"],
    "tasima": os.environ["TRANSPORT_KEY"],
}
MAX_FILE_BYTES = int(os.environ.get("MAX_FILE_BYTES", "15728640"))
COGNITO_ISSUER = os.environ["COGNITO_ISSUER"]
COGNITO_SCOPE = os.environ.get("COGNITO_SCOPE", "dincer-data/read")
COGNITO_CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
COGNITO_LOGIN_DOMAIN = os.environ["COGNITO_LOGIN_DOMAIN"]
CLAUDE_ORIGINS = ("https://claude.ai", "https://claude.com")
CLAUDE_OAUTH_CALLBACKS = tuple(
    origin + "/api/mcp/auth_callback" for origin in CLAUDE_ORIGINS
)
ICON_PATH = Path(__file__).with_name("dincer-connector-icon.png")
API_STAGE = os.environ.get("API_STAGE", "").strip("/")
DAILY_QUERY_LIMIT = int(os.environ.get("DAILY_QUERY_LIMIT", "30"))
QUERY_LIMIT_TABLE = os.environ.get("QUERY_LIMIT_TABLE", "")
CONTACT_EMAIL = "info@dincerlogistics.com"
CONTACT_LINK = f"[{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL}?subject=Bilgi%20Talebi)"
CONTACT_MESSAGE = (
    f"Güncel fiyat ve hizmet bilgisi için {CONTACT_LINK} adresine e-posta "
    "gönderebilirsiniz."
)
QUERY_TOOL_DESCRIPTION = (
    "Search approved Dincer Logistics commercial data. Present only business "
    "results. Never mention sources, files, workbooks, sheets, rows, MCP, S3, "
    "metadata, missing records, or unsupported locations. Whenever message is not "
    "empty, include it verbatim, including for contact or referral questions."
)
TURKEY_TZ = timezone(timedelta(hours=3))
_cache: dict[str, tuple[str, bytes]] = {}
_s3_client = None
_ddb_client = None
_ssm_client = None
_instructions_cache = None

TRANSPORT_TERMS = {
    "kamyon", "kırkayak", "kirkayak", "tır", "tir", "ftl", "komple",
    "çıkış", "cikis", "çıkışlı", "cikisli", "varış", "varis",
}
STORAGE_TERMS = {
    "depo", "depolama", "antrepo", "palet", "elleçleme", "ellecleme",
    "tuzla", "dilovası", "dilovasi",
}
CONTACT_TERMS = {
    "iletişim", "iletisim", "iletişime", "iletisime", "iletişim bilgisi",
    "iletişim adresi", "kiminle konuş", "kiminle konus", "kimle konuş",
    "kimle konus", "e-posta", "eposta", "mail", "ulaş", "ulas",
    "yönlendir", "yonlendir",
}


def _s3():
    global _s3_client
    if _s3_client is None:
        import boto3

        _s3_client = boto3.client("s3")
    return _s3_client


def _ddb():
    global _ddb_client
    if _ddb_client is None:
        import boto3

        _ddb_client = boto3.client("dynamodb")
    return _ddb_client


def _assistant_instructions() -> str:
    global _ssm_client, _instructions_cache
    if _instructions_cache is not None:
        return _instructions_cache
    if value := os.environ.get("ASSISTANT_INSTRUCTIONS"):
        _instructions_cache = value
        return value
    parameter_name = os.environ.get("ASSISTANT_INSTRUCTIONS_PARAMETER")
    if not parameter_name:
        return "Use only approved data, do not expose technical metadata, and do not guess."
    if _ssm_client is None:
        import boto3

        _ssm_client = boto3.client("ssm")
    _instructions_cache = _ssm_client.get_parameter(
        Name=parameter_name,
        WithDecryption=True,
    )["Parameter"]["Value"]
    return _instructions_cache


def _query_call_name(event: dict) -> str | None:
    body = event.get("body")
    if not body:
        return None
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    try:
        payload = json.loads(body)
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("method") != "tools/call":
        return None
    return payload.get("params", {}).get("name")


def _enforce_daily_query_limit(event: dict) -> dict | None:
    if _query_call_name(event) != "query_data":
        return None

    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    user_id = claims.get("sub")
    if not user_id:
        return {"statusCode": 401, "body": '{"error":"Unauthorized"}'}

    now = datetime.now(TURKEY_TZ)
    user_day = f"{user_id}#{now.date().isoformat()}"
    expires_at = int((now + timedelta(days=2)).timestamp())
    try:
        _ddb().update_item(
            TableName=QUERY_LIMIT_TABLE,
            Key={"user_day": {"S": user_day}},
            UpdateExpression=(
                "SET #count = if_not_exists(#count, :zero) + :one, "
                "expires_at = :expires_at"
            ),
            ConditionExpression="attribute_not_exists(#count) OR #count < :limit",
            ExpressionAttributeNames={"#count": "query_count"},
            ExpressionAttributeValues={
                ":zero": {"N": "0"},
                ":one": {"N": "1"},
                ":limit": {"N": str(DAILY_QUERY_LIMIT)},
                ":expires_at": {"N": str(expires_at)},
            },
        )
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code")
        if code != "ConditionalCheckFailedException":
            raise
        return {
            "statusCode": 429,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "error": "daily_query_limit_exceeded",
                    "message": f"Günlük {DAILY_QUERY_LIMIT} soru hakkınız doldu.",
                },
                ensure_ascii=False,
            ),
        }
    return None


def _workbook_bytes(source: str) -> bytes:
    key = SOURCES[source]
    metadata = _s3().head_object(Bucket=BUCKET, Key=key)
    size = metadata["ContentLength"]
    if size > MAX_FILE_BYTES:
        raise ValueError(f"{source} çalışma kitabı izin verilen boyutu aşıyor.")

    etag = metadata["ETag"].strip('"')
    cached = _cache.get(source)
    if cached and cached[0] == etag:
        return cached[1]

    body = _s3().get_object(Bucket=BUCKET, Key=key)["Body"].read()
    _cache[source] = (etag, body)
    return body


def query_data(
    question: str,
    source: Literal["all", "depo", "tasima"] = "all",
    max_results: int = 8,
) -> dict:
    """Search approved data with automatic routing; return only after all searches finish."""
    question = question.strip()
    if not 2 <= len(question) <= 200:
        raise ValueError("Soru 2-200 karakter arasında olmalı.")
    if not 1 <= max_results <= 20:
        raise ValueError("max_results 1-20 arasında olmalı.")

    terms = set(re.findall(r"\w+", question.casefold()))
    if terms & TRANSPORT_TERMS:
        source = "tasima"
    elif terms & STORAGE_TERMS:
        source = "depo"
    selected = list(SOURCES) if source == "all" else [source]
    matches = []
    truncated = False
    for name in selected:
        rows, was_truncated = search_workbook(
            _workbook_bytes(name), question, name, max_results
        )
        matches.extend(rows)
        truncated = truncated or was_truncated

    matches.sort(key=lambda item: (-item["score"], item["source"], item["row"]))
    results = [item["values"] for item in matches[:max_results]]
    contact_requested = any(term in question.casefold() for term in CONTACT_TERMS)
    return {
        "results": results,
        "message": (
            CONTACT_MESSAGE
            if contact_requested or not results
            else ""
        ),
    }


async def protected_resource_metadata(request: Request) -> JSONResponse:
    stage = f"/{API_STAGE}" if API_STAGE else ""
    origin = f"https://{request.headers['host']}{stage}"
    resource = f"{origin}/mcp"
    return JSONResponse(
        {
            "resource": resource,
            "authorization_servers": [origin],
            "scopes_supported": [COGNITO_SCOPE],
            "bearer_methods_supported": ["header"],
        }
    )


async def oauth_authorization_server_metadata(request: Request) -> JSONResponse:
    stage = f"/{API_STAGE}" if API_STAGE else ""
    origin = f"https://{request.headers['host']}{stage}"
    return JSONResponse(
        authorization_server_metadata(origin, COGNITO_LOGIN_DOMAIN, COGNITO_SCOPE)
    )


async def oauth_register(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
        registration = register_public_client(
            payload, COGNITO_CLIENT_ID, CLAUDE_OAUTH_CALLBACKS
        )
    except RegistrationError as exc:
        return JSONResponse(
            {"error": exc.error, "error_description": exc.description},
            status_code=400,
            headers={"Cache-Control": "no-store"},
        )
    except Exception:
        return JSONResponse(
            {
                "error": "invalid_client_metadata",
                "error_description": "Registration body must be valid JSON.",
            },
            status_code=400,
            headers={"Cache-Control": "no-store"},
        )

    return JSONResponse(
        registration,
        status_code=201,
        headers={"Cache-Control": "no-store"},
    )


async def enforce_claude_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in CLAUDE_ORIGINS:
        return JSONResponse({"error": "Invalid Origin"}, status_code=403)
    return await call_next(request)


async def favicon(request: Request) -> FileResponse:
    return FileResponse(
        ICON_PATH,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


def _create_app(allowed_host: str):
    server = FastMCP(
        "Dincer Logistics",
        instructions=_assistant_instructions(),
        stateless_http=True,
        json_response=True,
        streamable_http_path="/mcp",
        transport_security=TransportSecuritySettings(
            allowed_hosts=[allowed_host],
            allowed_origins=list(CLAUDE_ORIGINS),
        ),
    )
    read_only = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    server.add_tool(
        query_data,
        title="Search Dincer Logistics data",
        description=QUERY_TOOL_DESCRIPTION,
        annotations=read_only.model_copy(
            update={"title": "Search Dincer Logistics data"}
        ),
    )
    app = server.streamable_http_app()
    app.add_middleware(BaseHTTPMiddleware, dispatch=enforce_claude_origin)
    app.add_route(
        "/.well-known/oauth-protected-resource",
        protected_resource_metadata,
        methods=["GET"],
    )
    app.add_route(
        "/.well-known/oauth-authorization-server",
        oauth_authorization_server_metadata,
        methods=["GET"],
    )
    app.add_route("/oauth/register", oauth_register, methods=["POST"])
    app.add_route("/favicon.ico", favicon, methods=["GET"])
    return app


def handler(event, context):
    limited = _enforce_daily_query_limit(event)
    if limited:
        return limited
    allowed_host = event["requestContext"]["domainName"]
    app = _create_app(allowed_host)
    return Mangum(
        app,
        lifespan="auto",
        api_gateway_base_path=API_STAGE or "/",
    )(event, context)
