# 🎯 Orion Project

**Passione, Precisione, Innovazione** — A comprehensive platform for archery analysis, 3D printing projects, and electronics, built to run on an OrangePi via Docker.

## 📚 Documentation

All documentation is organized in `site01/docs/` for easy navigation:

| Category | Path | Contents |
|---|---|---|
| Setup | [site01/docs/setup/](site01/docs/setup/) | Installation, env config, admin setup |
| Deployment | [site01/docs/deployment/](site01/docs/deployment/) | Docker, Dockge, recovery guides |
| API | [site01/docs/api/](site01/docs/api/) | API spec and usage guides |
| Features | [site01/docs/features/](site01/docs/features/) | Feature-specific documentation |
| Troubleshooting | [site01/docs/troubleshooting/](site01/docs/troubleshooting/) | Common issues and solutions |
| Scripts | [scripts/](scripts/) | Deployment, diagnostics, maintenance |

For the full navigation index see [site01/docs/INDEX.md](site01/docs/INDEX.md).

---

## Features

### 🏹 Archery Analysis

A full-featured analysis system that pulls data from the external Orion API and presents interactive statistics and charts.

**Athlete Search & Selection**
- Search athletes by name or membership card (*tessera*) number
- Add up to 5 athletes simultaneously for comparison
- Auto-refreshes results when athletes are added or removed

**Charts & Visualization**
- Interactive Chart.js line graphs for score history
- Zoom and pan support on both desktop and mobile (pinch-to-zoom)
- Toggle between total score and **average per arrow** view
- Filters: date range, macro category (indoor/outdoor), specific competition type

**Statistics — Single Athlete**
- Dual statistics view: **Career stats** (all-time) are always shown; **Filtered stats** appear as a separate highlighted section when any filter is active
- Career/Filtered stats include: total competitions, gold/silver/bronze medals, average position, average percentile, best score ever (with competition name)
- Category breakdown: separate best scores and averages for Indoor vs Outdoor

**Statistics — Multi-Athlete Comparison (2–5 athletes)**
- Side-by-side comparison table: competitions, medals (🥇🥈🥉), average position, best score
- Individual highlight cards for each athlete below the comparison table
- All filters apply simultaneously to every athlete in the comparison
- Automatically switches between single-detail and comparison-table mode

**Underlying Data**
- `app/data/competition_arrows.csv` — ~35 pre-populated competition types with arrow counts and max scores
- `app/archery_utils.py` — utility library for score calculations, medal counts, percentile analysis, and best-score-by-category

---

### 🏆 Competition & Athlete Management

For members of **ASD Compagnia Arcieri Carraresi** only (club member role required).

**Competition States**
Each competition on the portal is in one of three states:
1. **Interest Only** — invite not yet published; user can register interest
2. **Invite Published** — invite is live; user can select a turn and subscribe
3. **Active Subscription** — user already subscribed; subscription status visible (pending / confirmed / cancelled)

**Turn Selection**
- Turns (*turni*) are fetched live from the external API: turn number, day, gathering time, shooting start time
- User selects turn from a dropdown; optional notes field

**Authorized Athletes System**
- Each user can be authorized to manage one or more athletes (e.g., a parent managing a junior archer)
- When subscribing, a dropdown shows the user's authorized athletes; if only one is assigned it is auto-selected
- Competition class (CO — Compound, OL — Olympic/Recurve, AN — Barebow) and age category (GM, GF, RM, RF, AM, AF, JM, JF, SM, SF, MM, MF) are stored per athlete

**Locked Section Access Control**
A third authorization layer above login and role check:
```
Layer 1: @login_required        → user is logged in
Layer 2: role check             → admin / club member / regular
Layer 3: @locked_section_required → explicit grant by admin required
```
The `has_locked_section_access` boolean flag on the User model controls access. Defaults to `False` (deny by default).

---

### 🖨️ 3D Printing

**Project Gallery / Blog**
- Each project is a full blog post with bilingual content (Italian + English)
- SEO-friendly slugs (e.g., `/project/arduino-weather-station`)
- Content authored in a **WYSIWYG editor** with toggleable raw HTML mode and **live preview** in real time
- Gallery image management: add/remove images per project in the admin panel
- View count tracked per project; admin can reset counters
- Related projects are shown automatically (same category)
- Link to Printables or GitHub per project

