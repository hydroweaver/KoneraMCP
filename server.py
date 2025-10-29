from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider

import os
from typing import Any, Dict
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

import httpx

# The GoogleProvider handles Google's token format and validation
auth_provider = GoogleProvider(
    client_id= os.getenv("GOOGLE_CLIENT_ID"),  # Your Google OAuth Client ID
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),                  # Your Google OAuth Client Secret
    base_url=os.getenv("SERVER_URL"),                  # Must match your OAuth configuration
    required_scopes=[                                  # Request user information
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
    ],
    # redirect_path="/auth/callback"                  # Default value, customize if needed
)

mcp = FastMCP("Demo Server", auth=auth_provider)

# Add a protected tool to test authentication
@mcp.tool
async def get_user_info() -> dict:
    """Returns information about the authenticated Google user."""
    from fastmcp.server.dependencies import get_access_token
    
    token = get_access_token()
    # The GoogleProvider stores user data in token claims
    return {
        "google_id": token.claims.get("sub"),
        "email": token.claims.get("email"),
        "name": token.claims.get("name"),
        "picture": token.claims.get("picture"),
        "locale": token.claims.get("locale")
    }

@mcp.tool
async def get_phone_id(phoneNumber: str) -> Dict[str, Any]:
    """Retrieve PhoneID information from Telesign for a given phone number.

    Args:
        phoneNumber: The target phone number in E.164 format, e.g. "+14155550123".

    Returns:
        The JSON response from Telesign's PhoneID API, or an object with an
        "error" field describing what went wrong.
    """
    # Read credentials from environment
    username = os.getenv("TELESIGN_ID")
    password = os.getenv("TELESIGN_TOKEN")

    if not username or not password:
        return {
            "error": (
                "Missing credentials: set TELESIGN_ID and TELESIGN_TOKEN in the environment."
            )
        }

    url = f"https://rest-ww.telesign.com/v1/phoneid/{phoneNumber}"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            # httpx will add the proper Basic Auth header when auth=(user, pass)
            resp = await client.post(
                url,
                headers={
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                json={},
                auth=(username, password),
            )

        # Raise for non-2xx and capture response body for clearer errors
        if resp.status_code // 100 != 2:
            # Try to parse JSON error, fall back to text
            try:
                err_payload = resp.json()
            except Exception:
                err_payload = {"status": resp.status_code, "body": resp.text[:2000]}
            return {
                "error": "Telesign PhoneID request failed",
                "status": resp.status_code,
                "details": err_payload,
            }

        return resp.json()

    except httpx.RequestError as e:
        return {"error": f"Network error while calling Telesign: {e.__class__.__name__}: {e}"}
    except Exception as e:  # final catch-all to avoid crashing the MCP tool
        return {"error": f"Unexpected error: {e.__class__.__name__}: {e}"}

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)