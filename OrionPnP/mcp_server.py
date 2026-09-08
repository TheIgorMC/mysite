"""MCP server exposing OrionPnP content for agent editing.

Runs as a standalone HTTP process alongside the Flask app (does not import
Flask's `app` object as a WSGI app itself) and operates on the same
local_data/ JSON files, reusing the persistence helpers from app.py so
writes stay consistent (atomic writes, same write lock, same seeding rules).

Two ways in, both ending at the same set of tools:

1. OAuth 2.1 (for claude.ai's connector UI, or any MCP client that speaks
   OAuth). Dynamic client registration is enabled, so a client only needs
   this server's URL - it registers itself and gets its own client_id/secret
   automatically, no manual entry required. The human approval step reuses
   the same admin password as the /edit CMS (see app.py's AUTH_FILE):
   authorizing a client means typing that password once in a browser tab.

2. A static bearer token (ORION_MCP_TOKEN) for simple, non-browser clients
   like the Claude Code CLI, sent as `Authorization: Bearer <token>`.
"""

import os
import secrets
import time
from urllib.parse import urlparse

import uvicorn
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthClientInformationFull,
    OAuthToken,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from werkzeug.security import check_password_hash

import app as orion

ISSUER_URL = os.getenv("ORION_MCP_ISSUER_URL", "http://127.0.0.1:8765").rstrip("/")
STATIC_TOKEN = os.getenv("ORION_MCP_TOKEN", "").strip()
ACCESS_TOKEN_TTL_SECONDS = 3600
AUTH_CODE_TTL_SECONDS = 300

CONTENT_SECTIONS = {"updates", "timeline", "milestones", "planned_work", "gallery"}

LOGIN_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>OrionPnP MCP access</title>
<style>
body{{font-family:system-ui,sans-serif;background:#060d1a;color:#e8f1ff;display:flex;
  align-items:center;justify-content:center;min-height:100vh;margin:0}}
form{{background:rgba(11,22,41,.95);border:1px solid rgba(255,255,255,.18);border-radius:12px;
  padding:1.5rem;width:min(360px,90vw)}}