**Database fields added to `gallery_items`:**
`content_it`, `content_en`, `slug` (unique), `pcb_background`, `updated_at`, `view_count`

---

### ⚡ Electronics

**Public Gallery**
- Blog-style project pages identical to 3D Printing above
- **PCB Parallax Effect**: for electronics projects with a `pcb_background` image set, the PCB artwork scrolls at a different rate than the page content, creating a depth effect

**Electronics Management Portal** (`/admin/electronics`, admin-only)

A 5-tab management interface backed by `app/routes/electronics_admin.py`:

| Tab | Feature |
|---|---|
| **Components** | Component inventory; smart search (e.g., "R0402" returns all 0402 resistors); type/package filters; add/edit/delete; color-coded stock badges (green >10, yellow 1–10, red 0) |
| **Boards & BOMs** | Create PCB boards (name, version, variant); upload BOM from CSV; view component list with stock status; export BOM to CSV; link files to boards |
| **Production Jobs** | Create jobs; assign multiple boards + quantities; real-time stock check per component (available/low/missing); reserve stock (deducts from inventory); generate shopping list for missing parts |
| **File Manager** | Register files from external nginx storage (`ELECTRONICS_STORAGE_URL`); supported types: BOM, Pick & Place, Gerber, Schematics, PCB layout, Interactive BOM (HTML) |
| **Stock Overview** | Analytics dashboard across all components |

The portal proxies requests to the external Orion API with Cloudflare Access authentication.

---

### 🛒 Shop

- Product grid with multi-category support (Archery, 3D Printing, Electronics)
- Products have bilingual names and descriptions (`name_it`/`name_en`, `description_it`/`description_en`)
- Tags for search and filtering
- Products can be linked to a gallery item (`gallery_item_id`)

**Product Variants**
- Each product can define a `variant_config` JSON field with one or more option axes:
  ```json
  {
    "length": { "type": "select", "options": ["66","68","70","72"], "unit": "inches", "label_en": "String Length", "label_it": "Lunghezza Corda" },
    "color":  { "type": "color",  "options": { "black": "#000000", "white": "#FFFFFF" } }
  }
  ```
- Each variant combination is stored in `product_variants` with its own `price_modifier`, `sku`, and `stock_quantity`
- Customization flags: `is_custom_string` (enables string customizer UI), `is_custom_print` (enables 3D print customizer UI)

**Cart**
- Persisted in `localStorage` under the key `shopping_cart`
- Stores full product data (id, name, price, image, description) for correct cart display
- All add-to-cart and error actions use the **toast notification system** — no `alert()` popups
- Category filter buttons on desktop become a full-width dropdown on mobile

---

### 🔐 Authentication & Security

**User Model fields:**
| Field | Type | Description |
|---|---|---|
| `username` | String(64) | Unique, indexed |
| `email` | String(120) | Unique, indexed |
| `is_admin` | Boolean | Full admin access |
| `is_club_member` | Boolean | Archery club member features |
| `has_locked_section_access` | Boolean | Locked section third-layer access |
| `preferred_language` | String(2) | `it` or `en` |
| `reset_token` | String(256) | Indexed, 24-hour expiry |
| `reset_token_expiry` | DateTime | Token expiry timestamp |

**Password Reset Flow (self-service):**
1. User clicks "Password Dimenticata?" on login page
2. Enters email → system generates `secrets.token_urlsafe(32)` token, stores hash + expiry
3. Reset link emailed via SMTP (`/auth/reset-password/<token>`)
4. Token expires after 24 hours; consumed after use

**Admin Password Management:**
- **Send reset email** — sends the standard reset email on behalf of admin
- **Set password directly** — admin sets a new password immediately (for users without email access); clears any pending reset tokens

**Session security:** `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE=Lax` enforced in production

---

### 🌍 Internationalization

- Full bilingual support: Italian (`it`) and English (`en`)
- Language preference stored in the `User.preferred_language` column; defaults to `it`
- Dynamic language switching in the navbar without page reload
- Translation files at `translations/it.json` and `translations/en.json` (100+ keys each)
- All templates, flash messages, API responses, and email content are translated

---

### 🛡️ Admin Panel

Accessible at `/admin` (admin role required).

