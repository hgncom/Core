from flask import Flask, request, jsonify
import requests
import time
import random
import sys
import threading
import logging
from threading import Thread
from time import sleep

app = Flask(__name__)

class PeerNetwork:
    def __init__(self):
        self.logger = logging.getLogger('PeerNetwork')
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler('peernetwork.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.peers = set()  # A set of peer URLs
        self.bootstrap_peers = {'http://bootstrap1.example.com', 'http://bootstrap2.example.com'}  # Replace with actual bootstrap peer URLs
        self.known_peers = set()  # A set to keep track of all known peers
        self.lock = threading.Lock()  # To ensure thread-safe operations on peers
        self.last_successful_ping = time.time()

    def add_peer(self, peer_url):
        self.peers.add(peer_url)
        with self.lock:
            self.peers.add(peer_url)

    def broadcast_transaction(self, transaction_data):
        successful_broadcasts = 0
        failed_broadcasts = 0
        self.logger.info(f"Broadcasting transaction {transaction_data.get('transaction_id')} to peers")
        for peer in list(self.peers):  # Convert to list to avoid runtime errors if peers set changes
            try:
                response = requests.post(f"{peer}/submit-transaction", json=transaction_data, timeout=5)
                if response.status_code == 200:
                    successful_broadcasts += 1
                    self.logger.info(f"Transaction broadcasted to {peer}")
                else:
                    failed_broadcasts += 1
                    self.logger.warning(f"Failed to broadcast transaction to {peer}, status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                failed_broadcasts += 1
                self.peers.remove(peer)  # Remove unresponsive peer
                self.logger.error(f"Network error when broadcasting to {peer}: {e}")
        return successful_broadcasts, failed_broadcasts

    def share_known_peers(self):
        """
        Share the list of known peers with all connected peers.
        """
        for peer in self.peers:
            try:
                requests.post(f"{peer}/discover-peers", json={'peers': list(self.known_peers)})
            except requests.exceptions.RequestException as e:
                print(f"Network error when sharing peers with {peer}: {e}")

    def propagate_transaction(self, transaction_data):
        self.logger.info(f"Propagating transaction {transaction_data.get('transaction_id')} to peers")
        for peer in self.peers:
            try:
                response = requests.post(f"{peer}/propagate-transaction", json=transaction_data)
                if response.status_code == 200:
                    print(f"Transaction propagated to {peer}")
                else:
                    print(f"Failed to propagate transaction to {peer}")
            except requests.exceptions.RequestException as e:
                print(f"Network error when propagating to {peer}: {e}")
                self.logger.error(f"Network error when propagating to {peer}: {e}")

    def heartbeat(self):
        """
        Regularly checks the status of peers and removes any that are unresponsive.
        """
        while True:
            with self.lock:
                for peer in list(self.peers):
                    try:
                        response = requests.get(f"{peer}/ping")
                        if response.status_code != 200:
                            self.peers.remove(peer)
                            print(f"Peer {peer} is unresponsive and has been removed.")
                    except requests.exceptions.RequestException:
                        self.peers.remove(peer)
                        print(f"Peer {peer} is unresponsive and has been removed.")
            sleep(30)  # Check every 30 seconds

peer_network = PeerNetwork()  # Instantiate your PeerNetwork
threading.Thread(target=peer_network.heartbeat).start()  # Start the heartbeat thread

@app.route('/discover-peers', methods=['POST'])
def register_peer():
    peer_url = request.json.get('peer_url')
    if peer_url:
        peer_network.add_peer(peer_url)
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error', 'message': 'Invalid Peer URL'}), 400

@app.route('/ping', methods=['GET'])
def ping():
    """
    Endpoint for checking the status of this node.
    """
    return jsonify({'status': 'success'}), 200

@app.route('/submit-transaction', methods=['POST'])
def submit_transaction():
    transaction_data = request.json
    peer_network.broadcast_transaction(transaction_data)
    return jsonify({'status': 'success', 'transaction_id': transaction_data.get('transaction_id')}), 200

@app.route('/propagate-transaction', methods=['POST'])
def propagate_transaction():
    transaction_data = request.json
    peer_network.propagate_transaction(transaction_data)
    return jsonify({'status': 'success', 'transaction_id': transaction_data.get('transaction_id')}), 200

if __name__ == '__main__':
    port = 5000  # Default port
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=port)
    self.known_peers = set()  # A set to keep track of all known peers

    def share_known_peers(self):
        """
        Share the list of known peers with all connected peers.
        """
        for peer in list(self.peers):  # Use a list to avoid set size change during iteration
            try:
                response = requests.post(f"{peer}/discover-peers", json={'peers': list(self.known_peers)})
                if response.status_code == 200:
                    print(f"Known peers shared with {peer}")
                else:
                    print(f"Failed to share known peers with {peer}")
            except requests.exceptions.RequestException as e:
                print(f"Network error when sharing peers with {peer}: {e}")

        self.share_known_peers()  # Share known peers before broadcasting

@app.route('/discover-peers', methods=['POST'])
def discover_peers():
    """
    Endpoint to discover new peers. Peers share their known peers with each other.
    """
    incoming_peers = request.json.get('peers', [])
    with peer_network.lock:
        for peer in incoming_peers:
            if peer not in peer_network.peers:
                peer_network.known_peers.update(incoming_peers)
                peer_network.peers.add(peer)
    return jsonify({'status': 'success', 'message': 'Peers discovered'}), 200

    # Update the last successful ping time
    self.last_successful_ping = time.time()


    def check_network_partition(self):
        """
        Checks if the node is partitioned from the network by attempting to ping known peers.
        If partitioned, it will try to reconnect to bootstrap peers.
        """
        current_time = time.time()
        # Check if we haven't had a successful ping in the last 60 seconds
        if current_time - self.last_successful_ping > 60:
            print("Detected potential network partition. Attempting to reconnect to bootstrap peers.")
            for bootstrap_peer in self.bootstrap_peers:
                try:
                    response = requests.get(f"{bootstrap_peer}/ping")
                    if response.status_code == 200:
                        self.add_peer(bootstrap_peer)
                        print(f"Reconnected to bootstrap peer: {bootstrap_peer}")
                        self.last_successful_ping = current_time
                        break
                except requests.exceptions.RequestException as e:
                    print(f"Failed to reconnect to bootstrap peer {bootstrap_peer}: {e}")
            else:
                print("Failed to reconnect to any bootstrap peers. Will retry.")



