"""
Application entry point
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app, db
from app.models import User, Competition, Result

app = create_app(os.getenv('FLASK_CONFIG') or 'development')

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell"""
    return dict(db=db, User=User, Competition=Competition, Result=Result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
