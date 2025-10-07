"""
Electronics routes blueprint
"""
from flask import Blueprint, render_template
from app.models import GalleryItem
from app.utils import t

bp = Blueprint('electronics', __name__, url_prefix='/electronics')

@bp.route('/')
def index():
    """Electronics section main page"""
    # Get first 8 gallery items for preview
    gallery_items = GalleryItem.query.filter_by(
        category='electronics',
        is_active=True
    ).limit(8).all()
    return render_template('electronics/index.html', gallery_items=gallery_items)

@bp.route('/gallery')
def gallery():
    """Electronics gallery"""
    items = GalleryItem.query.filter_by(
        category='electronics',
        is_active=True
    ).all()
    return render_template('electronics/gallery.html', items=items)

@bp.route('/shop')
def shop():
    """Electronics shop"""
    return render_template('shop/index.html', category='electronics')
