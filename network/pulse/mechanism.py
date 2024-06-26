import json
import threading
import time
import random
from cryptography.fernet import Fernet
import logging
from urllib.parse import urlparse
import requests

# Setup enhanced logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PulseConsensus')

def rate_limited(max_per_minute):
    """Decorator to rate-limit function calls."""
    min_interval = 60.0 / max_per_minute
    last_called = {}
    def decorator(func):        
        if func not in last_called:
            last_called[func] = {'time': None, 'lock': threading.Lock()}
        def wrapper(*args, **kwargs):
            with last_called[func]['lock']:
                current_time = time.monotonic()
                if last_called[func]['time'] is not None and current_time - last_called[func]['time'] < min_interval:
                    time.sleep(min_interval - (current_time - last_called[func]['time']))
                last_called[func]['time'] = time.monotonic()
            return func(*args, **kwargs)
        return wrapper
    return decorator

class PulseConsensusMechanism:
    def __init__(self, ledger_interaction, network_communication, encryption_key):
        self.ledger_interaction = ledger_interaction
        self.network_communication = network_communication
        self.fernet = Fernet(encryption_key)
        if self.network_communication is not None:
            self.init_background_tasks()
        else:
            logger.error("Network communication must be initialized before starting background tasks.")

    def init_background_tasks(self):
        threading.Thread(target=self.peer_discovery_task, daemon=True).start()
        threading.Thread(target=self.transaction_gossip_task, daemon=True).start()

    @rate_limited(60)
    def process_incoming_transaction(self, encrypted_data):
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            transaction = json.loads(decrypted_data)
            if self.validate_and_reach_consensus(transaction):
                if self.ledger_interaction.add_transaction(transaction):
                    logger.info(f"Transaction {transaction['id']} added to the ledger.")
                    self.broadcast_transaction(transaction)
                else:
                    logger.warning("Transaction validation failed, or ledger update unsuccessful.")
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")

    def confirm_transaction(self, transaction):
        """
        Attempt to confirm a transaction based on network-wide consensus.
        """
        transaction_id = transaction['id']
        logger.info(f"Attempting to confirm transaction {transaction_id}...")

        try:
            # Determine the sample size of peers to request validation from
            sample_peers = self.determine_sample_size()
            logger.info(f"Requesting validation from {sample_peers} peers...")

            # Request validation from a sample of peers
            validations_received = 0
            peers = list(self.network_communication.peers)
            logger.debug(f"Available peers: {peers}")

            for peer in random.sample(peers, sample_peers):
                logger.debug(f"Requesting validation from peer: {peer}")
                if self.request_peer_validation(peer, transaction):
                    validations_received += 1
                    logger.debug(f"Validation received from peer: {peer}")
                else:
                    logger.debug(f"Validation not received from peer: {peer}")

            # Check if the required consensus threshold is met
            consensus_threshold = 0.6
            consensus_ratio = validations_received / sample_peers
            logger.info(f"Validations received: {validations_received} out of {sample_peers} ({consensus_ratio:.2%})")

            if consensus_ratio >= consensus_threshold:
                logger.info(f"Transaction {transaction_id} confirmed by network consensus.")
                return True
            else:
                logger.warning(f"Transaction {transaction_id} failed to achieve consensus.")
                return False

        except Exception as e:
            logger.error(f"Error occurred while confirming transaction {transaction_id}: {str(e)}")
            return False

    def validate_and_reach_consensus(self, transaction):
        # Placeholder for comprehensive validation and consensus reaching process
        return True

    def peer_discovery_task(self):
        while True:
            self.discover_peers()
            time.sleep(300)

    def discover_peers(self):
        with self.network_communication.lock:  # Removed the nested lock
                current_peers = list(self.network_communication.peers)
        for peer in current_peers:
            try:
                response = requests.get(f"{peer}/peers", timeout=5)
                if response.status_code == 200:
                    new_peers = response.json().get('peers', [])
                    with self.network_communication.lock:  # Use the existing lock
                        self.network_communication.peers.update(new_peers - {peer})
            except Exception as e:
                logger.error(f"Failed to discover peers from {peer}: {e}")
                with self.network_communication.lock:  # Use the existing lock
                    self.network_communication.peers.discard(peer)

    def transaction_gossip_task(self):
        while True:
            transactions = self.ledger_interaction.get_transactions_for_gossip()
            for transaction in transactions:
                self.gossip_transaction(transaction)
            time.sleep(10)

    def broadcast_transaction(self, transaction):
        encrypted_data = self.fernet.encrypt(json.dumps(transaction).encode())
        for peer in list(self.network_communication.peers):
            self.send_transaction(peer, encrypted_data)

    def gossip_transaction(self, transaction):
        transaction_data = {
            "id": transaction.id,
            "sender": transaction.sender,
            "receiver": transaction.receiver,
            "amount": transaction.amount,
            # Include other necessary fields
        }
        encrypted_data = self.fernet.encrypt(json.dumps(transaction_data).encode())

    def send_transaction(self, peer, encrypted_data):
        try:
            response = requests.post(f"{peer}/transactions", data=encrypted_data, timeout=5)
            if response.status_code != 200:
                raise Exception("Network error or peer rejection.")
        except Exception as e:
            logger.error(f"Failed to send transaction to {peer}: {e}")
            with threading.Lock():
                self.network_communication.peers.discard(peer)

    def random_sampling_consensus(self, transaction):
        # Implement random sampling consensus mechanism here
        return True

    def request_peer_validation(self, peer_url, transaction):
        # Implement peer validation request logic here
        return True

    def determine_sample_size(self):
        with threading.Lock():
            num_peers = len(self.network_communication.peers)
        return max(3, min(num_peers, int(num_peers * 0.2)))

