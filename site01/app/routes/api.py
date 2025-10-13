"""
API Routes for Website-Level Features
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import AuthorizedAthlete, User
from datetime import datetime

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
