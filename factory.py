import logging
from flask import Flask
from models.base import db
from frontend.x.user.blueprint import user_blueprint
from frontend.x.wallet.blueprint import wallet_blueprint

def configure_logging(app):
    """
    Configures logging for the application.

    Args:
    - app: The Flask application instance.
    """
    if app.config['DEBUG']:
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)

    # Stream logs to stdout, which is useful for Docker/container setups
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(app.logger.level)
    app.logger.addHandler(stream_handler)
    app.logger.info("Logging configured.")

def register_blueprints(app):
    """
    Registers Flask blueprints for modular architecture.

    Args:
    - app: The Flask application instance.
    """
    app.register_blueprint(user_blueprint, url_prefix='/user')
    app.register_blueprint(wallet_blueprint, url_prefix='/wallet')
    app.logger.debug('Blueprints registered.')

def init_db(app):
    """
    Initializes and creates necessary database tables.

    Args:
    - app: The Flask application instance.
    """
    with app.app_context():
        try:
            db.create_all()
            app.logger.info('Database tables created successfully.')
        except Exception as e:
            app.logger.error(f'Error creating database tables: {e}')

def create_app(config_class='config.DevelopmentConfig'):
    """
    Factory function to create and configure the Flask app.

    Args:
    - config_class (str): The configuration class to use for the Flask app.

    Returns:
    - app: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize logging
    configure_logging(app)

    # Initialize extensions like SQLAlchemy
    db.init_app(app)

    # Register application blueprints
    register_blueprints(app)

    # Initialize and create the database tables
    init_db(app)

    app.logger.debug('Application created and configured.')

    return app
