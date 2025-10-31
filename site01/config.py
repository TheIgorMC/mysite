import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Language settings
    LANGUAGES = ['it', 'en']
    DEFAULT_LANGUAGE = 'it'
    
    # API Configuration
    API_BASE_URL = os.environ.get('API_BASE_URL') or 'http://localhost:9090'
    API_PORT = os.environ.get('API_PORT') or '9090'
    CF_ACCESS_ID = os.environ.get('CF_ACCESS_ID') or ''
    CF_ACCESS_SECRET = os.environ.get('CF_ACCESS_SECRET') or ''
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Pagination
    ITEMS_PER_PAGE = 12
    
    # Organization settings
    ORGANIZATION_NAME = "Orion Project"
    ORGANIZATION_START_YEAR = 2024
    CLUB_NAME = "ASD Compagnia Arcieri Carraresi"
    
    # External links
    PRINTABLES_URL = "https://www.printables.com/@TheIgorMC"
    GITHUB_URL = "https://github.com/TheIgorMC"
    FITARCO_URL = "https://www.fitarco-italia.org/arcieri/situazione.php?Codice=93229"
    KOFI_URL = "https://ko-fi.com/theigormc"
    
    # Electronics file storage (external nginx server)
    ELECTRONICS_STORAGE_URL = os.environ.get('ELECTRONICS_STORAGE_URL') or 'https://elec.orion-project.it'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Force template reloading in production (for updates)
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0  # Disable static file caching

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
