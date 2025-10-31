"""
API Client for Cloudflare-protected external API
"""
import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class OrionAPIClient:
    """Client for interacting with Archery API via Cloudflare Access"""
    
    def __init__(self):
        base_url = current_app.config['API_BASE_URL']
        api_port = current_app.config['API_PORT']
        
        # Parse the base URL and reconstruct it with the port
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(base_url)
        
        # Reconstruct netloc with explicit port (if port is standard 443/80, it's optional)
        netloc = parsed.hostname
        if api_port and api_port not in ['80', '443']:
            netloc = f"{parsed.hostname}:{api_port}"
        elif api_port == '443' and parsed.scheme == 'https':
            # Standard HTTPS port, just use hostname
            netloc = parsed.hostname
        elif api_port == '80' and parsed.scheme == 'http':
            # Standard HTTP port, just use hostname
            netloc = parsed.hostname
        elif api_port:
            # Non-standard port, include it
            netloc = f"{parsed.hostname}:{api_port}"
        
        # Store the base URL without trailing slash
        self.base_url = urlunparse((
            parsed.scheme,
            netloc,
            parsed.path.rstrip('/'),
            '',
            '',
            ''
        ))
        
        logger.info(f"API Client initialized with base URL: {self.base_url}")
        
        self.headers = {
            'CF-Access-Client-Id': current_app.config['CF_ACCESS_ID'],
            'CF-Access-Client-Secret': current_app.config['CF_ACCESS_SECRET'],
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {method} {url}: {e}")
            raise

        # Log status and content-type for debugging
        content_type = response.headers.get('Content-Type', '')
        logger.debug(f"API response {response.status_code} {method} {url} content-type: {content_type}")

        # If there was an HTTP error, log response text (truncated) and raise
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            text_preview = (response.text[:1000] + '...') if response.text and len(response.text) > 1000 else response.text
            logger.error(f"API HTTP error for {method} {url}: {e}")
            logger.error(f"Response text (truncated): {text_preview}")
            raise

        # Try to parse JSON; if it's not JSON, log and raise informative error
        try:
            parsed = response.json()
        except ValueError as e:
            text_preview = (response.text[:2000] + '...') if response.text and len(response.text) > 2000 else response.text
            logger.error(f"Failed to parse JSON from API {method} {url}: {e}")
            logger.error(f"Response text (truncated): {text_preview}")
            raise

        # If API returned a primitive (string/number) instead of expected dict/list, log it
        if not isinstance(parsed, (dict, list)):
            logger.warning(f"API returned unexpected JSON type {type(parsed)} for {method} {url}: {repr(parsed)[:1000]}")

        return parsed
    
    def get_athlete(self, athlete_id):
        """Get athlete information by ID"""
        return self._make_request('GET', f'/api/atleti?q={athlete_id}')
    
    def search_athlete(self, name):
        """Search for athletes by name"""
        return self._make_request('GET', '/api/atleti', params={'q': name})
    
    def get_athlete_results(self, athlete_id, competition_type=None, start_date=None, end_date=None, limit=500):
        """Get results for an athlete using /api/athlete/{tessera}/results endpoint
        
        This endpoint returns actual competition results with scores and positions.
        
        Args:
            athlete_id: Athlete tessera ID
            competition_type: Optional filter by event type (passed as 'event_type' param)
            start_date: Optional start date filter (not supported by API, filtered client-side)
            end_date: Optional end date filter (not supported by API, filtered client-side)
            limit: Maximum number of results
            
        Returns:
            List of competition results with scores and positions
        """
        params = {'limit': limit}
        if competition_type:
            params['event_type'] = competition_type
        # Note: start_date and end_date are not supported by this endpoint
        # They should be filtered client-side after fetching results
        
        return self._make_request('GET', f'/api/athlete/{athlete_id}/results', params=params)
    
    def get_competition_types(self):
        """Get list of available competition types"""
        return self._make_request('GET', '/api/event_types')
    
    def get_competitions(self, status=None):
        """Get list of competitions"""
        params = {}
        if status:
            params['status'] = status
        # Note: competitions endpoint doesn't exist in API spec - keeping for backward compatibility
        return self._make_request('GET', '/api/competitions', params=params)
    
    def get_competition(self, competition_id):
        """Get competition details"""
        # Note: competition detail endpoint doesn't exist in API spec - keeping for backward compatibility
        return self._make_request('GET', f'/api/competitions/{competition_id}')
    
    def submit_subscription(self, competition_id, user_data):
        """Submit competition subscription"""
        # Note: subscription endpoint doesn't exist in API spec - keeping for backward compatibility
        return self._make_request('POST', f'/api/competitions/{competition_id}/subscribe', data=user_data)
    
    def get_statistics(self, athlete_ids, event_type=None, from_date=None, to_date=None, period_months=None):
        """Get athlete statistics chart data from /api/stats endpoint
        
        Args:
            athlete_ids: Single athlete ID or list of athlete IDs
            event_type: Optional event type filter (e.g., "Indoor", "18 m")
            from_date: Optional start date filter (YYYY-MM-DD)
            to_date: Optional end date filter (YYYY-MM-DD)
            period_months: Optional period in months
            
        Returns:
            Chart data with labels and datasets
        """
        # Ensure athlete_ids is a list
        if not isinstance(athlete_ids, list):
            athlete_ids = [athlete_ids]
        
        params = {'athletes': athlete_ids}
        if event_type:
            params['event_type'] = event_type
        if from_date:
            params['from_date'] = from_date
        if to_date:
            params['to_date'] = to_date
        if period_months:
            params['period_months'] = period_months
            
        return self._make_request('GET', '/api/stats', params=params)
    
    def get_competitions(self, future=False, limit=100):
        """Get list of competitions (gare)"""
        params = {'limit': limit}
        if future:
            params['future'] = 'true'
        return self._make_request('GET', '/api/gare', params=params)
    
    def get_turns(self, codice_gara):
        """Get turns (turni) for a specific competition"""
        return self._make_request('GET', '/api/turni', params={'codice_gara': codice_gara})
    
    def get_inviti(self, codice=None, only_open=False, only_youth=False):
        """Get invitations (inviti) from FastAPI"""
        params = {}
        if codice:
            params['codice'] = codice
        if only_open:
            params['only_open'] = 'true'
        if only_youth:
            params['only_youth'] = 'true'
        return self._make_request('GET', '/api/inviti', params=params)
    
    def get_subscriptions(self, tessera_atleta):
        """Get subscriptions (iscrizioni) for an athlete"""
        return self._make_request('GET', '/api/iscrizioni', params={'tessera_atleta': tessera_atleta})
    
    def get_all_subscriptions(self):
        """Get all subscriptions (iscrizioni) - mass export"""
        # Use export=full parameter as per API spec
        return self._make_request('GET', '/api/iscrizioni', params={'export': 'full'})
    
    def create_subscription(self, codice_gara, tessera_atleta, categoria, turno, classe='', stato='confermato', note=''):
        """Create a new subscription (iscrizione)"""
        data = {
            'codice_gara': codice_gara,
            'tessera_atleta': tessera_atleta,
            'categoria': categoria,
            'classe': classe,
            'turno': turno,
            'stato': stato,
            'note': note
        }
        return self._make_request('POST', '/api/iscrizioni', data=data)
    
    def delete_subscription(self, subscription_id):
        """Delete a subscription (iscrizione) by ID"""
        return self._make_request('DELETE', f'/api/iscrizioni/{subscription_id}')

    def update_subscription(self, subscription_id, data):
        """Update a subscription (iscrizione) by ID"""
        return self._make_request('PATCH', f'/api/iscrizioni/{subscription_id}', json=data)
    
    # Interest expressions (interesse) endpoints
    def get_interests(self, tessera_atleta=None, codice_gara=None):
        """Get interest expressions for an athlete or competition"""
        params = {}
        if tessera_atleta:
            params['tessera_atleta'] = tessera_atleta
        if codice_gara:
            params['codice_gara'] = codice_gara
        return self._make_request('GET', '/api/interesse', params=params)
    
    def get_all_interests(self):
        """Get all interest expressions - mass export"""
        # Call without filters to get all (both params are optional per API spec)
        return self._make_request('GET', '/api/interesse')
    
    def create_interest(self, codice_gara, tessera_atleta, categoria, classe='', note=''):
        """Create a new interest expression"""
        from datetime import date
        data = {
            'codice_gara': codice_gara,
            'tessera_atleta': tessera_atleta,
            'categoria': categoria,
            'classe': classe,
            'data_interesse': date.today().isoformat(),  # Add current date in YYYY-MM-DD format
            'note': note,
            'stato': 'attivo'
        }
        logger.info(f"Creating interest with data: {data}")
        return self._make_request('POST', '/api/interesse', data=data)
    
    def delete_interest(self, interest_id):
        """Delete an interest expression by ID"""
        return self._make_request('DELETE', f'/api/interesse/{interest_id}')
    
    # ==================== MATERIALS (STRINGMAKING STOCK) ====================
    
    def get_materials(self, q=None, tipo=None, low_stock_lt=None, limit=100, offset=0):
        """
        Get materials with optional filters
        
        Args:
            q: Search in materiale/colore/spessore
            tipo: Filter by type (string, serving, center, etc.)
            low_stock_lt: Show only items with rimasto below threshold
            limit: Number of results (default 100)
            offset: Offset for pagination (default 0)
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        if q:
            params['q'] = q
        if tipo:
            params['tipo'] = tipo
        if low_stock_lt is not None:
            params['low_stock_lt'] = low_stock_lt
        
        return self._make_request('GET', '/api/materiali', params=params)
    
    def create_material(self, materiale, colore, spessore, rimasto, costo, tipo):
        """
        Create a new material entry
        
        Args:
            materiale: Material name (e.g., "BCY X99")
            colore: Color
            spessore: Thickness
            rimasto: Remaining quantity
            costo: Cost per unit
            tipo: Type (string, serving, center, etc.)
        """
        data = {
            'materiale': materiale,
            'colore': colore,
            'spessore': spessore,
            'rimasto': float(rimasto),
            'costo': float(costo),
            'tipo': tipo
        }
        return self._make_request('POST', '/api/materiali', data=data)
    
    def update_material(self, material_id, **fields):
        """
        Update material fields (partial update)
        
        Args:
            material_id: ID of the material
            **fields: Any fields to update (rimasto, costo, etc.)
        """
        return self._make_request('PATCH', f'/api/materiali/{material_id}', data=fields)
    
    def consume_material(self, material_id, quantita):
        """
        Consume a quantity from stock (atomic, non-negative)
        
        Args:
            material_id: ID of the material
            quantita: Quantity to consume
        
        Returns:
            Updated material with new rimasto value
        
        Raises:
            409 if stock insufficient
        """
        data = {'quantita': float(quantita)}
        return self._make_request('POST', f'/api/materiali/{material_id}/consume', data=data)
    
    def delete_material(self, material_id):
        """Delete a material entry"""
        return self._make_request('DELETE', f'/api/materiali/{material_id}')
    
    # ==================== ELECTRONICS ====================
    
    def get_components(self, q=None, category=None, in_stock=None, limit=100, offset=0):
        """
        Get electronic components with optional filters
        
        Args:
            q: Search in name/description/mpn
            category: Filter by category
            in_stock: Filter by stock status (true/false)
            limit: Number of results (default 100)
            offset: Offset for pagination (default 0)
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        if q:
            params['q'] = q
        if category:
            params['category'] = category
        if in_stock is not None:
            params['in_stock'] = in_stock
        
        return self._make_request('GET', '/api/elec/components', params=params)
    
    def search_components(self, q):
        """Search components by name, description, or MPN"""
        return self._make_request('GET', '/api/elec/components/search', params={'q': q})
    
    def create_component(self, name, category, description=None, mpn=None, datasheet_url=None, 
                        stock_qty=0, min_stock=0, unit_price=0.0, supplier=None, notes=None):
        """Create a new electronic component"""
        data = {
            'name': name,
            'category': category,
            'description': description,
            'mpn': mpn,
            'datasheet_url': datasheet_url,
            'stock_qty': int(stock_qty),
            'min_stock': int(min_stock),
            'unit_price': float(unit_price),
            'supplier': supplier,
            'notes': notes
        }
        return self._make_request('POST', '/api/elec/components', data=data)
    
    def update_component(self, component_id, **fields):
        """Update component fields (partial update)"""
        return self._make_request('PATCH', f'/api/elec/components/{component_id}', data=fields)
    
    def delete_component(self, component_id):
        """Delete a component"""
        return self._make_request('DELETE', f'/api/elec/components/{component_id}')
    
    def get_boards(self, q=None, limit=100, offset=0):
        """
        Get PCB boards with optional search
        
        Args:
            q: Search in board name/description
            limit: Number of results (default 100)
            offset: Offset for pagination (default 0)
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        if q:
            params['q'] = q
        
        return self._make_request('GET', '/api/elec/boards', params=params)
    
    def create_board(self, name, version, description=None, schematic_file_id=None, 
                    layout_file_id=None, gerber_file_id=None):
        """Create a new PCB board"""
        data = {
            'name': name,
            'version': version,
            'description': description,
            'schematic_file_id': schematic_file_id,
            'layout_file_id': layout_file_id,
            'gerber_file_id': gerber_file_id
        }
        return self._make_request('POST', '/api/elec/boards', data=data)
    
    def update_board(self, board_id, **fields):
        """Update board fields (partial update)"""
        return self._make_request('PATCH', f'/api/elec/boards/{board_id}', data=fields)
    
    def delete_board(self, board_id):
        """Delete a board"""
        return self._make_request('DELETE', f'/api/elec/boards/{board_id}')
    
    def get_board_bom(self, board_id):
        """Get BOM for a specific board"""
        return self._make_request('GET', f'/api/elec/boards/{board_id}/bom')
    
    def upload_board_bom(self, board_id, bom_items):
        """
        Upload/replace BOM for a board
        
        Args:
            board_id: Board ID
            bom_items: List of dicts with keys: component_id, quantity, designators
        """
        return self._make_request('POST', f'/api/elec/boards/{board_id}/bom/upload', data=bom_items)
    
    def get_production_jobs(self, status=None, board_id=None, limit=100, offset=0):
        """
        Get production jobs with optional filters
        
        Args:
            status: Filter by status (pending, in_progress, completed, cancelled)
            board_id: Filter by board ID
            limit: Number of results (default 100)
            offset: Offset for pagination (default 0)
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        if status:
            params['status'] = status
        if board_id:
            params['board_id'] = board_id
        
        return self._make_request('GET', '/api/elec/jobs', params=params)
    
    def create_production_job(self, name, description=None, target_quantity=1, priority='normal'):
        """
        Create a new production job
        
        Args:
            name: Job name
            description: Job description
            target_quantity: Number of units to produce
            priority: Priority level (low, normal, high, urgent)
        """
        data = {
            'name': name,
            'description': description,
            'target_quantity': int(target_quantity),
            'priority': priority
        }
        return self._make_request('POST', '/api/elec/jobs', data=data)
    
    def get_production_job(self, job_id):
        """Get details of a specific production job"""
        return self._make_request('GET', f'/api/elec/jobs/{job_id}')
    
    def update_production_job(self, job_id, **fields):
        """Update production job fields (partial update)"""
        return self._make_request('PATCH', f'/api/elec/jobs/{job_id}', data=fields)
    
    def delete_production_job(self, job_id):
        """Delete a production job"""
        return self._make_request('DELETE', f'/api/elec/jobs/{job_id}')
    
    def add_board_to_job(self, job_id, board_id, quantity):
        """
        Add a board to a production job
        
        Args:
            job_id: Production job ID
            board_id: Board ID to add
            quantity: Number of this board to produce
        """
        data = {
            'board_id': board_id,
            'quantity': int(quantity)
        }
        return self._make_request('POST', f'/api/elec/jobs/{job_id}/boards', data=data)
    
    def check_job_stock(self, job_id):
        """Check stock availability for all boards in a production job"""
        return self._make_request('GET', f'/api/elec/jobs/{job_id}/check_stock')
    
    def reserve_job_stock(self, job_id):
        """Reserve stock for a production job (atomically decrements stock)"""
        return self._make_request('POST', f'/api/elec/jobs/{job_id}/reserve_stock')
    
    def get_job_missing_bom(self, job_id):
        """Get boards in job that don't have BOM defined"""
        return self._make_request('GET', f'/api/elec/jobs/{job_id}/missing_bom')
    
    def get_files(self, category=None, board_id=None, limit=100, offset=0):
        """
        Get files with optional filters
        
        Args:
            category: Filter by category (schematic, layout, gerber, datasheet, other)
            board_id: Filter by associated board ID
            limit: Number of results (default 100)
            offset: Offset for pagination (default 0)
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        if category:
            params['category'] = category
        if board_id:
            params['board_id'] = board_id
        
        return self._make_request('GET', '/api/elec/files', params=params)
    
    def register_file(self, filename, category, storage_path, board_id=None, description=None):
        """
        Register a file in the database
        
        Args:
            filename: Original filename
            category: File category (schematic, layout, gerber, datasheet, other)
            storage_path: Path where file is stored
            board_id: Optional associated board ID
            description: Optional description
        """
        data = {
            'filename': filename,
            'category': category,
            'storage_path': storage_path,
            'board_id': board_id,
            'description': description
        }
        return self._make_request('POST', '/api/elec/files/register', data=data)
    
    def delete_file(self, file_id):
        """Delete a file record (does not delete actual file from storage)"""
        return self._make_request('DELETE', f'/api/elec/files/{file_id}')