h1{{font-size:1rem;margin:0 0 .75rem}}
p{{color:#7da4c8;font-size:.85rem;margin:0 0 1rem}}
input{{width:100%;box-sizing:border-box;background:rgba(6,13,26,.85);border:1px solid rgba(255,255,255,.09);
  border-radius:8px;color:#e8f1ff;font-size:.95rem;padding:.6rem .8rem;margin-bottom:.75rem}}
button{{width:100%;background:#e07c24;border:none;border-radius:10px;color:#fff;font-weight:600;
  font-size:.9rem;padding:.6rem;cursor:pointer}}
.err{{color:#f87171;font-size:.82rem;margin:0 0 .75rem}}
</style></head><body>
<form method="post" action="/login">
<h1>Authorize agent access to OrionPnP</h1>
<p>An MCP client is requesting access to the OrionPnP CMS. Sign in with the admin password to approve it.</p>
{error_html}
<input type="hidden" name="txn" value="{txn}">
<input type="password" name="password" placeholder="Admin password" autofocus required>
<button type="submit">Authorize</button>
</form></body></html>"""


class OrionOAuthProvider:
    """Minimal in-memory OAuth 2.1 authorization server, gated by the CMS admin password."""

    def __init__(self):
        self.clients: dict[str, OAuthClientInformationFull] = {}
        self.auth_codes: dict[str, AuthorizationCode] = {}
        self.access_tokens: dict[str, AccessToken] = {}
        self.refresh_tokens: dict[str, RefreshToken] = {}
        self._pending: dict[str, tuple[OAuthClientInformationFull, AuthorizationParams]] = {}

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self.clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self.clients[client_info.client_id] = client_info

    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        txn = secrets.token_urlsafe(24)
        self._pending[txn] = (client, params)
        return f"/login?txn={txn}"

    async def load_authorization_code(self, client, authorization_code: str) -> AuthorizationCode | None:
        code = self.auth_codes.get(authorization_code)
        if code is None or code.client_id != client.client_id:
            return None
        if code.expires_at < time.time():
            self.auth_codes.pop(authorization_code, None)
            return None
        return code

    async def exchange_authorization_code(self, client, authorization_code: AuthorizationCode) -> OAuthToken:
        self.auth_codes.pop(authorization_code.code, None)
        return self._issue_token(client, authorization_code.scopes)

    async def load_refresh_token(self, client, refresh_token: str) -> RefreshToken | None:
        token = self.refresh_tokens.get(refresh_token)
        if token is None or token.client_id != client.client_id:
            return None
        return token

    async def exchange_refresh_token(self, client, refresh_token: RefreshToken, scopes: list[str]) -> OAuthToken:
        self.refresh_tokens.pop(refresh_token.token, None)
        return self._issue_token(client, scopes or refresh_token.scopes)

    async def load_access_token(self, token: str) -> AccessToken | None:
        if STATIC_TOKEN and secrets.compare_digest(token, STATIC_TOKEN):
            return AccessToken(token=token, client_id="static-token", scopes=["orionpnp"], expires_at=None)

        access = self.access_tokens.get(token)
        if access is None:
            return None
        if access.expires_at and access.expires_at < time.time():
            self.access_tokens.pop(token, None)
            return None
        return access

    async def revoke_token(self, token) -> None:
        self.access_tokens.pop(getattr(token, "token", token), None)
        self.refresh_tokens.pop(getattr(token, "token", token), None)

    def _issue_token(self, client: OAuthClientInformationFull, scopes: list[str]) -> OAuthToken:
        access = secrets.token_urlsafe(32)
        refresh = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + ACCESS_TOKEN_TTL_SECONDS
        self.access_tokens[access] = AccessToken(
            token=access, client_id=client.client_id, scopes=scopes, expires_at=expires_at
        )
        self.refresh_tokens[refresh] = RefreshToken(token=refresh, client_id=client.client_id, scopes=scopes)
        return OAuthToken(
            access_token=access,
            expires_in=ACCESS_TOKEN_TTL_SECONDS,
            scope=" ".join(scopes) if scopes else None,
            refresh_token=refresh,
        )

    def complete_login(self, txn: str) -> str | None:
        pending = self._pending.pop(txn, None)
        if pending is None:
            return None
        client, params = pending
        code_value = secrets.token_urlsafe(32)
        self.auth_codes[code_value] = AuthorizationCode(
            code=code_value,
            scopes=params.scopes or [],
            expires_at=time.time() + AUTH_CODE_TTL_SECONDS,
            client_id=client.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
        )
        return construct_redirect_uri(str(params.redirect_uri), code=code_value, state=params.state)


provider = OrionOAuthProvider()

_issuer = urlparse(ISSUER_URL)
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[_issuer.netloc],
    allowed_origins=[f"{_issuer.scheme}://{_issuer.netloc}"],
)

mcp = MCPServer(
    "orionpnp-cms",
    auth_server_provider=provider,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(ISSUER_URL),
        client_registration_options=ClientRegistrationOptions(
            enabled=True, valid_scopes=["orionpnp"], default_scopes=["orionpnp"]
        ),
        resource_server_url=AnyHttpUrl(f"{ISSUER_URL}/mcp"),
        validate_token_resource=False,
    ),
)


@mcp.custom_route("/login", methods=["GET"])
async def login_form(request: Request):
    txn = request.query_params.get("txn", "")
    if txn not in provider._pending:
        return HTMLResponse("This login link is invalid or has expired.", status_code=400)
    return HTMLResponse(LOGIN_PAGE.format(txn=txn, error_html=""))


@mcp.custom_route("/login", methods=["POST"])
async def login_submit(request: Request):
    form = await request.form()
    txn = str(form.get("txn", ""))
    password = str(form.get("password", ""))

    if txn not in provider._pending:
        return HTMLResponse("This login link is invalid or has expired.", status_code=400)

    auth_config = orion._load_json(orion.AUTH_FILE, {"password_hash": ""})
    password_hash = auth_config.get("password_hash") if isinstance(auth_config, dict) else ""
    if not password_hash or not check_password_hash(password_hash, password):
        error_html = '<p class="err">Invalid password.</p>'
        return HTMLResponse(LOGIN_PAGE.format(txn=txn, error_html=error_html), status_code=401)

    redirect_url = provider.complete_login(txn)
    if redirect_url is None:
        return HTMLResponse("This login link is invalid or has expired.", status_code=400)
    return RedirectResponse(redirect_url, status_code=302)


@mcp.tool()
def get_content() -> dict:
    """Return the full OrionPnP content.json: updates, timeline, milestones, planned_work, gallery."""
    return orion._read_content_file()


@mcp.tool()
def update_content_section(section: str, items: list) -> dict:
    """Replace one content section with a new list of items.

    section must be one of: updates, timeline, milestones, planned_work, gallery.
    Fetch get_content() first, edit the section's list client-side, then pass
    the full updated list back here (this replaces the whole section).
    """
    if section not in CONTENT_SECTIONS:
        raise ValueError(f"section must be one of {sorted(CONTENT_SECTIONS)}")
    if not isinstance(items, list):
        raise ValueError("items must be a list")

    with orion.WRITE_LOCK:
        existing = orion._read_content_file()
        existing[section] = items
        orion._atomic_write_json(orion.CONTENT_FILE, existing)

    return {"ok": True, "section": section, "count": len(items)}


@mcp.tool()
def get_locales() -> dict:
    """Return all locale translation dictionaries (en, it, fr, es)."""
    return orion._read_locales_file()


@mcp.tool()
def update_locale_key(lang: str, key: str, value: str) -> dict:
    """Set a single translation key in one locale file (en|it|fr|es)."""
    if lang not in orion.SUPPORTED_LOCALES:
        raise ValueError(f"lang must be one of {orion.SUPPORTED_LOCALES}")

    path = orion.LOCALES_DIR / f"{lang}.json"
    with orion.WRITE_LOCK:
        data = orion._load_json(path, {})
        if not isinstance(data, dict):
            data = {}
        data[str(key)] = str(value)
        orion._atomic_write_json(path, data)

    return {"ok": True, "lang": lang, "key": key}


@mcp.tool()
def update_locale_bulk(lang: str, entries: dict, replace: bool = False) -> dict:
    """Set multiple translation keys in one locale file (en|it|fr|es) in a single call.

    entries is a {key: value} map merged into the existing locale file (or replacing
    it entirely if replace=True). Prefer this over repeated update_locale_key calls
    when updating more than a couple of keys at once.
    """
    if lang not in orion.SUPPORTED_LOCALES:
        raise ValueError(f"lang must be one of {orion.SUPPORTED_LOCALES}")
    if not isinstance(entries, dict):
        raise ValueError("entries must be an object of {key: value}")

    path = orion.LOCALES_DIR / f"{lang}.json"
    with orion.WRITE_LOCK:
        data = {} if replace else orion._load_json(path, {})
        if not isinstance(data, dict):
            data = {}
        data.update({str(k): str(v) for k, v in entries.items()})
        orion._atomic_write_json(path, data)

    return {"ok": True, "lang": lang, "count": len(data)}


@mcp.tool()
def list_assets() -> list:
    """List available image assets on the site (name, url, size, whether it can be deleted)."""
    return orion._collect_assets()


@mcp.tool()
def get_registrations() -> list:
    """Return the list of interest-form registrations submitted by site visitors."""
    data = orion._load_json(orion.REGISTRATIONS_FILE, [])
    return data if isinstance(data, list) else []


def build_app():
    return mcp.streamable_http_app(stateless_http=True, transport_security=transport_security)


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8765"))
    uvicorn.run(build_app(), host=host, port=port)
