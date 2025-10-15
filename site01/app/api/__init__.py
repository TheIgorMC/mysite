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
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"API HTTP error: {e}")
            logger.error(f"Response text: {e.response.text if e.response else 'No response'}")
            raise  # Re-raise so Flask can handle it properly
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise  # Re-raise instead of returning None
    
    def get_athlete(self, athlete_id):
        """Get athlete information by ID"""
        return self._make_request('GET', f'/api/atleti?q={athlete_id}')
    
    def search_athlete(self, name):
        """Search for athletes by name"""
        return self._make_request('GET', '/api/atleti', params={'q': name})
    
    def get_athlete_results(self, athlete_id, competition_type=None, start_date=None, end_date=None, limit=500):
        """Get results for an athlete"""
        # API endpoint is /api/athlete/{tessera}/results
        params = {'limit': limit}
        if competition_type:
            params['event_type'] = competition_type
        # Note: start_date and end_date don't appear to be supported in the API spec
        
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
    
    def get_statistics(self, athlete_id):
        """Get athlete statistics"""
        # API expects 'athletes' as an array parameter
        return self._make_request('GET', '/api/stats', params={'athletes': [athlete_id]})
    
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
