from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import UserModel, WalletModel, db
from plugins.wallet.backend.wallet import WalletPlugin
from utilities.logging import create_main_logger
from sqlalchemy.exc import IntegrityError

main_logger = create_main_logger()

class User(db.Model):

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def associate_wallet_with_user(username, wallet_details):
    logger = main_logger
    logger.info(f"Attempting to associate wallet with user: {username}")

    try:
        # Check if user exists
        user = UserModel.query.filter_by(username=username).first()
        if not user:
            logger.error(f"Attempt to associate wallet with non-existent user: {username}")
            return {"error": "User does not exist."}

        # Check if user already has an associated wallet
        if hasattr(user, 'wallet') and user.wallet:
            logger.error(f"User {username} already has an associated wallet.")
            return {"error": "User already has an associated wallet."}

        # Validate wallet details
        if 'public_key' not in wallet_details or 'wallet_address' not in wallet_details:
            logger.error(f"Invalid wallet details provided for user: {username}. Details: {wallet_details}")
            return {"error": "Invalid wallet details."}

        # Ensure that the wallet is not already associated with another user
        existing_wallet = WalletModel.query.filter_by(wallet_address=wallet_details['wallet_address']).first()
        if existing_wallet:
            logger.error(f"Wallet address {wallet_details['wallet_address']} is already associated with a user.")
            return {"error": "Wallet address is already associated with a user."}

        # Create and associate wallet with user
        new_wallet = WalletModel(
            user_id=user.id,
            wallet_address=wallet_details['wallet_address'],
            public_key=wallet_details['public_key']
        )
        db.session.add(new_wallet)
        db.session.commit()

        logger.info(f"Wallet successfully associated with user: {username}")
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error associating wallet with user {username}: {e}", exc_info=True)
        return {"error": "An error occurred during wallet association."}





def register_user(username, email, password):
    logger = main_logger
    logger.info(f"Starting registration for username: {username}")

    try:
        if not username or not email or not password:
            logger.error("Invalid registration data provided.")
            return {"error": "Invalid registration data."}

        # Check if a user with the same username or email already exists
        existing_user = UserModel.query.filter(
            (UserModel.username == username) | (UserModel.email == email)
        ).first()
        if existing_user:
            logger.error(f"User with given username or email already exists: {username}")
            return {"error": "User already exists.", "user_exists": True, "user_id": existing_user.id}

        user = UserModel(username=username, email=email)
        user.password = password  # This uses the @password.setter to hash the password
        user.password_hash = generate_password_hash(password)  # Hash the password and set it directly

        db.session.add(user)
        db.session.flush()  # This is important to get the user ID

        wallet_plugin = WalletPlugin()
        wallet_details, private_key_pem = wallet_plugin.create_wallet(username)
        if 'error' in wallet_details:
            logger.error(f"Error creating wallet for user: {username}")
            db.session.rollback()
            return {"error": "Error creating wallet."}

        logger.info(f"User {username} with ID {user.id} is being committed to the database.")
        db.session.commit()
        logger.info(f"User {username} registered successfully.")
        return {"success": True, "private_key": private_key_pem}
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during user registration for {username}: {e}", exc_info=True)
        return {"error": "An error occurred during registration."}

