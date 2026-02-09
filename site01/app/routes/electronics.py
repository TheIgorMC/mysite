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
        related_items = [ri for ri, score in items_with_score[:4]]
    
    return render_template('electronics/item_detail.html', item=item, related_items=related_items)

@bp.route('/shop')
def shop():
    """Electronics shop"""
    return render_template('shop/index.html', category='electronics')
