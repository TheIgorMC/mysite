"""
Electronics Admin Management Routes
Admin-only portal for electronics inventory, boards, BOMs, production jobs, and file management
"""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
import requests
import csv
import io
from functools import wraps
from app.api import OrionAPIClient

# Try to import openpyxl, provide helpful error if missing
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    current_app.logger.warning("openpyxl not installed - Excel BOM parsing will not work")

bp = Blueprint('electronics_admin', __name__, url_prefix='/admin/electronics')

# Also register API proxy routes under /electronics/api/ (like /archery/api/)
api_bp = Blueprint('electronics_api', __name__, url_prefix='/electronics/api')

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
    
    current_app.logger.info(f"[Electronics API] {method} {url}")
    if params:
        current_app.logger.info(f"[Electronics API] Params: {params}")
    if data:
        current_app.logger.info(f"[Electronics API] Data: {data}")
    
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
        current_app.logger.info(f"[Electronics API] Using CF Access authentication")
    else:
        current_app.logger.warning(f"[Electronics API] No CF Access credentials configured")
    
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
            current_app.logger.error(f"[Electronics API] Invalid method: {method}")
            return None
        
        current_app.logger.info(f"[Electronics API] Response status: {response.status_code}")
        
        if response.status_code >= 400:
            current_app.logger.error(f"[Electronics API] Error response: {response.text}")
        
        response.raise_for_status()
        result = response.json()
        current_app.logger.info(f"[Electronics API] Success: {len(str(result))} bytes")
        return result
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"[Electronics API] Request failed: {str(e)}")
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
    current_app.logger.info("[Electronics] get_components called")
    
    params = {
        'q': request.args.get('q', ''),
        'product_type': request.args.get('product_type', ''),
        'package': request.args.get('package', ''),
        'limit': request.args.get('limit', 100),
        'offset': request.args.get('offset', 0)
    }
    # Remove empty params
    params = {k: v for k, v in params.items() if v}
    
    current_app.logger.info(f"[Electronics] Calling API with params: {params}")
    result = api_request('/api/elec/components', params=params)
    
    if result is not None:
        current_app.logger.info(f"[Electronics] Returning {len(result.get('components', []))} components")
        return jsonify(result)
    
    current_app.logger.error("[Electronics] API request failed, returning error")
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

# ============================================================================
# PUBLIC API PROXY ROUTES (like /archery/api/)
# These routes proxy to the external API and are used by the frontend JavaScript
# ============================================================================

@api_bp.route('/components', methods=['GET'])
@login_required
def api_proxy_get_components():
    """Proxy: Get components list"""
    result = api_request('/api/elec/components', params=request.args.to_dict())
    return jsonify(result) if result else (jsonify({'error': 'Failed to fetch components'}), 500)

@api_bp.route('/components/search', methods=['GET'])
@login_required
def api_proxy_search_components():
    """Proxy: Smart component search"""
    params = request.args.to_dict()
    
    # API requires 'q' parameter - provide empty string if missing
    if 'q' not in params or not params['q']:
        params['q'] = ''
    
    result = api_request('/api/elec/components/search', params=params)
    return jsonify(result) if result else (jsonify({'error': 'Search failed'}), 500)

@api_bp.route('/components/types', methods=['GET'])
@login_required
def get_component_types():
    """Get unique component types from database"""
    try:
        api_client = OrionAPIClient()
        components = api_client.get_components(limit=10000)
        
        if not isinstance(components, list):
            return jsonify([])
        
        # Extract unique types/categories
        types = set()
        for comp in components:
            comp_type = comp.get('product_type') or comp.get('category')
            if comp_type:
                types.add(comp_type)
        
        return jsonify(sorted(list(types)))
    except Exception as e:
        current_app.logger.error(f"[Component Types] Error: {e}")
        return jsonify([])

@api_bp.route('/components/packages', methods=['GET'])
@login_required
def get_component_packages():
    """Get unique component packages/footprints from database"""
    try:
        api_client = OrionAPIClient()
        components = api_client.get_components(limit=10000)
        
        if not isinstance(components, list):
            return jsonify([])
        
        # Extract unique packages
        packages = set()
        for comp in components:
            pkg = comp.get('package')
            if pkg:
                packages.add(pkg)
        
        return jsonify(sorted(list(packages)))
    except Exception as e:
        current_app.logger.error(f"[Component Packages] Error: {e}")
        return jsonify([])

@api_bp.route('/components', methods=['POST'])
@login_required
def api_proxy_create_component():
    """Proxy: Create component"""
    result = api_request('/api/elec/components', method='POST', data=request.get_json())
    return (jsonify(result), 201) if result else (jsonify({'error': 'Failed to create component'}), 500)

