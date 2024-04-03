import json
import time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, load_pem_public_key, serialize_public_key

class Transaction:
    def __init__(self, sender, receiver, amount, signature=None, sender_public_key=None, timestamp=None, dependencies=None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.signature = signature
        self.sender_public_key = sender_public_key
        self.timestamp = timestamp if timestamp else time.time()
        self.dependencies = dependencies if dependencies else []

    def serialize_for_signing(self):
        """Serialize transaction for signing, excluding the signature."""
        return json.dumps({
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'dependencies': self.dependencies,
        }, sort_keys=True).encode('utf-8')

    def sign(self, private_key):
        """Sign the transaction with the sender's private key."""
        signer = private_key.signer(
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        signer.update(self.serialize_for_signing())
        self.signature = signer.finalize()

    def verify_signature(self):
        """Verify the transaction signature using the sender's public key."""
        public_key = load_pem_public_key(self.sender_public_key)
        verifier = public_key.verifier(
            self.signature,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        verifier.update(self.serialize_for_signing())
        try:
            verifier.verify()
            return True
        except InvalidSignature:
            return False

    def to_dict(self):
        """Convert transaction to dictionary for network transmission."""
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'signature': self.signature.hex(),
            'sender_public_key': self.sender_public_key.decode('utf-8'),
            'timestamp': self.timestamp,
            'dependencies': self.dependencies,
        }

    @staticmethod
    def from_dict(data):
        """Instantiate a Transaction object from a dictionary."""
        return Transaction(
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount'],
            signature=bytes.fromhex(data['signature']),
            sender_public_key=data['sender_public_key'].encode('utf-8'),
            timestamp=data['timestamp'],
            dependencies=data['dependencies']
        )
