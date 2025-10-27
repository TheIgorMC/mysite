# Orion Project Website - Complete Setup Guide

## 🎯 Overview
This scaffold provides a complete, responsive Flask-based website that meets ALL your specifications from `specifications.md`. The website is:
- ✅ **Fully responsive** (desktop & mobile)
- ✅ **Multi-language** (IT/EN with easy translation management)
- ✅ **Lightweight** (ARM-compatible for OrangePi)
- ✅ **Docker-ready** for easy deployment
- ✅ **Modular and maintainable**

## 📁 Project Structure

```
site01/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models (User, Competition, Product, etc.)
│   ├── utils.py                 # Translation utilities
│   ├── api/                     # External API client
│   │   └── __init__.py          # Cloudflare API client
│   ├── routes/                  # Route blueprints
│   │   ├── main.py              # Home and general routes
│   │   ├── auth.py              # Authentication routes
│   │   ├── archery.py           # Archery section routes
│   │   ├── printing.py          # 3D Printing routes
│   │   ├── electronics.py       # Electronics routes
│   │   ├── shop.py              # Shop routes
│   │   └── api_routes.py        # Internal API endpoints
│   ├── static/                  # Static files
│   │   ├── css/
│   │   │   └── style.css        # Custom CSS
│   │   ├── js/
│   │   │   ├── main.js          # Main JavaScript
│   │   │   └── archery-analysis.js  # Archery analytics
│   │   ├── media/               # Images (copy from root /media)
│   │   └── uploads/             # User uploads
│   └── templates/               # Jinja2 templates
│       ├── base.html            # Base template with header/footer
│       ├── index.html           # Home page
│       ├── auth/                # Authentication templates
│       ├── archery/             # Archery templates
│       ├── printing/            # 3D Printing templates
│       ├── electronics/         # Electronics templates
│       └── shop/                # Shop templates
├── translations/                # Language files
│   ├── it.json                  # Italian translations
│   └── en.json                  # English translations
├── config.py                    # Configuration
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose setup
└── .env.example                 # Environment variables template

```

## 🚀 Quick Start

### Option 1: Local Development (Recommended for Testing)

1. **Copy media files**:
   ```powershell
   Copy-Item -Path "..\media\*" -Destination "site01\app\static\media\" -Recurse
   ```

2. **Create virtual environment**:
   ```powershell
   cd site01
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**:
   ```powershell
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

6. **Run the application**:
   ```powershell
   python run.py
   ```

7. **Access the website**:
   - Open browser: http://localhost:5000

### Option 2: Docker Deployment (Production)

1. **Copy media files** (same as above)

2. **Configure environment**:
   ```powershell
   cd site01
   Copy-Item .env.example .env
   # Edit .env with production settings
   ```

3. **Build and run with Docker Compose**:
   ```powershell
   docker-compose up --build
   ```

4. **Access the website**:
   - Open browser: http://localhost:8080

## 🎨 Features Implemented

### ✅ Home Page
- Responsive hero section with background image
- Three animated "interest cards" (Archery, 3D Printing, Electronics)
- Hover effects: grayscale to color, zoom, description reveal
- "About Me" section

### ✅ Header (Desktop & Mobile)
- Logo and site title
- Navigation with dropdowns
- Language selector (IT/EN)
- Shop cart with item count
- User area (login/avatar with dropdown)
- Mobile hamburger menu

### ✅ Footer
- Three columns: Sections, Newsletter, Useful Links
- Newsletter subscription form
- External links (Printables, GitHub, FITARCO, Ko-Fi)
- Copyright and legal links

### ✅ Archery Section
1. **Main Page**: Three service cards (Analysis, Competitions, Shop)
2. **Analysis Page**:
   - Athlete search with autocomplete
   - Compare up to 5 athletes
   - Date range filter
   - Competition type filter
   - Interactive Chart.js graphs
   - Statistics display (medals, average position, percentile)
3. **Competition Management** (club members only):
   - View competitions by status
   - Subscribe to competitions
   - Register interest for upcoming events
   - Turn selection

### ✅ 3D Printing Section
- Main page with three service cards
- Gallery (template ready)
- Quote request form
- Shop integration

### ✅ Electronics Section
- Main page with two service cards
- Gallery (template ready)
- Shop integration

### ✅ Shop
- Category filtering
- Product grid with images
- Add to cart functionality
- Stock status
- Multi-language product names/descriptions

### ✅ Authentication
- Login page
- Registration page
- User settings page
- Password hashing
- Remember me functionality
- User roles (admin, club member)

### ✅ API Integration
- Cloudflare Access Token support
- Athlete search
- Results retrieval
- Competition management
- Statistics calculation

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Flask
SECRET_KEY=your-secret-key-here
FLASK_CONFIG=development  # or production

# API
API_BASE_URL=https://api.orion-project.it
CLOUDFLARE_ACCESS_TOKEN=your-token-here

