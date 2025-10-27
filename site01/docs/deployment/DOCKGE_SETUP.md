# Orion Project - Dockge Setup Guide

## What is Dockge?

Dockge is a fancy, easy-to-use Docker Compose manager with a web UI. It's perfect for managing Docker containers on your OrangePi!

## Installation on OrangePi

### 1. Install Dockge (if not already installed)

```bash
# Create dockge directory
mkdir -p /opt/dockge
cd /opt/dockge

# Create docker-compose.yml for dockge
cat > docker-compose.yml << 'EOF'
version: "3.8"
services:
  dockge:
    image: louislam/dockge:1
    restart: unless-stopped
    ports:
      - 5001:5001
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/app/data
      - /opt/stacks:/opt/stacks
    environment:
      - DOCKGE_STACKS_DIR=/opt/stacks
EOF

# Start Dockge
docker-compose up -d

# Access Dockge at http://your-orangepi-ip:5001
```

## Deploy Orion Project with Dockge

### Method 1: Using Dockge UI (Recommended)

1. **Access Dockge Web UI**
   - Open `http://your-orangepi-ip:5001`
   - Create an admin account (first time)

2. **Add New Stack**
   - Click "+ Compose" button
   - Name it `orion-project`

3. **Paste docker-compose.yml content**
   - Copy the content from your `docker-compose.yml`
   - Or use the Git integration (see Method 2)

4. **Configure Environment Variables**
   - Click on "Environment Variables"
   - Add:
     ```
     SECRET_KEY=<generate-with-command-below>
     CF_ACCESS_CLIENT_ID=your-id
     CF_ACCESS_CLIENT_SECRET=your-secret
     ```

5. **Deploy**
   - Click "Deploy" button
   - Watch the logs as it builds and starts

### Method 2: Using Git Integration (Best for updates)

1. **In Dockge, click "+ Compose"**

2. **Choose "Clone from Git"**

3. **Enter Repository Details**
   ```
   Repository URL: https://github.com/TheIgorMC/mysite.git
   Branch: main
   Stack Name: orion-project
   ```

4. **Configure Environment**
   - After cloning, click on the stack
   - Go to "Environment Variables"
   - Add your variables from `.env.example`

5. **Deploy**
   - Click "Deploy"
   - Dockge will handle building and starting

### Method 3: Manual Git Clone + Dockge

```bash
# On your OrangePi, navigate to stacks directory
cd /opt/stacks

# Clone the repository
git clone https://github.com/TheIgorMC/mysite.git orion-project
cd orion-project

# Create .env file
cp .env.example .env

# Generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy output and paste in .env

# Edit .env with your values
nano .env

# The stack will now appear in Dockge UI automatically!
# Just click on it and hit "Deploy"
```

## Generate Secret Key

On your OrangePi or any computer with Python:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Or with OpenSSL:

```bash
openssl rand -hex 32
```

## Environment Variables to Configure

**Required:**
- `SECRET_KEY` - Generate with command above

**Optional (but recommended):**
- `CF_ACCESS_CLIENT_ID` - Your Cloudflare Access Client ID
- `CF_ACCESS_CLIENT_SECRET` - Your Cloudflare Access Client Secret
- Email settings if you want newsletter functionality

## Accessing Your Application

After deployment:
- **Orion Project**: `http://your-orangepi-ip:5000`
- **Dockge**: `http://your-orangepi-ip:5001`

## Managing with Dockge

### View Logs
- Click on `orion-project` stack
- Click "Logs" tab
- Real-time log streaming

### Update Application
When you push changes to GitHub:
1. In Dockge, click on `orion-project`
2. Click "Terminal" tab
3. Run: `git pull`
4. Click "Restart" button
5. Dockge will rebuild and restart automatically

Or use the UI:
1. Click "Actions" → "Pull" (if using Git integration)
2. Click "Rebuild" → "Restart"

### Stop/Start
- Click the stack name
- Use Start/Stop/Restart buttons

### View Stats
- CPU usage
- Memory usage
- Network traffic
- All visible in real-time

## Backup Your Data

### Using Docker Commands

```bash
# Backup database
docker run --rm \
  -v mysite_orion-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/orion-backup-$(date +%Y%m%d).tar.gz /data

# Restore database
docker run --rm \
  -v mysite_orion-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/orion-backup-YYYYMMDD.tar.gz -C /
```

### Using Dockge

1. Go to stack settings
2. Click "Volumes"
3. View volume locations
4. Use standard backup tools to backup volume directories

## Reverse Proxy Setup (Optional but Recommended)

If you want to access via domain name with SSL:

### Using Traefik with Dockge

1. **Deploy Traefik in Dockge** (separate stack)

2. **Update orion-project docker-compose.yml** - uncomment Traefik labels:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.orion.rule=Host(`orion.yourdomain.com`)"
  - "traefik.http.routers.orion.entrypoints=websecure"
  - "traefik.http.routers.orion.tls.certresolver=letsencrypt"
  - "traefik.http.services.orion.loadbalancer.server.port=5000"
```

3. **Redeploy in Dockge**

## Troubleshooting in Dockge

### Container Won't Start
1. Check logs in "Logs" tab
2. Verify environment variables
3. Check if port 5000 is available

### Out of Memory (OrangePi has limited RAM)
1. Reduce Gunicorn workers in Dockerfile:
   ```dockerfile
   CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "site01.app:app"]
   ```
2. Rebuild in Dockge

### Permission Errors
```bash
# In Dockge terminal for orion-project:
docker-compose exec orion-web chown -R root:root /app/data
```

## Performance Tips for OrangePi

1. **Limit Resources** - Add to docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 512M
   ```

2. **Use Docker Buildx Cache** - Speeds up rebuilds

3. **Monitor with Dockge** - Watch resource usage

## Security Checklist

- [ ] Change SECRET_KEY from default
- [ ] Configure firewall (ufw) to only allow necessary ports
- [ ] Use strong passwords for Dockge
- [ ] Enable SSL/TLS with reverse proxy
- [ ] Regular backups of data volume
- [ ] Keep Docker and Dockge updated

## Updates

### Automatic Updates (Recommended)

Set up a cron job on OrangePi:

```bash
# Edit crontab
crontab -e

# Add this line to check for updates daily at 2 AM
0 2 * * * cd /opt/stacks/orion-project && git pull && docker-compose up -d --build
```

### Manual Updates via Dockge

1. Click stack → Terminal
2. Run: `git pull`
3. Click "Restart"

## Getting Help

- Check logs in Dockge "Logs" tab
- Review documentation in `site01/docs/`
- Check GitHub issues

---

**Enjoy your self-hosted Orion Project! 🎯**
