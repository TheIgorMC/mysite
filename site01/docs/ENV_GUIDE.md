# 📝 Environment Variables Guide

## 🎯 IMPORTANT: Only ONE .env file!

The `.env` file should be in the **root directory** only:
```
mysite/
├── .env          ← HERE (create from .env.example)
├── .env.example  ← Template
└── site01/
    └── NO .env here!
```

---

## 🚀 Quick Setup

### 1. Create .env file
```bash
cp .env.example .env
```

### 2. Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste it in `.env` as `SECRET_KEY=...`

### 3. Add Your Cloudflare Credentials
Edit `.env` and replace:
```bash
CF_ACCESS_ID=your-actual-cf-access-id
CF_ACCESS_SECRET=your-actual-cf-access-secret
```

---

## 📋 Required Variables

### SECRET_KEY ⚠️ REQUIRED
```bash
SECRET_KEY=abc123...
```
**How to generate:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### CF_ACCESS_ID and CF_ACCESS_SECRET ⚠️ REQUIRED for API
```bash
CF_ACCESS_ID=e300e6d3df61da308babde201af291a8.access
CF_ACCESS_SECRET=6500bd7bb91bd6f2314dee9a0c03d52529605290dee104fe221433795b14bfc8
```
Get these from Cloudflare Access dashboard for api.orion-project.it

---

## 📋 Optional Variables

### API Configuration
```bash
API_BASE_URL=https://api.orion-project.it
API_PORT=443
```
Default values are already correct. Only change if API endpoint changes.

### Database
```bash
DATABASE_URL=sqlite:////app/data/orion.db
```
Default uses Docker volume. Don't change unless using external database.

### Language
```bash
DEFAULT_LANGUAGE=it
```
Options: `it` (Italian) or `en` (English)

### Email (for newsletters, contact form)
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_USE_TLS=true
```

---

## 🔍 Variable Name Reference

**IMPORTANT:** The variable names MUST match what's in `site01/config.py`

| .env Variable | Used By | Purpose |
|--------------|---------|---------|
| `SECRET_KEY` | Flask | Session encryption |
| `API_BASE_URL` | config.py | Orion API endpoint |
| `API_PORT` | config.py | API port |
| `CF_ACCESS_ID` | config.py | Cloudflare Access ID |
| `CF_ACCESS_SECRET` | config.py | Cloudflare Access secret |
| `DATABASE_URL` | SQLAlchemy | Database location |
| `DEFAULT_LANGUAGE` | Flask | UI language |

---

## ⚠️ Common Mistakes

### ❌ Wrong Variable Names
Docker compose used to have:
```bash
# WRONG - config.py doesn't read these!
ORION_API_URL=...
CF_ACCESS_CLIENT_ID=...
CF_ACCESS_CLIENT_SECRET=...
```

**✅ Correct names** (match config.py):
```bash
API_BASE_URL=https://api.orion-project.it
API_PORT=443
CF_ACCESS_ID=...
CF_ACCESS_SECRET=...
```

### ❌ Multiple .env Files
```
mysite/
├── .env          ← Keep this one!
└── site01/
    └── .env      ← DELETE this!
```

Only have ONE `.env` in the root!

### ❌ Not Creating .env
Docker Compose reads `.env` automatically. If it doesn't exist:
- `${CF_ACCESS_ID}` → empty string
- API calls fail: "Connection refused"

**Solution:** Copy `.env.example` to `.env` and fill in values!

---

## 🐳 How Docker Uses .env

### Automatic Loading
Docker Compose automatically loads `.env` from the same directory:
```yaml
environment:
  - CF_ACCESS_ID=${CF_ACCESS_ID:-}
```
Reads `CF_ACCESS_ID` from `.env` file.

### In Container
Environment variables are available to the Flask app:
```python
# In site01/config.py
CF_ACCESS_ID = os.environ.get('CF_ACCESS_ID') or ''
```

---

## 🔒 Security

### Never Commit .env!
`.gitignore` already contains:
```
.env
.env.local
.env.*.local
```

### For OrangePi Deployment
1. Create `.env` on the OrangePi:
   ```bash
   cd /path/to/stack
   cp .env.example .env
   nano .env  # Edit with your values
   ```

2. Or copy from your local machine:
   ```bash
   scp .env user@orangepi:/path/to/stack/.env
   ```

---

## ✅ Verification

### Check if .env is loaded:
```bash
# In Dockge or via SSH
docker-compose config
```
Should show your actual values, not `${...}`

### Check in running container:
```bash
docker-compose exec orion-web env | grep API
```
Should show:
```
API_BASE_URL=https://api.orion-project.it
API_PORT=443
CF_ACCESS_ID=your-actual-id
CF_ACCESS_SECRET=your-actual-secret
```

---

## 📝 Complete .env Template

```bash
# Orion Project Environment Configuration

# REQUIRED: Flask secret key for session encryption
SECRET_KEY=generate-with-python-secrets-token-hex-32

# REQUIRED: Cloudflare Access credentials for API
CF_ACCESS_ID=your-cf-access-id
CF_ACCESS_SECRET=your-cf-access-secret

# Optional: API Configuration (defaults are fine)
API_BASE_URL=https://api.orion-project.it
API_PORT=443

# Optional: Database (default is correct for Docker)
DATABASE_URL=sqlite:////app/data/orion.db

# Optional: Default language
DEFAULT_LANGUAGE=it

# Optional: Email configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_USE_TLS=true
```

---

**Remember: ONE .env file in the root, variable names must match config.py!** 🎯
