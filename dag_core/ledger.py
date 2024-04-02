from .sharding import ShardManager
from network.pulse.mechanism import PulseConsensusMechanism
from collections import defaultdict
import random
import logging
from flask import current_app
from cryptography.fernet import Fernet

# Configure logging
main_logger = logging.getLogger('Ledger')
main_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('ledger.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
main_logger.addHandler(file_handler)

class Ledger:
    def __init__(self, fernet_key, network_communication):
        self.logger = main_logger
        self.transactions = {}
        self.confirmed_transactions = set()
        self.pending_transactions = set()
        self.balance_sheet = {}
        self.approval_graph = defaultdict(set)
        self.confirmation_threshold = 5

        # Initialize Fernet key from the Flask app's configuration
        fernet_key = 'aqg0ahE_7tGYt8KauLRLNyeEhSAOm0nehgIlcQ-zbkg='
        # Initialize PulseConsensusMechanism with the Fernet key
        self.pulse_consensus = PulseConsensusMechanism(ledger_interaction=self, network_communication=network_communication, encryption_key=fernet_key)
        self.shard_manager = ShardManager(num_shards=10)
        # self.shard_manager initialization will be handled elsewhere to avoid circular import
                # self.shard_manager initialization will be handled elsewhere to avoid circular import

    def get_transactions_for_gossip(self):
        """
        Placeholder method to retrieve transactions that need to be gossiped to peers.
        This method should return a list of transactions.
        """
        # Placeholder implementation, adjust with your actual logic
        return [transaction for transaction_id, transaction in self.transactions.items() if transaction_id not in self.confirmed_transactions]

    # Rest of the Ledger class remains unchanged...

    def attach_transaction_to_dag(self, transaction):
        tips = self.select_tips()
        self.approve_transaction(transaction.transaction_id, tips)
        self.transactions[transaction.transaction_id] = transaction
        self.pending_transactions.add(transaction.transaction_id)
        for tip in tips:
            self.approval_graph[tip].add(transaction.transaction_id)

    def is_transaction_confirmed(self, transaction_id):
        if transaction_id in self.confirmed_transactions:
            return True
        subsequent_transactions = self.get_subsequent_transactions(transaction_id)
        if len(subsequent_transactions) >= self.confirmation_threshold:
            self.confirmed_transactions.add(transaction_id)
            self.pending_transactions.remove(transaction_id)
            return True
        return False

    def get_subsequent_transactions(self, transaction_id):
        subsequent_transactions = set()
        transactions_to_process = [transaction_id]
        while transactions_to_process:
            current_id = transactions_to_process.pop()
            for subsequent_id in self.approval_graph.get(current_id, []):
                if subsequent_id not in subsequent_transactions:
                    subsequent_transactions.add(subsequent_id)
                    transactions_to_process.append(subsequent_id)
        return subsequent_transactions

    def verify_tips(self, tips):
        """
        Verifies the tips that a new transaction is approving.
        """
        for tip_id in tips:
            if tip_id not in self.transactions or tip_id in self.confirmed_transactions:
                raise ValueError(f"Tip {tip_id} is invalid or already confirmed.")

    def select_tips(self):
        if len(self.pending_transactions) < 2:
            return list(self.pending_transactions)
        return random.sample(self.pending_transactions, 2)

    def approve_transaction(self, approving_transaction_id, tips):
        """
        Marks the given tips as approved by the approving transaction.
        """
        for tip in tips:
            self.approval_graph[tip].add(approving_transaction_id)

        self.shard_manager = ShardManager(num_shards=10)  # Initialize ShardManager with 10 shards

    def add_transaction(self, transaction):
        main_logger.info(f"Adding transaction {transaction.transaction_id} to the ledger")
        if not self.pulse_consensus.validate_and_reach_consensus(transaction.to_dict()):
            main_logger.error(f"Transaction {transaction.transaction_id} failed consensus validation.")
            return False
        shard_id = self.shard_manager.assign_shard(transaction)
        self.shard_manager.process_transaction_in_shard(transaction, shard_id)
        self.attach_transaction_to_dag(transaction)
        main_logger.info(f"Transaction {transaction.transaction_id} successfully added to the ledger")
        return True

    def verify_transaction_signature(self, transaction):
        """
        Verifies the transaction's signature.
        """
        sender_public_key = self.get_public_key(transaction.sender)
        return transaction.verify_signature(sender_public_key)

    def get_public_key(self, sender_address):
        """
        Retrieves the public key for the given sender address.
        """
        # Placeholder for public key retrieval logic
        # In practice, this would fetch the public key from a trusted source or the user's wallet
        return sender_public_key

    def confirm_transaction(self, transaction_id):
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            self.logger.warning(f"Transaction {transaction_id} not found.")
            return False
        if self.pulse_consensus.confirm_transaction(transaction):
            self.update_balances(transaction)
            self.logger.info(f"Transaction {transaction_id} confirmed.")
            return True
        else:
            self.logger.warning(f"Transaction {transaction_id} could not be confirmed.")
            return False

    def verify_transaction(self, transaction):
        """
        Verify the signature and other properties of the transaction.
        """
        # Your verification logic here
        return True

    def can_update_balances(self, transaction):
        """
        Checks if the transaction can be safely processed without resulting in negative balances.
        """
        sender_balance = self.balance_sheet.get(transaction.sender, 0)
        return sender_balance >= transaction.amount

    def update_balances(self, transaction):
        sender_balance = self.balance_sheet.get(transaction.sender, 0)
        receiver_balance = self.balance_sheet.get(transaction.receiver, 0)
        self.balance_sheet[transaction.sender] = sender_balance - transaction.amount
        self.balance_sheet[transaction.receiver] = receiver_balance + transaction.amount