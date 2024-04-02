from network.pulse.mechanism import PulseConsensusMechanism

class DAG:
    def __init__(self, pulse_consensus_mechanism_params, network_communication):
        self.nodes = {}
        self.pulse_consensus = PulseConsensusMechanism(ledger_interaction=None, network_communication=network_communication, encryption_key='YourEncryptionKeyHere')

    def add_node(self, node):
        if node.transaction_id in self.nodes:
            raise ValueError(f"Transaction {node.transaction_id} already exists in the DAG")
        main_logger.info(f"Attempting to add transaction {node.transaction_id} to the DAG")

        if not self.pulse_consensus.validate_and_reach_consensus(node.to_dict()):
            raise Exception("Failed to reach consensus for transaction. Node not added to DAG.")
        main_logger.info(f"Transaction {node.transaction_id} successfully added to the DAG")
        self.nodes[node.transaction_id] = node

        self.nodes[node.transaction_id] = node

    def add_dependency(self, from_transaction_id, to_transaction_id):
        if from_transaction_id not in self.nodes or to_transaction_id not in self.nodes:
            raise ValueError("One or both of the specified transactions do not exist in the DAG.")
        self.nodes[from_transaction_id].successors.append(to_transaction_id)
        self.nodes[to_transaction_id].dependencies.append(from_transaction_id)

    def is_cyclic(self):
        visited = {node: False for node in self.nodes}
        rec_stack = {node: False for node in self.nodes}
        for node in self.nodes:
            if not visited[node]:
                if self.is_cyclic_util(node, visited, rec_stack):
                    return True
        return False

    def is_cyclic_util(self, node, visited, rec_stack):
        visited[node] = True
        rec_stack[node] = True
        for successor in self.nodes[node].successors:
            if not visited[successor]:
                if self.is_cyclic_util(successor, visited, rec_stack):
                    return True
            elif rec_stack[successor]:
                return True
        rec_stack[node] = False
        return False

    def execute(self):
        executed = set()
        to_execute = [node_id for node_id, node in self.nodes.items() if not node.dependencies]

        while to_execute:
            current_transaction_id = to_execute.pop(0)
            self.process_transaction(current_transaction_id)
            executed.add(current_transaction_id)

            for node_id, node in self.nodes.items():
                if node_id not in executed and all(dep in executed for dep in node.dependencies):
                    to_execute.append(node_id)

    def process_transaction(self, transaction_id):
        transaction = self.nodes.get(transaction_id)
        if transaction:
            print(f"Processing transaction {transaction_id}: from {transaction.sender} to {transaction.receiver}, amount: {transaction.amount}")
        else:
            print(f"Transaction {transaction_id} not found.")
