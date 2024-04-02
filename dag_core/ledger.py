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
        if not self.verify_transaction(transaction):
            raise ValueError("Invalid transaction.")

        # Add the transaction to the ledger
        self.transactions[transaction.transaction_id] = transaction
        self.pending_transactions.add(transaction.transaction_id)

        # Select tips to approve and record the approval
        tips = self.select_tips()
        self.approve_transaction(transaction.transaction_id, tips)

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

        # Update balances and transaction status
        if self.can_update_balances(transaction):
            self.update_balances(transaction)
            self.pending_transactions.remove(transaction_id)
            self.confirmed_transactions.add(transaction_id)
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
