from models.transaction import TransactionModel
from models.dagnode import DAGNodeModel
from models.base import db
from collections import defaultdict
import random
import logging

class Ledger:
    def __init__(self):
        self.logger = logging.getLogger('Ledger')
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler('ledger.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.transactions = {}
        self.confirmed_transactions = set()
        self.pending_transactions = set()
        self.tip_selection_algorithm = self.random_tip_selection
        self.balance_sheet = {}
        self.approval_graph = defaultdict(set)  # Tracks which transactions have approved which

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
    def random_tip_selection(self):
        """
        Randomly selects two tips (unconfirmed transactions) from the set of pending transactions.
        """
        return random.sample(self.pending_transactions, 2) if len(self.pending_transactions) >= 2 else list(self.pending_transactions)

    def add_transaction(self, transaction):
        """
        Adds a transaction to the ledger after validation and verification.
        """
        self.logger.info(f"Adding transaction {transaction.transaction_id} to the ledger")
        # Verify the transaction's signature first
        if not self.verify_transaction_signature(transaction):
            raise ValueError("Invalid transaction signature.")

        # Perform transaction-specific validations, including double spending checks
        if not self.validate_transaction_rules(transaction):
            raise ValueError("Transaction validation failed.")

        new_transaction = TransactionModel(sender=transaction.sender, receiver=transaction.receiver, amount=transaction.amount, signature=transaction.signature, transaction_id=transaction.transaction_id)
        db.session.add(new_transaction)
        db.session.commit()
        print(f"Transaction {transaction.transaction_id} added to the database.")
        # Select tips to approve and record the approval
        tips = self.tip_selection_algorithm()
        self.approve_transaction(transaction.transaction_id, tips)
        # Select tips to approve and record the approval
        tips = self.select_tips()
        self.approve_transaction(transaction.transaction_id, tips)

    def confirm_transaction(self, transaction_id):
        self.logger.info(f"Confirming transaction {transaction_id}")
        """
        Confirms a transaction and updates the ledger and wallet balances.
        Ensures that the transaction exists and has not been confirmed already.
        """
        if transaction_id not in self.transactions:
            self.logger.warning(f"Transaction {transaction_id} not found or already confirmed.")
            print(f"Transaction {transaction_id} not found or already confirmed.")
            return False

        transaction = self.transactions[transaction_id]

        # Check if we can update balances safely
        if not self.can_update_balances(transaction):
            print(f"Cannot confirm transaction {transaction_id}: insufficient funds.")
            return False

        # Update balances based on the transaction
        self.update_balances(transaction)

        # Move the transaction from pending to confirmed
        self.confirmed_transactions.add(transaction_id)
        self.pending_transactions.remove(transaction_id)
        del self.transactions[transaction_id]
        # Update the approval graph
        for approver in self.approval_graph[transaction_id]:
            self.pending_transactions.discard(approver)
            self.confirmed_transactions.add(approver)
        del self.approval_graph[transaction_id]

        print(f"Transaction {transaction_id} confirmed.")
        self.logger.info(f"Transaction {transaction_id} confirmed.")
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
        Deducts the amount from the sender and adds it to the receiver.
        """
        # Safely deduct the amount from the sender's balance
        self.balance_sheet[transaction.sender] = self.balance_sheet.get(transaction.sender, 0) - transaction.amount

        # Safely add the amount to the receiver's balance
        self.balance_sheet[transaction.receiver] = self.balance_sheet.get(transaction.receiver, 0) + transaction.amount
