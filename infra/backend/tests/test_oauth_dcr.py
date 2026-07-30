from oauth_dcr import RegistrationError, register_public_client


CALLBACKS = (
    "https://claude.ai/api/mcp/auth_callback",
    "https://claude.com/api/mcp/auth_callback",
)


def test_registration_accepts_only_claude_public_pkce_client():
    result = register_public_client(
        {
            "redirect_uris": [CALLBACKS[0]],
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
        },
        "public-client-id",
        CALLBACKS,
    )
    assert result["client_id"] == "public-client-id"
    assert result["token_endpoint_auth_method"] == "none"

    try:
        register_public_client(
            {"redirect_uris": ["https://attacker.example/callback"]},
            "public-client-id",
            CALLBACKS,
        )
    except RegistrationError as exc:
        assert exc.error == "invalid_redirect_uri"
    else:
        raise AssertionError("Unapproved redirect URI was accepted")
