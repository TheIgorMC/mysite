"""
Database Models
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    avatar = db.Column(db.String(256), default='default-avatar.png')
    
    # Authorization flags
    is_admin = db.Column(db.Boolean, default=False)
    is_club_member = db.Column(db.Boolean, default=False)  # For ASD Compagnia Arcieri Carraresi
    has_locked_section_access = db.Column(db.Boolean, default=False, index=True)  # For highly restricted sections
    club_name = db.Column(db.String(128))
    
    # Preferences
    preferred_language = db.Column(db.String(2), default='it')
    
    # Password reset
    reset_token = db.Column(db.String(256), index=True)
    reset_token_expiry = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    competition_subscriptions = db.relationship('CompetitionSubscription', 
                                               back_populates='user', 
                                               lazy='dynamic')
    authorized_athletes = db.relationship('AuthorizedAthlete',
                                         back_populates='user',
                                         lazy='dynamic',
                                         foreign_keys='AuthorizedAthlete.user_id')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        """Generate a password reset token"""
        import secrets
        from datetime import timedelta
        
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=24)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify if reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return True
    
    def clear_reset_token(self):
        """Clear reset token after use"""
        self.reset_token = None
        self.reset_token_expiry = None
    
    def __repr__(self):
        return f'<User {self.username}>'


class AuthorizedAthlete(db.Model):
    """Athletes that a user is authorized to manage"""
    __tablename__ = 'authorized_athletes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tessera_atleta = db.Column(db.String(10), nullable=False)
    nome_atleta = db.Column(db.String(100), nullable=False)
    cognome_atleta = db.Column(db.String(100), nullable=False)
    data_nascita = db.Column(db.Date)
    categoria = db.Column(db.String(10))  # Age category: GM, GF, RM, RF, AM, AF, JM, JF, SM, SF, MM, MF
    classe = db.Column(db.String(10))  # Competition class: CO (Compound), OL (Olympic), AN (Barebow)
    
    # Metadata
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', 
                          back_populates='authorized_athletes',
                          foreign_keys=[user_id])
    added_by_user = db.relationship('User', foreign_keys=[added_by])
    
    # Unique constraint: one user can't have duplicate athletes
    __table_args__ = (
        db.UniqueConstraint('user_id', 'tessera_atleta', name='unique_user_athlete'),
    )
    
    @property
    def nome_completo(self):
        """Full name of athlete"""
        return f"{self.nome_atleta} {self.cognome_atleta}"
    
    @property
    def display_name(self):
        """Display format: tessera - full name"""
        return f"{self.tessera_atleta} - {self.nome_completo}"
    
    def __repr__(self):
        return f'<AuthorizedAthlete {self.tessera_atleta} for User {self.user_id}>'


class Competition(db.Model):
    """Competition model for archery events"""
    __tablename__ = 'competitions'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(64), unique=True, index=True)  # ID from external API
    name = db.Column(db.String(256), nullable=False)
    location = db.Column(db.String(256))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    # Competition details
    competition_type = db.Column(db.String(64))  # Indoor, Outdoor, Field, 3D, etc.
    category = db.Column(db.String(64))
    
    # Subscription status
    invite_published = db.Column(db.Boolean, default=False)
    subscription_open = db.Column(db.Boolean, default=False)
    subscription_deadline = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('CompetitionSubscription', 
                                   back_populates='competition', 
                                   lazy='dynamic')
    
    def __repr__(self):
        return f'<Competition {self.name}>'

class CompetitionSubscription(db.Model):
    """User subscriptions to competitions"""
    __tablename__ = 'competition_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    
    # Subscription details
    turn = db.Column(db.String(64))  # Selected turn/shift
    status = db.Column(db.String(32), default='pending')  # pending, confirmed, cancelled
    interest_only = db.Column(db.Boolean, default=False)  # True if only expressing interest
    
    # Additional info
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='competition_subscriptions')
    competition = db.relationship('Competition', back_populates='subscriptions')
    
    def __repr__(self):
        return f'<Subscription {self.user_id} -> {self.competition_id}>'

class Result(db.Model):
    """Archery competition results"""
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.String(64), index=True)  # External athlete ID
    athlete_name = db.Column(db.String(128))
    competition_id = db.Column(db.String(64), index=True)
    competition_name = db.Column(db.String(256))
    competition_type = db.Column(db.String(64))
    date = db.Column(db.DateTime)
    
    # Results
    score = db.Column(db.Integer)
    position = db.Column(db.Integer)
    total_participants = db.Column(db.Integer)
    
    # Medals
    medal = db.Column(db.String(16))  # gold, silver, bronze
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Result {self.athlete_name} - {self.competition_name}>'

class Newsletter(db.Model):
    """Newsletter subscriptions"""
    __tablename__ = 'newsletter_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Newsletter {self.email}>'

class Product(db.Model):
    """Shop products"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name_it = db.Column(db.String(256), nullable=False)
    name_en = db.Column(db.String(256), nullable=False)
    description_it = db.Column(db.Text)
    description_en = db.Column(db.Text)
    
    # Product details
    category = db.Column(db.String(64))  # Primary category: archery, 3dprinting, electronics
    categories = db.Column(db.Text)  # Comma-separated list of all categories for multi-category support
    price = db.Column(db.Float)
    currency = db.Column(db.String(3), default='EUR')
    tags = db.Column(db.Text)  # Comma-separated tags for search/filtering
    
    # Link to gallery item
    gallery_item_id = db.Column(db.Integer, db.ForeignKey('gallery_items.id'), nullable=True)
    
    # Images
    main_image = db.Column(db.String(256))
    images = db.Column(db.Text)  # JSON array of image URLs
    
    # Availability
    in_stock = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer)
    
    # Customization flags
    is_custom_string = db.Column(db.Boolean, default=False)  # Enable string customizer
    is_custom_print = db.Column(db.Boolean, default=False)   # Enable 3D print customizer
    
    # Variant configuration (JSON)
    # Example: {"length": {"type": "select", "options": ["66", "68", "70"], "label_en": "Length", "label_it": "Lunghezza", "unit": "inches"}}
    variant_config = db.Column(db.Text)  # JSON configuration for product variants
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    variants = db.relationship('ProductVariant', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name_en}>'

