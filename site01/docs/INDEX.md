# Documentation Index

Welcome to the Orion Project documentation! All documentation has been organized by category for easy navigation.

## 📚 Quick Navigation

### 🚀 Getting Started
- **[Main README](../../README.md)** - Project overview and quick links
- **[Setup Guides](setup/)** - Installation, environment configuration, admin setup
  - [Quickstart Guide](setup/QUICKSTART.md)
  - [Setup Guide](setup/SETUP_GUIDE.md)
  - [Environment Guide](setup/ENV_GUIDE.md)
  - [Admin Setup](setup/ADMIN_SETUP.md)

### 🐳 Deployment & Operations
- **[Deployment](deployment/)** - Docker setup, deployment procedures, recovery guides
  - [Deployment Guide](deployment/DEPLOYMENT.md)
  - [Dockge Setup](deployment/DOCKGE_SETUP.md)
  - [Docker Database Guide](deployment/DOCKER_DATABASE_GUIDE.md)
  - [Database Recovery](deployment/DATABASE_RECOVERY.md)
  - [Emergency Rebuild](deployment/EMERGENCY_REBUILD.md)
  - [Force Rebuild](deployment/FORCE_REBUILD.md)
  - [Rebuild Guide](deployment/REBUILD.md)
  - [Deployment Checklist](deployment/CHECKLIST.md)

### 🔧 Troubleshooting
- **[Troubleshooting](troubleshooting/)** - Common issues and solutions
  - [General Troubleshooting](troubleshooting/TROUBLESHOOTING.md)
  - [Image Troubleshooting](troubleshooting/IMAGE_TROUBLESHOOTING.md)
  - [Cache Issues](troubleshooting/CACHE_TROUBLESHOOTING.md)
  - [Anti-Cache Update](troubleshooting/ANTI_CACHE_UPDATE.md)
  - [Critical Fixes Needed](troubleshooting/CRITICAL_FIXES_NEEDED.md)

### 🏗️ Architecture & Design
- [System Architecture](ARCHITECTURE.md) - Overall system design
- [Project Overview](OVERVIEW.md) - High-level overview
- [Project Summary](PROJECT_SUMMARY.md) - Complete project summary
- [File Index](FILE_INDEX.md) - Complete file structure reference
- [Project Specifications](specifications.md) - Original project requirements

### ✨ Features Documentation
- **[Features](features/)** - Feature-specific documentation and guides
  - [Archery Analysis Features](features/ARCHERY_ANALYSIS_FEATURES.md)
  - [Competition Class Feature](features/COMPETITION_CLASS_FEATURE.md)
  - [Statistics Features](features/STATISTICS_FEATURES.md)
  - [Statistics Quick Reference](features/STATISTICS_QUICK_REFERENCE.md)
  - [Statistics Enhancement Summary](features/STATISTICS_ENHANCEMENT_SUMMARY.md)
  - [Date Handling Guide](features/DATE_HANDLING_GUIDE.md)
  - [Date Fix Summary](features/FIX_SUMMARY_DATES.md)
  - [Loading States](features/loading-states.md)
  - [Mobile Improvements](features/MOBILE_IMPROVEMENTS.md)
  - [Notification Update](features/NOTIFICATION_UPDATE.md)
  - [Tags & Drag-Drop Features](features/FEATURES_TAGS_DRAGDROP.md)
  - [Internationalization](features/internationalization.md)
  - [i18n Testing](features/i18n-testing.md)
  - [i18n Summary](features/i18n-summary.md)
  
### 📝 Gallery & Blog System
- [Gallery Blog System](GALLERY_BLOG_SYSTEM.md) - Complete blog transformation guide
  - Full HTML blog posts with SEO-friendly URLs
  - PCB parallax backgrounds for electronics projects
  - WYSIWYG editor with HTML raw mode
  - Live preview in real-time
  - Gallery image management
  - Statistics tracking and reset
  
