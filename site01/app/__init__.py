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
    login_manager.login_message = 'Effettua il login per accedere a questa pagina.'
    login_manager.login_message_category = 'info'
    
    # Language selector
    @app.before_request
    def before_request():
        if 'language' not in session:
            session['language'] = app.config['DEFAULT_LANGUAGE']
    
    # Disable caching for HTML responses (force browser to check for updates)
    @app.after_request
    def add_header(response):
        # Don't cache HTML pages
        if response.content_type and 'text/html' in response.content_type:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '-1'
        return response
    
    # Register blueprints
    from app.routes import main, auth, archery, printing, electronics, shop, admin, api_routes, api
    
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(archery.bp)
    app.register_blueprint(printing.bp)
    app.register_blueprint(electronics.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(shop.bp)
    app.register_blueprint(api_routes.bp)
    app.register_blueprint(api.bp)  # Website-level API (authorized athletes, etc.)
    
    # Register template utilities
    from app.template_utils import register_template_utilities
    register_template_utilities(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
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

def register_error_handlers(app):
    """Register error handlers"""
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html', error_details=str(error) if app.debug else None), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/404.html'), 403  # Use 404 template for 403
    return app

def register_cli_commands(app):
    """Register Flask CLI commands"""
    import click
    
    @app.cli.command()
    @click.option('--username', prompt=True, help='Admin username')
    @click.option('--email', prompt=True, help='Admin email')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
    @click.option('--first-name', default='', help='First name')
    @click.option('--last-name', default='', help='Last name')
    @click.option('--locked-section', is_flag=True, help='Grant access to locked section')
    def create_admin(username, email, password, first_name, last_name, locked_section):
        """Create an admin user"""
        from app.models import User
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            click.echo(f'❌ Error: Username "{username}" already exists')
            return
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            click.echo(f'❌ Error: Email "{email}" already exists')
            return
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            first_name=first_name or None,
            last_name=last_name or None,
            is_admin=True,
            is_club_member=False,
            has_locked_section_access=locked_section,
            preferred_language='it'
        )
        admin.set_password(password)
        
        try:
            db.session.add(admin)
            db.session.commit()
            click.echo(f'✅ Admin user "{username}" created successfully!')
            click.echo(f'   Email: {email}')
            click.echo(f'   Admin: Yes')
            if locked_section:
                click.echo(f'   🔒 Locked Section Access: Yes')
        except Exception as e:
            db.session.rollback()
            click.echo(f'❌ Error creating admin: {e}')
    
    @app.cli.command()
    def list_users():
        """List all users"""
        from app.models import User
        
        users = User.query.all()
        if not users:
            click.echo('No users found')
            return
        
        click.echo('\n=== Users ===')
        for user in users:
            admin_badge = '👑 ADMIN' if user.is_admin else ''
            club_badge = '🏹 CLUB' if user.is_club_member else ''
            lock_badge = '🔒 LOCKED' if user.has_locked_section_access else ''
            click.echo(f'{user.id:3d}. {user.username:20s} ({user.email:30s}) {admin_badge} {club_badge} {lock_badge}')
        click.echo('')
    
    @app.cli.command()
    @click.argument('user_id', type=int)
    def make_admin(user_id):
        """Make a user an admin"""
        from app.models import User
        
        user = User.query.get(user_id)
        if not user:
            click.echo(f'❌ User with ID {user_id} not found')
            return
        
        if user.is_admin:
            click.echo(f'ℹ️  User "{user.username}" is already an admin')
            return
        
        user.is_admin = True
        db.session.commit()
        click.echo(f'✅ User "{user.username}" is now an admin!')
