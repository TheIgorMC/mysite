"""
Orion Project - Application Entry Point
This file is used to run the Flask application with Gunicorn
"""
import os
import sys

# Ensure the app package directory is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from the app package (directory)
from app import create_app

# Create the Flask application
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    # For development only - use gunicorn in production
    app.run(debug=False)