@api_bp.route('/components/<component_id>', methods=['PATCH'])
@login_required
def api_proxy_update_component(component_id):
    """Proxy: Update component"""
    result = api_request(f'/api/elec/components/{component_id}', method='PATCH', data=request.get_json())
    return jsonify(result) if result else (jsonify({'error': 'Failed to update component'}), 500)

@api_bp.route('/components/<component_id>', methods=['DELETE'])
@login_required
def api_proxy_delete_component(component_id):
    """Proxy: Delete component"""
    result = api_request(f'/api/elec/components/{component_id}', method='DELETE')
    return jsonify(result) if result else (jsonify({'error': 'Failed to delete component'}), 500)

@api_bp.route('/boards', methods=['GET'])
@login_required
def api_proxy_get_boards():
    """Proxy: Get boards list"""
    result = api_request('/api/elec/boards', params=request.args.to_dict())
    return jsonify(result) if result else (jsonify({'error': 'Failed to fetch boards'}), 500)

@api_bp.route('/boards', methods=['POST'])
@login_required
def api_proxy_create_board():
    """Proxy: Create board"""
    result = api_request('/api/elec/boards', method='POST', data=request.get_json())
    return (jsonify(result), 201) if result else (jsonify({'error': 'Failed to create board'}), 500)

@api_bp.route('/boards/<board_id>', methods=['GET'])
@login_required
def api_proxy_get_board(board_id):
    """Proxy: Get board details"""
    result = api_request(f'/api/elec/boards/{board_id}')
    return jsonify(result) if result else (jsonify({'error': 'Failed to fetch board'}), 500)

@api_bp.route('/boards/<board_id>/bom', methods=['GET'])
@login_required
def api_proxy_get_board_bom(board_id):
    """Proxy: Get board BOM"""
    result = api_request(f'/api/elec/boards/{board_id}/bom')
    return jsonify(result) if result else (jsonify({'error': 'Failed to fetch BOM'}), 500)

@api_bp.route('/boards/<board_id>/bom/upload', methods=['POST'])
@login_required
def api_proxy_upload_bom(board_id):
    """Proxy: Upload BOM CSV"""
    result = api_request(f'/api/elec/boards/{board_id}/bom/upload', method='POST', data=request.get_json())
    return jsonify(result) if result else (jsonify({'error': 'Failed to upload BOM'}), 500)

@api_bp.route('/jobs', methods=['GET'])
@login_required
def api_proxy_get_jobs():
    """Proxy: Get jobs list"""
    try:
        result = api_request('/api/elec/jobs', params=request.args.to_dict())
        if result is None:
            current_app.logger.error("[Jobs Proxy] API request returned None")
            return jsonify({'error': 'Failed to fetch jobs - API returned no data'}), 500
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"[Jobs Proxy] Exception: {e}", exc_info=True)
        return jsonify({'error': f'Failed to fetch jobs: {str(e)}'}), 500

@api_bp.route('/jobs', methods=['POST'])
@login_required
def api_proxy_create_job():
    """Proxy: Create job"""
    result = api_request('/api/elec/jobs', method='POST', data=request.get_json())
    return (jsonify(result), 201) if result else (jsonify({'error': 'Failed to create job'}), 500)

@api_bp.route('/jobs/<job_id>', methods=['GET'])
@login_required
def api_proxy_get_job(job_id):
    """Proxy: Get job details"""
    result = api_request(f'/api/elec/jobs/{job_id}')
    return jsonify(result) if result else (jsonify({'error': 'Failed to fetch job'}), 500)

@api_bp.route('/jobs/<job_id>/boards', methods=['POST'])
@login_required
def api_proxy_add_board_to_job(job_id):
    """Proxy: Add board to job"""
    result = api_request(f'/api/elec/jobs/{job_id}/boards', method='POST', data=request.get_json())
    return jsonify(result) if result else (jsonify({'error': 'Failed to add board'}), 500)

@api_bp.route('/jobs/<job_id>/check_stock', methods=['GET'])
@login_required
def api_proxy_check_job_stock(job_id):
    """Proxy: Check stock for job"""
    result = api_request(f'/api/elec/jobs/{job_id}/check_stock')
    return jsonify(result) if result else (jsonify({'error': 'Failed to check stock'}), 500)

@api_bp.route('/jobs/<job_id>/reserve_stock', methods=['POST'])
@login_required
def api_proxy_reserve_stock(job_id):
    """Proxy: Reserve stock for job"""
    result = api_request(f'/api/elec/jobs/{job_id}/reserve_stock', method='POST')
    return jsonify(result) if result else (jsonify({'error': 'Failed to reserve stock'}), 500)

