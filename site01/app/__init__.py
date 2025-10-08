"""
Flask Application Factory
"""
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='default'):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Language selector
    @app.before_request
    def before_request():
        if 'language' not in session:
            session['language'] = app.config['DEFAULT_LANGUAGE']
    
    # Register blueprints
    from app.routes import main, auth, archery, printing, electronics, shop, api_routes
    
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(archery.bp)
    app.register_blueprint(printing.bp)
    app.register_blueprint(electronics.bp)
    app.register_blueprint(shop.bp)
    app.register_blueprint(api_routes.bp)
    
    # Register template utilities
    from app.template_utils import register_template_utilities
    register_template_utilities(app)
    
    # Create database tables if they don't exist
    # Using inspector to check if tables exist first (avoids race conditions with multiple workers)
    with app.app_context():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            # Only create tables if database is empty
            if not tables:
                from app import models
                db.create_all()
                app.logger.info("Database tables created")
        except Exception as e:
            # Tables might already exist or be created by another worker
            app.logger.debug(f"Database check: {e}")
    
    return app