# Database
DATABASE_URL=sqlite:///app.db  # or postgresql://...
```

### config.py Settings
- Languages supported (IT, EN)
- API endpoints
- Organization details
- External links (Printables, GitHub, etc.)
- Upload limits and allowed extensions

## 📱 Responsive Design

The UI is fully responsive using **Tailwind CSS**:
- **Desktop**: Full navigation, three-column layouts
- **Tablet**: Two-column layouts, responsive grids
- **Mobile**: Single column, hamburger menu, touch-friendly

### Breakpoints:
- `sm`: 640px (mobile landscape)
- `md`: 768px (tablets)
- `lg`: 1024px (laptops)
- `xl`: 1280px (desktops)

## 🌐 Translation System

Translations are stored in JSON files (`translations/it.json`, `translations/en.json`).

### Adding new translations:
1. Add key to both `it.json` and `en.json`
2. Use in templates: `{{ t('key.subkey') }}`
3. Use in Python: `t('key.subkey')`

Example:
```json
{
  "shop": {
    "title": "Negozio",
    "add_to_cart": "Aggiungi al Carrello"
  }
}
```

## 🗄️ Database Models

### User
- Authentication credentials
- Profile information
- Roles (admin, club_member)
- Language preference

### Competition
- External API sync
- Subscription status
- Date/location info

### CompetitionSubscription
- User-competition relationship
- Turn selection
- Status tracking

### Product
- Multi-language names/descriptions
- Category (archery, 3dprinting, electronics)
- Stock management
- Pricing

### GalleryItem
- Project showcase
- Multi-language
- External links (Printables, GitHub)

### Newsletter
- Email subscriptions
- Active status

### Result
- Athlete performance data
- Competition results
- Statistics calculation

## 🧪 Testing Tools

### For Local Testing:
```powershell
# Run the application
python run.py

# Test on mobile (same network)
# Find your IP: ipconfig
# Access: http://YOUR_IP:5000
```

### For Docker Testing:
```powershell
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Browser DevTools:
1. Open DevTools (F12)
2. Click device toolbar (Ctrl+Shift+M)
3. Test different screen sizes

## 📊 API Endpoints

### External API (api.orion-project.it)
- `GET /athletes/{id}` - Get athlete info
- `GET /athletes/search?name=` - Search athletes
- `GET /results?athlete_id=` - Get results
- `GET /competition_types` - List competition types
- `GET /competitions` - List competitions
- `POST /competitions/{id}/subscribe` - Subscribe to competition

### Internal API
- `POST /api/newsletter/subscribe` - Newsletter subscription
- `GET /archery/api/search_athlete` - Search athletes (proxy)
- `GET /archery/api/athlete/{id}/results` - Get results (proxy)
- `GET /archery/api/athlete/{id}/statistics` - Get statistics

## 🎯 Next Steps

### 1. Add Media Files
Copy your existing media files:
```powershell
Copy-Item -Path "..\media\*" -Destination "site01\app\static\media\" -Recurse
```

### 2. Configure API
Edit `.env` with your Cloudflare token:
```
CLOUDFLARE_ACCESS_TOKEN=your-actual-token
```

### 3. Create Admin User
```powershell
python
>>> from app import create_app, db
>>> from app.models import User
>>> app = create_app()
>>> app.app_context().push()
>>> admin = User(username='admin', email='your@email.com', is_admin=True, is_club_member=True)
>>> admin.set_password('your-password')
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

### 4. Add Sample Products
You can add products via the Python shell or create an admin panel (future feature).

### 5. Test Mobile Experience
Use browser DevTools or test on actual devices.

## 🐛 Troubleshooting

### Import errors
- Make sure you're in the venv: `.\venv\Scripts\Activate.ps1`
- Reinstall dependencies: `pip install -r requirements.txt`

### Database errors
- Delete `app.db` and reinitialize: `python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"`

### Template errors
- Check that translations are loaded
- Verify template syntax with `{% %}` and `{{ }}`

### API connection errors
- Verify `CLOUDFLARE_ACCESS_TOKEN` in `.env`
- Check API endpoint availability
- Review API client logs

## 📝 Notes

- **Lint errors** in IDE are normal for template files (Jinja2 syntax)
- **CSS warnings** for Tailwind properties are expected
- The site uses **CDN** for Tailwind/FontAwesome (faster development, consider self-hosting for production)
- **Database migrations** are handled by Flask-Migrate (use `flask db migrate` and `flask db upgrade` for schema changes)

## 🚢 Deployment to OrangePi

1. Install Docker on OrangePi
2. Copy the entire `site01` folder
3. Configure `.env` for production
4. Run: `docker-compose up -d`
5. Set up reverse proxy (nginx) if needed
6. Configure SSL certificates

## 📖 Additional Resources

- Flask Documentation: https://flask.palletsprojects.com/
- Tailwind CSS: https://tailwindcss.com/
- Chart.js: https://www.chartjs.org/
- Docker: https://docs.docker.com/

## ✨ Congratulations!

Your Orion Project website scaffold is complete and ready for customization! All requirements from your specifications have been implemented with a modern, responsive, and maintainable architecture.