@api_bp.route('/jobs/<job_id>/missing_bom', methods=['GET'])
@login_required
def api_proxy_missing_bom(job_id):
    """Proxy: Get missing components BOM"""
    result = api_request(f'/api/elec/jobs/{job_id}/missing_bom')
    return jsonify(result) if result else (jsonify({'error': 'Failed to generate BOM'}), 500)

@api_bp.route('/files', methods=['GET'])
@login_required
def api_proxy_get_files():
    """Proxy: Get files list"""
    result = api_request('/api/elec/files', params=request.args.to_dict())
    return jsonify(result) if result else (jsonify({'error': 'Failed to fetch files'}), 500)

@api_bp.route('/files/register', methods=['POST'])
@login_required
def api_proxy_register_file():
    """Proxy: Register file"""
    result = api_request('/api/elec/files', method='POST', data=request.get_json())
    return (jsonify(result), 201) if result else (jsonify({'error': 'Failed to register file'}), 500)

@api_bp.route('/files/<file_id>', methods=['DELETE'])
@login_required
def api_proxy_delete_file(file_id):
    """Proxy: Delete file"""
    result = api_request(f'/api/elec/files/{file_id}', method='DELETE')
    return jsonify(result) if result else (jsonify({'error': 'Failed to delete file'}), 500)

# ==================== ORDER IMPORTER ====================

