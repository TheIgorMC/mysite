# OrionPnP Self-Contained Website

OrionPnP is a fully self-contained, single-folder website + API stack designed to run in Docker (including Dockge).

## What this folder includes

- English launch page (translation-ready structure)
- Smooth animations and optional background video support
- Updates section (blog-like project log)
- Milestones section (targets and progress)
- Planned work section (roadmap tasks)
- Interest registration form
- Single-file JSON storage for registrations
- Docker setup on port 1080

## Folder contents

- app.py: Flask app serving frontend + JSON API
- index.html: single-page presentation site
- styles.css: visual style and animations
- app.js: frontend logic and content rendering (currently EN only)
- content.json: updates, milestones, planned work content
- registrations.json: registrations list storage
- local_data/: persistent runtime overlay for content, locales, registrations, uploads, and auth
- Dockerfile: container build
- docker-compose.yml: stack definition (port 1080)
- DEPLOY_DOCKGE.md: pull/deploy instructions
- requirements.txt: Python dependencies

## Run locally with Docker

From OrionPnP folder:

```bash
docker compose up -d --build
```

Open:

- http://localhost:1080

Stop:

```bash
docker compose down
```

## API endpoints

- GET /health
- GET /api/content
- POST /api/register
- GET /api/registrations/export?token=YOUR_TOKEN (token optional unless ORION_ADMIN_TOKEN is configured)

## Edit project updates and roadmap

Use the editor or update the tracked defaults, then run the local-data sync script so the persisted copy picks up new keys without overwriting old content:

- updates: blog/status entries
- milestones: goals and progress percentage
- planned_work: upcoming tasks

For persistent editing, the runtime now uses `local_data/` instead of writing back into the tracked source files. Run `python scripts/setup_local_data.py` once after install or after pulling updates to seed the local copy and merge any new keys or content without overwriting existing values.

## Admin access

The CMS editor at `/edit` requires a password-backed login session for save, import, upload, and delete actions.
Once unlocked, edits autosave a moment after you stop typing (no more clicking "Save Changes" after every field) — the button becomes "Save now" for an immediate manual save.

Set or reset the password with:

```bash
python scripts/setup_local_data.py --reset-password
```

The password hash and session secret are stored in `local_data/auth.json`.

## MCP server (agent access)

`mcp_server.py` runs a separate MCP server so AI agents can read and update OrionPnP content directly, without going through the browser CMS. It reuses the same `local_data/` JSON files and write helpers as the Flask app, so content stays consistent either way.

Tools exposed: `get_content`, `update_content_section`, `get_locales`, `update_locale_key`, `update_locale_bulk`, `list_assets`, `get_registrations`.

There are two ways to authenticate, pick whichever fits the client:

**1. OAuth 2.1 (for claude.ai's connector UI, or any MCP client that speaks OAuth).**
Dynamic client registration is on, so you just give the client this server's URL (`http://<host>:8765/mcp`) — no manual client ID/secret to create. The client registers itself, then opens a browser tab where you approve access with the **same admin password used for `/edit`**. No separate setup page or token to copy — the password *is* the credential.

- In claude.ai: Settings → Connectors → Add custom connector → paste the server URL. Claude discovers the OAuth endpoints and registration automatically.
- `ORION_MCP_ISSUER_URL` (env var) must be set to the server's real public URL (e.g. `https://mcp.yourdomain.com`), since it's advertised in the OAuth metadata and used to restrict allowed hosts — it defaults to `http://127.0.0.1:8765`, which only works for local testing.

**2. Static bearer token (for simple clients like the Claude Code CLI).**
Set `ORION_MCP_TOKEN` and send `Authorization: Bearer <token>` — no OAuth dance needed:

```bash
claude mcp add --transport http orionpnp http://<host>:8765/mcp --header "Authorization: Bearer <token>"
```

With no `ORION_MCP_TOKEN` set, that fallback is simply disabled; OAuth still works.

Run it standalone:

```bash
pip install -r requirements-mcp.txt
ORION_MCP_ISSUER_URL=https://mcp.yourdomain.com ORION_MCP_TOKEN=change-me python mcp_server.py
```

Or via Docker Compose (already wired up alongside the site, on port 8765 — set `ORION_MCP_ISSUER_URL`/`ORION_MCP_TOKEN` for your deployment before exposing it):

```bash
docker compose up -d --build orionpnp-mcp
```

## Registration storage

Registrations are appended to `local_data/registrations.json` as JSON objects.
You can manually fetch this file periodically from the folder, or use the export endpoint.

## Optional background video

To enable background video:

1. Place a file named background.mp4 in this same folder.
2. Refresh the page.

If the file is missing, the page automatically falls back to animated gradients.

## Reverse proxy usage

This stack exposes port 1080. You can route it through your proxy manager as needed.

## Notes

- No external frontend dependencies are required.
- Everything needed to run is in this folder.
