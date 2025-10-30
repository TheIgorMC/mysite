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
    
    def get_athlete_results(self, athlete_id, limit=500):
        """Get results/registrations for an athlete using /api/iscrizioni endpoint
        
        Returns list of competition registrations/results for the athlete.
        """
        return self._make_request('GET', '/api/iscrizioni', params={'tessera': athlete_id, 'limit': limit})
    
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