@api_bp.route('/orders/parse', methods=['POST'])
@login_required
def parse_order_file():
    """Parse order file (LCSC CSV or Mouser XLS) and match components"""
    from werkzeug.utils import secure_filename
    import csv
    import io
    from datetime import datetime
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    supplier = request.form.get('supplier', '')
    order_date = request.form.get('order_date', '')
    
    # Validate inputs
    if not file or not supplier or not order_date:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Safely convert supplier to uppercase
    supplier = str(supplier).strip().upper() if supplier else ''
    if not supplier:
        return jsonify({'error': 'Supplier cannot be empty'}), 400
    
    try:
        # Read file content
        file_content = file.read()
        
        if not file_content:
            return jsonify({'error': 'File is empty'}), 400
        
        # Parse based on supplier
        if supplier == 'LCSC':
            items = parse_lcsc_csv(file_content)
        elif supplier == 'MOUSER':
            items = parse_mouser_xls(file_content)
        else:
            return jsonify({'error': 'Unsupported supplier'}), 400
        
        # Match components with database
        matched = []
        unmatched = []
        
        api_client = OrionAPIClient()
        components_result = api_client.get_components(limit=10000)
        all_components = components_result if isinstance(components_result, list) else []
        
        for item in items:
            # Try to match by seller_code or manufacturer_code
            matched_comp = None
            
            # Match by seller code first (safely)
            seller_code = item.get('seller_code', '').strip() if item.get('seller_code') else ''
            if seller_code:
                matched_comp = next((c for c in all_components 
                                   if str(c.get('seller_code', '')).strip().lower() == seller_code.lower()), None)
                
                # Also try 'supplier_code' field
                if not matched_comp:
                    matched_comp = next((c for c in all_components 
                                       if str(c.get('supplier_code', '')).strip().lower() == seller_code.lower()), None)
            
            # If not found, try manufacturer code (safely)
            if not matched_comp:
                mfg_code = item.get('manufacturer_code', '').strip() if item.get('manufacturer_code') else ''
                if mfg_code:
                    matched_comp = next((c for c in all_components 
                                       if str(c.get('manufacturer_code', '')).strip().lower() == mfg_code.lower()), None)
                    
                    # Also try 'mpn' field
                    if not matched_comp:
                        matched_comp = next((c for c in all_components 
                                           if str(c.get('mpn', '')).strip().lower() == mfg_code.lower()), None)
            
            if matched_comp:
                matched.append({
                    'component_id': matched_comp['id'],
                    'seller_code': item.get('seller_code'),
                    'manufacturer': item.get('manufacturer'),
                    'manufacturer_code': item.get('manufacturer_code'),
                    'package': item.get('package'),
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'total_price': item['quantity'] * item['unit_price']
                })
            else:
                unmatched.append({
                    'seller_code': item.get('seller_code'),
                    'manufacturer': item.get('manufacturer'),
                    'manufacturer_code': item.get('manufacturer_code'),
                    'package': item.get('package'),
                    'description': item.get('description', ''),
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'total_price': item['quantity'] * item['unit_price']
                })
        
        return jsonify({
            'supplier': supplier,
            'order_date': order_date,
            'matched': matched,
            'unmatched': unmatched
        })
        
    except Exception as e:
        current_app.logger.error(f"[Order Parse] Error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@api_bp.route('/orders/import', methods=['POST'])
@login_required
def import_order():
    """Import order and update component stock quantities"""
    data = request.get_json()
    
    if not data or 'matched' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    try:
        api_client = OrionAPIClient()
        
        # Get all components first to check current stock
        all_components_result = api_client.get_components(limit=10000)
        all_components = all_components_result if isinstance(all_components_result, list) else []
        components_by_id = {c['id']: c for c in all_components}
        
        updated_count = 0
        
        # Update stock for each matched component
        for item in data['matched']:
            component_id = item['component_id']
            quantity_to_add = item['quantity']
            unit_price = item['unit_price']
            
            # Get current component data
            current_comp = components_by_id.get(component_id)
            if not current_comp:
                current_app.logger.warning(f"[Order Import] Component {component_id} not found, skipping")
                continue
            
            # Calculate new stock (add to existing) - handle NULL/None values safely
            current_stock = current_comp.get('qty_left') or current_comp.get('stock_qty') or 0
            # Ensure current_stock is an integer (could be None, null, or string)
            try:
                current_stock = int(current_stock) if current_stock is not None else 0
            except (ValueError, TypeError):
                current_stock = 0
            
            new_stock = current_stock + quantity_to_add
            
            current_app.logger.info(f"[Order Import] Updating component {component_id}: {current_stock} + {quantity_to_add} = {new_stock}")
            
            # Update component stock and price
            update_data = {
                'qty_left': new_stock,
                'stock_qty': new_stock,  # Update both fields for compatibility
                'price': float(unit_price),
                'unit_price': float(unit_price)  # Update both fields for compatibility
            }
            
            api_client.update_component(component_id, **update_data)
            updated_count += 1
        
        return jsonify({'success': True, 'updated': updated_count})
        
    except Exception as e:
        current_app.logger.error(f"[Order Import] Error: {e}")
        return jsonify({'error': str(e)}), 500


def parse_lcsc_csv(file_content):
    """Parse LCSC CSV format"""
    items = []
    content = file_content.decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    
    # USD to EUR conversion rate (approximate)
    USD_TO_EUR = 0.92  # Update this periodically or use an API
    
    for row in reader:
        # Try both Euro and Dollar currency symbols for Unit Price
        unit_price_eur = row.get('Unit Price(€)', '')
        unit_price_usd = row.get('Unit Price($)', '')
        
        unit_price = 0.0
        if unit_price_eur:
            # Price is already in euros
            unit_price = float(unit_price_eur.strip().replace(',', ''))
        elif unit_price_usd:
            # Price is in dollars, convert to euros
            unit_price_usd_float = float(unit_price_usd.strip().replace(',', ''))
            unit_price = unit_price_usd_float * USD_TO_EUR
        
        items.append({
            'seller_code': row.get('LCSC Part Number', '').strip(),
            'manufacturer_code': row.get('Manufacture Part Number', '').strip(),
            'manufacturer': row.get('Manufacturer', '').strip(),
            'package': row.get('Package', '').strip(),
            'description': row.get('Description', '').strip(),
            'quantity': int(row.get('Quantity', 0)),
            'unit_price': unit_price
        })
    
    return items


def parse_mouser_xls(file_content):
    """Parse Mouser XLS format"""
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required for Excel file parsing. Install it with: pip install openpyxl")
    
    items = []
    workbook = openpyxl.load_workbook(io.BytesIO(file_content))
    sheet = workbook.active
    
    # Find header row (usually row 1 or 2)
    headers = []
    for row in sheet.iter_rows(min_row=1, max_row=5):
        if any('Mouser' in str(cell.value) for cell in row if cell.value):
            headers = [cell.value for cell in row]
            break
    
    if not headers:
        raise ValueError("Could not find Mouser header row")
    
    # Parse data rows
    for row in sheet.iter_rows(min_row=sheet.min_row + 1):
        row_data = {headers[i]: cell.value for i, cell in enumerate(row) if i < len(headers)}
        
        # Skip empty rows
        if not row_data.get('Mouser Part No.'):
            continue
        
        items.append({
            'seller_code': str(row_data.get('Mouser Part No.', '')).strip(),
            'manufacturer_code': str(row_data.get('Manufacturer Part No.', '')).strip(),
            'manufacturer': str(row_data.get('Manufacturer', '')).strip(),
            'package': '',  # Mouser doesn't always include package in packing list
            'description': str(row_data.get('Description', '')).strip(),
            'quantity': int(row_data.get('Quantity', 0) or 0),
            'unit_price': float(row_data.get('Unit Price', 0) or 0)
        })
    
    return items
