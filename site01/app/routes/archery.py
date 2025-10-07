"""
Archery routes blueprint
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.api import OrionAPIClient
from app.utils import t
from app.archery_utils import (
    get_categories,
    get_competition_types_by_category,
    calculate_average_per_competition,
    filter_by_category,
    get_statistics_summary
)

bp = Blueprint('archery', __name__, url_prefix='/archery')

@bp.route('/')
def index():
    """Archery section main page"""
    return render_template('archery/index.html')

@bp.route('/analysis')
def analysis():
    """Performance analysis page"""
    return render_template('archery/analysis.html')

@bp.route('/api/search_athlete')
def search_athlete():
    """Search for athletes via API"""
    name = request.args.get('name', '')
    if not name:
        return jsonify({'error': 'Name required'}), 400
    
    client = OrionAPIClient()
    results = client.search_athlete(name)
    
    # Transform API response to match frontend expectations
    # API returns: tessera, nome, classe, societa_codice
    # Frontend expects: id, name
    if results:
        transformed = [
            {
                'id': athlete.get('tessera'),
                'name': athlete.get('nome'),
                'classe': athlete.get('classe'),
                'societa': athlete.get('societa_codice')
            }
            for athlete in results
        ]
        return jsonify(transformed)
    
    return jsonify([])

@bp.route('/api/athlete/<athlete_id>/results')
def get_athlete_results(athlete_id):
    """Get athlete results"""
    # API parameters - only use parameters that exist in API spec
    competition_type = request.args.get('competition_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # LOCAL filter parameters - NOT sent to API
    category = request.args.get('category')  # Filter locally using CSV
    include_average = request.args.get('include_average', 'false').lower() == 'true'
    
    client = OrionAPIClient()
    # Call API with ONLY valid parameters (no category!)
    results = client.get_athlete_results(
        athlete_id,
        competition_type=competition_type,
        start_date=start_date,
        end_date=end_date
    )
    
    if not results:
        return jsonify([])
    
    # Transform API response to standard format
    transformed = [
        {
            'athlete': result.get('atleta'),
            'competition_name': result.get('nome_gara'),
            'competition_type': result.get('tipo_gara'),
            'date': result.get('data_gara'),
            'position': result.get('posizione'),
            'score': result.get('punteggio'),
            'club_code': result.get('codice_societa_atleta'),
            'club_name': result.get('nome_societa_atleta'),
            'organizer_code': result.get('codice_societa_organizzatrice'),
            'organizer_name': result.get('nome_societa_organizzatrice')
        }
        for result in results
    ]
    
    # Filter by category LOCALLY using CSV data (not API)
    if category:
        transformed = filter_by_category(transformed, category)
    
    # Add average per arrow if requested (local calculation using CSV)
    if include_average:
        transformed = calculate_average_per_competition(transformed, include_average=True)
    
    return jsonify(transformed)

@bp.route('/api/athlete/<athlete_id>/statistics')
def get_athlete_statistics(athlete_id):
    """Get athlete statistics"""
    client = OrionAPIClient()
    
    # Get stats data (chart format from API) - uses /api/stats endpoint
    stats_data = client.get_statistics(athlete_id)
    
    # Get all results to compute statistics - uses /api/athlete/{tessera}/results
    all_results = client.get_athlete_results(athlete_id)
    
    if not all_results:
        return jsonify({
            'total_competitions': 0,
            'gold_medals': 0,
            'silver_medals': 0,
            'bronze_medals': 0,
            'avg_position': None,
            'avg_percentile': None,
            'best_score': None,
            'best_score_competition': None,
            'chart_data': stats_data
        })
    
    # Transform results to standard format
    transformed_results = [
        {
            'athlete': result.get('atleta'),
            'competition_name': result.get('nome_gara'),
            'competition_type': result.get('tipo_gara'),
            'date': result.get('data_gara'),
            'position': result.get('posizione'),
            'score': result.get('punteggio')
        }
        for result in all_results
    ]
    
    # Use comprehensive statistics calculation (local processing, no API call)
    stats_summary = get_statistics_summary(transformed_results, last_n=10)
    
    # Format for frontend
    statistics = {
        'total_competitions': stats_summary['total_competitions'],
        'gold_medals': stats_summary['medals']['gold'],
        'silver_medals': stats_summary['medals']['silver'],
        'bronze_medals': stats_summary['medals']['bronze'],
        'avg_position': stats_summary['percentile_stats'].get('avg_position'),
        'avg_percentile': stats_summary['percentile_stats'].get('avg_percentile'),
        'top_finishes': stats_summary['percentile_stats'].get('top_finishes', 0),
        'recent_competitions_analyzed': stats_summary['percentile_stats'].get('competitions_analyzed', 0),
        'best_scores_by_category': stats_summary['best_scores'],
        'category_breakdown': stats_summary['categories']
    }
    
    # Find overall best score
    if transformed_results:
        best_result = max(transformed_results, key=lambda x: x.get('score', 0))
        statistics['best_score'] = best_result.get('score')
        statistics['best_score_competition'] = best_result.get('competition_name')
    
    # Include chart data if available
    if stats_data:
        statistics['chart_data'] = stats_data
    
    return jsonify(statistics)

@bp.route('/api/competition_types')
def get_competition_types():
    """Get available competition types from API /api/event_types"""
    client = OrionAPIClient()
    # This calls /api/event_types which is the authoritative source
    types = client.get_competition_types()
    
    # API returns: ["1/2 FITA", "12+12", ...]
    # Transform to objects with id and name for dropdown
    if types:
        transformed = [
            {
                'id': event_type,
                'name': event_type
            }
            for event_type in types
        ]
        return jsonify(transformed)
    
    return jsonify([])

@bp.route('/api/categories')
def get_competition_categories():
    """Get available categories (Indoor, FITA, H&F, etc.) from local CSV data"""
    try:
        # Get categories from local CSV file, not from API
        categories = get_categories()
        
        if not categories:
            # Return empty array if no categories found
            return jsonify([])
        
        transformed = [
            {
                'id': category,
                'name': category
            }
            for category in categories
        ]
        
        return jsonify(transformed)
    except Exception as e:
        # Log error and return empty array
        print(f"Error getting categories: {e}")
        return jsonify([]), 500

@bp.route('/api/category/<category>/types')
def get_types_by_category(category):
    """Get competition types for a specific category
    
    This works by:
    1. Getting ALL event types from the API
    2. Filtering them using local CSV data to find which ones belong to this category
    """
    try:
        client = OrionAPIClient()
        # Get ALL types from API first
        all_types = client.get_competition_types()
        
        if not all_types:
            return jsonify([])
        
        # Filter using local CSV to find which types belong to this category
        types_in_category = get_competition_types_by_category(category)
        
        if not types_in_category:
            return jsonify([])
        
        # Only include types that:
        # 1. Are in the CSV for this category
        # 2. Are also returned by the API (so they actually exist)
        filtered_types = [
            t for t in all_types 
            if t in types_in_category
        ]
        
        transformed = [
            {
                'id': comp_type,
                'name': comp_type
            }
            for comp_type in filtered_types
        ]
        
        return jsonify(transformed)
    except Exception as e:
        # Log error and return empty array
        print(f"Error getting types for category {category}: {e}")
        return jsonify([]), 500

@bp.route('/competitions')
@login_required
def competitions():
    """Competition management page - club members only"""
    if not current_user.is_club_member:
        return render_template('errors/403.html'), 403
    
    return render_template('archery/competitions.html')

@bp.route('/api/competitions')
@login_required
def get_competitions():
    """Get competitions list"""
    if not current_user.is_club_member:
        return jsonify({'error': 'Unauthorized'}), 403
    
    status = request.args.get('status')
    client = OrionAPIClient()
    competitions = client.get_competitions(status=status)
    
    return jsonify(competitions or [])

@bp.route('/api/competitions/<competition_id>/subscribe', methods=['POST'])
@login_required
def subscribe_to_competition(competition_id):
    """Subscribe to a competition"""
    if not current_user.is_club_member:
        return jsonify({'error': 'Unauthorized'}), 403
    
    from app.models import CompetitionSubscription, Competition
    from app import db
    
    data = request.get_json()
    turn = data.get('turn')
    notes = data.get('notes', '')
    interest_only = data.get('interest_only', False)
    
    # Get or create competition
    competition = Competition.query.filter_by(external_id=competition_id).first()
    if not competition:
        # Fetch from API and create
        client = OrionAPIClient()
        comp_data = client.get_competition(competition_id)
        if not comp_data:
            return jsonify({'error': 'Competition not found'}), 404
        
        competition = Competition(
            external_id=competition_id,
            name=comp_data.get('name'),
            location=comp_data.get('location'),
            start_date=comp_data.get('start_date'),
            end_date=comp_data.get('end_date'),
            competition_type=comp_data.get('type'),
            invite_published=comp_data.get('invite_published', False),
            subscription_open=comp_data.get('subscription_open', False)
        )
        db.session.add(competition)
        db.session.commit()
    
    # Create subscription
    subscription = CompetitionSubscription(
        user_id=current_user.id,
        competition_id=competition.id,
        turn=turn,
        notes=notes,
        interest_only=interest_only,
        status='pending'
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({'success': True, 'subscription_id': subscription.id})

@bp.route('/shop')
def shop():
    """Archery shop"""
    return render_template('shop/index.html', category='archery')
