"""
Database Recovery and Backup Utilities
Run this to check database status and create backups
"""
import os
import sys
import shutil
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, AuthorizedAthlete, Competition, CompetitionSubscription, GalleryItem, Product
from sqlalchemy import inspect, text

def check_database_status():
    """Check if database exists and is accessible"""
    app = create_app()
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print("\n" + "="*60)
        print("DATABASE STATUS CHECK")
        print("="*60)
        
        # Check if database file exists
        if os.path.exists(db_path):
            print(f"✅ Database file exists: {db_path}")
            print(f"   Size: {os.path.getsize(db_path) / 1024:.2f} KB")
            print(f"   Modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
        else:
            print(f"❌ Database file NOT found: {db_path}")
            print("   Database may have been deleted or path is incorrect")
            return False
        
        # Check if we can connect
        try:
            db.session.execute(text('SELECT 1'))
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
        
        # Check tables
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Tables found: {len(tables)}")
        expected_tables = ['users', 'authorized_athletes', 'competitions', 
                          'competition_subscriptions', 'gallery_items', 'products',
                          'results', 'newsletter_subscriptions']
        
        for table in expected_tables:
            if table in tables:
                count = db.session.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
                print(f"   ✅ {table}: {count} records")
            else:
                print(f"   ❌ {table}: MISSING")
        
        # Check for critical data
        print("\n🔍 Critical Data Check:")
        user_count = User.query.count()
        admin_count = User.query.filter_by(is_admin=True).count()
        athlete_count = AuthorizedAthlete.query.count()
        
        print(f"   Users: {user_count} (Admins: {admin_count})")
        print(f"   Authorized Athletes: {athlete_count}")
        print(f"   Gallery Items: {GalleryItem.query.count()}")
        print(f"   Products: {Product.query.count()}")
        
        if user_count == 0:
            print("\n⚠️  WARNING: No users found! Database may need to be restored.")
            return False
        
        if admin_count == 0:
            print("\n⚠️  WARNING: No admin users found!")
        
        print("\n✅ Database appears healthy!")
        return True

def create_backup():
    """Create a backup of the database"""
    app = create_app()
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if not os.path.exists(db_path):
            print("❌ Cannot backup: Database file not found")
            return False
        
        # Create backups directory
        backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'site_backup_{timestamp}.db')
        
        # Copy database
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ Backup created: {backup_path}")
        print(f"   Size: {os.path.getsize(backup_path) / 1024:.2f} KB")
        
        # Also export critical data as JSON
        export_critical_data(backup_dir, timestamp)
        
        return True

def export_critical_data(backup_dir, timestamp):
    """Export users and athletes as JSON for extra safety"""
    app = create_app()
    
    with app.app_context():
        # Export users
        users = User.query.all()
        users_data = [
            {
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'is_admin': u.is_admin,
                'is_club_member': u.is_club_member,
                'created_at': u.created_at.isoformat() if u.created_at else None
            }
            for u in users
        ]
        
        # Export authorized athletes
        athletes = AuthorizedAthlete.query.all()
        athletes_data = [
            {
                'user_id': a.user_id,
                'tessera': a.tessera_atleta,
                'nome': a.nome_atleta,
                'cognome': a.cognome_atleta,
                'categoria': a.categoria,
                'data_nascita': a.data_nascita.isoformat() if a.data_nascita else None
            }
            for a in athletes
        ]
        
        # Save to JSON
        json_path = os.path.join(backup_dir, f'critical_data_{timestamp}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'backup_date': datetime.now().isoformat(),
                'users': users_data,
                'authorized_athletes': athletes_data
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Critical data exported: {json_path}")

def restore_from_backup(backup_file):
    """Restore database from a backup file"""
    app = create_app()
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False
        
        # Create a backup of current database (if exists)
        if os.path.exists(db_path):
            temp_backup = db_path + '.before_restore'
            shutil.copy2(db_path, temp_backup)
            print(f"📦 Current database backed up to: {temp_backup}")
        
        # Restore from backup
        shutil.copy2(backup_file, db_path)
        print(f"✅ Database restored from: {backup_file}")
        
        # Verify restore
        check_database_status()
        
        return True

def list_backups():
    """List all available backups"""
    app = create_app()
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
        
        if not os.path.exists(backup_dir):
            print("No backups directory found")
            return
        
        backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')], reverse=True)
        
        print("\n" + "="*60)
        print("AVAILABLE BACKUPS")
        print("="*60)
        
        if not backups:
            print("No backups found")
            return
        
        for i, backup in enumerate(backups, 1):
            backup_path = os.path.join(backup_dir, backup)
            size = os.path.getsize(backup_path) / 1024
            modified = datetime.fromtimestamp(os.path.getmtime(backup_path))
            print(f"{i}. {backup}")
            print(f"   Size: {size:.2f} KB | Date: {modified}")

def recreate_tables():
    """Recreate all database tables"""
    app = create_app()
    
    with app.app_context():
        print("\n⚠️  WARNING: This will drop all existing tables!")
        response = input("Are you sure you want to recreate tables? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Operation cancelled")
            return
        
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()
        
        print("✅ Tables recreated successfully!")
        print("\n⚠️  Note: All data has been lost. Restore from backup if needed.")

def main():
    """Main menu"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         DATABASE RECOVERY & BACKUP UTILITY               ║
╚══════════════════════════════════════════════════════════╝
    
Choose an option:
    
1. Check Database Status
2. Create Backup
3. List Backups
4. Restore from Backup
5. Recreate Tables (DANGEROUS - will lose all data)
6. Exit
    """)
    
    choice = input("Enter choice (1-6): ").strip()
    
    if choice == '1':
        check_database_status()
    elif choice == '2':
        create_backup()
    elif choice == '3':
        list_backups()
    elif choice == '4':
        list_backups()
        backup_file = input("\nEnter backup filename (or full path): ").strip()
        if not os.path.isabs(backup_file):
            app = create_app()
            with app.app_context():
                db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
                backup_file = os.path.join(backup_dir, backup_file)
        restore_from_backup(backup_file)
    elif choice == '5':
        recreate_tables()
    elif choice == '6':
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice")

if __name__ == '__main__':
    main()
