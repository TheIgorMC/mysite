"""
Shop routes blueprint
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models import Product
from app.utils import t
from app.config.string_pricing import (
    calculate_string_price, 
    BASE_PRICE,
    COLOR_PATTERN_PRICES,
    PINSTRIPE_PRICES,
    DIFFERENT_CENTER_SERVING_COLOR
)

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


@bp.route('/customize/string/<int:product_id>')
@login_required
def customize_string(product_id):
    """String customizer for custom bowstrings"""
    product = Product.query.get_or_404(product_id)
    
    # Verify product has customization enabled
    if not product.is_custom_string:
        from flask import abort
        abort(404)
    
    # Pass pricing configuration to template
    pricing = {
        'base_price': BASE_PRICE,
        'color_pattern_prices': COLOR_PATTERN_PRICES,
        'pinstripe_prices': PINSTRIPE_PRICES,
        'different_center_serving_color': DIFFERENT_CENTER_SERVING_COLOR
    }
    
    return render_template('shop/customize_string.html', product=product, pricing=pricing)


@bp.route('/api/calculate-string-price', methods=['POST'])
@login_required
def calculate_price():
    """
    Calculate string price server-side to prevent client manipulation
    Expects JSON with string configuration
    """
    try:
        config = request.get_json()
        
        if not config:
            return jsonify({'error': 'No configuration provided'}), 400
        
        # Calculate price using server-side pricing logic
        price_data = calculate_string_price(config)
        
        return jsonify(price_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/add-to-cart', methods=['POST'])
@login_required
def add_to_cart_api():
    """
    Add custom string to cart with server-side price validation
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        config = data.get('config')
        client_price = data.get('price')
        
        # SECURITY: Calculate actual price server-side
        price_data = calculate_string_price(config)
        actual_price = price_data['total']
        
        # Validate that client price matches server calculation
        if client_price and abs(float(client_price) - actual_price) > 0.01:
            return jsonify({
                'error': 'Price mismatch detected. Please refresh and try again.',
                'expected_price': actual_price
            }), 400
        
        # TODO: Add to cart session/database
        # For now, just validate and return success
        
        return jsonify({
            'success': True,
            'message': 'String configuration added to cart',
            'price': actual_price,
            'price_breakdown': price_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
