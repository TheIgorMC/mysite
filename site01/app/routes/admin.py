"""
Admin routes blueprint
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, PrintMaterial, PrintSettings, PrintPrinter, PrintQuoteRequest

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required():
    """Abort with 403 unless the current user is an admin"""
    if not getattr(current_user, 'is_admin', False):
        from flask import abort
        abort(403)


@bp.route('/')
@login_required
def index():
    """Admin dashboard landing (minimal)"""
    # A simple admin landing page may already exist; render a generic admin index if present
    try:
        return render_template('admin/index.html')
    except Exception:
        return render_template('admin/dashboard.html')


@bp.route('/materials')
@login_required
def materials():
    """Materials management page for admins"""
    # Only admins should access this page
    if not getattr(current_user, 'is_admin', False):
        from flask import abort
        abort(403)
    return render_template('admin/materials.html')


@bp.route('/products')
@login_required
def products():
    """Products management page for admins"""
    # Only admins should access this page
    if not getattr(current_user, 'is_admin', False):
        from flask import abort
        abort(403)
    return render_template('admin/products.html')


@bp.route('/users')
@login_required
def users():
    """User management page for admins"""
    if not current_user.is_admin:
        from flask import abort
        abort(403)
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@bp.route('/users/<int:user_id>/force-reset-password', methods=['POST'])
@login_required
def force_reset_password(user_id):
    """Admin: Force a user to reset their password"""
    if not current_user.is_admin:
        from flask import abort
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    # Generate reset token
    token = user.generate_reset_token()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating reset token: {str(e)}', 'error')
        return redirect(url_for('admin.users'))
    
    # Create reset URL
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    # Try to send email
    try:
        from flask import current_app
        from app.api import OrionAPIClient
        client = OrionAPIClient()
        
        email_body = f"""
Ciao {user.first_name or user.username},

Un amministratore ha richiesto il reset della tua password. Clicca sul link seguente per reimpostare la tua password:

{reset_url}

Questo link è valido per 24 ore.

Saluti,
Il Team
        """
        
        client.send_email(
            recipient_email=user.email,
            mail_type='password_reset',
            locale='it',
            subject='Reset Password Richiesto',
            body_text=email_body,
            details_json={'reset_url': reset_url}
        )
        flash(f'Reset email sent to {user.email}', 'success')
    except Exception as e:
        current_app.logger.error(f'Failed to send reset email: {e}')
        flash(f'Email service unavailable. Reset link: {reset_url}', 'warning')
    
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/set-password', methods=['POST'])
@login_required
def admin_set_password(user_id):
    """Admin: Directly set a user's password"""
    if not current_user.is_admin:
        from flask import abort
        abort(403)
    
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('admin.users'))
    
    user.set_password(new_password)
    user.clear_reset_token()  # Clear any pending reset tokens
    try:
        db.session.commit()
        flash(f'Password updated for {user.username}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating password: {str(e)}', 'error')
    return redirect(url_for('admin.users'))


# ============================================================================
# 3D PRINT QUOTE CALCULATOR: materials, settings, incoming leads
# ============================================================================

@bp.route('/print-materials')
@login_required
def print_materials():
    """List/manage the filament materials used by the print quote calculator"""
    admin_required()
    materials = PrintMaterial.query.order_by(PrintMaterial.name).all()
    settings = PrintSettings.get()
    return render_template('admin/print_materials.html', materials=materials, settings=settings)


@bp.route('/print-printers')
@login_required
def print_printers():
    """List/manage the physical printers used by the print quote calculator"""
    admin_required()
    printers = PrintPrinter.query.order_by(PrintPrinter.name).all()
    return render_template('admin/print_printers.html', printers=printers)


@bp.route('/print-printers/add', methods=['POST'])
@login_required
def print_printer_add():
    admin_required()
    technology = request.form.get('technology', 'fdm')
    if technology not in ('fdm', 'resin'):
        technology = 'fdm'
    try:
        printer = PrintPrinter(
            name=request.form.get('name', '').strip(),
            technology=technology,
            max_build_x_mm=float(request.form.get('max_build_x_mm')),
            max_build_y_mm=float(request.form.get('max_build_y_mm')),
            max_build_z_mm=float(request.form.get('max_build_z_mm')),
            max_materials=int(request.form.get('max_materials') or 1),
            is_active=True
        )
        if not printer.name:
            raise ValueError('name required')
        db.session.add(printer)
        db.session.commit()
        flash(f'Stampante "{printer.name}" aggiunta', 'success')
    except (TypeError, ValueError):
        flash('Nome e dimensioni devono essere validi', 'error')
    return redirect(url_for('admin.print_printers'))


@bp.route('/print-printers/<int:printer_id>/edit', methods=['POST'])
@login_required
def print_printer_edit(printer_id):
    admin_required()
    printer = PrintPrinter.query.get_or_404(printer_id)
    technology = request.form.get('technology', printer.technology)
    if technology not in ('fdm', 'resin'):
        technology = printer.technology
    try:
        printer.name = request.form.get('name', '').strip() or printer.name
        printer.technology = technology
        printer.max_build_x_mm = float(request.form.get('max_build_x_mm'))
        printer.max_build_y_mm = float(request.form.get('max_build_y_mm'))
        printer.max_build_z_mm = float(request.form.get('max_build_z_mm'))
        printer.max_materials = int(request.form.get('max_materials') or 1)
        printer.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash(f'Stampante "{printer.name}" aggiornata', 'success')
    except (TypeError, ValueError):
        db.session.rollback()
        flash('Nome e dimensioni devono essere validi', 'error')
    return redirect(url_for('admin.print_printers'))


