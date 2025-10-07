"""
3D Printing routes blueprint
"""
from flask import Blueprint, render_template
from app.models import GalleryItem
from app.utils import t

bp = Blueprint('printing', __name__, url_prefix='/3dprinting')

@bp.route('/')
def index():
    """3D Printing section main page"""
    # Get first 8 gallery items for preview
    gallery_items = GalleryItem.query.filter_by(
        category='3dprinting',
        is_active=True
    ).limit(8).all()
    return render_template('printing/index.html', gallery_items=gallery_items)

@bp.route('/gallery')
def gallery():
    """3D Printing gallery"""
    items = GalleryItem.query.filter_by(
        category='3dprinting',
        is_active=True
    ).all()
    return render_template('printing/gallery.html', items=items)

@bp.route('/quote')
def quote():
    """Request a quote - requires login"""
    return render_template('printing/quote.html')

@bp.route('/shop')
def shop():
    """3D Printing shop"""
    return render_template('shop/index.html', category='3dprinting')
