from .transaction import Transaction
from .ledger_interaction import LedgerInteraction
from .networking import NetworkCommunication
import time

class TransactionValidation:
    def __init__(self, ledger_interaction: LedgerInteraction, network_communication: NetworkCommunication):
        self.ledger_interaction = ledger_interaction
        self.network_communication = network_communication

    def is_transaction_valid(self, transaction: Transaction) -> bool:
        """Comprehensive transaction validation against consensus-specific and general ledger rules."""
        if not self.is_structure_valid(transaction):
            return False
        if not self.is_signature_valid(transaction):
            return False
        if not self.are_dependencies_resolved(transaction):
            return False
        if not self.is_timestamp_valid(transaction):
            return False
        if not self.is_within_network_consensus(transaction):
            return False
        return True

    def is_structure_valid(self, transaction: Transaction) -> bool:
        """Ensure transaction has all required fields and a non-negative amount."""
        required_fields = ['sender', 'receiver', 'amount', 'signature', 'timestamp', 'dependencies']
        return all(getattr(transaction, field, None) is not None for field in required_fields) and transaction.amount >= 0

    def is_signature_valid(self, transaction: Transaction) -> bool:
        """Check if the transaction's signature is valid."""
        return transaction.verify_signature()

    def are_dependencies_resolved(self, transaction: Transaction) -> bool:
        """Ensure all transactions that this one depends on are confirmed."""
        return all(self.ledger_interaction.is_transaction_confirmed(dep) for dep in transaction.dependencies)

    def is_timestamp_valid(self, transaction: Transaction) -> bool:
        """Validate that the transaction's timestamp is reasonable and respects the order of dependencies."""
        current_time = time.time()
        return transaction.timestamp <= current_time and all(transaction.timestamp >= self.ledger_interaction.get_transaction_timestamp(dep) for dep in transaction.dependencies)

    def is_within_network_consensus(self, transaction: Transaction) -> bool:
        """Ensure the transaction is accepted by a consensus of peers, using random sampling."""
        return self.network_communication.random_sampling_consensus(transaction)

# Additional helper methods might be defined here for detailed validation, such as checking for double spending.