### 🔐 Authentication & Security
- [Password Reset Guide](PASSWORD_RESET_GUIDE.md) - User password management
  - Self-service password reset flow
  - Admin password management tools
  - Token-based security (24-hour expiration)

### 🏆 Competition & Athlete Management
- [Authorized Athletes Guide](AUTHORIZED_ATHLETES_GUIDE.md) - Athlete management
- [Locked Section Guide](LOCKED_SECTION_GUIDE.md) - Premium content access

### ⚙️ Electronics Portal
- [Electronics Portal](ELECTRONICS_PORTAL.md) - PCB management and production

### 🛍️ E-commerce Features
- [Product Variants](PRODUCT_VARIANTS.md) - Product variation system
- [Product Customization](PRODUCT_CUSTOMIZATION.md) - Customization options

### 🔌 API Documentation
- **[API](api/)** - API specifications and usage guides
  - [API Specification](api/APIspec.md)
  - [API Usage Guide](api/usage-guide.md)
  - [Competition API Spec](COMPETITION_API_SPEC.md)

### 🛠️ Utilities & Scripts
- **[Scripts](../../scripts/)** - Utility scripts for deployment, diagnostics, and maintenance
  - `check_deployment.sh` - Verify deployment status
  - `check_images.sh` - Validate images
  - `check_local_changes.ps1` - Check local modifications (PowerShell)
  - `diagnose_images.ps1` - Diagnose image issues (PowerShell)
  - `emergency-rebuild.sh` - Emergency rebuild procedure
  - `force_deploy.sh` - Force deployment
  - `force_update.sh` - Force update
  - `setup.sh` - Initial setup script

### 📖 Reference Guides
- [Quick Reference](QUICK_REFERENCE.md) - Quick command and feature reference
- [Admin Panel Guide](ADMIN_PANEL_GUIDE.md) - Admin interface documentation
- [Authorized Athletes Guide](AUTHORIZED_ATHLETES_GUIDE.md) - Athlete management
- [Automatic Migrations](AUTOMATIC_MIGRATIONS.md) - Database migration guide
- [Documentation Organization](DOCS_ORGANIZATION.md) - This documentation structure

### 📦 Examples
- **[Examples](examples/)** - Code examples and demonstrations

### 📜 Historical Documentation
- **[Archive](../../archive/)** - Historical fix documentation and temporal files
  - Contains 20+ archived documents from previous bug fixes and feature implementations
  - Preserved for reference but not needed for current development

## 🎯 Feature Highlights

### Gallery Blog System (Latest - Feb 2026)
Transform gallery projects into full blog posts with:
- **PCB Parallax Backgrounds**: Stunning scrolling effects for electronics projects
- **Dual Editor Modes**: WYSIWYG (Quill.js) + Raw HTML mode
- **Live Preview**: Real-time preview in Italian/English
- **Gallery Management**: Add/remove multiple images
- **Statistics**: View tracking with admin reset
- **SEO-Friendly**: Custom slugs and optimized URLs
- **Glassmorphism**: Semi-transparent boxes with backdrop blur
- **Mobile-First**: Fully responsive design

**Learn more:** [Gallery Blog System](GALLERY_BLOG_SYSTEM.md)

### Advanced Statistics
The system provides comprehensive statistics with:
- **Dual View**: Career statistics + Filtered period statistics
- **Comparison Mode**: Compare up to 5 athletes side-by-side
- **Dynamic Updates**: Auto-refresh when athletes added/removed
- **Flexible Filters**: Date range, competition type, category
- **Loading Indicators**: Visual feedback during API calls

**Learn more:** [Statistics Features](features/STATISTICS_FEATURES.md)

### Date Handling
Robust date processing ensuring:
- Support for multiple date formats
- Proper chronological ordering
- Accurate athlete comparisons
- Reliable statistics calculations

**Learn more:** [Date Handling Guide](features/date-handling.md)

