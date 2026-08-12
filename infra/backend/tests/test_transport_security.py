from mcp.server.transport_security import (
    TransportSecurityMiddleware,
    TransportSecuritySettings,
)
from starlette.testclient import TestClient

from app import CLAUDE_ORIGINS, _create_app


def test_rejects_unapproved_origin():
    middleware = TransportSecurityMiddleware(
        TransportSecuritySettings(
            allowed_hosts=["mcp.dincerlogistics.com"],
            allowed_origins=list(CLAUDE_ORIGINS),
        )
    )

    assert middleware._validate_origin("https://claude.ai")
    assert middleware._validate_origin("https://claude.com")
    assert not middleware._validate_origin("https://evil.example")

    client = TestClient(_create_app("testserver"))
    metadata = "/.well-known/oauth-authorization-server"
    assert client.get(metadata, headers={"Origin": "https://claude.com"}).status_code == 200
    assert client.get(metadata, headers={"Origin": "https://evil.example"}).status_code == 403


def test_favicon_returns_dincer_icon():
    client = TestClient(_create_app("testserver"))
    response = client.get("/favicon.ico")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
