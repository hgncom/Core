from flask import Flask
from plugins.wallet.backend.wallet import db
from frontend.x.wallet.blueprint import wallet_blueprint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../hgn.db'
db.init_app(app)

with app.app_context():
    db.create_all()

# Register the wallet blueprint
app.register_blueprint(wallet_blueprint, url_prefix='/wallet')

if __name__ == '__main__':
    app.run(debug=True)
