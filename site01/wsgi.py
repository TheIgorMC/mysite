"""
Orion Project - WSGI Entry Point
This file is used to run the Flask application with Gunicorn
"""
import os
import sys

# Ensure site01 directory is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import from the app package
from app import create_app

# Create the Flask application instance
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    # For development only - use gunicorn in production
    app.run(host='0.0.0.0', port=5000, debug=False)
