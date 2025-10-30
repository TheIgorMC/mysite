"""
Locked Section Routes - TEMPLATE BLUEPRINT
This is a template for creating routes that require locked section access.

SECURITY: All routes here are protected by @locked_section_required decorator.
Only users with has_locked_section_access=True can access these routes.

To use this blueprint:
1. Uncomment the registration in app/__init__.py
2. Create templates in app/templates/locked/
3. Test access control thoroughly
"""
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.utils import locked_section_required

bp = Blueprint('locked', __name__, url_prefix='/locked')

@bp.route('/')
@login_required
@locked_section_required
def index():
    """Locked section landing page"""
    return render_template('locked/index.html')

@bp.route('/dashboard')
@login_required
@locked_section_required
def dashboard():
    """
    Protected dashboard - only accessible to users with locked section access
    """
    # Add your dashboard logic here
    data = {
        'user': current_user.username,
        'access_level': 'Locked Section',
        'message': 'You have successfully accessed the locked section!'
    }
    return render_template('locked/dashboard.html', data=data)

@bp.route('/api/data')
@login_required
@locked_section_required
def api_data():
    """
    Protected API endpoint
    Returns JSON data only to authorized users
    """
    sensitive_data = {
        'status': 'success',
        'message': 'This is sensitive data',
        'user': current_user.username,
        'access': 'locked_section'
    }
    return jsonify(sensitive_data)

@bp.route('/settings')
@login_required
@locked_section_required
def settings():
    """
    Protected settings page
    """
    return render_template('locked/settings.html')

# Add more routes as needed...
