from __future__ import annotations

from typing import Any


class RegistrationError(ValueError):
    def __init__(self, error: str, description: str):
        super().__init__(description)
        self.error = error
        self.description = description


def authorization_server_metadata(
    origin: str,
    cognito_login_domain: str,
    scope: str,
) -> dict[str, Any]:
    oauth = cognito_login_domain.rstrip("/") + "/oauth2"
    return {
        "issuer": origin,
        "authorization_endpoint": f"{oauth}/authorize",
        "token_endpoint": f"{oauth}/token",
        "registration_endpoint": f"{origin}/oauth/register",
        "revocation_endpoint": f"{oauth}/revoke",
        "scopes_supported": [scope],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"],
    }


def register_public_client(
    payload: Any,
    client_id: str,
    allowed_redirect_uris: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RegistrationError(
            "invalid_client_metadata", "Registration body must be a JSON object."
        )

    redirect_uris = payload.get("redirect_uris")
    if (
        not isinstance(redirect_uris, list)
        or len(redirect_uris) != 1
        or redirect_uris[0] not in allowed_redirect_uris
    ):
        raise RegistrationError(
            "invalid_redirect_uri", "Only Claude's hosted OAuth callback is allowed."
        )

    if payload.get("token_endpoint_auth_method", "none") != "none":
        raise RegistrationError(
            "invalid_client_metadata", "Only public PKCE clients are supported."
        )

    grant_types = payload.get("grant_types", ["authorization_code"])
    if (
        not isinstance(grant_types, list)
        or "authorization_code" not in grant_types
        or not set(grant_types) <= {"authorization_code", "refresh_token"}
    ):
        raise RegistrationError(
            "invalid_client_metadata", "Unsupported OAuth grant type."
        )

    response_types = payload.get("response_types", ["code"])
    if response_types != ["code"]:
        raise RegistrationError(
            "invalid_client_metadata", "Only authorization code flow is supported."
        )

    return {
        "client_id": client_id,
        "redirect_uris": redirect_uris,
        "token_endpoint_auth_method": "none",
        "grant_types": grant_types,
        "response_types": response_types,
    }