class ProductVariant(db.Model):
    """Product variants for different configurations (length, color, material, etc.)"""
    __tablename__ = 'product_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Variant attributes (stored as JSON for flexibility)
    # Example: {"length": "68", "color": "black"}
    attributes = db.Column(db.Text, nullable=False)  # JSON object of variant attributes
    
    # Pricing
    price_modifier = db.Column(db.Float, default=0.0)  # Price difference from base product (can be negative)
    
    # Availability
    sku = db.Column(db.String(128))  # Optional SKU for inventory tracking
    stock_quantity = db.Column(db.Integer)
    in_stock = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductVariant {self.id} for Product {self.product_id}>'

class GalleryItem(db.Model):
    """Gallery items for 3D printing and electronics projects"""
    __tablename__ = 'gallery_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title_it = db.Column(db.String(256), nullable=False)
    title_en = db.Column(db.String(256), nullable=False)
    description_it = db.Column(db.Text)  # Short description for cards
    description_en = db.Column(db.Text)  # Short description for cards
    
    # Blog post content (full article)
    content_it = db.Column(db.Text)  # Full HTML/Markdown content in Italian
    content_en = db.Column(db.Text)  # Full HTML/Markdown content in English
    slug = db.Column(db.String(256), unique=True, index=True)  # URL-friendly identifier
    
    # Item details
    category = db.Column(db.String(64))  # Primary category: 3dprinting, electronics
    categories = db.Column(db.Text)  # Comma-separated list of all categories for multi-category support
    tags = db.Column(db.Text)  # Comma-separated tags for search/filtering
    main_image = db.Column(db.String(256))
    images = db.Column(db.Text)  # JSON array of image URLs
    
    # Electronics-specific: PCB background for parallax effect
    pcb_background = db.Column(db.String(256))  # Screenshot dello sbroglio PCB
    
    # External links
    external_url = db.Column(db.String(512))  # Link to Printables, GitHub, etc.
    
    # Relationship to products (one gallery item can have multiple products)
    products = db.relationship('Product', backref='gallery_item', lazy=True, foreign_keys='Product.gallery_item_id')
    
    # Relationship to blog posts (one project can have multiple blog posts)
    blog_posts = db.relationship('BlogPost', backref='project', lazy=True, cascade='all, delete-orphan')
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)  # Track popularity
    
    def __repr__(self):
        return f'<GalleryItem {self.title_en}>'


