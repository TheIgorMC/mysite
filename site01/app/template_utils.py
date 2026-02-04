"""
Template context processor to make utilities available in templates
"""
from flask import session, request
from app.utils import t, get_translation
from datetime import datetime
import os
import json

def utility_processor():
    """Make utility functions available in all templates"""
    
    def get_current_year():
        return datetime.now().year
    
    def get_config():
        from flask import current_app
        return current_app.config
    
    return dict(
        t=t,
        get_translation=get_translation,
        now=datetime.now(),
        session=session,
        config=get_config()
    )

def from_json_filter(value):
    """Convert JSON string to Python object"""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

def register_template_utilities(app):
    """Register template context processor and filters"""
    app.context_processor(utility_processor)
    app.jinja_env.filters['from_json'] = from_json_filter

