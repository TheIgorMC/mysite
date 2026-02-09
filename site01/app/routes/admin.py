"""
Admin routes blueprint
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/')
@login_required
def index():
    """Admin dashboard landing (minimal)"""
    # A simple admin landing page may already exist; render a generic admin index if present
    try:
        return render_template('admin/index.html')
    except Exception:
        return render_template('admin/dashboard.html')


@bp.route('/materials')
@login_required
def materials():
    """Materials management page for admins"""
    # Only admins should access this page
    if not getattr(current_user, 'is_admin', False):
        from flask import abort
        abort(403)
    return render_template('admin/materials.html')


@bp.route('/products')
@login_required
def products():
    """Products management page for admins"""
    # Only admins should access this page
    if not getattr(current_user, 'is_admin', False):
        from flask import abort
        abort(403)
    return render_template('admin/products.html')


@bp.route('/users')
@login_required
def users():
    """User management page for admins"""
    if not current_user.is_admin:
        from flask import abort
        abort(403)
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@bp.route('/users/<int:user_id>/force-reset-password', methods=['POST'])
@login_required
def force_reset_password(user_id):
    """Admin: Force a user to reset their password"""
    if not current_user.is_admin:
        from flask import abort
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    # Generate reset token
    token = user.generate_reset_token()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating reset token: {str(e)}', 'error')
        return redirect(url_for('admin.users'))
    
    # Create reset URL
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    # Try to send email
    try:
        from flask import current_app
        from app.api import OrionAPIClient
        client = OrionAPIClient()
        
        email_body = f"""
Ciao {user.first_name or user.username},

Un amministratore ha richiesto il reset della tua password. Clicca sul link seguente per reimpostare la tua password:

{reset_url}

Questo link è valido per 24 ore.

Saluti,
Il Team
        """
        
        client.send_email(
            recipient_email=user.email,
            mail_type='password_reset',
            locale='it',
            subject='Reset Password Richiesto',
            body_text=email_body,
            details_json={'reset_url': reset_url}
        )
        flash(f'Reset email sent to {user.email}', 'success')
    except Exception as e:
        current_app.logger.error(f'Failed to send reset email: {e}')
        flash(f'Email service unavailable. Reset link: {reset_url}', 'warning')
    
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/set-password', methods=['POST'])
@login_required
def admin_set_password(user_id):
    """Admin: Directly set a user's password"""
    if not current_user.is_admin:
        from flask import abort
        abort(403)
    
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('admin.users'))
    
    user.set_password(new_password)
    user.clear_reset_token()  # Clear any pending reset tokens
    try:
        db.session.commit()
        flash(f'Password updated for {user.username}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating password: {str(e)}', 'error')
    return redirect(url_for('admin.users'))
