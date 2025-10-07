"""
Archery routes blueprint
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
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

def normalize_date(date_str):
    """
    Normalize date strings to YYYY-MM-DD format.
    Handles multiple input formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, etc.
    """
    if not date_str:
        return None
    
    try:
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y']:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If no format matches, try parsing as ISO format
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d')
    except (ValueError, AttributeError) as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return date_str  # Return original if parsing fails


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
    
    # Transform API response to standard format with normalized dates
    transformed = [
        {
            'athlete': result.get('atleta'),
            'competition_name': result.get('nome_gara'),
            'competition_type': result.get('tipo_gara'),
            'date': normalize_date(result.get('data_gara')),  # Normalize date format
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
    """Get athlete statistics with optional filtering
    
    Returns both career statistics and filtered statistics when filters are applied
    """
    # Get filter parameters (same as results endpoint)
    competition_type = request.args.get('competition_type')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    client = OrionAPIClient()
    
    # Get stats data (chart format from API) - uses /api/stats endpoint
    stats_data = client.get_statistics(athlete_id)
    
    # Get all results to compute statistics - uses /api/athlete/{tessera}/results
    all_results = client.get_athlete_results(athlete_id, limit=500)
    
    if not all_results:
        return jsonify({
            'career': {
                'total_competitions': 0,
                'gold_medals': 0,
                'silver_medals': 0,
                'bronze_medals': 0,
                'avg_position': None,
                'avg_percentile': None,
                'best_score': None,
                'best_score_competition': None
            },
            'filtered': None,
            'chart_data': stats_data
        })
    
    # Transform results to standard format with normalized dates
    transformed_results = [
        {
            'athlete': result.get('atleta'),
            'competition_name': result.get('nome_gara'),
            'competition_type': result.get('tipo_gara'),
            'date': normalize_date(result.get('data_gara')),
            'position': result.get('posizione'),
            'score': result.get('punteggio')
        }
        for result in all_results
    ]
    
    # Calculate CAREER statistics (all data)
    career_stats = get_statistics_summary(transformed_results, last_n=10)
    
    career_statistics = {
        'total_competitions': career_stats['total_competitions'],
        'gold_medals': career_stats['medals']['gold'],
        'silver_medals': career_stats['medals']['silver'],
        'bronze_medals': career_stats['medals']['bronze'],
        'avg_position': career_stats['percentile_stats'].get('avg_position'),
        'avg_percentile': career_stats['percentile_stats'].get('avg_percentile'),
        'top_finishes': career_stats['percentile_stats'].get('top_finishes', 0),
        'recent_competitions_analyzed': career_stats['percentile_stats'].get('competitions_analyzed', 0),
        'best_scores_by_category': career_stats['best_scores'],
        'category_breakdown': career_stats['categories']
    }
    
    # Find overall best score
    if transformed_results:
        best_result = max(transformed_results, key=lambda x: x.get('score', 0))
        career_statistics['best_score'] = best_result.get('score')
        career_statistics['best_score_competition'] = best_result.get('competition_name')
    
    # Calculate FILTERED statistics if filters are applied
    filtered_statistics = None
    has_filters = competition_type or category or start_date or end_date
    
    if has_filters:
        # Apply filters
        filtered_results = transformed_results.copy()
        
        # Filter by competition type
        if competition_type:
            filtered_results = [r for r in filtered_results if r.get('competition_type') == competition_type]
        
        # Filter by category (using CSV data)
        if category:
            filtered_results = filter_by_category(filtered_results, category)
        
        # Filter by date range
        if start_date:
            filtered_results = [r for r in filtered_results if r.get('date', '') >= start_date]
        if end_date:
            filtered_results = [r for r in filtered_results if r.get('date', '') <= end_date]
        
        # Calculate statistics for filtered data
        if filtered_results:
            filtered_stats = get_statistics_summary(filtered_results, last_n=10)
            
            filtered_statistics = {
                'total_competitions': filtered_stats['total_competitions'],
                'gold_medals': filtered_stats['medals']['gold'],
                'silver_medals': filtered_stats['medals']['silver'],
                'bronze_medals': filtered_stats['medals']['bronze'],
                'avg_position': filtered_stats['percentile_stats'].get('avg_position'),
                'avg_percentile': filtered_stats['percentile_stats'].get('avg_percentile'),
                'top_finishes': filtered_stats['percentile_stats'].get('top_finishes', 0),
                'recent_competitions_analyzed': filtered_stats['percentile_stats'].get('competitions_analyzed', 0),
                'best_scores_by_category': filtered_stats['best_scores'],
                'category_breakdown': filtered_stats['categories']
            }
            
            # Find best score in filtered results
            best_filtered = max(filtered_results, key=lambda x: x.get('score', 0))
            filtered_statistics['best_score'] = best_filtered.get('score')
            filtered_statistics['best_score_competition'] = best_filtered.get('competition_name')
    
    response = {
        'career': career_statistics,
        'filtered': filtered_statistics,
        'athlete_id': athlete_id
    }
    
    # Include chart data if available
    if stats_data:
        response['chart_data'] = stats_data
    
    return jsonify(response)

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
