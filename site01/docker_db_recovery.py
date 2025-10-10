#!/usr/bin/env python3
"""
Docker Database Recovery Utility
Manages the SQLite database inside the Docker container
"""

import subprocess
import sys
import os
from datetime import datetime

CONTAINER_NAME = "orion-project"
DB_PATH = "/app/data/orion.db"
BACKUP_DIR = "./backups"

def run_docker_command(command, capture_output=True):
    """Run a command inside the Docker container"""
    full_command = ["docker", "exec", CONTAINER_NAME] + command
    try:
        if capture_output:
            result = subprocess.run(full_command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            subprocess.run(full_command, check=True)
            return None
    except subprocess.CalledProcessError as e:
        return None

def check_container_running():
    """Check if the container is running"""
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        return CONTAINER_NAME in result.stdout
    except:
        return False

def check_database_exists():
    """Check if database file exists in container"""
    result = run_docker_command(["test", "-f", DB_PATH])
    return result is not None

def get_database_info():
    """Get database information"""
    if not check_database_exists():
        return None
    
    size = run_docker_command(["stat", "-c%s", DB_PATH])
    tables = run_docker_command([
        "python", "-c",
        f"""
from app import create_app, db
app = create_app('production')
with app.app_context():
    inspector = db.inspect(db.engine)
    print(','.join(inspector.get_table_names()))
"""
    ])
    
    user_count = run_docker_command([
        "python", "-c",
        """
from app import create_app
from app.models import User
app = create_app('production')
with app.app_context():
    print(User.query.count())
"""
    ])
    
    admin_count = run_docker_command([
        "python", "-c",
        """
from app import create_app
from app.models import User
app = create_app('production')
with app.app_context():
    print(User.query.filter_by(is_admin=True).count())
"""
    ])
    
    return {
        'size': int(size) if size else 0,
        'tables': tables.split(',') if tables else [],
        'users': int(user_count) if user_count else 0,
        'admins': int(admin_count) if admin_count else 0
    }

def create_backup():
    """Create a backup of the database"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"orion_backup_{timestamp}.db")
    
    try:
        # Use docker cp to copy the file
        subprocess.run(
            ["docker", "cp", f"{CONTAINER_NAME}:{DB_PATH}", backup_file],
            check=True
        )
        print(f"✅ Backup created: {backup_file}")
        
        # Get file size
        size = os.path.getsize(backup_file)
        print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
        return backup_file
    except subprocess.CalledProcessError:
        print("❌ Failed to create backup")
        return None

def restore_backup(backup_file):
    """Restore database from backup"""
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    print(f"⚠️  This will replace the current database with: {backup_file}")
    confirm = input("Type 'yes' to confirm: ")
    if confirm.lower() != 'yes':
        print("Restore cancelled")
        return False
    
    # Create a backup of current database first
    print("Creating safety backup of current database...")
    create_backup()
    
    # Copy backup to container
    try:
        subprocess.run(
            ["docker", "cp", backup_file, f"{CONTAINER_NAME}:{DB_PATH}"],
            check=True
        )
        print("✅ Database restored successfully")
        print("   Restarting container...")
        subprocess.run(["docker-compose", "restart"], check=True)
        print("✅ Container restarted")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to restore backup")
        return False

def list_backups():
    """List available backups"""
    if not os.path.exists(BACKUP_DIR):
        print("No backups found")
        return []
    
    backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
    if not backups:
        print("No backups found")
        return []
    
    print("\nAvailable backups:")
    backups.sort(reverse=True)
    for i, backup in enumerate(backups, 1):
        path = os.path.join(BACKUP_DIR, backup)
        size = os.path.getsize(path)
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        print(f"{i}. {backup}")
        print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
        print(f"   Date: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return backups

def recreate_database():
    """Recreate database from scratch"""
    print("⚠️  WARNING: This will DELETE all data and recreate the database!")
    print("A backup will be created first.")
    confirm = input("Type 'DELETE' to confirm: ")
    if confirm != 'DELETE':
        print("Operation cancelled")
        return False
    
    # Backup first
    print("Creating backup...")
    create_backup()
    
    # Delete and recreate
    print("Recreating database...")
    result = run_docker_command([
        "python", "-c",
        """
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.drop_all()
    db.create_all()
    print('Database recreated')
"""
    ])
    
    if result:
        print("✅ Database recreated successfully")
        print("⚠️  You need to create an admin user now!")
        return True
    else:
        print("❌ Failed to recreate database")
        return False

def create_admin_user():
    """Create a new admin user"""
    print("\nCreate Admin User")
    print("-" * 50)
    
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    
    if not username or not email or not password:
        print("❌ All fields are required")
        return False
    
    command = f"""
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app('production')
with app.app_context():
    user = User(
        username='{username}',
        email='{email}',
        password_hash=generate_password_hash('{password}'),
        is_admin=True
    )
    db.session.add(user)
    db.session.commit()
    print('Admin user created')
"""
    
    result = run_docker_command(["python", "-c", command])
    if result:
        print(f"✅ Admin user '{username}' created successfully")
        return True
    else:
        print("❌ Failed to create admin user")
        return False

def main_menu():
    """Display main menu"""
    while True:
        print("\n" + "="*50)
        print("Docker Database Recovery Utility")
        print("="*50)
        
        # Check container status
        if not check_container_running():
            print("❌ Container is not running!")
            print("Start it with: docker-compose up -d")
            return
        
        print("✅ Container is running")
        
        # Check database status
        info = get_database_info()
        if info:
            print(f"✅ Database exists ({info['size']:,} bytes)")
            print(f"   Tables: {len(info['tables'])}")
            print(f"   Users: {info['users']} (Admins: {info['admins']})")
        else:
            print("❌ Database not found or inaccessible")
        
        print("\nOptions:")
        print("1. Create backup")
        print("2. List backups")
        print("3. Restore from backup")
        print("4. Recreate database (DELETE ALL DATA)")
        print("5. Create admin user")
        print("6. View database location")
        print("7. Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == '1':
            create_backup()
        elif choice == '2':
            list_backups()
        elif choice == '3':
            backups = list_backups()
            if backups:
                try:
                    idx = int(input("\nEnter backup number to restore: ")) - 1
                    if 0 <= idx < len(backups):
                        restore_backup(os.path.join(BACKUP_DIR, backups[idx]))
                    else:
                        print("Invalid backup number")
                except ValueError:
                    print("Invalid input")
        elif choice == '4':
            recreate_database()
        elif choice == '5':
            create_admin_user()
        elif choice == '6':
            print(f"\nDatabase location inside container: {DB_PATH}")
            print(f"Container name: {CONTAINER_NAME}")
            print("\nTo access directly:")
            print(f"  docker exec -it {CONTAINER_NAME} sqlite3 {DB_PATH}")
            print("\nTo copy to host:")
            print(f"  docker cp {CONTAINER_NAME}:{DB_PATH} ./backup.db")
            print("\nDocker volume:")
            print("  docker volume inspect orion-data")
        elif choice == '7':
            print("Goodbye!")
            break
        else:
            print("Invalid choice")

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
