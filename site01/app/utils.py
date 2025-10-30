"""
Translation utilities and access control decorators
"""
import json
from flask import session, current_app, flash, redirect, url_for
from flask_login import current_user
from functools import wraps
import os

_translations = {}

def load_translations():
    """Load all translation files"""
    global _translations
    translations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'translations')
    
    for lang in current_app.config['LANGUAGES']:
        filepath = os.path.join(translations_dir, f'{lang}.json')
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                _translations[lang] = json.load(f)

def get_translation(key, lang=None):
    """Get translation for a key"""
    if not _translations:
        load_translations()
    
    if lang is None:
        lang = session.get('language', current_app.config['DEFAULT_LANGUAGE'])
    
    # Navigate nested dictionary
    keys = key.split('.')
    value = _translations.get(lang, {})
    
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k, key)
        else:
            return key
    
    return value

def t(key, **kwargs):
    """Shorthand for get_translation with formatting"""
    translation = get_translation(key)
    if kwargs:
        return translation.format(**kwargs)
    return translation


# ============================================================================
# ACCESS CONTROL DECORATORS
# ============================================================================

def locked_section_required(f):
    """
    Decorator to require locked section access for a route.
    
    SECURITY: This provides an additional layer of authorization beyond login.
    Only users with has_locked_section_access=True can access decorated routes.
    
    Usage:
        @bp.route('/locked/secret')
        @login_required
        @locked_section_required
        def secret_page():
            return render_template('locked/secret.html')
    
    Note: Always use @login_required BEFORE this decorator to ensure user is authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        # Then check if user has locked section access
        if not current_user.has_locked_section_access:
            flash('You do not have permission to access this section.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin access for a route.
    
    Usage:
        @bp.route('/admin/settings')
        @login_required
        @admin_required
        def admin_settings():
            return render_template('admin/settings.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def club_member_required(f):
    """
    Decorator to require club member status for a route.
    
    Usage:
        @bp.route('/archery/competitions')
        @login_required
        @club_member_required
        def competitions():
            return render_template('archery/competitions.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_club_member:
            flash('Club member access required.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function