class BlogPost(db.Model):
    """Blog posts associated with gallery projects"""
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relationship to gallery project (optional - can be standalone)
    project_id = db.Column(db.Integer, db.ForeignKey('gallery_items.id'), nullable=True)
    
    # Author
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', backref='blog_posts')
    
    # Content in Italian
    title_it = db.Column(db.String(256), nullable=False)
    excerpt_it = db.Column(db.Text)  # Short summary for cards
    content_it = db.Column(db.Text, nullable=False)  # Full HTML content
    
    # Content in English  
    title_en = db.Column(db.String(256), nullable=False)
    excerpt_en = db.Column(db.Text)  # Short summary for cards
    content_en = db.Column(db.Text, nullable=False)  # Full HTML content
    
    # SEO
    slug = db.Column(db.String(256), unique=True, index=True, nullable=False)
    
    # Media
    cover_image = db.Column(db.String(256))  # Main cover image
    images = db.Column(db.Text)  # JSON array of additional images
    
    # Categorization
    tags = db.Column(db.Text)  # Comma-separated tags
    
    # Publishing
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<BlogPost {self.title_en}>'


class PrintMaterial(db.Model):
    """Filament/resin material available for the 3D print quote calculator"""
    __tablename__ = 'print_materials'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)  # e.g. "PLA", "PETG", "Resin standard"
    technology = db.Column(db.String(16), nullable=False, default='fdm')  # 'fdm' or 'resin' — drives the pricing formula
    density_g_cm3 = db.Column(db.Float, nullable=False)  # material density, g/cm3
    price_per_kg = db.Column(db.Float, nullable=False)  # EUR per kg
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PrintMaterial {self.name}>'


class PrintPrinter(db.Model):
    """A physical printer: its technology, build volume and how many materials/colors it can run at once"""
    __tablename__ = 'print_printers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)  # e.g. "Bambu X1C", "Elegoo Mars 4"
    technology = db.Column(db.String(16), nullable=False, default='fdm')  # 'fdm' or 'resin'
    max_build_x_mm = db.Column(db.Float, nullable=False)
    max_build_y_mm = db.Column(db.Float, nullable=False)
    max_build_z_mm = db.Column(db.Float, nullable=False)
    max_materials = db.Column(db.Integer, default=1)  # simultaneous colors/materials it can run (e.g. AMS slots)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PrintPrinter {self.name}>'


class PrintSettings(db.Model):
    """Single-row settings used by the 3D print quote calculator"""
    __tablename__ = 'print_settings'

    id = db.Column(db.Integer, primary_key=True)
    infill_percent = db.Column(db.Float, default=20.0)  # FDM: used to estimate weight from mesh volume
    resin_fill_percent = db.Column(db.Float, default=100.0)  # Resin: prints are ~solid, but large ones get hollowed
    setup_fee = db.Column(db.Float, default=0.0)  # flat EUR fee added to every quote
    minimum_price = db.Column(db.Float, default=5.0)  # EUR floor for the estimate
    multi_material_fee_per_extra = db.Column(db.Float, default=0.0)  # EUR per extra color/material beyond the first

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls):
        """Fetch the single settings row, creating it with defaults if missing"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self):
        return f'<PrintSettings infill={self.infill_percent}%>'


class PrintQuoteRequest(db.Model):
    """A 3D-print quote lead: file + auto-computed estimate, no checkout (fiscal reasons)"""
    __tablename__ = 'print_quote_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('print_materials.id'), nullable=True)
    printer_id = db.Column(db.Integer, db.ForeignKey('print_printers.id'), nullable=True)  # suggested printer, if any fit

    project_name = db.Column(db.String(256))
    notes = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)

    original_filename = db.Column(db.String(256))
    stored_filename = db.Column(db.String(256))  # sanitized name on disk, uploads/print_quotes/
    file_format = db.Column(db.String(8))  # 'stl' or '3mf'

    # Computed from the uploaded mesh at submit time (server-side, not trusted from the client)
    volume_cm3 = db.Column(db.Float)
    bbox_x_mm = db.Column(db.Float)
    bbox_y_mm = db.Column(db.Float)
    bbox_z_mm = db.Column(db.Float)
    fits_build_volume = db.Column(db.Boolean)
    fit_reason = db.Column(db.String(32))  # 'ok', 'too_big', 'too_many_materials', 'no_printer_for_technology'
    weight_g = db.Column(db.Float)
    detected_material_count = db.Column(db.Integer, default=1)  # distinct materials/colors found in the file (3MF only)
    estimated_price = db.Column(db.Float)

    status = db.Column(db.String(32), default='new')  # new, contacted, quoted, closed

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')
    material = db.relationship('PrintMaterial')
    printer = db.relationship('PrintPrinter')

    def __repr__(self):
        return f'<PrintQuoteRequest {self.id} {self.project_name}>'