### API Integration
Secure integration with Orion API via:
- Cloudflare Access authentication
- HTTPS connection (api.orion-project.it:443)
- CSV-based local filtering
- Proper error handling
- Loading states for all API calls

**Learn more:** [API Usage Guide](api/usage-guide.md)

## 📖 Documentation by Role

### For Developers
1. Start with [System Architecture](ARCHITECTURE.md)
2. Review [API Usage Guide](api/usage-guide.md)
3. Understand [Date Handling](features/date-handling.md)
4. Check [File Index](FILE_INDEX.md) for code structure

### For Users/Athletes
1. Start with [Quick Start](QUICK_START.txt)
2. Use [Statistics Quick Reference](features/statistics-quick-reference.md)
3. Learn about [Archery Analysis Features](ARCHERY_ANALYSIS_FEATURES.md)

### For Administrators
1. Follow [Setup Guide](SETUP_GUIDE.md)
2. Review [Project Summary](PROJECT_SUMMARY.md)
3. Understand [System Architecture](ARCHITECTURE.md)

## 📁 Folder Structure

```
docs/
├── INDEX.md (this file)    # Documentation navigation
├── README.md               # Main project README
├── features/               # Feature documentation
│   ├── statistics.md
│   ├── statistics-quick-reference.md
│   ├── statistics-summary.md
│   ├── date-handling.md
│   └── date-fix-summary.md
├── api/                    # API documentation
│   ├── usage-guide.md
│   └── spec.json
├── examples/               # Code examples (future)
└── *.md                    # General documentation

Root docs (general):
├── OVERVIEW.md
├── PROJECT_SUMMARY.md
├── ARCHITECTURE.md
├── SETUP_GUIDE.md
├── FILE_INDEX.md
└── specifications.md
```

## 🚀 Recent Updates

### Gallery Blog System (February 2026)
- ✅ Complete blog post transformation for gallery projects
- ✅ PCB parallax scrolling backgrounds (inverted movement, fit-to-width)
- ✅ WYSIWYG editor with HTML raw mode toggle
- ✅ Live preview with Italian/English switch
- ✅ Gallery image management (multiple upload, individual removal)
- ✅ Statistics tracking with admin reset button
- ✅ Glassmorphism design (semi-transparent boxes)
- ✅ Mobile-responsive with adaptive layouts
- ✅ SEO-friendly slugs and URLs

### Password Reset System (January 2026)
- ✅ Self-service password reset for users
- ✅ Admin tools for password management
- ✅ Email-based token system (24-hour expiration)
- ✅ Unified user management page
- ✅ Improved UI clarity for reset buttons

### Statistics Enhancement & Loading States
- ✅ Career vs Filtered statistics view
- ✅ Multi-athlete comparison (up to 5)
- ✅ Dynamic auto-refresh on athlete changes
- ✅ **Loading indicators for all API calls**
- ✅ Visual feedback during data fetch
- ✅ Improved UX with loading states

### Date Handling Improvements
- ✅ Multiple date format support
- ✅ Unified timeline for comparisons
- ✅ Proper chronological sorting
- ✅ Italian date display format

## 🔗 External Resources

- **API Endpoint**: https://api.orion-project.it:443
- **FITARCO Results**: https://www.fitarco-italia.org/
- **GitHub Repository**: https://github.com/TheIgorMC

## 📝 Contributing to Documentation

When adding new documentation:
1. Place feature docs in `features/`
2. Place API docs in `api/`
3. Place examples in `examples/`
4. Update this INDEX.md with links
5. Use clear headings and examples
6. Include code snippets where helpful

## ❓ Need Help?

- Check [Quick Start](QUICK_START.txt) for immediate help
- Review [Statistics Quick Reference](features/statistics-quick-reference.md) for usage
- See [Setup Guide](SETUP_GUIDE.md) for installation issues
- Consult [API Usage Guide](api/usage-guide.md) for API problems

## 📄 License & Copyright

Orion Project © 2024-2025
