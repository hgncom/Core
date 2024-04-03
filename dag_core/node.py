import uuid
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from network.pulse.networking import NetworkCommunication

# Initialize network communication with actual parameters
network_communication = NetworkCommunication(node_url="http://localhost:5000", initial_peers=["http://peer1.com", "http://peer2.com"])

class DAGNode:
    def __init__(self, transaction_id, sender, receiver, amount, dependencies=None):
        self.transaction_id = transaction_id
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.dependencies = dependencies or []
        self.successors = []

class Transaction:
    def __init__(self, sender, receiver, amount, signature=None, sender_public_key=None, transaction_id=None, dependencies=None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.signature = signature
        self.sender_public_key = sender_public_key
        self.transaction_id = transaction_id or self.generate_transaction_id()
        self.dependencies = dependencies or []

    def generate_transaction_id(self):
        return str(uuid.uuid4())

    def serialize_for_signing(self):
        return f"{self.sender}{self.receiver}{self.amount}".encode()

    def sign(self, private_key):
        self.signature = private_key.sign(
            self.serialize_for_signing(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

    def verify_signature(self, public_key):
        try:
            public_key.verify(
                self.signature,
                self.serialize_for_signing(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    @staticmethod
    def sign_transaction(private_key, transaction):
        return private_key.sign(
            transaction.serialize_for_signing(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

    @staticmethod
    def verify_signature(public_key, signature, transaction):
        try:
            public_key.verify(
                signature,
                transaction.serialize_for_signing(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False

def gossip_transaction(transaction):
    network_communication.gossip_about_transaction(transaction)
