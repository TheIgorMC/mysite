# 🎯 Orion Project

**Passione, Precisione, Innovazione** - A comprehensive platform for archery analysis, 3D printing projects, and electronics.

## Features

### 🏹 Archery Analysis
- Performance tracking and statistics
- Multi-athlete comparison (up to 5 athletes)
- Career vs filtered statistics
- Competition results visualization with Chart.js
- Support for multiple competition types and categories
- Date range filtering
- Average per arrow calculations

### 🖨️ 3D Printing
- Project gallery
- Custom model requests
- Integration with Printables

### ⚡ Electronics
- Project showcase
- Custom circuit services

### 🌍 Internationalization
- Full bilingual support (Italian/English)
- Dynamic language switching
- All UI elements, messages, and content translated

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: Tailwind CSS, Chart.js, Vanilla JavaScript
- **Database**: SQLite (with SQLAlchemy ORM)
- **Authentication**: Flask-Login
- **API Integration**: Orion API with Cloudflare Access
- **Deployment**: Docker + Docker Compose

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
│   │   ├── static/      # CSS, JS, images
│   │   ├── templates/   # Jinja2 templates
│   │   └── utils.py     # Utility functions
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

- **[Documentation Index](site01/docs/INDEX.md)** - Navigation to all docs
- **[Features](site01/docs/features/)** - Feature documentation
  - Statistics system
  - Date handling
  - Loading states
  - Internationalization
- **[API Documentation](site01/docs/api/)** - API usage guides
- **[Implementation Details](site01/docs/IMPLEMENTATION_SUMMARY.md)** - Technical details

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
