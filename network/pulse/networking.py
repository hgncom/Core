import requests
import random
import time
import threading
from urllib.parse import urlparse

class NetworkCommunication:
    def __init__(self, node_url, initial_peers=None):
        self.node_url = node_url
        self.peers = set(initial_peers or [])
        self.lock = threading.Lock()

        # Background thread for peer discovery and maintenance
        threading.Thread(target=self.peer_discovery_and_maintenance, daemon=True).start()

    def broadcast_transaction(self, transaction, exclude=None):
        """Broadcasts a transaction to all peers except the excluded ones."""
        main_logger.info(f"Broadcasting transaction {transaction['id']} to peers")
        exclude = exclude or set()
        peers_to_notify = self.peers.difference(exclude)
        for peer in peers_to_notify:
            self._send_transaction(peer, transaction)

    def random_sampling_consensus(self, transaction, sample_size=10):
        """Performs dynamic sampling among peers for consensus, adapting the sample size based on the network size."""
        with self.lock:
            if len(self.peers) < sample_size:
                sample_size = len(self.peers)
            sampled_peers = random.sample(self.peers, sample_size)

        votes = []
        for peer in sampled_peers:
            vote = self._request_validation(peer, transaction)
            votes.append(vote)

        consensus_reached = votes.count(True) / len(votes) > 0.66  # 66% consensus threshold
        return consensus_reached, sampled_peers

    def _send_transaction(self, peer_url, transaction):
        """Helper function to send a transaction to a peer."""
        try:
            response = requests.post(f"{peer_url}/transactions", json=transaction.to_dict(), timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            self.peers.discard(peer_url)  # Remove unresponsive peer
            return False

    def _request_validation(self, peer_url, transaction):
        """Requests a peer to validate a transaction."""
        try:
            response = requests.post(f"{peer_url}/validate", json=transaction.to_dict(), timeout=5)
            return response.status_code == 200 and response.json().get('valid', False)
        except requests.RequestException:
            self.peers.discard(peer_url)  # Remove unresponsive peer
            return False

    def peer_discovery_and_maintenance(self):
        """Regularly discovers new peers and removes unresponsive ones."""
        while True:
            self._discover_new_peers()
            self._remove_unresponsive_peers()
            time.sleep(60)  # Run every 60 seconds

    def _discover_new_peers(self):
        """Discovers new peers by asking current peers for their lists of peers."""
        for peer in list(self.peers):
            try:
                response = requests.get(f"{peer}/peers", timeout=5)
                if response.status_code == 200:
                    new_peers = response.json().get('peers', [])
                    with self.lock:
                        self.peers.update(new_peers)
                        self.peers.discard(self.node_url)  # Ensure not to add self
            except requests.RequestException:
                self.peers.discard(peer)  # Remove unresponsive peer

    def _remove_unresponsive_peers(self):
        """Pings peers to check responsiveness and removes any that are unresponsive."""
        for peer in list(self.peers):
            if not self._ping_peer(peer):
                with self.lock:
                    self.peers.discard(peer)

    def _ping_peer(self, peer_url):
        """Sends a ping to a peer to check if it's responsive."""
        try:
            response = requests.get(f"{peer_url}/ping", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def add_peer(self, peer_url):
        """Adds a new peer to the network."""
        parsed_url = urlparse(peer_url)
        if parsed_url.scheme and parsed_url.netloc:
            with self.lock:
                self.peers.add(peer_url)
