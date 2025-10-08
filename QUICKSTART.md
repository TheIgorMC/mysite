# 🚀 Quick Start - 5 Minutes to Deploy

## On Your OrangePi

### Step 1: Clone Repository
```bash
git clone https://github.com/TheIgorMC/mysite.git
cd mysite
```

### Step 2: Create .env File
```bash
cp .env.example .env
```

### Step 3: Generate Secret Key
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output.

### Step 4: Edit .env
```bash
nano .env
```
Replace `your-secret-key-here-change-this` with the key you generated.

### Step 5: Deploy
```bash
docker-compose up -d
```

### Step 6: Access
Open browser to: `http://your-orangepi-ip:5000`

---

## That's It! 🎉

### Useful Commands:

```bash
# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Update application
git pull && docker-compose up -d --build
```

### Need More Details?

- **Full Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Dockge Setup**: See [DOCKGE_SETUP.md](DOCKGE_SETUP.md)
- **Checklist**: See [CHECKLIST.md](CHECKLIST.md)
- **Documentation**: See `site01/docs/INDEX.md`

---

**Enjoy! 🎯**
