"""
Flask Application Factory
"""
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
import os

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
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
