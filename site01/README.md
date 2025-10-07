# Orion Project Website - Site01

A lightweight, responsive personal portfolio website with multi-language support (IT/EN).

## Tech Stack
- **Backend**: Flask (Python) - lightweight and ARM-compatible
- **Frontend**: HTML5, CSS3 (with Tailwind CSS), Vanilla JavaScript
- **Database**: SQLite (upgradeable to PostgreSQL/MySQL)
- **Authentication**: Flask-Login
- **API Integration**: Custom API client for Cloudflare-protected endpoints
- **Containerization**: Docker & Docker Compose

## Features
- ✅ Responsive design (desktop & mobile)
- ✅ Multi-language support (IT/EN)
- ✅ User authentication & authorization
- ✅ Three main sections: Archery, 3D Printing, Electronics
- ✅ Archery analytics with graphing
- ✅ Competition management system
- ✅ Shop functionality
- ✅ Newsletter subscription
- ✅ Easy translation management via JSON files

## Project Structure
```
site01/
├── app/
│   ├── __init__.py           # Flask app initialization
│   ├── models.py             # Database models
│   ├── routes/               # Route handlers
│   ├── api/                  # API client for external services
│   ├── static/               # Static files (CSS, JS, images)
│   └── templates/            # HTML templates
├── translations/             # Language files (IT/EN)
├── config.py                 # Configuration
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
└── run.py                   # Application entry point
```

## Running the Application

### Local Development
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python run.py
```

### Docker
```bash
docker-compose up --build
```

## Testing
The application will be available at:
- Local: http://localhost:5000
- Docker: http://localhost:8080

## Configuration
Edit `config.py` for:
- Database settings
- API endpoints
- Secret keys
- Language preferences
