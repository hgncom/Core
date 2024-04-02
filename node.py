from dag_core.node import DAGNode
from dag_core.dag import DAG, DAGFactory
from dag_core.executor import DAGExecutor

app.register_blueprint(user_blueprint, url_prefix='/user')

# Create DAG instance
dag = DAG()

# Create nodes with transaction details
transaction1 = DAGNode("tx1", "Alice", "Bob", 100)
transaction2 = DAGNode("tx2", "Bob", "Charlie", 50)

# Add nodes to the DAG
dag.add_node(transaction1)
dag.add_node(transaction2)
# Optionally, define dependencies if any

# Execute the DAG - assuming you will adjust DAGExecutor to fit the transaction model
executor = DAGExecutor(dag)
executor.execute_dag()