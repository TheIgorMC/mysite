# 🎯 Orion Project

**Passione, Precisione, Innovazione** - A comprehensive platform for archery analysis, 3D printing projects, and electronics.

## 📚 Documentation

All documentation has been organized in `site01/docs/` for easy navigation:

- **[Setup Guides](site01/docs/setup/)** - Installation, environment configuration, admin setup
- **[Deployment](site01/docs/deployment/)** - Docker setup, deployment procedures, recovery guides
- **[API Documentation](site01/docs/api/)** - API specifications and usage guides
- **[Features](site01/docs/features/)** - Feature-specific documentation and guides
- **[Troubleshooting](site01/docs/troubleshooting/)** - Common issues and solutions
- **[Scripts](scripts/)** - Utility scripts for deployment, diagnostics, and maintenance

For a complete overview, see [site01/docs/INDEX.md](site01/docs/INDEX.md).

## Features

### 🏹 Archery Analysis
- Performance tracking and statistics
- Multi-athlete comparison (up to 5 athletes) with side-by-side comparison table
- Dual statistics view: career vs. filtered (date/type/category)
- Dynamic auto-refresh when athletes are added or removed
- Competition results visualization with Chart.js (zoom and pan on mobile/desktop)
- Support for multiple competition types and categories
- Date range filtering
- Average per arrow calculations

### 🏆 Competition & Athlete Management
- Club member competition portal (ASD Compagnia Arcieri Carraresi)
- Three competition states: active subscriptions, invite published, interest registration
- Turn selection with notes
- Authorized athletes system: admins assign athletes to users for multi-athlete registration
- Admin panel (`/admin/manage-athletes`) for athlete–user assignment with real-time search
- Locked section access control: a third authorization layer above login and role checks

### 🖨️ 3D Printing
- Full blog-style project gallery with SEO-friendly slugs
- Rich HTML/Markdown content per project with WYSIWYG + raw HTML editor
- Live preview in admin editor
- Gallery image management (add/remove)
- View count statistics with admin reset
- Related projects shown automatically
- Custom model requests
- Integration with Printables

### ⚡ Electronics
- Blog-style project gallery with PCB parallax background effect (scrolling PCB artwork)
- Full electronics management portal (admin-only):
  - Component inventory with smart search (e.g., "R0402" finds all 0402 resistors)
  - PCB board and BOM management (upload, view, export CSV)
  - Production job tracking with real-time stock checking
  - Shopping list generation for missing components
  - File manager with Interactive BOM (iBOM) viewer
- Custom circuit services

### 🛒 Shop
- Multi-category product grid (Archery, 3D Printing, Electronics)
- Product variants system (length, material, color, etc.) with per-variant pricing and stock
- Product customization options
- Cart synced to localStorage with toast notifications (no more `alert()` popups)
- Mobile-optimized category filter (dropdown on small screens, buttons on desktop)
- Stock management per variant

### 🔐 Authentication & Security
- Login / registration with role-based access (admin, club member, regular user)
- Self-service password reset via email (token expires in 24 hours)
- Admin password management: send reset email or set password directly
- Locked section access control for highly sensitive areas
- Password hashing, remember me, session security

### 🌍 Internationalization
- Full bilingual support (Italian/English)
- Dynamic language switching
- All UI elements, messages, and content translated (100+ keys)

### 🎨 UI/UX
- Dark mode with full support across all components (hamburger menu, nav links, modals)
- Toast notification system (success, error, warning, info) — replaces all browser `alert()` calls
- Animated, stackable toasts with auto-dismiss and manual close
- Responsive mobile improvements: image sizing, spacing, date inputs, chart zoom/pan
- Loading spinners with correct animation
- Glassmorphism card design

## Technology Stack

- **Backend**: Flask (Python), blueprint-based modular architecture
- **Frontend**: Tailwind CSS, Chart.js (with zoom/pan plugin), Vanilla JavaScript
- **Database**: SQLite (with SQLAlchemy ORM and migration scripts)
- **Authentication**: Flask-Login (roles: admin, club member, locked section)
- **API Integration**: Orion API with Cloudflare Access
- **Email**: SMTP-based password reset with token security
- **Deployment**: Docker + Docker Compose, compatible with Dockge

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- (Recommended) Dockge for easy management

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/TheIgorMC/mysite.git
   cd mysite
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your values
   ```

3. **Generate a secure secret key**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   # Copy the output to SECRET_KEY in .env
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   - Open your browser to `http://localhost:5000`
   - Or `http://your-server-ip:5000`

### Dockge Integration

This project is fully compatible with Dockge! Simply:

1. Add the repository URL in Dockge
2. It will automatically detect the `docker-compose.yml`
3. Configure environment variables in Dockge UI
4. Deploy with one click! 🎉

## Configuration

### Environment Variables

All configuration is done through environment variables. See `.env.example` for all options.

**Required:**
- `SECRET_KEY`: Flask secret key (generate a strong random key)

**Optional:**
- `CF_ACCESS_CLIENT_ID`: Cloudflare Access client ID
- `CF_ACCESS_CLIENT_SECRET`: Cloudflare Access client secret
- `MAIL_SERVER`: SMTP server for emails
- Database, API, and other settings

### Data Persistence

Data is stored in Docker volumes:
- `orion-data`: Database and user data
- `orion-logs`: Application logs

To backup your data:
```bash
docker run --rm -v mysite_orion-data:/data -v $(pwd):/backup alpine tar czf /backup/orion-backup.tar.gz /data
```

