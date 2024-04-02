from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask import make_response
import uuid, logging
from network.server import PeerNetwork
from models.wallet import WalletModel
from models.transaction import TransactionModel
from models.base import db
from utilities.logging import create_main_logger
from plugins.wallet.backend.wallet import WalletPlugin

wallet_plugin = WalletPlugin()

main_logger = create_main_logger()

# Instantiate WalletPlugin and Blueprint
peer_network = PeerNetwork()
wallet_blueprint = Blueprint('wallet', __name__, template_folder='templates', static_folder='static')

@wallet_blueprint.route('/dashboard')
def dashboard():
    # Retrieve the username from the session
    username = session.get('username')
    logging.info(f"Dashboard accessed by user: {username}")

    # Redirect to login if user is not logged in
    if not username:
        return redirect(url_for('user.login'))

    try:
        # Fetch wallet data for the user
        wallet_data = wallet_plugin.fetch_wallet_data(username)
        logging.info("Fetched wallet data for user %s: %s", username, wallet_data)
        return render_template('dashboard.html', wallet=wallet_data)
    except Exception as e:
        # Log and render error message
        logging.error("Error fetching wallet data for user %s: %s", username, str(e))
        return render_template('error.html', message="An error occurred while fetching wallet data.")

@wallet_blueprint.route('/send', methods=['GET', 'POST'])
def send():
    # Redirect to login if user is not logged in
    if 'username' not in session:
        return redirect(url_for('user.login'))

    if request.method == 'POST':
        main_logger.info("Initiating transaction process.")
        # Retrieve form data
        recipient_address = request.form.get('recipient_address')
        amount = request.form.get('amount', type=float)
        main_logger.info(f"Form data retrieved: recipient_address={recipient_address}, amount={amount}")
        # Validation for recipient address and amount

        # Validation for recipient address and amount
        if not recipient_address or amount <= 0:
            flash('Invalid recipient address or amount', 'error')
            main_logger.error("Validation failed: Invalid recipient address or amount.")
            return render_template('send.html')

        username = session['username']
        try:
            main_logger.info(f"Attempting to send funds from user {username} to {recipient_address} with amount {amount}.")           
            # Retrieve sender and recipient wallets from the database
            sender_wallet = WalletModel.query.join(UserModel).filter(UserModel.username == username).first()
            recipient_wallet = WalletModel.query.filter_by(wallet_address=recipient_address).first()

            # Check if sender has enough balance and recipient exists, then perform the transaction
            main_logger.info("Sender and recipient wallets retrieved from the database.")
            # Check if sender has enough balance and recipient exists, then perform the transaction
            if sender_wallet and recipient_wallet and sender_wallet.amount >= amount:
                # Create a new transaction
                new_transaction = TransactionModel(sender=sender_wallet.wallet_address, receiver=recipient_wallet.wallet_address, amount=amount, signature=None, transaction_id=str(uuid.uuid4()))
                # Sign the transaction with the sender's private key (retrieved securely)
                sender_private_key_pem = get_private_key_for_user(sender_wallet.user_id)  # This function needs to be implemented to retrieve the private key securely
                new_transaction.sign(sender_private_key_pem)
                db.session.add(new_transaction)
                main_logger.info(f"New transaction created with ID {new_transaction.transaction_id}.")
                # Attempt to sign the transaction
                try:
                    new_transaction.sign(sender_private_key_pem)
                except Exception as e:
                    main_logger.exception(f"Failed to sign transaction {new_transaction.transaction_id}: {e}")
                    flash('Failed to sign transaction.', 'error')
                    return render_template('send.html')

                # Update wallet balances and commit the transaction
                sender_wallet.amount -= amount
                recipient_wallet.amount += amount
                db.session.commit()
                main_logger.info("Transaction committed to the database and wallet balances updated.")

                # Broadcast the transaction to the peer network
                try:
                    peer_network.broadcast_transaction(new_transaction.to_dict())
                    main_logger.info(f"Transaction {new_transaction.transaction_id} broadcasted to the peer network.")
                    flash('Funds successfully sent.', 'success')
                    return redirect(url_for('.dashboard'))
                except Exception as e:
                    main_logger.exception(f"Failed to broadcast transaction {new_transaction.transaction_id} to the peer network: {e}")
                    flash('Failed to broadcast transaction.', 'error')
                    return render_template('send.html')
            else:
                flash('Insufficient funds or invalid recipient address.', 'error')
                main_logger.error("Transaction failed: Insufficient funds or invalid recipient address.")
                return render_template('send.html')
        except Exception as e:
            main_logger.exception(f"Exception occurred during transaction process: {e}")
            flash(f'An error occurred while sending funds: {e}', 'error')
            return render_template('send.html')
    else:
        # Render the send form
        return render_template('send.html')
            # The rest of the code remains unchanged
from utilities.logging import create_main_logger

main_logger = create_main_logger()
