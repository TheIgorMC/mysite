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

When you are already inside `OrionPnP` and want to update from git:

```bash
git pull --ff-only origin main
python scripts/setup_local_data.py
docker compose up -d --build
```

This works when `OrionPnP` is part of a repository checkout (not when it was copied as a standalone folder without `.git`).

If your sparse-checkout rules were changed, re-apply them from the same folder:

```bash
git sparse-checkout reapply
```

The site will be available on port 1080.

## Option B: Deploy with Dockge

1. Copy the OrionPnP folder to your Dockge stacks location.
2. In Dockge, create/import a stack from OrionPnP/docker-compose.yml.
3. Start the stack.
4. Access via http://YOUR_HOST:1080 (or your reverse proxy).

### If you already have `stacks/OrionPnP` as a copied folder and want `git pull`

Because your upstream repo is `mysite` (monorepo), a plain `git pull` from `stacks/OrionPnP` cannot directly map only that subfolder to `.`.

Use this pattern instead:

1. Keep `stacks/OrionPnP` as your runtime folder.
2. Create a hidden sparse checkout sibling that tracks only `mysite/OrionPnP`.
3. Sync that subfolder into `stacks/OrionPnP`.

One-time setup (run from `stacks`):

```bash
git clone --filter=blob:none --no-checkout <YOUR_REPO_URL> .mysite_upstream
cd .mysite_upstream
git sparse-checkout init --cone
git sparse-checkout set OrionPnP
git checkout main
```

Initial sync into your runtime folder:

```bash
cd ../OrionPnP
rsync -a --delete \
	--filter='P content.json' \
	--filter='P registrations.json' \
	--exclude 'content.json' \
	--exclude 'registrations.json' \
	../.mysite_upstream/OrionPnP/ ./
```

Daily update flow (run from inside `stacks/OrionPnP`):

```bash
git -C ../.mysite_upstream pull --ff-only origin main
python ../.mysite_upstream/OrionPnP/scripts/setup_local_data.py
rsync -a --delete \
	--filter='P content.json' \
	--filter='P registrations.json' \
	--exclude 'content.json' \
	--exclude 'registrations.json' \
	../.mysite_upstream/OrionPnP/ ./
docker compose up -d --build
```

Notes:

- This keeps your login folder as `stacks/OrionPnP`.
- `local_data/` stores the persistent runtime copies and the editor password hash.
- `content.json` and `registrations.json` are protected from deletion and excluded from overwrite during sync when using the legacy copy flow.
- If you also want to overwrite those two files from git, remove the `--exclude` flags.

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
