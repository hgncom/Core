from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import UserModel, WalletModel, db
from plugins.wallet.backend.wallet import WalletPlugin
import logging

class User(db.Model):

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def associate_wallet_with_user(username, wallet_details):
    """
    Associates wallet details with a user account, with validation, error handling, and debugging.
    """
    try:
        # Validate user existence
        user = UserModel.query.filter_by(username=username).first()
        if not user:
            logging.error("Attempt to associate wallet with non-existent user: %s", username)
            return {"error": "User does not exist."}

        # Data validation for wallet_details could be more comprehensive depending on requirements
        if 'public_key' not in wallet_details or 'address' not in wallet_details:
            logging.error("Invalid wallet details provided for user: %s", username)
            return {"error": "Invalid wallet details."}

        public_key_pem = wallet_details['public_key'].public_bytes(
            encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        user_wallet = WalletModel(user_id=user.id, wallet_address=wallet_details['address'], public_key=public_key_pem)

        db.session.add(user_wallet)
        db.session.commit()

        logging.info("Successfully associated wallet with user: %s", username)
        return {"success": True}

    except Exception as e:
        db.session.rollback()
        logging.error("Error associating wallet with user %s: %s", username, str(e))
        return {"error": "An error occurred during wallet association."}

def register_user(username, email, password):
    """
    Registers a new user with validation, error handling, and debugging.
    """
    try:
        # Input data validation (simplified example, consider more comprehensive checks)
        if not username or not email or not password:
            logging.error("Invalid registration data provided.")
            return {"error": "Invalid registration data."}

        # Check for existing user
        existing_user = UserModel.query.filter((UserModel.username == username) | (UserModel.email == email)).first()
        if existing_user:
            logging.error("User with given username or email already exists: %s", username)
            return {"error": "User already exists."}

        user = UserModel(username=username, email=email)
        user.password = password  # Assumes a password setter exists that handles hashing

        db.session.add(user)
        db.session.flush()  # Flush to assign an ID to the user before committing

        # Create a new wallet for the user
        wallet_plugin = WalletPlugin()
        wallet_details = wallet_plugin.create_wallet(username)
        if 'error' in wallet_details:
            logging.error("Error creating wallet for user: %s", username)
            db.session.rollback()
            return {"error": "Error creating wallet."}

        # Associate the wallet with the user
        wallet_association_result = associate_wallet_with_user(username, wallet_details)
        if 'error' in wallet_association_result:
            logging.error("Error associating wallet with user: %s", username)
            db.session.rollback()
            return {"error": "Error associating wallet with user."}

        db.session.commit()

        logging.info("User registered successfully: %s", username)
        return {"success": True}

    except Exception as e:
        db.session.rollback()
        logging.error("Error during user registration for %s: %s", username, str(e))
        return {"error": "An error occurred during registration."}
