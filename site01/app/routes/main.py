"""
Main routes blueprint
"""
from flask import Blueprint, render_template, session, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import User, GalleryItem, Product, AuthorizedAthlete, CompetitionSubscription
from app import db
from app.utils import t, load_translations
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.before_app_request
def before_request():
    """Load translations before each request"""
    load_translations()

@bp.route('/')
@bp.route('/index')
def index():
    """Home page"""
    return render_template('index.html')

@bp.route('/set_language/<lang>')
def set_language(lang):
    """Set user's preferred language"""
    from flask import current_app
    if lang in current_app.config['LANGUAGES']:
        session['language'] = lang
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@bp.route('/admin')
@login_required
def admin():
    """Admin panel - only accessible to admins"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    gallery_items = GalleryItem.query.all()
    products = Product.query.all()
    return render_template('admin.html', users=users, gallery_items=gallery_items, products=products)

@bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('admin.html')

@bp.route('/admin/manage-athletes')
@login_required
def admin_manage_athletes():
    """Admin page for managing authorized athletes"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('admin/manage_athletes.html')

@bp.route('/admin/competition-subscriptions')
@login_required
def admin_competition_subscriptions():
    """Admin page for managing competition subscriptions and interest expressions"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('admin/competition_subscriptions.html')

@bp.route('/admin/toggle_club_member/<int:user_id>', methods=['POST'])
@login_required
def toggle_club_member(user_id):
    """Toggle club member status"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    user.is_club_member = not user.is_club_member
    db.session.commit()
    flash(f'Club member status updated for {user.username}', 'success')
    return redirect(url_for('main.admin'))