| Route | Feature |
|---|---|
| `/admin` | Dashboard with quick-access cards to all tools |
| `/admin/users` | List all users sorted by registration date; manage roles and locked-section access |
| `/admin/users/<id>/force-reset-password` | Send password reset email to a specific user |
| `/admin/users/<id>/set-password` | Directly set a user's password (min. 6 chars) |
| `/admin/manage-athletes` | Assign/remove authorized athletes per user |
| `/admin/materials` | Manage stringmaking materials |
| `/admin/products` | Manage shop products and variants |
| `/admin/electronics` | Electronics portal (5-tab PCB/component management) |

**Manage Athletes UI (`/admin/manage-athletes`):**
- Left panel: search users by username or email; click to select
- Left panel: search athletes from Orion API by name or tessera (min 2 chars); already-assigned athletes are filtered out
- Class selection modal appears when adding an athlete (CO / OL / AN); pre-filled from API suggestion
- Right panel: shows selected user's authorized athletes with tessera, full name, category, class, birth date; trash icon with confirmation modal to remove
- All changes take effect in real time with toast notifications

**Gallery Admin (per project):**
- WYSIWYG editor (TinyMCE or similar) with raw HTML toggle
- Live preview pane updates in real time as you type
- Slug auto-generated from title; editable
- PCB background field (electronics only) for the parallax effect
- Image gallery manager: upload images, reorder, remove
- View count displayed with a reset button

---

### 🎨 UI/UX

**Dark Mode**
- Tailwind `dark:` classes applied throughout all components
- Hamburger menu icon and mobile nav links correctly visible in dark mode (`dark:text-white`, `dark:hover:text-blue-400`)
- Modals, dropdowns, and cards all support dark variants

**Toast Notification System**
- Replaces all `alert()`, `confirm()`, and flash-message patterns
- Four types: `success` (green), `error` (red), `warning` (yellow), `info` (blue)
- Slides in from the right; auto-dismisses after 3 seconds
- Manual close button (×); multiple toasts stack vertically
- Implemented in `static/js/main.js` via `showNotification(message, type)`
- Toast container injected into `base.html`; works on every page

**Mobile Improvements**
- Section images on home page: `h-64 md:h-80` (responsive height)
- About Me section: reduced padding and font sizes on small screens
- Shop category filter: horizontal buttons on desktop (`hidden md:inline-flex`) → full-width `<select>` on mobile (`md:hidden`)
- Date range inputs on analysis page: `flex` layout with a `-` separator instead of `grid-cols-2`
- Chart zoom/pan: pinch-to-zoom on mobile, scroll-to-zoom on desktop (Chart.js zoom plugin)
- Loading spinners: `@keyframes spin` animation added to `style.css` to fix broken spinners

**General Design**
- Glassmorphism card style
- Grayscale-to-color hover transitions on home page section images
- Smooth CSS transitions on all interactive elements

---

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3.0 (Python), blueprint-based modular architecture |
| Frontend | Tailwind CSS, Chart.js + zoom plugin, Vanilla JavaScript |
| Database | SQLite via SQLAlchemy ORM; incremental migration scripts in `migrations/` |
| Authentication | Flask-Login; roles: admin, club member, locked section; token-based password reset |
| Forms | Flask-WTF with CSRF protection |
| Images | Pillow for server-side image processing |
| Spreadsheets | openpyxl for BOM import/export |
| API Integration | Orion API (`https://api.orion-project.it:443`) via Cloudflare Access (CF_ACCESS_ID / CF_ACCESS_SECRET) |
| Email | SMTP via `MAIL_SERVER` env var; used for password reset |
| Deployment | Docker + Docker Compose; Gunicorn WSGI server; compatible with Dockge |
| Target Hardware | OrangePi (ARM); 2–4 Gunicorn workers recommended |

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
   - Exposed on host port **6080**, mapped to container port 5000
   - Open your browser to `http://localhost:6080` or `http://your-server-ip:6080`

### Dockge Integration

1. Add the repository URL in Dockge
2. It will automatically detect the `docker-compose.yml`
3. Configure environment variables in Dockge UI (see table below)
4. Deploy with one click!

