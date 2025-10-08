# 📋 Pre-Deployment Checklist

Use this checklist before pushing to GitHub and deploying to your OrangePi.

## 🔒 Security & Secrets

- [ ] Remove any hardcoded API keys or passwords from code
- [ ] Check `.env.example` - no real secrets, only placeholders
- [ ] Verify `.gitignore` excludes `.env` file
- [ ] Verify `.gitignore` excludes database files (`*.db`, `*.sqlite`)
- [ ] Check for any TODO comments with sensitive info
- [ ] Review all configuration files for sensitive data

## 📁 Files to Review Before Push

- [ ] `site01/app/config.py` - No hardcoded secrets
- [ ] `site01/app/__init__.py` - No development keys
- [ ] `docker-compose.yml` - Uses environment variables
- [ ] `.env.example` - Only example values
- [ ] `README.md` - Instructions are clear

## 🧪 Testing

- [ ] Application runs locally with Docker
- [ ] Translation system works (EN/IT switching)
- [ ] Dark/Light theme switching works
- [ ] All archery analysis features work
- [ ] No console errors in browser (F12)
- [ ] Database operations work
- [ ] Charts render correctly

## 📦 Docker Configuration

- [ ] `Dockerfile` exists and is optimized
- [ ] `docker-compose.yml` exists
- [ ] `.dockerignore` excludes unnecessary files
- [ ] Health check configured
- [ ] Volumes defined for data persistence
- [ ] Environment variables properly set

## 📚 Documentation

- [ ] `README.md` is complete and accurate
- [ ] `DEPLOYMENT.md` has deployment instructions
- [ ] `DOCKGE_SETUP.md` has Dockge-specific guide
- [ ] `.env.example` has all required variables
- [ ] `setup.sh` script is executable

## 🔧 Configuration Files

- [ ] `requirements.txt` has all dependencies
- [ ] `translations/en.json` is complete
- [ ] `translations/it.json` is complete
- [ ] All static files are committed
- [ ] Templates are complete

## 🚀 Pre-Push Actions

```bash
# 1. Test Docker build locally
docker-compose build

# 2. Test running locally
docker-compose up -d
docker-compose logs -f

# 3. Test accessing the app
curl http://localhost:5000

# 4. Stop containers
docker-compose down

# 5. Check git status
git status

# 6. Review what will be committed
git diff

# 7. Commit and push
git add .
git commit -m "Ready for deployment"
git push origin main
```

## 📤 Deployment Steps

After pushing to GitHub:

1. [ ] SSH into OrangePi
2. [ ] Follow DEPLOYMENT.md instructions
3. [ ] Clone repository
4. [ ] Create `.env` with real values
5. [ ] Generate SECRET_KEY
6. [ ] Add Cloudflare credentials
7. [ ] Deploy with Dockge or docker-compose
8. [ ] Test application
9. [ ] Check logs for errors
10. [ ] Verify all features work

## ✅ Post-Deployment Verification

- [ ] Application accessible at `http://orangepi-ip:5000`
- [ ] Homepage loads correctly
- [ ] Language switching works
- [ ] Theme switching works
- [ ] Archery analysis works
- [ ] No errors in logs
- [ ] Database persists after restart
- [ ] Health check passes

## 🔐 Security Hardening (Production)

- [ ] Change SECRET_KEY from example
- [ ] Configure firewall (ufw)
- [ ] Set up reverse proxy with SSL
- [ ] Enable rate limiting
- [ ] Configure secure session cookies
- [ ] Regular backups configured
- [ ] Monitor logs for suspicious activity

## 📊 Monitoring Setup

- [ ] Set up log rotation
- [ ] Configure backup cron job
- [ ] Set up uptime monitoring (optional)
- [ ] Configure alerts for errors (optional)

## 🎯 Final Check

```bash
# On OrangePi after deployment:

# 1. Check container is running
docker-compose ps

# 2. Check logs for errors
docker-compose logs --tail=50

# 3. Test endpoints
curl http://localhost:5000
curl http://localhost:5000/archery

# 4. Check resources
docker stats --no-stream

# 5. Verify data persistence
docker volume ls | grep orion
```

---

## ⚠️ Important Notes

1. **Never commit `.env` with real secrets!**
2. **Always use `.env.example` with placeholder values**
3. **Test locally before deploying to production**
4. **Backup data before major updates**
5. **Keep Docker and system updated**

---

## 🆘 If Something Goes Wrong

### Rollback Plan

```bash
# Stop current deployment
docker-compose down

# Restore from backup
docker run --rm \
  -v mysite_orion-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/orion-backup-YYYYMMDD.tar.gz -C /

# Revert to previous version
git checkout <previous-commit>
docker-compose up -d
```

### Emergency Contacts

- GitHub Issues: https://github.com/TheIgorMC/mysite/issues
- Documentation: `site01/docs/INDEX.md`

---

**Ready to deploy? Double-check everything, then go for it! 🚀**
