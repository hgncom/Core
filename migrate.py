from factory import create_app
from models.base import db
from sqlalchemy import text
from models.transaction import TransactionModel
from models.dagnode import DAGNodeModel, DAGNodeDependencies

def create_transaction_and_dagnode_tables():
    with db.engine.connect() as connection:
        # Create the 'transactions' and 'dagnodes' tables
        db.create_all  (bind=connection)
        print("Created 'transactions' and 'dagnodes' tables successfully.")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        create_transaction_and_dagnode_tables()
