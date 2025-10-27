# Automatic Migrations and Cache Clearing

## Overview
The Docker container now automatically handles migrations and cache clearing on every rebuild and restart.

## What Happens Automatically

### On Build (`docker-compose build --pull`)
1. **Python Cache Cleared**: All `__pycache__` directories and `.pyc` files are removed
2. **Fresh Templates**: Ensures templates are never cached from previous builds
3. **Triggered by**: Any code change or `CACHE_BUST` argument change

### On Container Start (`docker-compose up`)
1. **Database Migrations Run**: All migration scripts in `migrations/` directory are executed
2. **Runtime Cache Cleared**: Python bytecode cache cleared again at startup
3. **Application Started**: Flask/Gunicorn starts with clean state

## Files Modified

### Dockerfile
```dockerfile
# After copying code, clear cache
RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
RUN find /app -type f -name "*.pyc" -delete 2>/dev/null || true

# Use entrypoint script
ENTRYPOINT ["/app/site01/entrypoint.sh"]
```

### entrypoint.sh (NEW)
Bash script that runs before the application starts:
- Waits for database volume to be ready
- Runs all migration scripts
- Clears Python cache
- Starts the application

## Usage

### Regular Rebuild (with cache clearing)
```bash
docker-compose build --pull
docker-compose up -d
```

### Force Complete Rebuild
```bash
docker-compose build --no-cache --pull
docker-compose up -d
```

### Check Migration Output
```bash
docker logs orion-project | grep -A 5 "Running database migrations"
```

## Current Migrations

### add_classe_field.py
- **Purpose**: Adds `classe` column to `authorized_athletes` table
- **Safe**: Checks if column exists before adding
- **Default**: Sets 'CO' for existing records

## Benefits

1. **No Manual Steps**: Migrations run automatically on deployment
2. **No Cache Issues**: Templates always fresh after rebuild
3. **Idempotent**: Safe to run multiple times
4. **Production Ready**: Works on server without manual intervention

## Troubleshooting

### Migration Failed
Check logs:
```bash
docker logs orion-project 2>&1 | grep -C 10 "Running database migrations"
```

### Cache Still Present
Verify cache clearing in logs:
```bash
docker logs orion-project | grep "Clearing Python cache"
```

### Manual Migration Run
If needed:
```bash
docker exec -it orion-project python /app/site01/migrations/add_classe_field.py
```

## Created: 2025-10-13
**Author**: GitHub Copilot  
**Context**: Fixing "no such column: authorized_athletes.classe" error and automating cache clearing
