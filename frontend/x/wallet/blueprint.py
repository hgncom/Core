import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask import make_response
from models import UserModel, WalletModel
from models.user import UserModel
from models import WalletModel
from network.server import PeerNetwork
from models.transaction import TransactionModel
from models.base import db
from plugins.wallet.backend.wallet import WalletPlugin
from utilities.logging import create_main_logger

wallet_plugin = WalletPlugin()
main_logger = create_main_logger()

# Instantiate WalletPlugin and Blueprint
peer_network = PeerNetwork()
wallet_blueprint = Blueprint('wallet', __name__, template_folder='templates', static_folder='static')

@wallet_blueprint.route('/dashboard')
def dashboard():
    # Retrieve the username from the session
    username = session.get('username')
    main_logger.info(f"Dashboard accessed by user: {username}")

    # Redirect to login if user is not logged in
    if not username:
        return redirect(url_for('user.login'))

    try:
        # Fetch wallet data for the user
        wallet_data = wallet_plugin.fetch_wallet_data(username)
        main_logger.info("Fetched wallet data for user %s: %s", username, wallet_data)
        return render_template('dashboard.html', wallet=wallet_data)
    except Exception as e:
        # Log and render error message
        main_logger.error("Error fetching wallet data for user %s: %s", username, str(e))
        return render_template('error.html', message="An error occurred while fetching wallet data.")

@wallet_blueprint.route('/send', methods=['GET', 'POST'])
def send():
    if 'username' not in session:
        return redirect(url_for('user.login'))

    if request.method == 'POST':
        recipient_address = request.form.get('recipient_address')
        amount = request.form.get('amount', type=float)

        if not recipient_address or amount <= 0:
            flash('Invalid recipient address or amount', 'error')
            return render_template('send.html')

        username = session['username']
        try:
            sender_wallet = WalletModel.query.join(UserModel).filter(UserModel.username == username).first()
            recipient_wallet = WalletModel.query.filter_by(wallet_address=recipient_address).first()

            if not sender_wallet or not recipient_wallet or sender_wallet.amount < amount:
                flash('Insufficient funds or invalid recipient address.', 'error')
                return render_template('send.html')

            new_transaction = TransactionModel(
                sender=sender_wallet.wallet_address,
                receiver=recipient_wallet.wallet_address,
                amount=amount,
                signature='',  # Placeholder for actual signature
                transaction_id=str(uuid.uuid4())
            )

            # Retrieve the actual private key for the sender
            sender_private_key_pem = wallet_plugin.get_private_key_for_user(sender_wallet.user_id)
            if not sender_private_key_pem:
                flash('Private key not found.', 'error')
                return render_template('send.html')

            # Sign the transaction with the sender's private key
            # Implement the signature process correctly based on your application's requirements
            # This part of the code assumes you have a mechanism to sign transactions
            if sender_wallet:
                sender_private_key_pem = "TEST1"
                #sender_private_key_pem = wallet_plugin.get_private_key_for_user(sender_wallet.user_id)
            else:
                flash('Wallet not found.', 'error')
                return render_template('send.html')
            # Assuming the `sign` method exists and works with the provided private key
            new_transaction.signature = wallet_plugin.sign_transaction(sender_private_key_pem, new_transaction)

            db.session.add(new_transaction)
            sender_wallet.amount -= amount
            recipient_wallet.amount += amount
            db.session.commit()

            main_logger.info(f"Transaction {new_transaction.transaction_id} successfully processed.")
            flash('Funds successfully sent.', 'success')
            return redirect(url_for('.dashboard'))

        except Exception as e:
            main_logger.exception(f"Exception occurred during transaction process: {e}")
            flash(f'An error occurred while sending funds: {e}', 'error')
            return render_template('send.html')

    return render_template('send.html')
