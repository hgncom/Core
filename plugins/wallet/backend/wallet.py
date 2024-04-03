import threading
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from network.server import PeerNetwork
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import base64
from .wallet_interface import WalletInterface
from network.pulse.networking import NetworkCommunication
from models import UserModel, WalletModel, db
from dag_core.ledger import Ledger
from dag_core.node import Transaction
from .wallet_interface import WalletInterface
from flask import current_app
from base64 import b64decode


from utilities.logging import create_main_logger
main_logger = create_main_logger()


class WalletPlugin(WalletInterface):
    def __init__(self):
        # Retrieve the Fernet key from the app's configuration
        self.fernet_key = current_app.config['FERNET_KEY']
        # Initialize the Ledger with the necessary configuration
        self.network_communication = NetworkCommunication(node_url=current_app.config['NODE_URL'])  # Use the node URL from the app's configuration
        self.ledger = Ledger(fernet_key=self.fernet_key, network_communication=self.network_communication)
        self.ledger = Ledger(fernet_key=fernet_key, network_communication=self.network_communication)
        # Initialize other necessary components like the peer network
        self.peer_network = PeerNetwork() # Assuming PeerNetwork is implemented in the network module
        # Ensures that the logger is configured for the class

    def get_private_key_for_user(self, user_id):
        """
        Retrieves the private key for the user with the given user_id.
        This is a placeholder function and should be implemented with proper security.
        """
        # Generate a new RSA private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Get the PEM representation of the private key
        private_key_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        return private_key_pem

    def send_funds_to_address(self, sender_username, recipient_address, amount, private_key):
        sender_user = UserModel.query.filter_by(username=sender_username).first()
        if not sender_user or not sender_user.wallet:
            main_logger.error(f"send_funds_to_address: Sender user {sender_username} or wallet not found.")
            return False, "Sender user or wallet not found."
        main_logger.info(f"send_funds_to_address: Sender {sender_username} initiating a transaction to {recipient_address} for amount {amount}.")
        main_logger.info(f"Sender {sender_username} initiating a transaction to {recipient_address} for amount {amount}.")
        if sender_user.wallet.amount < amount:
            main_logger.error(f"send_funds_to_address: Insufficient funds for sender {sender_username}.")
            self.logger.error("Insufficient funds.")
            return False, "Insufficient funds."
        recipient_wallet = WalletModel.query.filter_by(wallet_address=recipient_address).first()
        if not recipient_wallet:
            main_logger.error(f"send_funds_to_address: Recipient wallet {recipient_address} not found.")
            return False, "Recipient wallet not found."

        # Create a new transaction
        transaction = Transaction(
            sender=sender_user.wallet.wallet_address,
            receiver=recipient_wallet.wallet_address,
            amount=amount,
            signature=''  # Placeholder for the actual signature
        )
        main_logger.info(f"send_funds_to_address: Transaction created for {sender_username} to {recipient_address} for amount {amount}.")
        main_logger.info(f"Transaction created for {sender_username} to {recipient_address} for amount {amount}.")
        # Sign the transaction with the sender's private key (retrieved securely)
        signature = self.sign_transaction(transaction, private_key)
        transaction.signature = signature
        main_logger.info(f"send_funds_to_address: Transaction signed with signature {signature}.")
        main_logger.info(f"Transaction signed with signature {signature}.")

        # Propagate the transaction to the network and add to the ledger
        transaction_data = transaction.to_dict()  # Assuming Transaction has a to_dict method
        transaction_data['signature'] = signature
        main_logger.info(f"Broadcasting transaction {transaction.transaction_id} to the network.")
        # Sign the transaction with the sender's private key (retrieved securely)
        signature = transaction.sign(private_key)
        transaction.signature = signature

        # Propagate the transaction to the network and add to the ledger
        transaction_data = transaction.to_dict()  # Assuming Transaction has a to_dict method
        transaction_data['signature'] = signature
        try:
            self.peer_network.broadcast_transaction(transaction_data)
            main_logger.info(f"send_funds_to_address: Transaction {transaction.transaction_id} broadcasted to peers.")
            main_logger.info(f"Transaction {transaction.transaction_id} broadcasted to peers.")
            # Add transaction to ledger and update sender's balance
            if self.ledger.add_transaction(transaction):
                main_logger.info(f"send_funds_to_address: Transaction {transaction.transaction_id} added to ledger, awaiting confirmation.")
                main_logger.info(f"Transaction {transaction.transaction_id} added to ledger, awaiting confirmation.")
                return True, "Transaction sent and awaiting confirmation."
            else:
                main_logger.error(f"send_funds_to_address: Transaction {transaction.transaction_id} could not be added to ledger.")
                main_logger.error(f"Transaction {transaction.transaction_id} could not be added to the ledger.")
                main_logger.error(f"Transaction {transaction.transaction_id} could not be added to ledger.")
                return False, "Transaction failed to be added to the ledger."
        except Exception as e:
            main_logger.error(f"send_funds_to_address: Error during sending funds: {e}")
            main_logger.error(f"Error during sending funds: {e}")
            return False, "An error occurred during the sending process."

    def fetch_wallet_data(self, username):
        """
        Fetches wallet data for the specified user from the database.
        """
        main_logger.info(f"Attempting to fetch wallet data for username: {username}")
        try:
            user = UserModel.query.filter_by(username=username).first()
            if not user:
                main_logger.warning(f"User {username} not found.")
                return {"error": "User not found."}
            wallet = WalletModel.query.filter_by(user_id=user.id).first()
            if not wallet:
                main_logger.warning(f"Wallet not found for user: {username}")
                return {"error": "Wallet not found."}
            main_logger.info(f"Wallet data found for user: {username}")
            return {
                "address": wallet.wallet_address,
                "public_key": wallet.public_key,
                "amount": wallet.amount
            }
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

        # Add logging statement to trace the execution flow
        main_logger.debug("Before generating private key PEM")

        private_key_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()  # Consider using encryption for real-world applications
        ).decode('utf-8')

        # Add logging statement to trace the execution flow
        main_logger.debug("After generating private key PEM")

        main_logger.debug(f"Private key PEM before encoding: {private_key_pem}")
        # Encode the private key to base64
        private_key_base64 = base64.b64encode(private_key_pem.encode('utf-8')).decode('utf-8')
        main_logger.debug(f"Private key encoded to base64: {private_key_base64}")

        address = self._generate_address(public_key)
        new_wallet = WalletModel(user_id=user.id, wallet_address=address, public_key=public_key_pem)
        db.session.add(new_wallet)
        db.session.commit()

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

    @staticmethod
    def safe_b64decode(data):
        """Safely decodes a base64-encoded string, ensuring correct padding."""
        original_data = data  # Store the original data for logging
        data = data.strip()  # Remove any trailing whitespace or newlines
        main_logger.info(f"Original data before strip: {original_data}")
        main_logger.info(f"Data after strip: {data}")

        # Add padding if necessary before decoding
        if len(data) % 4 != 0:
            data += '=' * (4 - len(data) % 4)
            main_logger.info(f"Data after adding padding: {data}")

        try:
            decoded_data = base64.b64decode(data)
            main_logger.info(f"Decoded data: {decoded_data}")
            main_logger.info(f"Decoded data length: {len(decoded_data)}")
            return decoded_data
        except Exception as e:
            main_logger.error(f"Error decoding base64 data: {e}")
            raise

    def sign_transaction(self, transaction, private_key_pem):
        try:
            # Load the private key from the PEM data
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'), password=None, backend=default_backend()
            )

            # Serialize the transaction data for signing
            transaction_data = transaction.serialize_for_signing()

            # Sign the transaction
            signature = private_key.sign(
                transaction_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Update the transaction with the signature
            transaction.signature = base64.b64encode(signature).decode('utf-8')

            return transaction
        except Exception as e:
            main_logger.error(f"Exception occurred during transaction signing: {e}")
            raise


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
            success = self.ledger.add_transaction(transaction)
            if success:
                return True, "Transaction added to ledger successfully."
            else:
                return False, "Failed to add transaction to ledger."
        except Exception as e:
            main_logger.error(f"Error adding transaction to ledger: {e}")
            return False, f"Error adding transaction to ledger: {e}"

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
