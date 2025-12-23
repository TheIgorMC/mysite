"""
Archery routes blueprint
"""
from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from app.api import OrionAPIClient
from app.utils import t
from app.archery_utils import (
    get_categories,
    get_competition_types_by_category,
    calculate_average_per_competition,
    filter_by_category,
    get_statistics_summary
)
from app.models import AuthorizedAthlete, User
from app.ranking_positions import get_ranking_positions
from app import db

bp = Blueprint('archery', __name__, url_prefix='/archery')

def get_user_emails_for_athlete(tessera_atleta):
    """
    Get all user emails who are authorized to manage this athlete
    
    Args:
        tessera_atleta: Athlete's tessera ID
        
    Returns:
        List of email addresses
    """
    try:
        # Query authorized_athletes table to find users managing this athlete
        authorized = db.session.query(User.email).join(
            AuthorizedAthlete, 
            User.id == AuthorizedAthlete.user_id
        ).filter(
            AuthorizedAthlete.tessera_atleta == tessera_atleta
        ).all()
        
        emails = [row[0] for row in authorized if row[0]]  # Extract emails, skip None
        current_app.logger.info(f"Found {len(emails)} user(s) managing athlete {tessera_atleta}: {emails}")
        return emails
    except Exception as e:
        current_app.logger.error(f"Error fetching user emails for athlete {tessera_atleta}: {e}")
        return []

def get_athlete_name(tessera_atleta):
    """Get athlete's full name from authorized_athletes table"""
    try:
        athlete = AuthorizedAthlete.query.filter_by(tessera_atleta=tessera_atleta).first()
        if athlete:
            return f"{athlete.nome_atleta} {athlete.cognome_atleta}"
        return None
    except Exception as e:
        current_app.logger.error(f"Error fetching athlete name for {tessera_atleta}: {e}")
        return None

def get_competition_details(codice_gara, client):
    """Fetch competition details from Orion API"""
    try:
        # Get all competitions and filter by code
        competitions = client._make_request('GET', '/api/gare', params={'future': 'false', 'limit': 1000})
        if competitions:
            for comp in competitions:
                if comp.get('codice') == codice_gara:
                    return comp
        return None
    except Exception as e:
        current_app.logger.error(f"Error fetching competition details for {codice_gara}: {e}")
        return None

