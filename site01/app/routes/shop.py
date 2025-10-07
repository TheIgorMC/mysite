"""
Shop routes blueprint
"""
from flask import Blueprint, render_template, request, jsonify
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
    """Product detail page"""
    product = Product.query.get_or_404(product_id)
    return render_template('shop/product.html', product=product)

@bp.route('/cart')
def cart():
    """Shopping cart"""
    return render_template('shop/cart.html')
