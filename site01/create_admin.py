#!/usr/bin/env python
"""
Script to create an admin user
Usage: python create_admin.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

def create_admin_user():
    """Create an admin user interactively"""
    app = create_app()
    
    with app.app_context():
        print("\n=== Create Admin User ===\n")
        
        # Get user input
        username = input("Enter admin username: ").strip()
        if not username:
            print("❌ Username cannot be empty")
            return
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            print(f"❌ Username '{username}' already exists")
            return
        
        email = input("Enter admin email: ").strip()
        if not email:
            print("❌ Email cannot be empty")
            return
        
        # Check if email exists
        if User.query.filter_by(email=email).first():
            print(f"❌ Email '{email}' already exists")
            return
        
        password = input("Enter admin password: ").strip()
        if not password:
            print("❌ Password cannot be empty")
            return
        
        if len(password) < 6:
            print("❌ Password must be at least 6 characters")
            return
        
        first_name = input("Enter first name (optional): ").strip()
        last_name = input("Enter last name (optional): ").strip()
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            first_name=first_name or None,
            last_name=last_name or None,
            is_admin=True,
            is_club_member=False,
            preferred_language='it'
        )
        admin.set_password(password)
        
        try:
            db.session.add(admin)
            db.session.commit()
            print(f"\n✅ Admin user '{username}' created successfully!")
            print(f"   Email: {email}")
            print(f"   Admin: Yes")
            print(f"\nYou can now log in at: http://localhost:5000/auth/login\n")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error creating admin user: {e}\n")

if __name__ == '__main__':
    create_admin_user()
