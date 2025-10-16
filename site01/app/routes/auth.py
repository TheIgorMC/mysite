"""
Authentication routes blueprint
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User
from app.utils import t

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember_me', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.last_login = db.func.now()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash(t('auth.invalid_credentials'), 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash(t('auth.username_exists'), 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash(t('auth.email_exists'), 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            preferred_language=session.get('language', 'it')
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(t('auth.registration_success'), 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('auth/settings.html')

@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    from werkzeug.utils import secure_filename
    import os
    from flask import current_app
    
    current_user.username = request.form.get('username')
    current_user.email = request.form.get('email')
    current_user.first_name = request.form.get('first_name')
    current_user.last_name = request.form.get('last_name')
    
    # Handle avatar upload
    avatar = request.files.get('avatar')
    if avatar and avatar.filename:  # Only process if a file was actually uploaded
        filename = secure_filename(avatar.filename)
        # Create unique filename
        import uuid
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
        unique_filename = f"avatar_{current_user.id}_{uuid.uuid4().hex}.{ext}"
        
        upload_folder = os.path.join(current_app.root_path, 'static', 'media')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Delete old avatar if not default
        if current_user.avatar and current_user.avatar != 'default-avatar.png':
            old_avatar_path = os.path.join(upload_folder, current_user.avatar)
            if os.path.exists(old_avatar_path):
                try:
                    os.remove(old_avatar_path)
                except Exception as e:
                    current_app.logger.warning(f'Could not delete old avatar: {e}')
        
        avatar.save(os.path.join(upload_folder, unique_filename))
        current_user.avatar = unique_filename
    # If no file uploaded, avatar stays the same (preserved automatically)
    
    db.session.commit()
    flash('Profile updated successfully', 'success')
    return redirect(url_for('auth.settings'))

@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('auth.settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('auth.settings'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('auth.settings'))
    
    current_user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully', 'success')
    return redirect(url_for('auth.settings'))

