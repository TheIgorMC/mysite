"""
Admin routes blueprint
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

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
