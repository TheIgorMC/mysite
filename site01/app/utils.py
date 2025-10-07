"""
Translation utilities
"""
import json
from flask import session, current_app
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
