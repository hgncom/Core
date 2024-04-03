import threading
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from network.server import PeerNetwork
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from .wallet_interface import WalletInterface
from network.pulse.networking import NetworkCommunication
from models import UserModel, WalletModel, db
from dag_core.ledger import Ledger
from dag_core.node import Transaction
from .wallet_interface import WalletInterface
from flask import current_app

from utilities.logging import create_main_logger
main_logger = create_main_logger()


class WalletPlugin(WalletInterface):
    def __init__(self):
        # Retrieve the Fernet key from the app's configuration
        fernet_key = 'aqg0ahE_7tGYt8KauLRLNyeEhSAOm0nehgIlcQ-zbkg='
        # Initialize the Ledger with the necessary configuration
        self.network_communication = NetworkCommunication(node_url="http://localhost:5000")  # Replace with actual node URL
        self.ledger = Ledger(fernet_key=fernet_key, network_communication=self.network_communication)
        # Initialize other necessary components like the peer network
        self.peer_network = PeerNetwork() # Assuming PeerNetwork is implemented in the network module
        # Ensures that the logger is configured for the class

    def get_private_key_for_user(self, user_id):
        """
        Retrieves the private key for the user with the given user_id.
        This is a placeholder function and should be implemented with proper security.
        """
        # Placeholder implementation - replace with actual key retrieval logic
        # In a real-world application, this would involve secure storage and retrieval mechanisms.
        # For demonstration purposes, we're returning a hardcoded key.
        print ("test")
        return "secure_private_key_pem"

    def send_funds_to_address(self, sender_username, recipient_address, amount, private_key):
        sender_user = UserModel.query.filter_by(username=sender_username).first()
        if not sender_user or not sender_user.wallet:
            return False, "Sender user or wallet not found."
        if sender_user.wallet.amount < amount:
            self.logger.error("Insufficient funds.")
            return False, "Insufficient funds."
        recipient_wallet = WalletModel.query.filter_by(wallet_address=recipient_address).first()
        if not recipient_wallet:
            return False, "Recipient wallet not found."

        # Create a new transaction
        transaction = Transaction(
            sender=sender_user.wallet.wallet_address,
            receiver=recipient_wallet.wallet_address,
            amount=amount,
            signature=''  # Placeholder for the actual signature
        )
        # Sign the transaction with the sender's private key (retrieved securely)
        signature = transaction.sign(private_key)
        transaction.signature = signature

        # Propagate the transaction to the network and add to the ledger
        transaction_data = transaction.to_dict()  # Assuming Transaction has a to_dict method
        transaction_data['signature'] = signature
        try:
            self.peer_network.broadcast_transaction(transaction_data)
            if self.ledger.add_transaction(transaction, sender_user.wallet.public_key):
                # Temporarily deduct the amount from the sender's wallet
                sender_user.wallet.amount -= amount
                db.session.commit()
                return True, "Transaction sent and awaiting confirmation."
            else:
                return False, "Transaction failed to be added to the ledger."
        except NetworkError as e:  # Assuming NetworkError is defined in the network module
            main_logger.error(f"Failed to broadcast transaction: {e}")
            return False, "Failed to broadcast transaction."
        except Exception as e:
            main_logger.error(f"Unexpected error during transaction processing: {e}")
            return False, "An unexpected error occurred."

    def fetch_wallet_data(self, username):
        """
        Fetches wallet data for the specified user from the database.
        """
        main_logger.info(f"Attempting to fetch wallet data for username: {username}")
        try:
            user = UserModel.query.filter_by(username=username).first()
            if not user:
                main_logger.warning(f"User not found for username: {username}")
                return None

            if user.wallet:
                main_logger.info(f"Wallet data found for username: {username}")
                return {"address": user.wallet.wallet_address, "public_key": user.wallet.public_key}
            else:
                main_logger.warning(f"No wallet associated with username: {username}")
                return None
        except Exception as e:
            main_logger.error(f"Error fetching wallet data for username: {username}: {e}")
            return None

    def create_wallet(self, username):
        user = UserModel.query.filter_by(username=username).first()
        if not user:
            return {"error": "User not found."}, None

        if user.wallet:
            return {"error": "Wallet already exists for this user."}, None

        main_logger.info(f"Creating wallet for username: {username}")
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        # Serialize the private key in PEM format
        private_key_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()  # Consider using encryption for real-world applications
        ).decode('utf-8')

        address = self._generate_address(public_key)
        new_wallet = WalletModel(user_id=user.id, wallet_address=address, public_key=public_key_pem)
        db.session.add(new_wallet)
        db.session.commit()

        # Debugging: Log the created private key
        main_logger.debug(f"Private key created for user {username}: {private_key_pem}")

        # Return the public key, address, and private key to the caller
        return {"public_key": public_key_pem, "address": address}, private_key_pem



    def _generate_address(self, public_key):
        """
        Generates a wallet address from a public key by hashing it.

        Args:
            public_key (RSAPublicKey): The RSA public key from which to generate the wallet address.

        Returns:
            str: A wallet address derived from the public key hash.
        """
        # Convert the public key to bytes
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        # Create a SHA-256 hash object
        digest = hashes.Hash(hashes.SHA256())
        # Update the hash object with the public key bytes
        digest.update(public_key_bytes)
        # Finalize the hash and encode it as a hexadecimal string
        address = digest.finalize().hex()
        # Return the first 40 characters to simulate an address (adjust as needed)
        return address[:40]

    def sign_transaction(self, private_key_pem, transaction):
        """
        Signs a transaction using the provided PEM-encoded private key.

        Args:
            private_key_pem (str): The PEM-encoded private key.
            transaction (TransactionModel): The transaction to sign.

        Returns:
            The signature as bytes.
        """
        # Convert the PEM-encoded private key string back into a private key object
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,  # Update accordingly if your private key is password-protected
        )

        # Sign the transaction data
        signature = private_key.sign(
            transaction.to_bytes(),  # Ensure you have a method to convert transaction to bytes
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return signature

    def verify_transaction(self, public_key, transaction, signature):
        """
        Verifies the signature of a transaction using the sender's public key.

        Args:
            public_key (RSAPublicKey): The RSA public key used for verification.
            transaction (dict): The transaction data that was signed.
            signature (bytes): The signature to verify.

        Returns:
            bool: True if verification succeeds, False otherwise.
        """
        try:
            public_key.verify(
                signature,
                str(transaction).encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def _generate_address(self, public_key):
        """
        Generates a wallet address from a public key by hashing it.

        Args:
            public_key (RSAPublicKey): The RSA public key from which to generate the wallet address.

        Returns:
            str: A wallet address derived from the public key hash.
        """
        pub_key_bytes = public_key.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )
        digest = hashes.Hash(hashes.SHA256())
        digest.update(pub_key_bytes)
        # Truncate the hash to create a wallet address, this is a common practice but ensure
        # it meets your security and functional requirements.
        return digest.finalize().hex()[:40]

    def create_transaction(self, sender_address, recipient_address, amount):
        """
        Creates and signs a transaction.
        """
        transaction = Transaction(sender=sender_address, receiver=recipient_address, amount=amount, signature=None)
        # Serialize, sign, and verify the transaction here
        # Assuming serialization and signing methods are implemented correctly
        return transaction if self.verify_transaction_signature(transaction) else None

    def add_transaction_to_ledger(self, transaction):
        """
        Adds a verified transaction to the ledger.
        """
        try:
            ledger = Ledger()
            ledger.add_transaction(transaction, transaction.sender)
            return True
        except Exception as e:
            main_logger.error(f"Error adding transaction to ledger: {e}")
            return False

    def verify_transaction_signature(self, transaction):
        """
        Verifies the transaction's signature.
        """
        # Implement signature verification logic here
        return True

    def confirm_transaction(self, transaction_id):
        """
        Confirms a transaction and updates wallets accordingly.
        """
        transaction = Ledger.get_transaction(transaction_id)
        if not transaction:
            main_logger.error(f"Transaction {transaction_id} not found for confirmation.")
            return

        sender_wallet = WalletModel.query.filter_by(wallet_address=transaction.sender).first()
        recipient_wallet = WalletModel.query.filter_by(wallet_address=transaction.receiver).first()
        if sender_wallet and recipient_wallet:
            sender_wallet.amount -= transaction.amount
            recipient_wallet.amount += transaction.amount
            db.session.commit()
            main_logger.info(f"Transaction {transaction_id} confirmed and balances updated.")
        else:
            main_logger.error(f"Failed to update wallets for transaction {transaction_id}.")

