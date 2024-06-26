from .sharding import ShardManager
from network.pulse.mechanism import PulseConsensusMechanism
from collections import defaultdict
import random
import logging
import threading
from time import sleep
from flask import current_app
from cryptography.fernet import Fernet

# Configure logging
main_logger = logging.getLogger('Ledger')
main_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('main.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
main_logger.addHandler(file_handler)

class Ledger:
    def __init__(self, fernet_key, network_communication):
        self.logger = main_logger
        self.logger.info("Ledger initialized with network communication and consensus mechanism.")
        self.transactions = {}
        self.confirmed_transactions = set()
        self.pending_transactions = set()
        self.balance_sheet = {}
        self.approval_graph = defaultdict(set)
        self.confirmation_threshold = 0

        # Initialize Fernet key from the Flask app's configuration
        fernet_key = 'aqg0ahE_7tGYt8KauLRLNyeEhSAOm0nehgIlcQ-zbkg='
        # Initialize PulseConsensusMechanism with the Fernet key
        self.pulse_consensus = PulseConsensusMechanism(ledger_interaction=self, network_communication=network_communication, encryption_key=fernet_key)
        self.shard_manager = ShardManager(num_shards=10)
        # Start the background task to check pending transactions
        self.start_background_task()

    def start_background_task(self):
        """
        Starts a background task that periodically checks for transaction confirmations.
        """
        def background_task():
            while True:
                self.logger.info("Starting background task to check for pending transactions.")
                self.check_pending_transactions()
                self.logger.info("Background task completed, sleeping for 60 seconds.")
                sleep(60)  # Wait for 60 seconds before checking again

        # Run the background task in a separate thread
        self.logger.info("Starting background thread for transaction confirmation.")
        threading.Thread(target=background_task, daemon=True).start()

    def check_pending_transactions(self):
        """
        Checks the status of pending transactions and updates the database accordingly.
        """
        self.logger.info("Checking for pending transactions.")
        for transaction_id in list(self.pending_transactions):
            self.logger.info(f"Checking transaction {transaction_id} for confirmation.")
            if self.is_transaction_confirmed(transaction_id):
                self.logger.info(f"Transaction {transaction_id} is confirmed, proceeding with confirmation.")
                self.confirm_transaction(transaction_id)
                self.logger.info(f"Transaction {transaction_id} confirmed and database updated.")
            else:
                self.logger.info(f"Transaction {transaction_id} is not yet confirmed.")

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
            self.logger.info(f"Transaction {transaction_id} is already confirmed.")
            return True
        subsequent_transactions = self.get_subsequent_transactions(transaction_id)
        if len(subsequent_transactions) >= self.confirmation_threshold:
            self.logger.info(f"Transaction {transaction_id} has met the confirmation threshold ({self.confirmation_threshold}).")
            self.confirmed_transactions.add(transaction_id)
            self.pending_transactions.remove(transaction_id)
            return True
        else:
            self.logger.info(f"Transaction {transaction_id} has not yet met the confirmation threshold ({len(subsequent_transactions)}/{self.confirmation_threshold}).")
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
        self.logger.info(f"Attempting to add transaction {transaction.transaction_id} to the ledger.")
        main_logger.info(f"Adding transaction {transaction.transaction_id} to the ledger")
        main_logger.debug(f"Transaction details: sender={transaction.sender}, receiver={transaction.receiver}, amount={transaction.amount}")
        if not self.pulse_consensus.validate_and_reach_consensus(transaction.to_dict()):
            self.logger.error(f"Transaction {transaction.transaction_id} failed consensus validation and will not be added to the ledger.")
            main_logger.error(f"Transaction {transaction.transaction_id} failed consensus validation.")
            return False
        self.logger.info(f"Transaction {transaction.transaction_id} passed consensus validation.")
        shard_id = self.shard_manager.assign_shard(transaction)
        main_logger.debug(f"Transaction {transaction.transaction_id} assigned to shard {shard_id} for processing.")
        self.logger.info(f"Transaction {transaction.transaction_id} assigned to shard {shard_id}.")
        self.shard_manager.process_transaction_in_shard(transaction, shard_id)
        main_logger.debug(f"Transaction {transaction.transaction_id} processed in shard {shard_id}. Checking for success...")
        self.logger.info(f"Transaction {transaction.transaction_id} processed in shard {shard_id}.")
        self.attach_transaction_to_dag(transaction)
        main_logger.debug(f"Transaction {transaction.transaction_id} attached to DAG. Awaiting further confirmations...")
        main_logger.info(f"Transaction {transaction.transaction_id} successfully added to the ledger")
        self.logger.info(f"Transaction {transaction.transaction_id} attached to the DAG.")
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
        self.logger.info(f"Attempting to confirm transaction {transaction_id}.")
        transaction = self.transactions.get(transaction_id)
        # Log transaction details
        self.logger.debug(f"Transaction details: ID={transaction_id}, Sender={transaction.sender}, Receiver={transaction.receiver}, Amount={transaction.amount}")

        if not transaction:
            self.logger.info(f"Transaction {transaction_id} not found in the ledger.")
            self.logger.info(f"Transaction {transaction_id} not found.")
            return False
        if self.pulse_consensus.confirm_transaction(transaction):
            sender_wallet = WalletModel.query.filter_by(wallet_address=transaction.sender).first()
            recipient_wallet = WalletModel.query.filter_by(wallet_address=transaction.receiver).first()

            # Log wallet lookup results
            if sender_wallet:
                self.logger.info(f"Sender wallet found: Address={sender_wallet.wallet_address}, Current amount={sender_wallet.amount}")
            else:
                self.logger.info(f"Sender wallet not found for address: {transaction.sender}")

            if recipient_wallet:
                self.logger.info(f"Recipient wallet found: Address={recipient_wallet.wallet_address}, Current amount={recipient_wallet.amount}")
            else:
                self.logger.info(f"Recipient wallet not found for address: {transaction.receiver}")

            if sender_wallet and recipient_wallet:
                self.logger.info(f"Updating wallets for transaction {transaction_id}.")
                sender_wallet.amount -= transaction.amount
                recipient_wallet.amount += transaction.amount
                db.session.commit()
                self.logger.info(f"Transaction {transaction_id} confirmed and balances updated.")
                self.confirmed_transactions.add(transaction_id)
                if transaction_id in self.pending_transactions:
                    self.pending_transactions.remove(transaction_id)
                return True
            else:
                self.logger.info(f"Failed to update wallets for transaction {transaction_id}.")
                return False
        else:
            self.logger.info(f"Transaction {transaction_id} could not be confirmed by consensus.")
            return False

    def verify_transaction(self, transaction):
        """
        Verify the signature and other properties of the transaction.
        """
        # Your verification logic here
        self.logger.info(f"Transaction {transaction.transaction_id} attached to the DAG.")
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