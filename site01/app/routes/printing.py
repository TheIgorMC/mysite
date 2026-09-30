"""
3D Printing routes blueprint
"""
import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import GalleryItem, PrintMaterial, PrintSettings, PrintQuoteRequest
from app.print_quote_utils import parse_stl, compute_quote, MeshParseError
from app.utils import t

bp = Blueprint('printing', __name__, url_prefix='/3dprinting')

ALLOWED_MESH_EXTENSIONS = {'stl'}

@bp.route('/')
def index():
    """3D Printing section main page"""
    # Get first 8 gallery items for preview
    gallery_items = GalleryItem.query.filter_by(
        category='3dprinting',
        is_active=True
    ).limit(8).all()
    return render_template('printing/index.html', gallery_items=gallery_items)

@bp.route('/gallery')
def gallery():
    """3D Printing gallery"""
    items = GalleryItem.query.filter_by(
        category='3dprinting',
        is_active=True
    ).all()
    return render_template('printing/gallery.html', items=items)

@bp.route('/gallery/<int:item_id>')
def item_detail(item_id):
    """Gallery item detail page with related items"""
    item = GalleryItem.query.get_or_404(item_id)
    
    # Find related items based on tags
    related_items = []
    if item.tags:
        item_tags = [tag.strip().lower() for tag in item.tags.split(',')]
        all_items = GalleryItem.query.filter(
            GalleryItem.category == item.category,
            GalleryItem.is_active == True,
            GalleryItem.id != item.id
        ).all()
        
        # Calculate similarity score based on matching tags
        items_with_score = []
        for other_item in all_items:
            if other_item.tags:
                other_tags = [tag.strip().lower() for tag in other_item.tags.split(',')]
                matching_tags = len(set(item_tags) & set(other_tags))
                if matching_tags > 0:
                    items_with_score.append((other_item, matching_tags))
        
        # Sort by number of matching tags
        items_with_score.sort(key=lambda x: x[1], reverse=True)
        related_items = [item for item, score in items_with_score[:4]]
    
    return render_template('printing/item_detail.html', item=item, related_items=related_items)

@bp.route('/quote')
def quote():
    """3D print quote calculator - requires login"""
    materials = PrintMaterial.query.filter_by(is_active=True).order_by(PrintMaterial.name).all()

    last_quote = None
    last_quote_id = request.args.get('quote_id', type=int)
    if current_user.is_authenticated and last_quote_id:
        last_quote = PrintQuoteRequest.query.filter_by(
            id=last_quote_id, user_id=current_user.id
        ).first()

    return render_template('printing/quote.html', materials=materials, last_quote=last_quote)


@bp.route('/quote/submit', methods=['POST'])
@login_required
def submit_quote():
    """
    Upload a mesh, compute a printability check + price estimate server-side,
    and store the request as a lead. No checkout here (fiscal reasons) — this
    just captures enough for a human to follow up and finalize manually.
    """
    mesh_file = request.files.get('mesh_file')
    material_id = request.form.get('material_id', type=int)
    project_name = request.form.get('project_name', '').strip()
    quantity = request.form.get('quantity', type=int) or 1
    notes = request.form.get('notes', '').strip()

    if not mesh_file or not mesh_file.filename:
        flash('Carica un file STL per calcolare il preventivo.', 'error')
        return redirect(url_for('printing.quote'))

    original_filename = mesh_file.filename
    ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else ''
    if ext not in ALLOWED_MESH_EXTENSIONS:
        flash('Formato non supportato: al momento accettiamo solo file STL.', 'error')
        return redirect(url_for('printing.quote'))

    material = PrintMaterial.query.filter_by(id=material_id, is_active=True).first()
    if not material:
        flash('Seleziona un materiale valido.', 'error')
        return redirect(url_for('printing.quote'))

    data = mesh_file.read()
    try:
        bbox, volume_mm3 = parse_stl(data)
    except MeshParseError as e:
        flash(f'Impossibile leggere il file: {e}', 'error')
        return redirect(url_for('printing.quote'))

    settings = PrintSettings.get()
    result = compute_quote(bbox, volume_mm3, material, settings)

    # Save the file after it parsed successfully
    safe_name = secure_filename(original_filename)
    stored_filename = f"{uuid.uuid4().hex}_{safe_name}"
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'print_quotes')
    os.makedirs(upload_folder, exist_ok=True)
    with open(os.path.join(upload_folder, stored_filename), 'wb') as f:
        f.write(data)

    quote_request = PrintQuoteRequest(
        user_id=current_user.id,
        material_id=material.id,
        project_name=project_name or original_filename,
        notes=notes,
        quantity=quantity,
        original_filename=original_filename,
        stored_filename=stored_filename,
        volume_cm3=result['volume_cm3'],
        bbox_x_mm=result['bbox_mm']['x'],
        bbox_y_mm=result['bbox_mm']['y'],
        bbox_z_mm=result['bbox_mm']['z'],
        fits_build_volume=result['fits'],
        weight_g=result['weight_g'],
        estimated_price=result['price'],
        status='new'
    )
    db.session.add(quote_request)
    db.session.commit()

    flash('Preventivo calcolato! Ti contatteremo per finalizzare l\'ordine.', 'success')
    return redirect(url_for('printing.quote', quote_id=quote_request.id))


@bp.route('/shop')
def shop():
    """3D Printing shop"""
    return render_template('shop/index.html', category='3dprinting')