@bp.route('/admin/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    """Toggle admin status"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'Admin status updated for {user.username}', 'success')
    return redirect(url_for('main.admin'))

@bp.route('/admin/toggle_locked_section/<int:user_id>', methods=['POST'])
@login_required
def toggle_locked_section(user_id):
    """Toggle locked section access - HIGHLY RESTRICTED"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    user.has_locked_section_access = not user.has_locked_section_access
    db.session.commit()
    
    status = 'granted' if user.has_locked_section_access else 'revoked'
    flash(f'Locked section access {status} for {user.username}', 'success')
    return redirect(url_for('main.admin'))

@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    if user_id == current_user.id:
        flash('Cannot delete yourself!', 'error')
        return redirect(url_for('main.admin'))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    
    try:
        # Delete related records first using synchronize_session=False
        # to avoid SQLAlchemy trying to update relationships
        
        # Delete authorized athletes
        AuthorizedAthlete.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        
        # Delete competition subscriptions (if any)
        CompetitionSubscription.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        
        # Now delete the user
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting user {username}: {str(e)}')
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('main.admin'))

@bp.route('/admin/add_gallery_item', methods=['POST'])
@login_required
def add_gallery_item():
    """Add a new gallery item"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    from werkzeug.utils import secure_filename
    import os
    from flask import current_app
    
    title_en = request.form.get('title_en', '')
    title_it = request.form.get('title_it', '')
    category = request.form.get('category')
    description_en = request.form.get('description_en', '')
    description_it = request.form.get('description_it', '')
    external_url = request.form.get('external_url', '')
    tags = request.form.get('tags', '')  # Comma-separated tags
    
    # Get additional categories from checkboxes
    additional_categories = request.form.getlist('gallery_categories')
    categories_str = ','.join(additional_categories) if additional_categories else None
    
    image = request.files.get('image')
    
    # Validation
    if not title_en or not title_it:
        flash('Title is required in both languages', 'error')
        return redirect(url_for('main.admin') + '#gallery')
    
    if not category:
        flash('Category is required', 'error')
        return redirect(url_for('main.admin') + '#gallery')
    
    unique_filename = None
    if image:
        filename = secure_filename(image.filename)
        # Create unique filename
        import uuid
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        image.save(os.path.join(upload_folder, unique_filename))
    
    item = GalleryItem(
        title_en=title_en,
        title_it=title_it,
        category=category,
        categories=categories_str,
        description_en=description_en,
        description_it=description_it,
        tags=tags.strip() if tags else None,
        main_image=unique_filename,
        external_url=external_url if external_url else None,
        is_active=True
    )
    db.session.add(item)
    db.session.commit()
    flash('Gallery item added successfully', 'success')
    
    return redirect(url_for('main.admin') + '#gallery')

@bp.route('/admin/toggle_gallery_item/<int:item_id>', methods=['POST'])
@login_required
def toggle_gallery_item(item_id):
    """Toggle gallery item active status"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    item = GalleryItem.query.get_or_404(item_id)
    item.is_active = not item.is_active
    db.session.commit()
    flash('Gallery item status updated', 'success')
    return redirect(url_for('main.admin') + '#gallery')

@bp.route('/admin/delete_gallery_item/<int:item_id>', methods=['POST'])
@login_required
def delete_gallery_item(item_id):
    """Delete a gallery item"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    item = GalleryItem.query.get_or_404(item_id)
    
    # Delete the image file
    import os
    from flask import current_app
    if item.main_image:
        image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'gallery', item.main_image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(item)
    db.session.commit()
    flash('Gallery item deleted', 'success')
    return redirect(url_for('main.admin') + '#gallery')

@bp.route('/admin/add_product', methods=['POST'])
@login_required
def add_product():
    """Add a new product"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    # Get form data
    name_en = request.form.get('name_en')
    name_it = request.form.get('name_it')
    category = request.form.get('category')
    price = request.form.get('price')
    description_en = request.form.get('description_en')
    description_it = request.form.get('description_it')
    stock_quantity = request.form.get('stock', 0)
    tags = request.form.get('tags', '')
    gallery_item_id = request.form.get('gallery_item_id')
    
    # Get additional categories from checkboxes
    additional_categories = request.form.getlist('categories')
    categories_str = ','.join(additional_categories) if additional_categories else None
    
    # Handle image upload
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            import os
            from werkzeug.utils import secure_filename
            from flask import current_app
            
            filename = secure_filename(file.filename)
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
            
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            file.save(os.path.join(upload_folder, unique_filename))
            image_filename = unique_filename
    
    # Create new product
    product = Product(
        name_en=name_en,
        name_it=name_it,
        category=category,
        categories=categories_str,
        price=float(price),
        description_en=description_en,
        description_it=description_it,
        stock_quantity=int(stock_quantity),
        tags=tags,
        main_image=image_filename,
        gallery_item_id=int(gallery_item_id) if gallery_item_id else None,
        is_active=True
    )
    
    db.session.add(product)
    db.session.commit()
    flash('Product added successfully', 'success')
    return redirect(url_for('main.admin') + '#shop')

@bp.route('/admin/toggle_product/<int:product_id>', methods=['POST'])
@login_required
def toggle_product(product_id):
    """Toggle product active status"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    flash('Product status updated', 'success')
    return redirect(url_for('main.admin') + '#shop')

@bp.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete a product"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    product = Product.query.get_or_404(product_id)
    
    # Delete the image file
    import os
    from flask import current_app
    if product.main_image:
        image_path = os.path.join(current_app.root_path, 'static', 'uploads', product.main_image)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted', 'success')
    return redirect(url_for('main.admin') + '#shop')


@bp.route('/locked')
def locked_section():
    """Locked section - returns 404 for unauthorized users to hide existence"""
    from flask import abort
    
    # Return 404 immediately if not logged in or no access (no redirect to login)
    if not current_user.is_authenticated or not current_user.has_locked_section_access:
        abort(404)
    
    return render_template('locked_section.html')


@bp.route('/locked/gallery')
def locked_gallery():
    """Private gallery for locked section users only"""
    from flask import abort
    
    if not current_user.is_authenticated or not current_user.has_locked_section_access:
        abort(404)
    
    # Get locked section gallery items (you can add a flag to GalleryItem model later)
    gallery_items = GalleryItem.query.filter_by(is_active=True).all()
    
    return render_template('locked_gallery.html', gallery_items=gallery_items)


@bp.route('/locked/shop')
def locked_shop():
    """Private shop for locked section - admin + locked access required"""
    from flask import abort
    
    # Requires BOTH admin AND locked section access
    if not current_user.is_authenticated or not current_user.is_admin or not current_user.has_locked_section_access:
        abort(404)
    
    # Get locked section products (you can add a flag to Product model later)
    products = Product.query.filter_by(is_active=True).all()
    
    return render_template('locked_shop.html', products=products)
