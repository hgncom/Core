import requests
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def sign_transaction(transaction_data, private_key_pem):
    private_key = load_pem_private_key(private_key_pem, password=None)
    signer = private_key.signer(
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    signer.update(json.dumps(transaction_data).encode())
    return signer.finalize()

def submit_transaction(transaction_data, node_url):
    response = requests.post(f"{node_url}/submit-transaction", json=transaction_data)
    if response.status_code == 200:
        print("Transaction submitted successfully.")
    else:
        print("Failed to submit transaction.")

# Example usage
private_key_pem = b"""-----BEGIN PRIVATE KEY-----\n...your private key here...\n-----END PRIVATE KEY-----"""
transaction_data = {
    "sender": "Alice",
    "receiver": "Bob",
    "amount": 100,
    # "signature" will be added after signing
}
transaction_data["signature"] = sign_transaction(transaction_data, private_key_pem)
node_url = "http://localhost:5000"
submit_transaction(transaction_data, node_url)