@bp.route('/print-printers/<int:printer_id>/delete', methods=['POST'])
@login_required
def print_printer_delete(printer_id):
    admin_required()
    printer = PrintPrinter.query.get_or_404(printer_id)
    if PrintQuoteRequest.query.filter_by(printer_id=printer.id).first():
        # Keep history intact: deactivate instead of deleting a printer that's
        # referenced by past quote requests.
        printer.is_active = False
        db.session.commit()
        flash(f'"{printer.name}" è referenziata da preventivi passati: disattivata invece di eliminata', 'warning')
    else:
        db.session.delete(printer)
        db.session.commit()
        flash('Stampante eliminata', 'success')
    return redirect(url_for('admin.print_printers'))


@bp.route('/print-materials/add', methods=['POST'])
@login_required
def print_material_add():
    admin_required()
    technology = request.form.get('technology', 'fdm')
    if technology not in ('fdm', 'resin'):
        technology = 'fdm'
    try:
        material = PrintMaterial(
            name=request.form.get('name', '').strip(),
            technology=technology,
            density_g_cm3=float(request.form.get('density_g_cm3')),
            price_per_kg=float(request.form.get('price_per_kg')),
            is_active=True
        )
        db.session.add(material)
        db.session.commit()
        flash(f'Materiale "{material.name}" aggiunto', 'success')
    except (TypeError, ValueError):
        flash('Densità e prezzo devono essere numeri validi', 'error')
    return redirect(url_for('admin.print_materials'))


@bp.route('/print-materials/<int:material_id>/edit', methods=['POST'])
@login_required
def print_material_edit(material_id):
    admin_required()
    material = PrintMaterial.query.get_or_404(material_id)
    technology = request.form.get('technology', material.technology)
    if technology not in ('fdm', 'resin'):
        technology = material.technology
    try:
        material.name = request.form.get('name', '').strip() or material.name
        material.technology = technology
        material.density_g_cm3 = float(request.form.get('density_g_cm3'))
        material.price_per_kg = float(request.form.get('price_per_kg'))
        material.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash(f'Materiale "{material.name}" aggiornato', 'success')
    except (TypeError, ValueError):
        db.session.rollback()
        flash('Densità e prezzo devono essere numeri validi', 'error')
    return redirect(url_for('admin.print_materials'))


@bp.route('/print-materials/<int:material_id>/delete', methods=['POST'])
@login_required
def print_material_delete(material_id):
    admin_required()
    material = PrintMaterial.query.get_or_404(material_id)
    if PrintQuoteRequest.query.filter_by(material_id=material.id).first():
        # Keep history intact: deactivate instead of deleting a material that's
        # referenced by past quote requests.
        material.is_active = False
        db.session.commit()
        flash(f'"{material.name}" è referenziato da preventivi passati: disattivato invece di eliminato', 'warning')
    else:
        db.session.delete(material)
        db.session.commit()
        flash('Materiale eliminato', 'success')
    return redirect(url_for('admin.print_materials'))


@bp.route('/print-settings', methods=['POST'])
@login_required
def print_settings_update():
    admin_required()
    settings = PrintSettings.get()
    try:
        settings.infill_percent = float(request.form.get('infill_percent'))
        settings.resin_fill_percent = float(request.form.get('resin_fill_percent'))
        settings.setup_fee = float(request.form.get('setup_fee'))
        settings.minimum_price = float(request.form.get('minimum_price'))
        settings.multi_material_fee_per_extra = float(request.form.get('multi_material_fee_per_extra'))
        db.session.commit()
        flash('Impostazioni aggiornate', 'success')
    except (TypeError, ValueError):
        db.session.rollback()
        flash('Tutti i valori devono essere numeri validi', 'error')
    return redirect(url_for('admin.print_materials'))


@bp.route('/print-quotes')
@login_required
def print_quotes():
    """List incoming 3D print quote requests (leads) for manual follow-up"""
    admin_required()
    status_filter = request.args.get('status', '')
    query = PrintQuoteRequest.query.order_by(PrintQuoteRequest.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    quotes = query.all()
    return render_template('admin/print_quotes.html', quotes=quotes, status_filter=status_filter)


@bp.route('/print-quotes/<int:quote_id>/status', methods=['POST'])
@login_required
def print_quote_status(quote_id):
    admin_required()
    quote_request = PrintQuoteRequest.query.get_or_404(quote_id)
    new_status = request.form.get('status')
    if new_status in ('new', 'contacted', 'quoted', 'closed'):
        quote_request.status = new_status
        db.session.commit()
        flash('Stato aggiornato', 'success')
    return redirect(url_for('admin.print_quotes', status=request.args.get('status', '')))
