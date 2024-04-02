from .base import db
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

class TransactionModel(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(120), nullable=False)
    receiver = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    signature = db.Column(db.Text, nullable=False)
    transaction_id = db.Column(db.String(120), unique=True, nullable=False)
    confirmed = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        """
        Serialize the transaction to a dictionary.
        """
        return {
            'id': self.id,
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'signature': self.signature,
            'transaction_id': self.transaction_id,
            'confirmed': self.confirmed
        }

    def sign(self, private_key_pem):
        """
        Signs the transaction using the provided private key in PEM format.
        """
        private_key = load_pem_private_key(private_key_pem.encode(), password=None)
        signature = private_key.sign(
            self.to_bytes(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        self.signature = signature.hex()

    def verify_signature(self, public_key_pem):
        """
        Verifies the transaction's signature using the sender's public key in PEM format.
        """
        public_key = load_pem_public_key(public_key_pem.encode())
        try:
            public_key.verify(
                bytes.fromhex(self.signature),
                self.to_bytes(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def to_bytes(self):
        # This method should serialize the transaction's data for signing or verification.
        return f"{self.sender}{self.receiver}{self.amount}".encode()

    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'
