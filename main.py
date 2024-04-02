# main.py
from models.base import db
from factory import create_app

# Create the Flask app instance
app = create_app('config.DevelopmentConfig')

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)