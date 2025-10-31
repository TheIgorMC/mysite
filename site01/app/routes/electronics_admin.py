"""
Electronics Admin Management Routes
Admin-only portal for electronics inventory, boards, BOMs, production jobs, and file management
"""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
import requests
from functools import wraps

bp = Blueprint('electronics_admin', __name__, url_prefix='/admin/electronics')

def admin_required(f):
    """Decorator to ensure user is admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def api_request(endpoint, method='GET', data=None, params=None):
    """
    Make authenticated request to the API
    
    Args:
        endpoint: API endpoint path (e.g., '/api/elec/components')
        method: HTTP method
        data: Request body for POST/PATCH
        params: Query parameters
    
    Returns:
        Response JSON or None on error
    """
    api_base = current_app.config['API_BASE_URL']
    url = f"{api_base}{endpoint}"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Add Cloudflare Access headers if configured
    cf_id = current_app.config.get('CF_ACCESS_ID')
    cf_secret = current_app.config.get('CF_ACCESS_SECRET')
    if cf_id and cf_secret:
        headers['CF-Access-Client-Id'] = cf_id
        headers['CF-Access-Client-Secret'] = cf_secret
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"API request failed: {e}")
        return None

@bp.route('/')
@admin_required
def index():
    """Electronics management portal main page"""
    storage_url = current_app.config.get('ELECTRONICS_STORAGE_URL', 'https://elec.orion-project.it')
    return render_template('admin/electronics.html', storage_url=storage_url)

# ============================================================================
# COMPONENTS API ENDPOINTS
# ============================================================================

@bp.route('/api/components', methods=['GET'])
@admin_required
def get_components():
    """Get components list with optional filters"""
    params = {
        'q': request.args.get('q', ''),
        'product_type': request.args.get('product_type', ''),
        'package': request.args.get('package', ''),
        'limit': request.args.get('limit', 100),
        'offset': request.args.get('offset', 0)
    }
    # Remove empty params
    params = {k: v for k, v in params.items() if v}
    
    result = api_request('/api/elec/components', params=params)
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to fetch components'}), 500

@bp.route('/api/components/search', methods=['GET'])
@admin_required
def search_components():
    """Smart component search (e.g., R0402 -> all 0402 resistors)"""
    q = request.args.get('q', '')
    result = api_request('/api/elec/components/search', params={'q': q})
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Search failed'}), 500

@bp.route('/api/components', methods=['POST'])
@admin_required
def create_component():
    """Create new component"""
    data = request.get_json()
    result = api_request('/api/elec/components', method='POST', data=data)
    if result is not None:
        return jsonify(result), 201
    return jsonify({'error': 'Failed to create component'}), 500

@bp.route('/api/components/<component_id>', methods=['PATCH'])
@admin_required
def update_component(component_id):
    """Update component (e.g., quantity, price)"""
    data = request.get_json()
    result = api_request(f'/api/elec/components/{component_id}', method='PATCH', data=data)
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to update component'}), 500

@bp.route('/api/components/<component_id>', methods=['DELETE'])
@admin_required
def delete_component(component_id):
    """Delete component"""
    result = api_request(f'/api/elec/components/{component_id}', method='DELETE')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to delete component'}), 500

# ============================================================================
# BOARDS API ENDPOINTS
# ============================================================================

@bp.route('/api/boards', methods=['GET'])
@admin_required
def get_boards():
    """Get boards list"""
    result = api_request('/api/elec/boards')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to fetch boards'}), 500

@bp.route('/api/boards', methods=['POST'])
@admin_required
def create_board():
    """Create new board"""
    data = request.get_json()
    result = api_request('/api/elec/boards', method='POST', data=data)
    if result is not None:
        return jsonify(result), 201
    return jsonify({'error': 'Failed to create board'}), 500

@bp.route('/api/boards/<board_id>', methods=['PATCH'])
@admin_required
def update_board(board_id):
    """Update board info"""
    data = request.get_json()
    result = api_request(f'/api/elec/boards/{board_id}', method='PATCH', data=data)
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to update board'}), 500

@bp.route('/api/boards/<board_id>', methods=['DELETE'])
@admin_required
def delete_board(board_id):
    """Delete board"""
    result = api_request(f'/api/elec/boards/{board_id}', method='DELETE')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to delete board'}), 500

@bp.route('/api/boards/<board_id>/bom', methods=['GET'])
@admin_required
def get_board_bom(board_id):
    """Get board's BOM"""
    result = api_request(f'/api/elec/boards/{board_id}/bom')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to fetch BOM'}), 500

@bp.route('/api/boards/<board_id>/bom', methods=['POST'])
@admin_required
def update_board_bom(board_id):
    """Add/update components in board BOM"""
    data = request.get_json()
    result = api_request(f'/api/elec/boards/{board_id}/bom', method='POST', data=data)
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to update BOM'}), 500

@bp.route('/api/boards/<board_id>/bom/<component_id>', methods=['DELETE'])
@admin_required
def delete_bom_component(board_id, component_id):
    """Remove component from board BOM"""
    result = api_request(f'/api/elec/boards/{board_id}/bom/{component_id}', method='DELETE')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to remove component from BOM'}), 500

