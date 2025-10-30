"""
Archery routes blueprint
"""
from flask import Blueprint, render_template, request, jsonify, current_app
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
        if not isinstance(results, list):
            current_app.logger.error(f"Unexpected API payload for athlete results (athlete_id={athlete_id}): {results}")
            # If it's a dict with a key 'results', try to extract it
            if isinstance(results, dict) and 'results' in results and isinstance(results['results'], list):
                results = results['results']
            else:
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

        # DEBUG: Log what we actually got from the API
        current_app.logger.info(f"API returned {len(all_results) if isinstance(all_results, list) else 'non-list'} results")
        if all_results and len(all_results) > 0:
            current_app.logger.info(f"First result keys: {list(all_results[0].keys())}")
            current_app.logger.info(f"First result sample: {all_results[0]}")

        # Defensive checks for all_results
        if all_results is None:
            current_app.logger.error(f"API returned None for all_results (athlete_id={athlete_id})")
            return jsonify({'career': None, 'filtered': None, 'chart_data': stats_data, 'athlete_id': athlete_id}), 502
        if not isinstance(all_results, list):
            current_app.logger.error(f"Unexpected API payload for all_results (athlete_id={athlete_id}): {all_results}")
            if isinstance(all_results, dict) and 'results' in all_results and isinstance(all_results['results'], list):
                all_results = all_results['results']
            else:
                return jsonify({'error': 'Unexpected API response format for results', 'details': str(type(all_results))}), 502

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
        # Try multiple possible field names since API spec may not match reality
        transformed_results = []
        for result in all_results:
            # Try to extract fields with multiple possible names
            score = result.get('punteggio_tot') or result.get('punteggio') or result.get('score')
            position = result.get('posizione') or result.get('position')
            competition_name = result.get('nome_gara') or result.get('competition_name')
            competition_type = result.get('tipo_gara') or result.get('tipo') or result.get('event_type')
            date = result.get('data_gara') or result.get('date') or result.get('data_inizio')
            athlete_name = result.get('nome_atleta') or result.get('atleta') or result.get('nome_completo')
            
            transformed_results.append({
                'athlete': athlete_name,
                'competition_name': competition_name,
                'competition_type': competition_type,
                'date': normalize_date(date),
                'position': position,
                'score': score
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
        current_app.logger.error(f"Error fetching athlete statistics: {str(e)}")
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
            result = client.delete_subscription(subscription_id)
            return jsonify(result if result else {'id': subscription_id, 'status': 'deleted'})
        
        elif request.method == 'PATCH':
            data = request.get_json()
            result = client.update_subscription(subscription_id, data)
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
            return jsonify(result)
        except Exception as e:
            current_app.logger.error(f"Error creating interest: {e}")
            return jsonify({'error': str(e)}), 500


@bp.route('/api/interesse/<int:interest_id>', methods=['DELETE'])
@login_required
def delete_interesse(interest_id):
    """Delete an interest expression by ID"""
    client = OrionAPIClient()
    
    try:
        result = client.delete_interest(interest_id)
        return jsonify(result if result else {'id': interest_id, 'status': 'deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

