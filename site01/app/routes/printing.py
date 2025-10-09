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

@bp.route('/gallery/<int:item_id>')
def item_detail(item_id):
    """Gallery item detail page with related items"""
    item = GalleryItem.query.get_or_404(item_id)
    
    # Find related items based on tags
    related_items = []
    if item.tags:
        item_tags = [tag.strip().lower() for tag in item.tags.split(',')]
        all_items = GalleryItem.query.filter(
            GalleryItem.category == item.category,
            GalleryItem.is_active == True,
            GalleryItem.id != item.id
        ).all()
        
        # Calculate similarity score based on matching tags
        items_with_score = []
        for other_item in all_items:
            if other_item.tags:
                other_tags = [tag.strip().lower() for tag in other_item.tags.split(',')]
                matching_tags = len(set(item_tags) & set(other_tags))
                if matching_tags > 0:
                    items_with_score.append((other_item, matching_tags))
        
        # Sort by number of matching tags
        items_with_score.sort(key=lambda x: x[1], reverse=True)
        related_items = [item for item, score in items_with_score[:4]]
    
    return render_template('printing/item_detail.html', item=item, related_items=related_items)

@bp.route('/quote')
def quote():
    """Request a quote - requires login"""
    return render_template('printing/quote.html')

@bp.route('/shop')
def shop():
    """3D Printing shop"""
    return render_template('shop/index.html', category='3dprinting')