def format_time(time_value):
    """Format time value - handle both string ("08:45:00") and number (seconds since midnight)"""
    if not time_value:
        return ''
    
    if isinstance(time_value, str):
        # Already a string like "08:45:00" - trim to HH:MM
        return time_value[:5] if len(time_value) >= 5 else time_value
    elif isinstance(time_value, (int, float)):
        # Seconds since midnight - convert to HH:MM
        hours = int(time_value // 3600)
        minutes = int((time_value % 3600) // 60)
        return f"{hours:02d}:{minutes:02d}"
    else:
        return str(time_value)

def get_turn_details(codice_gara, turno, client):
    """Fetch turn schedule details from Orion API"""
    try:
        turns = client._make_request('GET', '/api/turni', params={'codice_gara': codice_gara})
        if turns:
            for turn in turns:
                if turn.get('turno') == turno:
                    giorno = turn.get('giorno', '')
                    ora_ritrovo = turn.get('ora_ritrovo', '')
                    ora_inizio = turn.get('ora_inizio_tiri', '')
                    
                    parts = []
                    if giorno:
                        parts.append(giorno)
                    if ora_ritrovo:
                        parts.append(f"Ritrovo: {format_time(ora_ritrovo)}")
                    if ora_inizio:
                        parts.append(f"Inizio: {format_time(ora_inizio)}")
                    
                    return " - ".join(parts) if parts else None
        return None
    except Exception as e:
        current_app.logger.error(f"Error fetching turn details for {codice_gara} turn {turno}: {e}")
        return None

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


@bp.route('/admin/ranking-positions')
@login_required
def admin_ranking_positions():
    """Admin page for managing ranking positions CSV"""
    if not current_user.is_admin:
        return render_template('errors/403.html'), 403
    return render_template('archery/admin_ranking_positions.html')

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
    try:
        # Fetch filter parameters
        # competition_type can be passed to API as 'event_type'
        # start_date and end_date must be filtered CLIENT-SIDE
        competition_type = request.args.get('competition_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')  # Filter locally using CSV
        include_average = request.args.get('include_average', 'false').lower() == 'true'
        
        client = OrionAPIClient()
        # Call API with competition_type (converted to event_type)
        results = client.get_athlete_results(
            athlete_id,
            competition_type=competition_type,
            start_date=start_date,  # Not supported by API, will be filtered client-side
            end_date=end_date  # Not supported by API, will be filtered client-side
        )
        # Defensive: if the API returned a non-list (string or dict), log and return a clear error
        if results is None:
            current_app.logger.error(f"API returned None for athlete results (athlete_id={athlete_id})")
            return jsonify({'error': 'No data from API'}), 502
        
        # Handle both legacy (direct list) and new (wrapper with summary) API formats
        if not isinstance(results, list):
            current_app.logger.info(f"API returned wrapped format for results: {type(results)}")
            # If it's a dict with a key 'results', try to extract it
            if isinstance(results, dict) and 'results' in results and isinstance(results['results'], list):
                current_app.logger.info(f"Extracting results array ({len(results['results'])} items) from wrapper")
                results = results['results']
            else:
                current_app.logger.error(f"Unexpected API payload for athlete results (athlete_id={athlete_id}): {results}")
                return jsonify({'error': 'Unexpected API response format', 'details': str(type(results))}), 502
        
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
        
        # Filter by competition type LOCALLY (API doesn't support this filter)
        if competition_type:
            transformed = [r for r in transformed if r.get('competition_type') == competition_type]
        
        # Filter by category LOCALLY using CSV data (not API)
        if category:
            transformed = filter_by_category(transformed, category)
        
        # Filter by date range LOCALLY (API doesn't support this filter)
        if start_date:
            transformed = [r for r in transformed if r.get('date', '') >= start_date]
        if end_date:
            transformed = [r for r in transformed if r.get('date', '') <= end_date]
        
        # Add average per arrow if requested (local calculation using CSV)
        if include_average:
            transformed = calculate_average_per_competition(transformed, include_average=True)
        
        return jsonify(transformed)
    
    except Exception as e:
        current_app.logger.error(f"Error fetching athlete results: {str(e)}")
        return jsonify({'error': 'Failed to fetch athlete results', 'details': str(e)}), 500

@bp.route('/api/athlete/<athlete_id>/statistics')
def get_athlete_statistics(athlete_id):
    """Get athlete statistics with optional filtering
    
    Returns both career statistics and filtered statistics when filters are applied
    """
    try:
        # Get filter parameters (same as results endpoint)
        competition_type = request.args.get('competition_type')  # Will be 'event_type' for API
        category = request.args.get('category')
        start_date = request.args.get('start_date')  # Will be 'from_date' for API
        end_date = request.args.get('end_date')  # Will be 'to_date' for API
        
        client = OrionAPIClient()

        # Get stats data (chart format from API) - uses /api/stats endpoint
        # Convert our parameter names to API parameter names
        try:
            stats_data = client.get_statistics(
                athlete_id,
                event_type=competition_type,
                from_date=start_date,
                to_date=end_date
            )
        except Exception as e:
            current_app.logger.warning(f"Could not load stats chart data: {e}")
            stats_data = None

        # Get all results to compute statistics - uses /api/athlete/{tessera}/results endpoint
        all_results = client.get_athlete_results(
            athlete_id,
            competition_type=None,  # Get all types for career stats
            limit=500
        )

        # Defensive checks for all_results
        if all_results is None:
            current_app.logger.error(f"API returned None for all_results (athlete_id={athlete_id})")
            return jsonify({'career': None, 'filtered': None, 'chart_data': stats_data, 'athlete_id': athlete_id}), 502
        
        # Handle both legacy (direct list) and new (wrapper with summary) API formats
        if not isinstance(all_results, list):
            current_app.logger.info(f"API returned wrapped format: {type(all_results)}")
            if isinstance(all_results, dict) and 'results' in all_results and isinstance(all_results['results'], list):
                current_app.logger.info(f"Extracting results array ({len(all_results['results'])} items) from wrapper")
                all_results = all_results['results']
            else:
                current_app.logger.error(f"Unexpected API payload for all_results (athlete_id={athlete_id}): {all_results}")
                return jsonify({'error': 'Unexpected API response format for results', 'details': str(type(all_results))}), 502

        # DEBUG: Log what we actually got from the API (after extracting from wrapper if needed)
        current_app.logger.info(f"Processing {len(all_results)} results")
        if all_results and len(all_results) > 0:
            current_app.logger.info(f"First result keys: {list(all_results[0].keys())}")
            current_app.logger.info(f"First result sample: {all_results[0]}")

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
        # API returns results with these field names
        transformed_results = []
        for result in all_results:
            transformed_results.append({
                'athlete': result.get('atleta'),
                'competition_name': result.get('nome_gara'),
                'competition_type': result.get('tipo_gara'),
                'date': normalize_date(result.get('data_gara')),
                'position': result.get('posizione'),
                'score': result.get('punteggio')
            })
        
        current_app.logger.info(f"Transformed {len(transformed_results)} results")
        
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
            # Filter out results with None or 0 scores before finding max
            valid_scores = [r for r in transformed_results if r.get('score') is not None and r.get('score') > 0]
            if valid_scores:
                best_result = max(valid_scores, key=lambda x: x.get('score', 0))
                career_statistics['best_score'] = best_result.get('score')
                career_statistics['best_score_competition'] = best_result.get('competition_name')
            else:
                career_statistics['best_score'] = None
                career_statistics['best_score_competition'] = None
        else:
            career_statistics['best_score'] = None
            career_statistics['best_score_competition'] = None
        
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
                valid_filtered_scores = [r for r in filtered_results if r.get('score') is not None and r.get('score') > 0]
                if valid_filtered_scores:
                    best_filtered = max(valid_filtered_scores, key=lambda x: x.get('score', 0))
                    filtered_statistics['best_score'] = best_filtered.get('score')
                    filtered_statistics['best_score_competition'] = best_filtered.get('competition_name')
                else:
                    filtered_statistics['best_score'] = None
                    filtered_statistics['best_score_competition'] = None
        
        response = {
            'career': career_statistics,
            'filtered': filtered_statistics,
            'athlete_id': athlete_id
        }
        
        # Include chart data if available
        if stats_data:
            response['chart_data'] = stats_data
        
        return jsonify(response)
    
    except Exception as e:
        import traceback
        current_app.logger.error(f"Error fetching athlete statistics: {str(e)}")
        current_app.logger.error(f"Exception type: {type(e).__name__}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to fetch athlete statistics', 'details': str(e)}), 500

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
def competitions():
    """Competition management page - shows info page for non-members, competition page for members"""
    from flask_login import current_user
    
    # Log for debugging
    current_app.logger.info(f"Competitions page accessed. Authenticated: {current_user.is_authenticated}")
    
    # Check if user is authenticated
    if not current_user.is_authenticated:
        # Show informational page for unauthenticated users
        current_app.logger.info("Showing info page for unauthenticated user")
        return render_template('archery/competitions_info.html')
    
    # Check if authenticated user is a club member
    current_app.logger.info(f"User is authenticated. Club member: {current_user.is_club_member}")
    if not current_user.is_club_member:
        # Show informational page for non-club members
        current_app.logger.info("Showing info page for non-club member")
        return render_template('archery/competitions_info.html')
    
    # User is authenticated and is a club member - show competition management
    current_app.logger.info("Showing competition management page for club member")
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

# FastAPI Proxy Endpoints for Competitions
@bp.route('/api/gare')
def get_gare():
    """Proxy endpoint for fetching competitions (gare) from FastAPI"""
    future = request.args.get('future', 'false').lower() == 'true'
    limit = request.args.get('limit', '100')
    
    client = OrionAPIClient()
    
    try:
        # Fetch from FastAPI
        gare = client.get_competitions(future=future, limit=int(limit))
        return jsonify(gare if gare else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/turni')
def get_turni():
    """Proxy endpoint for fetching turns (turni) from FastAPI"""
    codice_gara = request.args.get('codice_gara')
    
    if not codice_gara:
        return jsonify({'error': 'codice_gara is required'}), 400
    
    client = OrionAPIClient()
    
    try:
        # Fetch from FastAPI
        turni = client.get_turns(codice_gara)
        return jsonify(turni if turni else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/societa')
def get_societa():
    """Proxy endpoint for fetching organizations (società) from Orion API"""
    export = request.args.get('export', 'false').lower() == 'full'
    include_coords = request.args.get('include_coords', 'false').lower() == 'true'
    
    client = OrionAPIClient()
    
    try:
        # Fetch from Orion API
        params = {'include_coords': str(include_coords).lower()}
        societa = client._make_request('GET', '/api/societa', params=params)
        return jsonify(societa if societa else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/inviti')
def get_inviti():
    """Proxy endpoint for fetching invitations (inviti) from FastAPI"""
    codice = request.args.get('codice')
    only_open = request.args.get('only_open', 'false').lower() == 'true'
    only_youth = request.args.get('only_youth', 'false').lower() == 'true'
    
    client = OrionAPIClient()
    
    try:
        # Fetch from FastAPI
        inviti = client.get_inviti(codice=codice, only_open=only_open, only_youth=only_youth)
        return jsonify(inviti if inviti else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/inviti/<codice>/text')
def get_invite_text(codice):
    """Proxy endpoint for fetching full invite details with raw HTML"""
    client = OrionAPIClient()
    
    try:
        invite = client.get_invite_text(codice)
        if not invite:
            return jsonify({'error': 'Invite not found'}), 404
        return jsonify(invite)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/iscrizioni', methods=['GET', 'POST'])
@login_required
def handle_iscrizioni():
    """Proxy endpoint for subscriptions (iscrizioni) to/from FastAPI"""
    client = OrionAPIClient()
    
    if request.method == 'GET':
        # Get subscriptions for an athlete or all subscriptions (mass export)
        tessera_atleta = request.args.get('tessera_atleta')
        export = request.args.get('export')
        
        try:
            if export == 'full':
                # Mass export - get all subscriptions
                # FastAPI doesn't support this, so we need to get all athletes and their subscriptions
                # For now, just call without tessera_atleta filter
                iscrizioni = client.get_all_subscriptions()
            elif tessera_atleta:
                iscrizioni = client.get_subscriptions(tessera_atleta)
            else:
                return jsonify({'error': 'tessera_atleta is required or use export=full'}), 400
                
            return jsonify(iscrizioni if iscrizioni else [])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    else:  # POST
        # Create a new subscription
        data = request.get_json()
        
        required_fields = ['codice_gara', 'tessera_atleta', 'categoria', 'turno']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            result = client.create_subscription(
                codice_gara=data['codice_gara'],
                tessera_atleta=data['tessera_atleta'],
                categoria=data['categoria'],
                classe=data.get('classe', ''),  # Add classe field
                turno=data['turno'],
                stato=data.get('stato', 'confermato'),
                note=data.get('note', '')
            )
            
            # Send email notification to all users managing this athlete
            try:
                current_app.logger.info(f'[EMAIL] Attempting to send subscription notification for athlete {data["tessera_atleta"]}')
                user_emails = get_user_emails_for_athlete(data['tessera_atleta'])
                
                if user_emails:
                    current_app.logger.info(f'[EMAIL] Found {len(user_emails)} user(s) to notify: {user_emails}')
                    
                    # Fetch competition and athlete details
                    comp_details = get_competition_details(data['codice_gara'], client)
                    athlete_name = get_athlete_name(data['tessera_atleta'])
                    turn_info = get_turn_details(data['codice_gara'], data['turno'], client)
                    
                    # Build details with custom subject
                    details = {}
                    
                    # Competition info
                    if comp_details:
                        details['Nome Gara'] = comp_details.get('nome', '')
                        if comp_details.get('data_inizio'):
                            data_inizio = comp_details['data_inizio']
                            data_fine = comp_details.get('data_fine')
                            if data_fine and data_fine != data_inizio:
                                details['Date'] = f"{data_inizio} / {data_fine}"
                            else:
                                details['Data'] = data_inizio
                        if comp_details.get('luogo'):
                            details['Luogo'] = comp_details['luogo']
                        if comp_details.get('societa_nome'):
                            details['Società Organizzatrice'] = comp_details['societa_nome']
                        elif comp_details.get('societa_codice'):
                            details['Società Organizzatrice'] = comp_details['societa_codice']
                    
                    details['Codice Gara'] = data['codice_gara']
                    
                    # Athlete info
                    athlete_display = f"{data['tessera_atleta']}"
                    if athlete_name:
                        athlete_display += f" - {athlete_name}"
                    details['Atleta'] = athlete_display
                    
                    details['Categoria'] = data['categoria']
                    details['Classe'] = data.get('classe', 'N/A')
                    
                    # Turn info
                    turn_display = str(data['turno'])
                    if turn_info:
                        turn_display += f" ({turn_info})"
                    details['Turno'] = turn_display
                    
                    details['Stato'] = data.get('stato', 'confermato')
                    
                    # Custom subject
                    subject = f"Iscrizione confermata"
                    if comp_details and comp_details.get('nome'):
                        subject += f" - {comp_details['nome']}"
                    
                    # Send email to each user managing this athlete
                    for user_email in user_emails:
                        current_app.logger.info(f'[EMAIL] Sending subscription email to {user_email}')
                        try:
                            result = client.send_email(
                                recipient_email=user_email,
                                mail_type='subscription',
                                locale='it',
                                subject=subject,
                                body_text='Iscrizione registrata con successo.',
                                details_json=details
                            )
                            current_app.logger.info(f'[EMAIL] Successfully queued subscription email to {user_email}: {result}')
                        except Exception as send_err:
                            current_app.logger.error(f'[EMAIL] Failed to send to {user_email}: {send_err}')
                else:
                    current_app.logger.warning(f'[EMAIL] No users found managing athlete {data["tessera_atleta"]}')
            except Exception as email_err:
                current_app.logger.error(f'[EMAIL] Error in subscription email process: {email_err}', exc_info=True)
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@bp.route('/api/iscrizioni/<int:subscription_id>', methods=['DELETE', 'PATCH'])
@login_required
def manage_iscrizione(subscription_id):
    """Delete or update a subscription (iscrizione) by ID"""
    client = OrionAPIClient()
    
    try:
        if request.method == 'DELETE':
            # Get subscription details before deletion for email
            subscription_data = request.args.to_dict()
            tessera_atleta = subscription_data.get('tessera_atleta')
            
            result = client.delete_subscription(subscription_id)
            
            # Send cancellation email to all users managing this athlete
            if tessera_atleta:
                try:
                    current_app.logger.info(f'[EMAIL] Attempting to send cancellation notification for athlete {tessera_atleta}')
                    user_emails = get_user_emails_for_athlete(tessera_atleta)
                    
                    if user_emails:
                        current_app.logger.info(f'[EMAIL] Found {len(user_emails)} user(s) to notify: {user_emails}')
                        
                        # Fetch details
                        codice_gara = subscription_data.get('codice_gara', '')
                        comp_details = get_competition_details(codice_gara, client) if codice_gara else None
                        athlete_name = get_athlete_name(tessera_atleta)
                        
                        details = {}
                        
                        if comp_details and comp_details.get('nome'):
                            details['Nome Gara'] = comp_details['nome']
                        
                        details['Codice Gara'] = codice_gara
                        
                        athlete_display = tessera_atleta
                        if athlete_name:
                            athlete_display += f" - {athlete_name}"
                        details['Atleta'] = athlete_display
                        
                        details['ID Iscrizione'] = str(subscription_id)
                        details['Stato'] = 'Cancellata'
                        
                        subject = "Iscrizione cancellata"
                        if comp_details and comp_details.get('nome'):
                            subject += f" - {comp_details['nome']}"
                        
                        for user_email in user_emails:
                            current_app.logger.info(f'[EMAIL] Sending cancellation email to {user_email}')
                            try:
                                result_email = client.send_email(
                                    recipient_email=user_email,
                                    mail_type='cancellation_confirmed',
                                    locale='it',
                                    subject=subject,
                                    body_text='Iscrizione cancellata con successo.',
                                    details_json=details
                                )
                                current_app.logger.info(f'[EMAIL] Successfully queued cancellation email to {user_email}: {result_email}')
                            except Exception as send_err:
                                current_app.logger.error(f'[EMAIL] Failed to send to {user_email}: {send_err}')
                    else:
                        current_app.logger.warning(f'[EMAIL] No users found managing athlete {tessera_atleta}')
                except Exception as email_err:
                    current_app.logger.error(f'[EMAIL] Error in cancellation email process: {email_err}', exc_info=True)
            else:
                current_app.logger.warning(f'[EMAIL] No tessera_atleta provided for subscription {subscription_id} deletion')
            
            return jsonify(result if result else {'id': subscription_id, 'status': 'deleted'})
        
        elif request.method == 'PATCH':
            data = request.get_json()
            tessera_atleta = data.get('tessera_atleta')
            
            result = client.update_subscription(subscription_id, data)
            
            # Send modification email to all users managing this athlete
            if tessera_atleta:
                try:
                    current_app.logger.info(f'[EMAIL] Attempting to send modification notification for athlete {tessera_atleta}')
                    user_emails = get_user_emails_for_athlete(tessera_atleta)
                    
                    if user_emails:
                        current_app.logger.info(f'[EMAIL] Found {len(user_emails)} user(s) to notify: {user_emails}')
                        
                        # Fetch details
                        codice_gara = data.get('codice_gara', '')
                        comp_details = get_competition_details(codice_gara, client) if codice_gara else None
                        athlete_name = get_athlete_name(tessera_atleta)
                        
                        # Build list of changes with turn details if changed
                        changes = []
                        for k, v in data.items():
                            if k not in ['tessera_atleta', 'codice_gara', 'athlete_email']:
                                if k == 'turno':
                                    turn_info = get_turn_details(codice_gara, v, client)
                                    display = str(v)
                                    if turn_info:
                                        display += f" ({turn_info})"
                                    changes.append(f"{k}: {display}")
                                else:
                                    changes.append(f"{k}: {v}")
                        
                        details = {}
                        
                        if comp_details and comp_details.get('nome'):
                            details['Nome Gara'] = comp_details['nome']
                        
                        details['Codice Gara'] = codice_gara
                        
                        athlete_display = tessera_atleta
                        if athlete_name:
                            athlete_display += f" - {athlete_name}"
                        details['Atleta'] = athlete_display
                        
                        details['ID Iscrizione'] = str(subscription_id)
                        details['Modifiche'] = ', '.join(changes) if changes else 'Nessuna modifica specifica'
                        
                        subject = "Iscrizione modificata"
                        if comp_details and comp_details.get('nome'):
                            subject += f" - {comp_details['nome']}"
                        
                        for user_email in user_emails:
                            current_app.logger.info(f'[EMAIL] Sending modification email to {user_email}')
                            try:
                                result_email = client.send_email(
                                    recipient_email=user_email,
                                    mail_type='modification_confirmed',
                                    locale='it',
                                    subject=subject,
                                    body_text='Iscrizione modificata con successo.',
                                    details_json=details
                                )
                                current_app.logger.info(f'[EMAIL] Successfully queued modification email to {user_email}: {result_email}')
                            except Exception as send_err:
                                current_app.logger.error(f'[EMAIL] Failed to send to {user_email}: {send_err}')
                    else:
                        current_app.logger.warning(f'[EMAIL] No users found managing athlete {tessera_atleta}')
                except Exception as email_err:
                    current_app.logger.error(f'[EMAIL] Error in modification email process: {email_err}', exc_info=True)
            
            return jsonify(result if result else {'id': subscription_id, 'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/interesse', methods=['GET', 'POST'])
@login_required
def handle_interesse():
    """Proxy endpoint for interest expressions (interesse) to/from FastAPI"""
    client = OrionAPIClient()
    
    if request.method == 'GET':
        # Get interest expressions for an athlete or competition
        tessera_atleta = request.args.get('tessera_atleta')
        codice_gara = request.args.get('codice_gara')
        export = request.args.get('export')
        
        try:
            if export == 'full':
                # Mass export - get all interests
                interests = client.get_all_interests()
            else:
                interests = client.get_interests(tessera_atleta=tessera_atleta, codice_gara=codice_gara)
            return jsonify(interests if interests else [])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    else:  # POST
        # Create a new interest expression
        data = request.get_json()
        
        current_app.logger.info(f"POST /api/interesse received data: {data}")
        
        required_fields = ['codice_gara', 'tessera_atleta', 'categoria']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        try:
            result = client.create_interest(
                codice_gara=data['codice_gara'],
                tessera_atleta=data['tessera_atleta'],
                categoria=data['categoria'],
                classe=data.get('classe', ''),
                note=data.get('note', '')
            )
            
            # Send email notification to all users managing this athlete
            try:
                current_app.logger.info(f'[EMAIL] Attempting to send interest notification for athlete {data["tessera_atleta"]}')
                user_emails = get_user_emails_for_athlete(data['tessera_atleta'])
                
                if user_emails:
                    current_app.logger.info(f'[EMAIL] Found {len(user_emails)} user(s) to notify: {user_emails}')
                    
                    # Fetch competition and athlete details
                    comp_details = get_competition_details(data['codice_gara'], client)
                    athlete_name = get_athlete_name(data['tessera_atleta'])
                    
                    details = {}
                    
                    # Competition info
                    if comp_details:
                        details['Nome Gara'] = comp_details.get('nome', '')
                        if comp_details.get('data_inizio'):
                            data_inizio = comp_details['data_inizio']
                            data_fine = comp_details.get('data_fine')
                            if data_fine and data_fine != data_inizio:
                                details['Date'] = f"{data_inizio} / {data_fine}"
                            else:
                                details['Data'] = data_inizio
                    
                    details['Codice Gara'] = data['codice_gara']
                    
                    # Athlete info
                    athlete_display = data['tessera_atleta']
                    if athlete_name:
                        athlete_display += f" - {athlete_name}"
                    details['Atleta'] = athlete_display
                    
                    details['Categoria'] = data['categoria']
                    details['Classe'] = data.get('classe', 'N/A')
                    
                    if data.get('note'):
                        details['Note'] = data['note']
                    
                    # Custom subject
                    subject = "Interesse registrato"
                    if comp_details and comp_details.get('nome'):
                        subject += f" - {comp_details['nome']}"
                    
                    for user_email in user_emails:
                        current_app.logger.info(f'[EMAIL] Sending interest email to {user_email}')
                        try:
                            result = client.send_email(
                                recipient_email=user_email,
                                mail_type='interest',
                                locale='it',
                                subject=subject,
                                body_text='Espressione di interesse registrata con successo.',
                                details_json=details
                            )
                            current_app.logger.info(f'[EMAIL] Successfully queued interest email to {user_email}: {result}')
                        except Exception as send_err:
                            current_app.logger.error(f'[EMAIL] Failed to send to {user_email}: {send_err}')
                else:
                    current_app.logger.warning(f'[EMAIL] No users found managing athlete {data["tessera_atleta"]}')
            except Exception as email_err:
                current_app.logger.error(f'[EMAIL] Error in interest email process: {email_err}', exc_info=True)
            
            return jsonify(result)
        except Exception as e:
            current_app.logger.error(f"Error creating interest: {e}")
            return jsonify({'error': str(e)}), 500


@bp.route('/api/interesse/<int:interest_id>', methods=['DELETE', 'PATCH'])
@login_required
def manage_interesse(interest_id):
    """Delete or update an interest expression by ID"""
    client = OrionAPIClient()
    
    try:
        if request.method == 'DELETE':
            # Get interest details before deletion for email
            interest_data = request.args.to_dict()
            tessera_atleta = interest_data.get('tessera_atleta')
            
            result = client.delete_interest(interest_id)
            
            # Send cancellation email to all users managing this athlete
            if tessera_atleta:
                try:
                    current_app.logger.info(f'[EMAIL] Attempting to send interest cancellation notification for athlete {tessera_atleta}')
                    user_emails = get_user_emails_for_athlete(tessera_atleta)
                    
                    if user_emails:
                        current_app.logger.info(f'[EMAIL] Found {len(user_emails)} user(s) to notify: {user_emails}')
                        
                        details = {
                            'ID Interesse': str(interest_id),
                            'Tessera Atleta': tessera_atleta,
                            'Codice Gara': interest_data.get('codice_gara', ''),
                            'Stato': 'Cancellata'
                        }
                        
                        for user_email in user_emails:
                            current_app.logger.info(f'[EMAIL] Sending interest cancellation email to {user_email}')
                            try:
                                result_email = client.send_email(
                                    recipient_email=user_email,
                                    mail_type='cancellation_confirmed',
                                    locale='it',
                                    body_text='Espressione di interesse cancellata con successo.',
                                    details_json=details
                                )
                                current_app.logger.info(f'[EMAIL] Successfully queued interest cancellation email to {user_email}: {result_email}')
                            except Exception as send_err:
                                current_app.logger.error(f'[EMAIL] Failed to send to {user_email}: {send_err}')
                    else:
                        current_app.logger.warning(f'[EMAIL] No users found managing athlete {tessera_atleta}')
                except Exception as email_err:
                    current_app.logger.error(f'[EMAIL] Error in interest cancellation email process: {email_err}', exc_info=True)
            else:
                current_app.logger.warning(f'[EMAIL] No tessera_atleta provided for interest {interest_id} deletion')
            
            return jsonify(result if result else {'id': interest_id, 'status': 'deleted'})
        
        elif request.method == 'PATCH':
            data = request.get_json()
            tessera_atleta = data.get('tessera_atleta')
            
            result = client.update_interest(interest_id, data)
            
            # Send modification email to all users managing this athlete
            if tessera_atleta:
                try:
                    current_app.logger.info(f'[EMAIL] Attempting to send interest modification notification for athlete {tessera_atleta}')
                    user_emails = get_user_emails_for_athlete(tessera_atleta)
                    
                    if user_emails:
                        current_app.logger.info(f'[EMAIL] Found {len(user_emails)} user(s) to notify: {user_emails}')
                        
                        # Build list of changes
                        changes = [f'{k}: {v}' for k, v in data.items() 
                                 if k not in ['tessera_atleta', 'codice_gara', 'athlete_email']]
                        
                        details = {
                            'ID Interesse': str(interest_id),
                            'Tessera Atleta': tessera_atleta,
                            'Codice Gara': data.get('codice_gara', ''),
                            'Modifiche': ', '.join(changes) if changes else 'Nessuna modifica specifica'
                        }
                        
                        for user_email in user_emails:
                            current_app.logger.info(f'[EMAIL] Sending interest modification email to {user_email}')
                            try:
                                result_email = client.send_email(
                                    recipient_email=user_email,
                                    mail_type='modification_confirmed',
                                    locale='it',
                                    body_text='Espressione di interesse modificata con successo.',
                                    details_json=details
                                )
                                current_app.logger.info(f'[EMAIL] Successfully queued interest modification email to {user_email}: {result_email}')
                            except Exception as send_err:
                                current_app.logger.error(f'[EMAIL] Failed to send to {user_email}: {send_err}')
                    else:
                        current_app.logger.warning(f'[EMAIL] No users found managing athlete {tessera_atleta}')
                except Exception as email_err:
                    current_app.logger.error(f'[EMAIL] Error in interest modification email process: {email_err}', exc_info=True)
            
            return jsonify(result if result else {'id': interest_id, 'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/ranking')
def get_rankings():
    """Get list of available rankings (qualifiche)"""
    try:
        client = OrionAPIClient()
        rankings = client.get_qualifiche()
        return jsonify(rankings)
    except Exception as e:
        current_app.logger.error(f"Error fetching rankings: {e}")
        return jsonify({'error': 'Failed to fetch rankings', 'details': str(e)}), 500

@bp.route('/api/ranking/official')
def get_official_ranking():
    """Get official FITARCO ranking data
    
    Required query parameters:
        code: Qualification code from ARC_qualifiche
        class_name: Exact class name (e.g., "Senior Maschile", "Junior Femminile")
        division: Division/category (e.g., "Compound", "Arco Nudo")
    """
    try:
        code = request.args.get('code')
        class_name = request.args.get('class_name')
        division = request.args.get('division')
        
        if not code or not class_name or not division:
            return jsonify({'error': 'Missing required parameters: code, class_name, division'}), 400
        
        client = OrionAPIClient()
        ranking_data = client.get_ranking_official(code, class_name, division)
        
        # Normalize class and division names for CSV lookup
        # CSV uses standardized format, API might use variations
        normalized_class = class_name
        normalized_division = division
        
        # Normalize class: Senior/Junior/Master/Allievi/Ragazzi/Giovanissimi + Maschile/Femminile
        class_lower = class_name.lower()
        if 'senior' in class_lower:
            normalized_class = class_name.replace('Seniores', 'Senior').replace('seniores', 'Senior')
        elif 'junior' in class_lower:
            normalized_class = class_name.replace('Juniores', 'Junior').replace('juniores', 'Junior')
        
        # Normalize division: add "Arco" prefix if not present
        division_lower = division.lower()
        if 'olimpic' in division_lower and 'arco' not in division_lower:
            normalized_division = 'Arco Olimpico'
        elif 'compound' in division_lower and 'arco' not in division_lower:
            normalized_division = 'Arco Compound'
        elif 'nudo' in division_lower and 'arco' not in division_lower:
            normalized_division = 'Arco Nudo'
        
        # Add available positions info if configured
        ranking_positions = get_ranking_positions()
        config = ranking_positions.get_positions(code, normalized_class, normalized_division)
        
        # Debug logging
        current_app.logger.info(f"Original params: code={code}, class={class_name}, division={division}")
        current_app.logger.info(f"Normalized params: class={normalized_class}, division={normalized_division}")
        current_app.logger.info(f"Found config: {config}")
        
        # If config exists, add it to each entry
        if config and isinstance(ranking_data, list):
            for entry in ranking_data:
                entry['max_positions'] = config['posti']
                entry['min_score'] = config['min_score']
            current_app.logger.info(f"Added max_positions={config['posti']}, min_score={config['min_score']} to {len(ranking_data)} entries")
        
        return jsonify(ranking_data)
    except Exception as e:
        current_app.logger.error(f"Error fetching official ranking: {e}")
        return jsonify({'error': 'Failed to fetch official ranking', 'details': str(e)}), 500


@bp.route('/api/ranking/positions')
def get_ranking_positions_api():
    """Get all configured ranking positions from CSV"""
    try:
        ranking_positions = get_ranking_positions()
        return jsonify(ranking_positions.get_all_positions())
    except Exception as e:
        current_app.logger.error(f"Error fetching ranking positions: {e}")
        return jsonify({'error': 'Failed to fetch ranking positions', 'details': str(e)}), 500


@bp.route('/api/ranking/positions/reload', methods=['POST'])
@login_required
def reload_ranking_positions():
    """Reload ranking positions CSV (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        ranking_positions = get_ranking_positions()
        ranking_positions.reload()
        return jsonify({'success': True, 'message': 'Ranking positions reloaded'})
    except Exception as e:
        current_app.logger.error(f"Error reloading ranking positions: {e}")
        return jsonify({'error': 'Failed to reload ranking positions', 'details': str(e)}), 500


@bp.route('/api/ranking/positions/upload', methods=['POST'])
@login_required
def upload_ranking_positions():
    """Upload new ranking positions CSV file (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        # Save to data directory
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(app_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        file_path = os.path.join(data_dir, 'ranking_positions.csv')
        file.save(file_path)
        
        # Reload the data
        ranking_positions = get_ranking_positions()
        ranking_positions.reload()
        
        return jsonify({
            'success': True, 
            'message': 'Ranking positions CSV uploaded and loaded successfully',
            'count': len(ranking_positions.positions)
        })
    except Exception as e:
        current_app.logger.error(f"Error uploading ranking positions: {e}")
        return jsonify({'error': 'Failed to upload ranking positions', 'details': str(e)}), 500


@bp.route('/api/ranking/positions/download')
@login_required
def download_ranking_positions():
    """Download current ranking positions CSV (admin only)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(app_dir, 'data')
        return send_from_directory(data_dir, 'ranking_positions.csv', as_attachment=True)
    except Exception as e:
        current_app.logger.error(f"Error downloading ranking positions: {e}")
        return jsonify({'error': 'Failed to download ranking positions', 'details': str(e)}), 500