> **Force a rebuild** in Dockge by incrementing `CACHE_BUST` in `docker-compose.yml` under `build.args`.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Flask session secret (generate with `secrets.token_hex(32)`) |
| `DATABASE_URL` | — | `sqlite:////app/data/orion.db` | SQLAlchemy database URI |
| `API_BASE_URL` | — | `https://api.orion-project.it` | Orion API base URL |
| `API_PORT` | — | `443` | Orion API port |
| `CF_ACCESS_ID` | — | — | Cloudflare Access client ID |
| `CF_ACCESS_SECRET` | — | — | Cloudflare Access client secret |
| `MAIL_SERVER` | — | — | SMTP server hostname |
| `MAIL_PORT` | — | `587` | SMTP port |
| `MAIL_USERNAME` | — | — | SMTP username |
| `MAIL_PASSWORD` | — | — | SMTP password |
| `MAIL_USE_TLS` | — | `true` | Enable STARTTLS |
| `DEFAULT_LANGUAGE` | — | `it` | Default UI language (`it` or `en`) |
| `SESSION_COOKIE_SECURE` | — | `true` | Requires HTTPS in production |
| `SESSION_COOKIE_HTTPONLY` | — | `true` | Prevents JS access to session cookie |
| `SESSION_COOKIE_SAMESITE` | — | `Lax` | CSRF protection level |
| `ELECTRONICS_STORAGE_URL` | — | `https://elec.orion-project.it` | External nginx file storage for electronics files |

### Docker Volumes

| Volume | Mount Point | Purpose |
|---|---|---|
| `orion-data` | `/app/data` | SQLite database |
| `orion-logs` | `/app/site01/logs` | Application logs |
| `orion-uploads` | `/app/site01/app/static/uploads` | User-uploaded images (gallery, products) |

### Backup

```bash
docker run --rm \
  -v mysite_orion-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/orion-backup.tar.gz /data
```

---

## Database Schema

The application uses 9 SQLAlchemy models in `site01/app/models.py`:

| Model | Table | Description |
|---|---|---|
| `User` | `users` | Authentication, roles, preferences, reset tokens |
| `AuthorizedAthlete` | `authorized_athletes` | Athletes a user can register for competitions |
| `Competition` | `competitions` | Cached competition data from external API |
| `CompetitionSubscription` | `competition_subscriptions` | User subscriptions with status (pending/confirmed/cancelled) |
| `Result` | `results` | Archery competition results (score, position, medal) |
| `Newsletter` | `newsletter_subscriptions` | Email newsletter subscriptions |
| `Product` | `products` | Shop products with bilingual content and variant config |
| `ProductVariant` | `product_variants` | Per-variant pricing, SKU, and stock |
| `GalleryItem` | `gallery_items` | 3D printing and electronics blog projects |
| `BlogPost` | `blog_posts` | Standalone or project-linked blog posts |

### Running Migrations

All migrations are in `site01/migrations/`. Run them inside the container:

```bash
docker exec -it orion-project python /app/site01/migrations/<script>.py
```

| Migration Script | Purpose |
|---|---|
| `add_authorized_athletes.py` | Create `authorized_athletes` table |
| `add_classe_field.py` | Add `classe` column to authorized_athletes |
| `add_blog_fields_to_gallery.py` | Add `content_it/en`, `slug`, `pcb_background`, `view_count` to gallery_items |
| `add_password_reset_tokens.py` | Add `reset_token`, `reset_token_expiry` to users |
| `add_locked_section_access.py` | Add `has_locked_section_access` to users |
| `add_product_variants.py` | Create `product_variants` table |
| `add_customization_flags.py` | Add `is_custom_string`, `is_custom_print` to products |

---

## Development

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r site01/requirements.txt
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

5. **Create an admin user** (first time only)
   ```bash
   cd site01
   python create_admin.py
   ```

### Python Dependencies

| Package | Version | Purpose |
|---|---|---|
| Flask | 3.0.0 | Web framework |
| Flask-Login | 0.6.3 | Authentication |
| Flask-SQLAlchemy | 3.1.1 | ORM |
| Flask-WTF | 1.2.1 | Forms + CSRF |
| Flask-Migrate | 4.0.5 | Database migrations |
| Werkzeug | 3.0.1 | WSGI utilities, password hashing |
| requests | 2.31.0 | HTTP client for Orion API |
| python-dotenv | 1.0.0 | `.env` file loading |
| email-validator | 2.1.0 | Email validation |
| gunicorn | 21.2.0 | Production WSGI server |
| Pillow | 10.3.0 | Image processing |
| openpyxl | 3.1.2 | BOM Excel import/export |

