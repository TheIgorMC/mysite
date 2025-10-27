"""
Shop routes blueprint
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models import Product
from app.utils import t

bp = Blueprint('shop', __name__, url_prefix='/shop')

@bp.route('/')
def index():
    """Shop main page"""
    category = request.args.get('category', 'all')
    
    query = Product.query.filter_by(is_active=True)
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    products = query.all()
    
    return render_template('shop/index.html', products=products, category=category)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page with related products"""
    product = Product.query.get_or_404(product_id)
    
    # Find related products based on tags
    related_products = []
    if product.tags:
        product_tags = [tag.strip().lower() for tag in product.tags.split(',')]
        all_products = Product.query.filter(
            Product.category == product.category,
            Product.is_active == True,
            Product.id != product.id
        ).all()
        
        # Calculate similarity score based on matching tags
        products_with_score = []
        for other_product in all_products:
            if other_product.tags:
                other_tags = [tag.strip().lower() for tag in other_product.tags.split(',')]
                matching_tags = len(set(product_tags) & set(other_tags))
                if matching_tags > 0:
                    products_with_score.append((other_product, matching_tags))
        
        # Sort by number of matching tags
        products_with_score.sort(key=lambda x: x[1], reverse=True)
        related_products = [prod for prod, score in products_with_score[:4]]
    
    return render_template('shop/product_detail.html', product=product, related_products=related_products)

@bp.route('/cart')
def cart():
    """Shopping cart"""
    return render_template('shop/cart.html')

