import sys
sys.path.append('..')  # Adds the parent directory to Python's search path

from flask import Flask, request, jsonify
import requests
import time
import threading
from utilities.logging import create_main_logger

app = Flask(__name__)
main_logger = create_main_logger()

class PeerNetwork:
    """
    Manages a network of peers for transaction broadcasts within a blockchain-like system.

    Utilizes a custom logging utility for detailed operational logging.
    """

    def __init__(self):
        self.peers = set()
        self.bootstrap_peers = {'http://bootstrap1.example.com', 'http://bootstrap2.example.com'}
        self.known_peers = set()
        self.lock = threading.Lock()
        self.last_successful_ping = time.time()

    def add_peer(self, peer_url):
        """
        Adds a new peer to the network, ensuring thread safety.
        """
        with self.lock:
            self.peers.add(peer_url)
            main_logger.info(f"New peer added: {peer_url}")

    def broadcast_transaction(self, transaction_data):
        """
        Broadcasts a transaction to all known peers, logging successes and failures.
        """
        with self.lock:
            successful_broadcasts, failed_broadcasts = 0, 0
            main_logger.info(f"Broadcasting transaction {transaction_data.get('transaction_id')}")

            for peer in list(self.peers):
                try:
                    response = requests.post(f"{peer}/submit-transaction", json=transaction_data, timeout=5)
                    if response.status_code == 200:
                        successful_broadcasts += 1
                        main_logger.info(f"Transaction {transaction_data.get('transaction_id')} broadcasted to {peer}")
                    else:
                        failed_broadcasts += 1
                        main_logger.warning(f"Transaction {transaction_data.get('transaction_id')} failed to broadcast to {peer}, status code: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    failed_broadcasts += 1
                    self.peers.remove(peer)
                    main_logger.error(f"Error broadcasting transaction {transaction_data.get('transaction_id')} to {peer}: {e}")

            return successful_broadcasts, failed_broadcasts

    def propagate_transaction(self, transaction_data):
        """
        Propagates a transaction to peers, used for transactions received from other nodes.

        Args:
            transaction_data (dict): The transaction data to propagate.
        """
        self.logger.info(f"Propagating transaction {transaction_data.get('transaction_id')} to peers")
        for peer in self.peers:
            try:
                response = requests.post(f"{peer}/propagate-transaction", json=transaction_data)
                if response.status_code == 200:
                    self.logger.info(f"Transaction propagated to {peer}")
                else:
                    self.logger.warning(f"Failed to propagate transaction to {peer}, status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error when propagating to {peer}: {e}")

    def heartbeat(self):
        """
        Periodically checks peer availability, removing unresponsive ones.
        """
        while True:
            with self.lock:
                for peer in list(self.peers):
                    try:
                        response = requests.get(f"{peer}/ping")
                        if response.status_code != 200:
                            self.peers.remove(peer)
                            main_logger.info(f"Unresponsive peer removed: {peer}")
                    except requests.exceptions.RequestException:
                        self.peers.remove(peer)
                        main_logger.error(f"Network error on ping: {peer}")
            time.sleep(30)

if __name__ == '__main__':
    # Set Flask to run in production mode.
    # Check if a port number is provided as a command line argument and use it, otherwise default to 5000.
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(debug=False, host='0.0.0.0', port=port)
