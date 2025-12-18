"""
API Routes for Website-Level Features
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import AuthorizedAthlete, User
from app.api import OrionAPIClient
from datetime import datetime
import requests

bp = Blueprint('website_api', __name__)

@bp.route('/api/user/authorized-athletes', methods=['GET'])
@login_required
def get_authorized_athletes():
    """Get authorized athletes for current user"""
    
    athletes = AuthorizedAthlete.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'authorized_athletes': [
            {
                'id': a.id,
                'tessera': a.tessera_atleta,
                'nome': a.nome_atleta,
                'cognome': a.cognome_atleta,
                'nome_completo': a.nome_completo,
                'display': a.display_name,
                'categoria': a.categoria,
                'classe': a.classe,
                'data_nascita': a.data_nascita.isoformat() if a.data_nascita else None
            }
            for a in athletes
        ]
    })


@bp.route('/api/user/authorized-athletes/<int:athlete_id>', methods=['PATCH'])
@login_required
def update_authorized_athlete(athlete_id):
    """Update athlete preferences (class/category) for current user"""
    
    athlete = AuthorizedAthlete.query.get_or_404(athlete_id)
    
    # Verify athlete belongs to current user
    if athlete.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update fields if provided
    if 'classe' in data:
        athlete.classe = data['classe']
    if 'categoria' in data:
        athlete.categoria = data['categoria']
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    
    return jsonify({
        'success': True,
        'athlete': {
            'id': athlete.id,
            'tessera': athlete.tessera_atleta,
            'classe': athlete.classe,
            'categoria': athlete.categoria
        }
    })


@bp.route('/admin/api/users', methods=['GET'])
@login_required
def admin_get_users():
    """Admin: Get all users for athlete assignment"""
    
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.order_by(User.username).all()
    
    return jsonify([
        {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'is_admin': u.is_admin,
            'is_club_member': u.is_club_member
        }
        for u in users
    ])


@bp.route('/admin/api/authorized-athletes', methods=['GET'])
@login_required
def admin_get_all_assignments():
    """Admin: Get all user-athlete assignments or for specific user"""
    
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user_id = request.args.get('user_id', type=int)
    
    if user_id:
        # Get athletes for specific user
        athletes = AuthorizedAthlete.query.filter_by(user_id=user_id).all()
        return jsonify({
            'user_id': user_id,
            'athletes': [
                {
                    'id': a.id,
                    'tessera': a.tessera_atleta,
                    'nome_completo': a.nome_completo,
                    'categoria': a.categoria,
                    'data_nascita': a.data_nascita.isoformat() if a.data_nascita else None,
                    'added_at': a.added_at.isoformat()
                }
                for a in athletes
            ]
        })
    
    # Get all assignments grouped by user
    users = User.query.all()
    
    assignments = []
    for user in users:
        athletes = AuthorizedAthlete.query.filter_by(user_id=user.id).all()
        if athletes:  # Only include users with athletes
            assignments.append({
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'athletes': [
                    {
                        'id': a.id,
                        'tessera': a.tessera_atleta,
                        'nome_completo': a.nome_completo,
                        'categoria': a.categoria,
                        'classe': a.classe,
                        'added_at': a.added_at.isoformat()
                    }
                    for a in athletes
                ]
            })
    
    return jsonify({'assignments': assignments})


@bp.route('/admin/api/authorized-athletes', methods=['POST'])
@login_required
def admin_add_athletes():
    """Admin: Assign athlete(s) to a user"""
    
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    athletes = data.get('athletes', [])
    
    if not user_id or not athletes:
        return jsonify({'error': 'Missing user_id or athletes'}), 400
    
    # Validate user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    added_count = 0
    errors = []
    
    for athlete_data in athletes:
        tessera = athlete_data.get('tessera')
        nome = athlete_data.get('nome')
        cognome = athlete_data.get('cognome')
        
        if not all([tessera, nome, cognome]):
            errors.append(f"Missing required fields for athlete")
            continue
        
        # Check if already exists
        existing = AuthorizedAthlete.query.filter_by(
            user_id=user_id,
            tessera_atleta=tessera
        ).first()
        
        if existing:
            errors.append(f"Athlete {tessera} already authorized for this user")
            continue
        
        # Create new authorization
        athlete = AuthorizedAthlete(
            user_id=user_id,
            tessera_atleta=tessera,
            nome_atleta=nome,
            cognome_atleta=cognome,
            categoria=athlete_data.get('categoria'),  # Age category: GM, GF, RM, etc.
            classe=athlete_data.get('classe'),  # Competition class: CO, OL, AN
            data_nascita=datetime.fromisoformat(athlete_data['data_nascita']).date() if athlete_data.get('data_nascita') else None,
            added_by=current_user.id
        )
        
        db.session.add(athlete)
        added_count += 1
    
    db.session.commit()
    
    response = {
        'success': True,
        'added': added_count,
        'message': f"Added {added_count} athlete(s) to user {user.username}"
    }
    
    if errors:
        response['errors'] = errors
    
    return jsonify(response)


@bp.route('/admin/api/authorized-athletes/<int:athlete_id>', methods=['DELETE'])
@login_required
def admin_remove_athlete(athlete_id):
    """Admin: Remove athlete assignment from a user"""
    
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    athlete = AuthorizedAthlete.query.get_or_404(athlete_id)
    
    db.session.delete(athlete)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Athlete removed from user'
    })


# ==================== MATERIALS (STRINGMAKING STOCK) API PROXY ====================

@bp.route('/api/materiali', methods=['GET'])
@login_required
def get_materials():
    """
    Get materials with optional filters
    Query params: q, tipo, low_stock_lt, limit, offset
    """
    from app.api import OrionAPIClient
    
    # Get query parameters
    q = request.args.get('q')
    tipo = request.args.get('tipo')
    low_stock_lt = request.args.get('low_stock_lt', type=float)
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    try:
        api = OrionAPIClient()
        materials = api.get_materials(
            q=q,
            tipo=tipo,
            low_stock_lt=low_stock_lt,
            limit=limit,
            offset=offset
        )
        return jsonify(materials)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/materiali', methods=['POST'])
@login_required
def create_material():
    """
    Create a new material entry
    Required: materiale, colore, spessore, rimasto, costo, tipo
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    from app.api import OrionAPIClient
    
    data = request.get_json()
    required_fields = ['materiale', 'colore', 'spessore', 'rimasto', 'costo', 'tipo']
    
    # Validate required fields
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        api = OrionAPIClient()
        result = api.create_material(
            materiale=data['materiale'],
            colore=data['colore'],
            spessore=data['spessore'],
            rimasto=data['rimasto'],
            costo=data['costo'],
            tipo=data['tipo']
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/materiali/<int:material_id>', methods=['PATCH'])
@login_required
def update_material(material_id):
    """
    Update material fields (partial update)
    Accepts any combination of: rimasto, costo, materiale, colore, spessore, tipo
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    from app.api import OrionAPIClient
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No update data provided'}), 400
    
    try:
        api = OrionAPIClient()
        result = api.update_material(material_id, **data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/materiali/<int:material_id>/consume', methods=['POST'])
@login_required
def consume_material(material_id):
    """
    Consume a quantity from stock (atomic, non-negative)
    Required: quantita
    Returns: 409 if stock insufficient
    """
    from app.api import OrionAPIClient
    
    data = request.get_json()
    
    if 'quantita' not in data:
        return jsonify({'error': 'Missing required field: quantita'}), 400
    
    try:
        quantita = float(data['quantita'])
        if quantita <= 0:
            return jsonify({'error': 'Quantity must be positive'}), 400
        
        api = OrionAPIClient()
        result = api.consume_material(material_id, quantita)
        return jsonify(result)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            return jsonify({'error': 'Insufficient stock'}), 409
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/materiali/<int:material_id>', methods=['DELETE'])
@login_required
def delete_material(material_id):
    """
    Delete a material entry
    Admin only
    """
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    from app.api import OrionAPIClient
    
    try:
        api = OrionAPIClient()
        result = api.delete_material(material_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Product Management Endpoints
@bp.route('/api/products', methods=['GET'])
@login_required
def list_products():
    """Get all products (admin only for management)"""
    from app.models import Product
    
    products = Product.query.all()
    
    return jsonify([
        {
            'id': p.id,
            'name_it': p.name_it,
            'name_en': p.name_en,
            'category': p.category,
            'price': p.price,
            'is_active': p.is_active,
            'is_custom_string': p.is_custom_string,
            'is_custom_print': p.is_custom_print,
            'in_stock': p.in_stock,
            'variant_config': p.variant_config
        }
        for p in products
    ])


@bp.route('/api/products/<int:product_id>', methods=['PATCH'])
@login_required
def update_product(product_id):
    """Update product flags (admin only)"""
    from app.models import Product
    
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Admin access required'}), 403
    
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    try:
        # Update customization flags
        if 'is_custom_string' in data:
            product.is_custom_string = bool(data['is_custom_string'])
        if 'is_custom_print' in data:
            product.is_custom_print = bool(data['is_custom_print'])
        if 'is_active' in data:
            product.is_active = bool(data['is_active'])
        
        # Update variant configuration
        if 'variant_config' in data:
            # If variant_config is None or empty, set to None
            # Otherwise, store as JSON string
            variant_config = data['variant_config']
            if variant_config:
                # If it's already a string, use it; if it's a dict, convert to JSON
                if isinstance(variant_config, dict):
                    import json
                    product.variant_config = json.dumps(variant_config)
                else:
                    product.variant_config = variant_config
            else:
                product.variant_config = None
        
        db.session.commit()
        
        return jsonify({
            'id': product.id,
            'is_custom_string': product.is_custom_string,
            'is_custom_print': product.is_custom_print,
            'is_active': product.is_active,
            'variant_config': product.variant_config
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/athlete/<int:tessera>/rankings', methods=['GET'])
def get_athlete_rankings(tessera):
    """
    Get all ranking positions for a specific athlete from the official ranking cache.
    Returns rankings ordered by most recent update first.
    """
    try:
        from app.ranking_positions import get_ranking_positions
        
        client = OrionAPIClient()
        rankings = client._make_request('GET', f'/api/athlete/{tessera}/rankings')
        
        if rankings is None:
            return jsonify([])
        
        # Add max_positions and min_score to each ranking
        ranking_positions = get_ranking_positions()
        for ranking in rankings:
            # Normalize class and division names
            qualifica = ranking.get('qualifica', '')
            classe = ranking.get('classe_gara', '')
            categoria = ranking.get('categoria', '')
            
            # Apply same normalization as in archery.py
            normalized_class = classe
            normalized_division = categoria
            
            classe_lower = classe.lower()
            if 'senior' in classe_lower:
                normalized_class = classe.replace('Seniores', 'Senior').replace('seniores', 'Senior')
            elif 'junior' in classe_lower:
                normalized_class = classe.replace('Juniores', 'Junior').replace('juniores', 'Junior')
            
            categoria_lower = categoria.lower()
            if 'olimpic' in categoria_lower and 'arco' not in categoria_lower:
                normalized_division = 'Arco Olimpico'
            elif 'compound' in categoria_lower and 'arco' not in categoria_lower:
                normalized_division = 'Arco Compound'
            elif 'nudo' in categoria_lower and 'arco' not in categoria_lower:
                normalized_division = 'Arco Nudo'
            
            config = ranking_positions.get_positions(qualifica, normalized_class, normalized_division)
            if config:
                ranking['max_positions'] = config['posti']
                ranking['min_score'] = config['min_score']
        
        return jsonify(rankings)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
