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

Edit content.json and restart the container if needed:

- updates: blog/status entries
- milestones: goals and progress percentage
- planned_work: upcoming tasks

## Registration storage

Registrations are appended to registrations.json as JSON objects.
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