### Project Structure

```
mysite/
├── site01/                     # Main application directory
│   ├── app/
│   │   ├── __init__.py         # Flask app factory, extensions init
│   │   ├── models.py           # 10 SQLAlchemy models
│   │   ├── archery_utils.py    # Score/stats calculation library
│   │   ├── email_grouping.py   # Email utilities
│   │   ├── ranking_positions.py# Ranking capacity logic
│   │   ├── template_utils.py   # Jinja2 template helpers
│   │   ├── utils.py            # Translation + general utilities
│   │   ├── api/
│   │   │   └── __init__.py     # OrionAPIClient (Cloudflare Access)
│   │   ├── config/             # Runtime config helpers
│   │   ├── data/
│   │   │   └── competition_arrows.csv  # ~35 competition types
│   │   ├── routes/
│   │   │   ├── main.py         # Home, about, admin dashboard
│   │   │   ├── auth.py         # Login, register, password reset
│   │   │   ├── archery.py      # Analysis, competitions, stats API
│   │   │   ├── printing.py     # 3D printing gallery/blog
│   │   │   ├── electronics.py  # Electronics gallery/blog
│   │   │   ├── electronics_admin.py  # Electronics portal (admin, 25+ endpoints)
│   │   │   ├── shop.py         # Shop and cart
│   │   │   ├── api.py          # Website-level APIs (athletes, newsletter)
│   │   │   ├── api_routes.py   # Internal utility APIs
│   │   │   ├── admin.py        # Admin panel routes
│   │   │   └── locked.py       # Locked section routes
│   │   ├── static/
│   │   │   ├── css/style.css   # Custom styles (animations, spinners, dark mode)
│   │   │   ├── js/main.js      # Shared JS: toast notifications, cart, language
│   │   │   ├── js/archery-analysis.js  # Charts, stats, multi-athlete
│   │   │   ├── js/electronics_admin.js # Electronics portal JS
│   │   │   ├── media/          # Static images
│   │   │   └── uploads/        # User-uploaded images (persisted in Docker volume)
│   │   └── templates/
│   │       ├── base.html       # Responsive header/footer, dark mode, toasts
│   │       ├── index.html      # Animated home page
│   │       ├── auth/           # Login, register, password reset
│   │       ├── archery/        # Analysis, competitions
│   │       ├── printing/       # 3D printing gallery
│   │       ├── electronics/    # Electronics gallery
│   │       ├── shop/           # Product grid, cart
│   │       ├── admin/          # Admin panel pages
│   │       │   ├── electronics/ # 5 tab sub-templates
│   │       │   ├── users.html
│   │       │   ├── manage_athletes.html
│   │       │   ├── materials.html
│   │       │   └── products.html
│   │       └── project_detail.html  # Universal blog project page
│   ├── migrations/             # Incremental DB migration scripts
│   ├── translations/
│   │   ├── it.json             # Italian translations (100+ keys)
│   │   └── en.json             # English translations (100+ keys)
│   ├── config.py               # Config classes (Development/Production/Testing)
│   ├── run.py                  # Dev server entry point
│   └── docs/                   # Full documentation
├── Dockerfile                  # Production Docker image
├── docker-compose.yml          # Single-command deployment (port 6080→5000)
├── requirements.txt            # Top-level Python dependencies
└── README.md                   # This file
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
- **[Admin Panel Guide](site01/docs/ADMIN_PANEL_GUIDE.md)** — athlete management, user tools
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

## API Integration

### External Orion API
- **Base URL**: `https://api.orion-project.it:443`
- **Authentication**: Cloudflare Access headers (`CF-Access-Client-Id`, `CF-Access-Client-Secret`), optional
- **Client**: `app/api/__init__.py` → `OrionAPIClient`

