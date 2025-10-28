"""
String Customization Pricing Configuration
Edit these values to adjust pricing for custom bowstrings
"""

# Base Prices
BASE_PRICE = 15.00  # Base price for any custom string

# Color Pattern Pricing
COLOR_PATTERN_PRICES = {
    'single': 0.00,     # Single color: no extra charge
    'double': 1.50,     # Dual color: +€1.50
    'triple': 4.00,     # Triple color: +€4.00
}

# Pinstripe Pricing (depends on base pattern)
PINSTRIPE_PRICES = {
    'single': 1.00,     # Pinstripe on single color: +€1
    'double': 1.50,     # Pinstripe on dual color: +€1.50
    'triple': 0.00,     # Triple doesn't allow pinstripe
}

# Serving Options
DIFFERENT_CENTER_SERVING_COLOR = 1.50  # Different center serving color: +€1.50


def calculate_string_price(config):
    """
    Calculate the total price for a custom string based on configuration
    
    Args:
        config (dict): String configuration with keys:
            - colorPattern: 'single', 'double', or 'triple'
            - hasPinstripe: boolean
            - centerServingColor: string or None
            - endServingColor: string or None
    
    Returns:
        dict: Price breakdown with 'base', 'customization', and 'total'
    """
    total_price = BASE_PRICE
    customization_cost = 0.0
    breakdown = []
    
    # Color pattern cost
    color_pattern = config.get('colorPattern', 'single')
    pattern_cost = COLOR_PATTERN_PRICES.get(color_pattern, 0)
    if pattern_cost > 0:
        customization_cost += pattern_cost
        breakdown.append({
            'description': f'{color_pattern.capitalize()} color pattern',
            'cost': pattern_cost
        })
    
    # Pinstripe cost
    has_pinstripe = config.get('hasPinstripe', False)
    if has_pinstripe:
        pinstripe_cost = PINSTRIPE_PRICES.get(color_pattern, 0)
        if pinstripe_cost > 0:
            customization_cost += pinstripe_cost
            breakdown.append({
                'description': 'Pinstripe',
                'cost': pinstripe_cost
            })
    
    # Different center serving color
    center_color = config.get('centerServingColor', '').lower() if config.get('centerServingColor') else None
    end_color = config.get('endServingColor', '').lower() if config.get('endServingColor') else None
    
    if center_color and end_color and center_color != end_color:
        customization_cost += DIFFERENT_CENTER_SERVING_COLOR
        breakdown.append({
            'description': 'Different center serving color',
            'cost': DIFFERENT_CENTER_SERVING_COLOR
        })
    
    total = total_price + customization_cost
    
    return {
        'base': round(total_price, 2),
        'customization': round(customization_cost, 2),
        'total': round(total, 2),
        'breakdown': breakdown
    }
