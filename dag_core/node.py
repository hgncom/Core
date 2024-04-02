from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

class DAGNode:
    def __init__(self, transaction_id, sender, receiver, amount, dependencies=None):
        self.transaction_id = transaction_id
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.dependencies = dependencies if dependencies is not None else []
        self.successors = []

class Transaction:
    def __init__(self, sender, receiver, amount, signature, transaction_id=None, dependencies=None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.signature = signature
        self.transaction_id = transaction_id if transaction_id else self.generate_transaction_id()
        self.dependencies = dependencies if dependencies is not None else []

    def generate_transaction_id(self):
        # Generate a unique transaction ID
        return str(uuid.uuid4())

    def sign(self, private_key):
        """
        Signs the transaction using the provided private key.

        Args:
            private_key (RSAPrivateKey): The RSA private key used for signing the transaction.

        Returns:
            The signature as bytes.
        """
        signer = private_key.signer(
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        signer.update(self.to_bytes())
        return signer.finalize()

    def verify_signature(self, public_key):
        """
        Verifies the transaction's signature using the sender's public key.

        Args:
            public_key (RSAPublicKey): The RSA public key used for verification.

        Returns:
            True if the signature is valid, False otherwise.
        """
        verifier = public_key.verifier(
            self.signature,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        verifier.update(self.to_bytes())
        try:
            verifier.verify()
            return True
        except InvalidSignature:
            return False

    def to_bytes(self):
        # This method should serialize the transaction's data for signing or verification.
        return f"{self.sender}{self.receiver}{self.amount}".encode()

    def to_bytes(self):
        # This method should serialize the transaction's data for signing or verification.
        return f"{self.sender}{self.receiver}{self.amount}".encode()

    @staticmethod
    def sign_transaction(private_key, transaction):
        signature = private_key.sign(
            transaction.to_bytes(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return signature

    @staticmethod
    def verify_signature(public_key, signature, data):
        try:
            public_key.verify(
                signature,
                data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False


# Example usage
if __name__ == "__main__":
    dag_config = {
        "task1": ["task2", "task3"],
        "task2": [],
        "task3": ["task2"]
    }
    factory = DAGFactory()
    try:
        dag = factory.create_dag(dag_config)
        print("DAG created successfully")
    except Exception as e:
        print(e)