## Development

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export FLASK_APP=site01.app
   export FLASK_ENV=development
   export SECRET_KEY=dev-secret-key
   ```

4. **Run development server**
   ```bash
   flask run --debug
   ```

### Project Structure

```
mysite/
├── site01/              # Main application directory
│   ├── app/             # Flask application
│   │   ├── routes/      # Route handlers
│   │   │   ├── main.py          # Home, about, admin dashboard
│   │   │   ├── auth.py          # Login, register, password reset
│   │   │   ├── archery.py       # Analysis, competitions
│   │   │   ├── printing.py      # 3D printing gallery/blog
│   │   │   ├── electronics.py   # Electronics gallery/blog
│   │   │   ├── electronics_admin.py  # Electronics portal (admin)
│   │   │   ├── shop.py          # Shop and cart
│   │   │   ├── api.py           # Website-level API (athletes, newsletter)
│   │   │   ├── api_routes.py    # Internal utility APIs
│   │   │   ├── admin.py         # Admin tools
│   │   │   └── locked.py        # Locked section routes
│   │   ├── api/         # Cloudflare/Orion API client
│   │   ├── static/      # CSS, JS, images
│   │   ├── templates/   # Jinja2 templates
│   │   └── utils.py     # Translation and utility functions
│   ├── migrations/      # Database migration scripts
│   ├── translations/    # i18n translation files
│   │   ├── en.json      # English translations
│   │   └── it.json      # Italian translations
│   └── docs/            # Documentation
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Documentation

Comprehensive documentation is available in the `site01/docs/` directory:

### 📖 Essential Guides
- **[Documentation Index](site01/docs/INDEX.md)** - Navigation to all docs
- **[Project Overview](site01/docs/OVERVIEW.md)** - High-level overview
- **[Architecture](site01/docs/ARCHITECTURE.md)** - System design diagrams
- **[Troubleshooting](site01/docs/troubleshooting/TROUBLESHOOTING.md)** - Complete debugging guide

### 🚀 Deployment
- **[Quick Start](site01/docs/setup/QUICKSTART.md)** - 5-minute deployment guide
- **[Deployment Guide](site01/docs/deployment/DEPLOYMENT.md)** - Complete deployment instructions
- **[Dockge Setup](site01/docs/deployment/DOCKGE_SETUP.md)** - Dockge-specific guide
- **[Force Rebuild](site01/docs/deployment/FORCE_REBUILD.md)** - How to force rebuilds in Dockge
- **[Emergency Rebuild](site01/docs/deployment/EMERGENCY_REBUILD.md)** - Manual rebuild via SSH

### ✨ Features
- **[Archery Analysis Features](site01/docs/features/ARCHERY_ANALYSIS_FEATURES.md)**
- **[Statistics Enhancement Summary](site01/docs/features/STATISTICS_ENHANCEMENT_SUMMARY.md)**
- **[Gallery & Blog System](site01/docs/GALLERY_BLOG_SYSTEM.md)** - Blog posts, PCB parallax, WYSIWYG editor
- **[Electronics Portal](site01/docs/ELECTRONICS_PORTAL.md)** - Inventory, BOM, production jobs
- **[Authorized Athletes Guide](site01/docs/AUTHORIZED_ATHLETES_GUIDE.md)**
- **[Locked Section Guide](site01/docs/LOCKED_SECTION_GUIDE.md)** - Premium content access
- **[Password Reset Guide](site01/docs/PASSWORD_RESET_GUIDE.md)**
- **[Product Variants](site01/docs/PRODUCT_VARIANTS.md)**
- **[Internationalization](site01/docs/features/internationalization.md)**
- **[Mobile Improvements](site01/docs/features/MOBILE_IMPROVEMENTS.md)**

### 🔌 API Documentation
- **[API Specification](site01/docs/api/APIspec.md)**
- **[API Usage Guide](site01/docs/api/usage-guide.md)**
- **[Competition API Spec](site01/docs/COMPETITION_API_SPEC.md)**

## Security Considerations

### Before Production:
1. ✅ Change `SECRET_KEY` to a strong random value
2. ✅ Set `SESSION_COOKIE_SECURE=true` (requires HTTPS)
3. ✅ Configure proper firewall rules
4. ✅ Use a reverse proxy (nginx, Traefik) with SSL/TLS
5. ✅ Enable rate limiting for API endpoints
6. ✅ Review and restrict exposed ports
7. ✅ Regular backups of the data volume

### Recommended Setup:
```
Internet → Reverse Proxy (nginx/Traefik) → Docker Container
         ↓ SSL/TLS
         ↓ Rate Limiting
         ↓ Security Headers
```

## API Integration

The application integrates with the Orion API for archery data:
- **Endpoint**: `https://api.orion-project.it:443`
- **Authentication**: Cloudflare Access (optional)
- **Data**: Competition results, athlete statistics, categories

## Updating

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs -f

# Check container status
docker-compose ps
```

### Database issues
```bash
# Access container shell
docker-compose exec orion-web bash

# Check database
python -c "from site01.app import app, db; app.app_context().push(); print(db.engine.table_names())"
```

### Permission issues
```bash
# Fix volume permissions
docker-compose exec orion-web chown -R root:root /app/data
```

## Performance Optimization

For production on OrangePi:

1. **Adjust worker count** in docker-compose.yml:
   ```yaml
   command: gunicorn -w 2 -b 0.0.0.0:5000 site01.app:app
   ```
   (OrangePi has limited CPU, use 2-4 workers)

2. **Enable caching**:
   - Flask-Caching is included
   - Configure Redis for better performance (optional)

3. **Use reverse proxy**:
   - nginx or Traefik for static file serving
   - Reduces load on Flask application

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Your License Here]

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check documentation in `site01/docs/`

## Acknowledgments

- FITARCO for archery competition data
- Orion API for data integration
- Chart.js for visualization
- Tailwind CSS for styling

---

**Made with ❤️ and precision** 🎯
