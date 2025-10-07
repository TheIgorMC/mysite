"""
API routes blueprint - for internal API endpoints
"""
from flask import Blueprint, request, jsonify
from app.models import Newsletter
from app import db
from app.utils import t

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    # Check if already subscribed
    existing = Newsletter.query.filter_by(email=email).first()
    if existing:
        if existing.is_active:
            return jsonify({'message': 'Already subscribed'}), 200
        else:
            existing.is_active = True
            db.session.commit()
            return jsonify({'message': 'Resubscribed successfully'}), 200
    
    # Create new subscription
    subscription = Newsletter(email=email)
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({'message': 'Subscribed successfully'}), 201
