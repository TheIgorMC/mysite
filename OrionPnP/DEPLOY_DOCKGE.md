# OrionPnP Dockge Deployment

This folder is self-contained and can be deployed alone as a Docker stack.

## Option A: Pull only OrionPnP folder from your repository

Use sparse checkout to pull only this folder:

```bash
git clone --filter=blob:none --no-checkout <YOUR_REPO_URL>
cd <YOUR_REPO_NAME>
git sparse-checkout init --cone
git sparse-checkout set OrionPnP
git checkout main
cd OrionPnP
```

Then run locally:

```bash
docker compose up -d --build
```

The site will be available on port 1080.

## Option B: Deploy with Dockge

1. Copy the OrionPnP folder to your Dockge stacks location.
2. In Dockge, create/import a stack from OrionPnP/docker-compose.yml.
3. Start the stack.
4. Access via http://YOUR_HOST:1080 (or your reverse proxy).

## Optional security for registration export endpoint

To protect registration export:

1. Set ORION_ADMIN_TOKEN in docker-compose.yml environment.
2. Restart stack.
3. Export data from:

```text
GET /api/registrations/export?token=YOUR_TOKEN
```

## Where data lives

- Registrations: registrations.json
- Updates, milestones, planned work: content.json

Both files are bind-mounted in the compose file so data persists.
