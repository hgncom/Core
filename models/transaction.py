from .base import db

class TransactionModel(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(120), nullable=False)
    receiver = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    signature = db.Column(db.Text, nullable=False)
    transaction_id = db.Column(db.String(120), unique=True, nullable=False)
    confirmed = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'
