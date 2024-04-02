class WalletInterface:
    def create_wallet(self):
        raise NotImplementedError

    def sign_transaction(self, transaction):
        raise NotImplementedError

    def verify_transaction(self, transaction, signature):
        raise NotImplementedError
