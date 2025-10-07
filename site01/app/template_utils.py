"""
Template context processor to make utilities available in templates
"""
from flask import session, request
from app.utils import t, get_translation
from datetime import datetime
import os

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

def register_template_utilities(app):
    """Register template context processor"""
    app.context_processor(utility_processor)