@bp.route('/api/boards/<board_id>/upload_bom', methods=['POST'])
@admin_required
def upload_board_bom(board_id):
    """Upload BOM CSV - proxy to API"""
    # This endpoint expects the frontend to parse CSV and send component data
    # Format: [{"component_id": "...", "qty": 10}, ...]
    data = request.get_json()
    result = api_request(f'/api/elec/boards/{board_id}/upload_bom', method='POST', data=data)
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to upload BOM'}), 500

# ============================================================================
# JOBS API ENDPOINTS
# ============================================================================

@bp.route('/api/jobs', methods=['GET'])
@admin_required
def get_jobs():
    """Get production jobs list"""
    result = api_request('/api/elec/jobs')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to fetch jobs'}), 500

@bp.route('/api/jobs', methods=['POST'])
@admin_required
def create_job():
    """Create new production job"""
    data = request.get_json()
    result = api_request('/api/elec/jobs', method='POST', data=data)
    if result is not None:
        return jsonify(result), 201
    return jsonify({'error': 'Failed to create job'}), 500

@bp.route('/api/jobs/<job_id>', methods=['GET'])
@admin_required
def get_job_details(job_id):
    """Get job details with BOM"""
    result = api_request(f'/api/elec/jobs/{job_id}')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to fetch job details'}), 500

@bp.route('/api/jobs/<job_id>', methods=['PATCH'])
@admin_required
def update_job(job_id):
    """Update job status/quantity/due_date"""
    data = request.get_json()
    result = api_request(f'/api/elec/jobs/{job_id}', method='PATCH', data=data)
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to update job'}), 500

@bp.route('/api/jobs/<job_id>/check_stock', methods=['GET'])
@admin_required
def check_job_stock(job_id):
    """Check if sufficient stock for job"""
    result = api_request(f'/api/elec/jobs/{job_id}/check_stock')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to check stock'}), 500

@bp.route('/api/jobs/<job_id>/reserve_stock', methods=['POST'])
@admin_required
def reserve_job_stock(job_id):
    """Reserve components for job (atomic operation)"""
    result = api_request(f'/api/elec/jobs/{job_id}/reserve_stock', method='POST')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to reserve stock'}), 500

@bp.route('/api/jobs/<job_id>/missing_bom', methods=['GET'])
@admin_required
def get_missing_bom(job_id):
    """Get list of missing components for job"""
    result = api_request(f'/api/elec/jobs/{job_id}/missing_bom')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to fetch missing components'}), 500

# ============================================================================
# FILES API ENDPOINTS
# ============================================================================

@bp.route('/api/boards/<board_id>/files', methods=['GET'])
@admin_required
def get_board_files(board_id):
    """Get list of files for a board"""
    result = api_request(f'/api/elec/boards/{board_id}/files')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to fetch files'}), 500

@bp.route('/api/boards/<board_id>/files', methods=['POST'])
@admin_required
def register_board_file(board_id):
    """Register file metadata (file must already exist on nginx storage)"""
    data = request.get_json()
    result = api_request(f'/api/elec/boards/{board_id}/files', method='POST', data=data)
    if result is not None:
        return jsonify(result), 201
    return jsonify({'error': 'Failed to register file'}), 500

@bp.route('/api/boards/<board_id>/files/<file_id>', methods=['DELETE'])
@admin_required
def delete_board_file(board_id, file_id):
    """Delete file metadata"""
    result = api_request(f'/api/elec/boards/{board_id}/files/{file_id}', method='DELETE')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to delete file'}), 500

@bp.route('/api/files/types', methods=['GET'])
@admin_required
def get_file_types():
    """Get supported file types"""
    result = api_request('/api/elec/files/types')
    if result is not None:
        return jsonify(result)
    return jsonify({'error': 'Failed to fetch file types'}), 500

# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@bp.route('/api/bom/export', methods=['GET'])
@admin_required
def export_bom():
    """Export BOM as CSV"""
    params = {
        'format': request.args.get('format', 'csv'),
        'job_id': request.args.get('job_id', ''),
        'board_id': request.args.get('board_id', ''),
        'qty': request.args.get('qty', '')
    }
    # Remove empty params
    params = {k: v for k, v in params.items() if v}
    
    # For CSV export, we need to proxy the response
    api_base = current_app.config['API_BASE_URL']
    url = f"{api_base}/api/elec/bom/export"
    
    headers = {
        'Accept': 'text/csv'
    }
    
    cf_id = current_app.config.get('CF_ACCESS_ID')
    cf_secret = current_app.config.get('CF_ACCESS_SECRET')
    if cf_id and cf_secret:
        headers['CF-Access-Client-Id'] = cf_id
        headers['CF-Access-Client-Secret'] = cf_secret
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        from flask import Response
        return Response(
            response.content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=bom_export.csv'
            }
        )
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"BOM export failed: {e}")
        return jsonify({'error': 'Failed to export BOM'}), 500
