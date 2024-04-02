from collections import defaultdict
import random
import logging

# Configure logging
main_logger = logging.getLogger('Ledger')
main_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('ledger.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
main_logger.addHandler(file_handler)

class Ledger:
    def __init__(self):
        self.logger = main_logger
        self.transactions = {}
        self.confirmed_transactions = set()
        self.pending_transactions = set()
        self.balance_sheet = {}
        self.approval_graph = defaultdict(set)
        self.confirmation_threshold = 5  # The required number of confirmations can be adjusted as needed

    def attach_transaction_to_dag(self, transaction):
        """
        Attaches the transaction to the DAG by selecting tips and updating the approval graph.
        """
        # Select tips to approve and record the approval
        tips = self.select_tips()
        self.approve_transaction(transaction.transaction_id, tips)

        # Add the transaction to the ledger
        self.transactions[transaction.transaction_id] = transaction
        self.pending_transactions.add(transaction.transaction_id)

        # Update the approval graph
        for tip in tips:
            self.approval_graph[tip].add(transaction.transaction_id)

    def is_transaction_confirmed(self, transaction_id):
        """
        Checks if the transaction is confirmed based on the number of subsequent transactions referencing it.
        """
        if transaction_id in self.confirmed_transactions:
            return True
        subsequent_transactions = self.get_subsequent_transactions(transaction_id)
        if len(subsequent_transactions) >= self.confirmation_threshold:
            self.confirmed_transactions.add(transaction_id)
            if transaction_id in self.pending_transactions:
                self.pending_transactions.remove(transaction_id)
            return True
        return False

    def get_subsequent_transactions(self, transaction_id):
        """
        Retrieves all subsequent transactions that reference the given transaction_id directly or indirectly.
        """
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
        """
        Selects two tips (unconfirmed transactions) to be approved by a new transaction.
        For simplicity, this example selects two random tips.
        """
        if len(self.pending_transactions) < 2:
            return list(self.pending_transactions)
        return random.sample(self.pending_transactions, 2)

    def approve_transaction(self, approving_transaction_id, tips):
        """
        Marks the given tips as approved by the approving transaction.
        """
        for tip in tips:
            self.approval_graph[tip].add(approving_transaction_id)

    def add_transaction(self, transaction):
        """
        Adds a transaction to the ledger after validation and verification.
        """
        self.logger.info(f"Adding transaction {transaction.transaction_id} to the ledger")

        # Verify and validate the transaction
        if not self.verify_transaction_signature(transaction):
            self.logger.error(f"Invalid transaction signature for {transaction.transaction_id}.")
            raise ValueError("Invalid transaction signature.")

        # Verify the tips the transaction is approving
        self.verify_tips(transaction.dependencies)

        if not self.verify_transaction(transaction):
            raise ValueError("Invalid transaction.")

        # Attach the transaction to the DAG
        self.attach_transaction_to_dag(transaction)

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
        """
        Confirms a transaction and updates the ledger and wallet balances.
        """
        self.logger.info(f"Confirming transaction {transaction_id}")

        # Check if the transaction exists and is pending confirmation
        if transaction_id not in self.transactions or transaction_id in self.confirmed_transactions:
            self.logger.warning(f"Transaction {transaction_id} not found or already confirmed.")
            return False

        # Get the transaction details
        transaction = self.transactions[transaction_id]

        # Check if the transaction has enough confirmations to be confirmed
        if not self.is_transaction_confirmed(transaction_id):
            self.logger.warning(f"Transaction {transaction_id} does not have enough confirmations yet.")
            return False

        # Confirm the transaction and update balances
        if not self.can_update_balances(transaction):
            self.logger.warning(f"Insufficient funds to confirm transaction {transaction_id}.")
            return False

        self.update_balances(transaction)
        return True
            return True
        else:
            self.logger.warning(f"Insufficient funds to confirm transaction {transaction_id}.")
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
        """
        Updates the ledger balances based on the transaction details.
        """
        self.balance_sheet[transaction.sender] -= transaction.amount
        self.balance_sheet[transaction.receiver] += transaction.amount
