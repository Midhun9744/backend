import os
from dotenv import load_dotenv
from app import create_app, db

# Load environment variables
load_dotenv()

# Create Flask app
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Database context
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    debug = os.getenv('DEBUG', 'True') == 'True'
    app.run(host='0.0.0.0', port=5000, debug=True)
