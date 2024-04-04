# models/wallet.py
from models.base import db

class WalletModel(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    wallet_address = db.Column(db.String(120), unique=True, nullable=False)
    public_key = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, default=1000000.0, nullable=False)

    user = db.relationship('UserModel', back_populates='wallet')  # Corrected back-reference

    def __repr__(self):
        return f'<Wallet {self.wallet_address}>'
    #amount = db.Column(db.Float, default=0.0, nullable=False)

