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
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
            
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
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Registration error: {str(e)}', 'error')
            return render_template('auth/register.html')
        
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
        
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
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
    
    try:
        db.session.commit()
        flash('Profile updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating profile: {str(e)}', 'error')
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
    try:
        db.session.commit()
        flash('Password changed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error changing password: {str(e)}', 'error')
    return redirect(url_for('auth.settings'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash('Error generating reset token. Please try again.', 'error')
                return redirect(url_for('auth.forgot_password'))
            
            # Send reset email
            from flask import current_app, url_for
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            try:
                # Try to use OrionAPIClient if available
                from app.api import OrionAPIClient
                client = OrionAPIClient()
                
                email_body = f"""
Ciao {user.first_name or user.username},

Hai richiesto il reset della password. Clicca sul link seguente per reimpostare la tua password:

{reset_url}

Questo link è valido per 24 ore.

Se non hai richiesto questo reset, ignora questa email.

Saluti,
Il Team
                """
                
                client.send_email(
                    recipient_email=user.email,
                    mail_type='password_reset',
                    locale='it',
                    subject='Reset Password',
                    body_text=email_body,
                    details_json={'reset_url': reset_url}
                )
                flash(t('auth.reset_email_sent'), 'success')
            except Exception as e:
                current_app.logger.error(f'Failed to send reset email: {e}')
                # Show token in flash for development (remove in production!)
                flash(f'Email service unavailable. Reset link: {reset_url}', 'warning')
        else:
            # Don't reveal if user exists - still show success message
            flash(t('auth.reset_email_sent'), 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash(t('auth.invalid_reset_token'), 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash(t('auth.passwords_do_not_match'), 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if len(password) < 6:
            flash(t('auth.password_too_short'), 'error')
            return render_template('auth/reset_password.html', token=token)
        
        user.set_password(password)
        user.clear_reset_token()
        try:
            db.session.commit()
            flash(t('auth.password_reset_success'), 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error resetting password: {str(e)}', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)
