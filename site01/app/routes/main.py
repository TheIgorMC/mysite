"""
Main routes blueprint
"""
from flask import Blueprint, render_template, session, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, GalleryItem
from app import db
from app.utils import t, load_translations

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
    return render_template('admin.html', users=users, gallery_items=gallery_items)

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
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted', 'success')
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
    
    title = request.form.get('title')
    category = request.form.get('category')
    description = request.form.get('description')
    image = request.files.get('image')
    
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
            title=title,
            category=category,
            description=description,
            image_path=unique_filename,
            is_active=True
        )
        db.session.add(item)
        db.session.commit()
        flash('Gallery item added successfully', 'success')
    else:
        flash('Image is required', 'error')
    
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
    if item.image_path:
        image_path = os.path.join(current_app.root_path, 'static', 'uploads', item.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(item)
    db.session.commit()
    flash('Gallery item deleted', 'success')
    return redirect(url_for('main.admin') + '#gallery')

