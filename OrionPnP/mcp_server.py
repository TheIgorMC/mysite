"""Token-authenticated MCP server exposing OrionPnP content for agent editing.

Runs as a standalone HTTP process alongside the Flask app (does not import
Flask itself) and operates on the same local_data/ JSON files, reusing the
persistence helpers from app.py so writes stay consistent (atomic writes,
same write lock, same seeding rules).

Auth: every request must carry `Authorization: Bearer <ORION_MCP_TOKEN>`.
The token is read from the ORION_MCP_TOKEN environment variable; if unset,
the server refuses all requests rather than running unauthenticated.
"""

import os

import uvicorn
from mcp.server.mcpserver import MCPServer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

import app as orion

MCP_TOKEN = os.getenv("ORION_MCP_TOKEN", "").strip()

mcp = MCPServer("orionpnp-cms")

CONTENT_SECTIONS = {"updates", "timeline", "milestones", "planned_work", "gallery"}


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
def list_assets() -> list:
    """List available image assets on the site (name, url, size, whether it can be deleted)."""
    return orion._collect_assets()


@mcp.tool()
def get_registrations() -> list:
    """Return the list of interest-form registrations submitted by site visitors."""
    data = orion._load_json(orion.REGISTRATIONS_FILE, [])
    return data if isinstance(data, list) else []


class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not MCP_TOKEN:
            return JSONResponse({"error": "ORION_MCP_TOKEN is not configured on the server"}, status_code=503)

        header = request.headers.get("authorization", "")
        expected = f"Bearer {MCP_TOKEN}"
        if header != expected:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        return await call_next(request)


def build_app():
    http_app = mcp.streamable_http_app(stateless_http=True)
    http_app.add_middleware(BearerAuthMiddleware)
    return http_app


if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8765"))
    uvicorn.run(build_app(), host=host, port=port)
