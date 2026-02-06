# 📁 Documentation Organization

## Root Directory
**Purpose:** Initial setup and deployment guides

Files in root:
- `README.md` - Main project readme
- `DEPLOYMENT.md` - Full deployment guide
- `DOCKGE_SETUP.md` - Dockge-specific setup
- `QUICKSTART.md` - 5-minute quick start
- `CHECKLIST.md` - Pre-deployment checklist
- `emergency-rebuild.sh` - Emergency rebuild script

## site01/docs/
**Purpose:** Technical documentation, troubleshooting, and feature guides

### Deployment & Troubleshooting
- `TROUBLESHOOTING.md` - Complete debugging guide
- `FORCE_REBUILD.md` - Force rebuilds in Dockge
- `EMERGENCY_REBUILD.md` - Manual rebuild via SSH
- `REBUILD.md` - Quick rebuild reference
- `IMPORT_FIX.md` - Config import fix
- `FIX_SUMMARY.md` - Complete fix summary
- `URGENT_FIX.md` - Naming conflict fix

### Technical Documentation
- `INDEX.md` - Documentation index
- `ARCHITECTURE.md` - System architecture
- `IMPLEMENTATION_SUMMARY.md` - Latest updates
- `PROJECT_SUMMARY.md` - Project overview
- `OVERVIEW.md` - High-level overview
- `SETUP_GUIDE.md` - Development setup
- `FILE_INDEX.md` - File structure
- `GALLERY_BLOG_SYSTEM.md` - Gallery blog feature (Feb 2026)
- `PASSWORD_RESET_GUIDE.md` - Password reset system (Jan 2026)
- `ADMIN_PANEL_GUIDE.md` - Admin interface guide
- `AUTHORIZED_ATHLETES_GUIDE.md` - Athlete management
- `AUTOMATIC_MIGRATIONS.md` - Database migrations

### Features
- `features/` - Feature-specific docs
  - `STATISTICS_FEATURES.md`
  - `DATE_HANDLING_GUIDE.md`
  - `loading-states.md`
  - `internationalization.md`
  - `MOBILE_IMPROVEMENTS.md`
  - `NOTIFICATION_UPDATE.md`

### API
- `api/` - API documentation
  - `usage-guide.md`
  - `spec.json`

---

## Quick Access

**Need to deploy?** Start with root:
- `QUICKSTART.md` → `DEPLOYMENT.md` → `DOCKGE_SETUP.md`

**Having issues?** Go to site01/docs:
- `TROUBLESHOOTING.md` → `FORCE_REBUILD.md` → `EMERGENCY_REBUILD.md`

**Development?** Check site01/docs:
- `INDEX.md` → `features/` → `api/`
