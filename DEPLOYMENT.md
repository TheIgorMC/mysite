# 🚀 Complete Deployment Guide for OrangePi

This guide will walk you through deploying the Orion Project on your OrangePi using Docker and Dockge.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Preparation](#preparation)
3. [Deployment Methods](#deployment-methods)
4. [Post-Deployment](#post-deployment)
5. [Maintenance](#maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### On Your OrangePi:

1. **Operating System**: Linux (Ubuntu/Debian/Armbian recommended)
2. **Docker**: Version 20.10 or higher
3. **Docker Compose**: Version 2.0 or higher
4. **Git**: For cloning the repository
5. **Minimum Resources**:
   - 1GB RAM (2GB recommended)
   - 5GB free disk space
   - ARM processor (OrangePi)

### Check if Docker is installed:

```bash
docker --version
docker-compose --version
```

### Install Docker if needed:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
# Or run: newgrp docker

# Verify installation
docker run hello-world
```

---

## Preparation

### Step 1: Prepare Your Repository

Before deploying, make sure you've:

1. **Created the repository on GitHub**:
   ```bash
   # On your development machine
   cd mysite
   git init
   git add .
   git commit -m "Initial commit - Orion Project"
   git branch -M main
   git remote add origin https://github.com/TheIgorMC/mysite.git
   git push -u origin main
   ```

2. **Set repository to private** (initially for safety):
   - Go to GitHub → Repository Settings → Danger Zone
   - Click "Change visibility" → "Make private"
   - You can make it public later after reviewing for sensitive data

### Step 2: Prepare Credentials

You'll need:

1. **SECRET_KEY**: Generate on OrangePi or locally:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Cloudflare Access Credentials** (if using):
   - Client ID
   - Client Secret

3. **Email Credentials** (if using newsletter feature):
   - SMTP server, port, username, password

**💡 Keep these in a secure note app - you'll need them!**

---

## Deployment Methods

Choose the method that works best for you:

### 🌟 Method 1: Using Dockge (Recommended - Easiest!)

Perfect for ongoing management with a nice UI.

#### Step 1: Install Dockge

```bash
# Create directory
sudo mkdir -p /opt/dockge /opt/stacks
cd /opt/dockge

# Create Dockge docker-compose.yml
sudo tee docker-compose.yml > /dev/null << 'EOF'
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
sudo docker-compose up -d

# Check if running
sudo docker-compose ps
```

#### Step 2: Access Dockge

- Open browser: `http://your-orangepi-ip:5001`
- Create admin account (first time)
- You'll see the Dockge dashboard

#### Step 3: Deploy Orion Project

**Option A: Using Git Integration**

1. Click "+ Compose" button
2. Select "Clone from Git"
3. Fill in:
   - **Repository URL**: `https://github.com/TheIgorMC/mysite.git`
   - **Branch**: `main`
   - **Stack Name**: `orion-project`
4. Click "Clone"
5. After cloning completes, click on the stack
6. Go to "Environment Variables" tab
7. Add your variables:
   ```
   SECRET_KEY=<your-generated-key>
   CF_ACCESS_CLIENT_ID=<your-id>
   CF_ACCESS_CLIENT_SECRET=<your-secret>
   ```
8. Click "Deploy" button
9. Watch the logs as it builds and starts!

**Option B: Manual Clone**

```bash
# Clone to stacks directory
cd /opt/stacks
sudo git clone https://github.com/TheIgorMC/mysite.git orion-project
cd orion-project

# Create .env file
sudo cp .env.example .env
sudo nano .env  # Edit with your values
```

Then in Dockge UI:
1. The stack appears automatically
2. Click on it
3. Click "Deploy"

#### Step 4: Verify Deployment

- Check logs in Dockge
- Access application: `http://your-orangepi-ip:5000`

---

### 📦 Method 2: Docker Compose Only (No Dockge)

If you prefer command-line management.

#### Step 1: Clone Repository

```bash
cd ~
git clone https://github.com/TheIgorMC/mysite.git
cd mysite
```

#### Step 2: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Edit .env file
nano .env
```

Paste your SECRET_KEY and other credentials.

#### Step 3: Deploy

```bash
# Build and start
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Step 4: Verify

- Access: `http://your-orangepi-ip:5000`
- Check logs: `docker-compose logs`

---

### ⚡ Method 3: Quick Setup Script

Use the provided setup script for automated deployment.

```bash
# Clone repository
git clone https://github.com/TheIgorMC/mysite.git
cd mysite

# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

The script will:
1. Check Docker installation
2. Create `.env` file
3. Generate SECRET_KEY automatically
4. Build and start containers
5. Show access URLs

**Note**: You'll still need to add Cloudflare credentials manually to `.env` after running the script.

---

## Post-Deployment

### 1. Test the Application

Visit `http://your-orangepi-ip:5000` and verify:

- [ ] Homepage loads correctly
- [ ] Dark/Light theme toggle works
- [ ] Language switching works (IT/EN)
- [ ] Archery analysis page loads
- [ ] No console errors (F12)

### 2. Create Admin User

If your app has user management:

```bash
# Access container
docker-compose exec orion-web bash

# Create admin (if you have a management script)
python -m flask create-admin
```

### 3. Configure Firewall (Recommended)

```bash
# Install ufw if not present
sudo apt install ufw -y

# Allow SSH (IMPORTANT! Don't lock yourself out!)
sudo ufw allow 22/tcp

# Allow Orion Project
sudo ufw allow 5000/tcp

# Allow Dockge (if using)
sudo ufw allow 5001/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 4. Set Up Reverse Proxy with SSL (Optional but Recommended)

For production with domain name and HTTPS.

#### Using Caddy (Easiest for SSL):

```bash
# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Create Caddyfile
sudo tee /etc/caddy/Caddyfile > /dev/null << 'EOF'
orion.yourdomain.com {
    reverse_proxy localhost:5000
}
EOF

# Restart Caddy
sudo systemctl restart caddy
```

Now access via: `https://orion.yourdomain.com`

---

## Maintenance

### Viewing Logs

**With Dockge:**
- Click on stack → "Logs" tab

**With Docker Compose:**
```bash
cd ~/mysite
docker-compose logs -f
```

### Updating the Application

**With Dockge:**
1. Click stack → "Terminal" tab
2. Run: `git pull`
3. Click "Restart" button

**With Docker Compose:**
```bash
cd ~/mysite
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backing Up Data

```bash
# Backup database and data
docker run --rm \
  -v mysite_orion-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/orion-backup-$(date +%Y%m%d).tar.gz /data

# Store backup safely
cp orion-backup-*.tar.gz /path/to/safe/location/
```

### Restoring from Backup

```bash
# Stop application
docker-compose down

# Restore data
docker run --rm \
  -v mysite_orion-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/orion-backup-YYYYMMDD.tar.gz -C /

# Start application
docker-compose up -d
```

### Automated Backups

Add to crontab:

```bash
crontab -e

# Add this line for daily backups at 3 AM
0 3 * * * cd /opt/stacks/orion-project && docker run --rm -v mysite_orion-data:/data -v $(pwd):/backup alpine tar czf /backup/backup-$(date +\%Y\%m\%d).tar.gz /data
```

---

## Troubleshooting

### Issue: Port 5000 Already in Use

```bash
# Find what's using port 5000
sudo lsof -i :5000

# Kill the process or change port in docker-compose.yml
ports:
  - "5050:5000"  # Change to 5050 or any free port
```

### Issue: Out of Memory

OrangePi has limited RAM. Reduce workers:

Edit `Dockerfile`:
```dockerfile
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "site01.app:app"]
```

Rebuild:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Container Keeps Restarting

```bash
# Check logs
docker-compose logs

# Common causes:
# 1. Missing SECRET_KEY in .env
# 2. Port conflict
# 3. Permission issues on volumes
```

### Issue: Cannot Access from Outside Network

1. Check firewall: `sudo ufw status`
2. Check if container is running: `docker-compose ps`
3. Check OrangePi IP: `hostname -I`
4. Test locally first: `curl http://localhost:5000`

### Issue: SSL Certificate Problems (Cloudflare Access)

```bash
# Update CA certificates
sudo apt update
sudo apt install ca-certificates -y
sudo update-ca-certificates

# Rebuild container
docker-compose build --no-cache
docker-compose up -d
```

---

## Performance Optimization for OrangePi

### 1. Limit Container Resources

Add to `docker-compose.yml`:

```yaml
services:
  orion-web:
    # ... existing configuration ...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 512M
        reservations:
          memory: 256M
```

### 2. Enable Swap (if needed)

```bash
# Check current swap
free -h

# Create 2GB swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 3. Use Docker Buildx Cache

Speeds up rebuilds:

```bash
docker buildx create --use
docker buildx build --cache-from type=local,src=/tmp/buildx-cache --cache-to type=local,dest=/tmp/buildx-cache -t orion-project .
```

---

## Security Checklist

Before going to production:

- [ ] Change `SECRET_KEY` from default
- [ ] Use strong password for Dockge admin
- [ ] Configure firewall (ufw)
- [ ] Set up SSL/TLS with reverse proxy
- [ ] Regular backups configured
- [ ] Keep Docker updated: `sudo apt update && sudo apt upgrade`
- [ ] Monitor logs regularly
- [ ] Restrict SSH access (key-based auth only)
- [ ] Set `SESSION_COOKIE_SECURE=true` in .env (requires HTTPS)

---

## Getting Help

1. **Check Documentation**: `site01/docs/INDEX.md`
2. **View Logs**: Most issues show up in logs
3. **GitHub Issues**: Open an issue with:
   - Error logs
   - Steps to reproduce
   - OrangePi model and OS version

---

## Quick Reference

### Start Application
```bash
docker-compose up -d
```

### Stop Application
```bash
docker-compose down
```

### Restart Application
```bash
docker-compose restart
```

### View Logs
```bash
docker-compose logs -f
```

### Update Application
```bash
git pull && docker-compose build && docker-compose up -d
```

### Access Container Shell
```bash
docker-compose exec orion-web bash
```

### Check Container Status
```bash
docker-compose ps
```

---

**You're all set! Enjoy your self-hosted Orion Project! 🎯🚀**