All Orion API calls are proxied through Flask routes. Key endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/api/gare` | GET | Competitions (params: `future`, `limit`) |
| `/api/turni` | GET | Turns for a competition (`codice_gara` required) |
| `/api/inviti` | GET | Invitations (`codice`, `only_open`, `only_youth`) |
| `/api/iscrizioni` | GET/POST | Subscriptions (`tessera_atleta`, `export=full`) |
| `/api/atleti` | GET | Athlete search (`q` parameter) |
| `/api/athlete/<tessera>/results` | GET | Competition results for athlete |
| `/api/stats` | GET | Chart data for statistics |
| `/api/event_types` | GET | Competition type list |
| `/api/materiali` | GET | Stringmaking materials |
| `/api/elec/components` | GET | Electronics components |

### Internal Website APIs

| Endpoint | Auth | Description |
|---|---|---|
| `GET /api/user/authorized-athletes` | Login required | Current user's authorized athletes |
| `GET /admin/api/users` | Admin | All users |
| `GET /admin/api/authorized-athletes?user_id=X` | Admin | Athletes for a specific user |
| `POST /admin/api/authorized-athletes` | Admin | Assign athletes to a user |
| `DELETE /admin/api/authorized-athletes/<id>` | Admin | Remove athlete from user |

---

## Security Considerations

### Before Production
1. ✅ Set `SECRET_KEY` to a strong random value (`secrets.token_hex(32)`)
2. ✅ `SESSION_COOKIE_SECURE=true` — enforced in production (requires HTTPS)
3. ✅ `SESSION_COOKIE_HTTPONLY=true` — prevents JS from accessing session cookie
4. ✅ `SESSION_COOKIE_SAMESITE=Lax` — CSRF protection
5. ✅ Use a reverse proxy (nginx, Traefik) with SSL/TLS termination
6. ✅ Enable rate limiting at the reverse proxy level for API endpoints
7. ✅ Restrict exposed ports — only expose 6080 (or proxy port) externally
8. ✅ Regular automated backups of the `orion-data` volume
9. ✅ Password reset tokens use `secrets.token_urlsafe(32)` and expire after 24 hours

### Recommended Production Architecture
```
Internet
   │
   ▼
Reverse Proxy (nginx / Traefik)
   │  SSL/TLS termination
   │  Rate limiting
   │  Security headers (HSTS, X-Frame-Options, CSP)
   │
   ▼
Docker Container (orion-project)
   │  Gunicorn WSGI server
   │  Port 5000 (internal only)
   │
   ▼
SQLite Volume (orion-data)
```

## Updating

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

Or in Dockge: increment `CACHE_BUST` in `docker-compose.yml` and click **Rebuild**.

---

## Troubleshooting

### Container won't start
```bash
docker-compose logs -f
docker-compose ps
```

### Database issues
```bash
# Access container shell
docker-compose exec orion-project bash

# Inspect tables
python -c "from site01.app import app, db; app.app_context().push(); print(db.engine.table_names())"

# Run a migration manually
python /app/site01/migrations/add_authorized_athletes.py
```

### Uploaded images not persisting after rebuild
Ensure the `orion-uploads` volume is mounted at `/app/site01/app/static/uploads`. Check `docker-compose.yml` volumes section.

### Permission issues
```bash
docker-compose exec orion-project chown -R root:root /app/data
```

### Electronics portal not loading files
Verify `ELECTRONICS_STORAGE_URL` points to your nginx file server (default: `https://elec.orion-project.it`).

For more troubleshooting see [site01/docs/troubleshooting/](site01/docs/troubleshooting/).

---

## Performance Optimization

For production on OrangePi:

1. **Gunicorn worker count** — edit `docker-compose.yml`:
   ```yaml
   command: gunicorn -w 2 -b 0.0.0.0:5000 site01.wsgi:app
   ```
   OrangePi has limited CPU — use 2–4 workers.

2. **Static file caching** — handled at the reverse proxy level; Flask sets `SEND_FILE_MAX_AGE_DEFAULT = 0` in production to avoid stale assets after deploys.

3. **Flask-Caching** — included in the codebase; configure Redis as the backend for better performance (optional).

4. **Reverse proxy for static files** — serve `static/` directly from nginx to offload Flask.

---

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
- Check documentation in [site01/docs/](site01/docs/)

## Acknowledgments

- FITARCO for archery competition data
- Orion API for data integration
- Chart.js for visualization
- Tailwind CSS for styling
- Dockge for container management

---

**Made with ❤️ and precision** 🎯
