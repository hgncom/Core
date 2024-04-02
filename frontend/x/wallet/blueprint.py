from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask import make_response
import uuid
from plugins.wallet.backend.wallet import WalletPlugin
from models.wallet import WalletModel
from models.transaction import TransactionModel
from models.base import db
import traceback
import traceback
import logging

# Set logging level to INFO for production
logging.basicConfig(level=logging.INFO)

# Instantiate WalletPlugin and Blueprint
wallet_plugin = WalletPlugin()
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
        # Retrieve form data
        recipient_address = request.form.get('recipient_address')
        amount = request.form.get('amount', type=float)
        # Validation for recipient address and amount

        # Validation for recipient address and amount
        if not recipient_address or amount <= 0:
            flash('Invalid recipient address or amount', 'error')
            return render_template('send.html')

        username = session['username']
        try:            
            # Retrieve sender and recipient wallets from the database
            sender_wallet = WalletModel.query.filter_by(user_id=session['user_id']).first()
            recipient_wallet = WalletModel.query.filter_by(wallet_address=recipient_address).first()

            # Check if sender has enough balance and recipient exists, then perform the transaction
            # Check if sender has enough balance and recipient exists, then perform the transaction
            if sender_wallet and recipient_wallet and sender_wallet.amount >= amount:
                # Create a new transaction
                new_transaction = TransactionModel(sender=sender_wallet.wallet_address, receiver=recipient_wallet.wallet_address, amount=amount, signature='placeholder_signature', transaction_id=str(uuid.uuid4()))
                db.session.add(new_transaction)                

                # Update wallet balances
                sender_wallet.amount -= amount
                recipient_wallet.amount += amount
                db.session.commit()

                db.session.commit()
                flash('Funds successfully sent.', 'success')
                return redirect(url_for('.dashboard'))
            else:
                flash('Insufficient funds or invalid recipient address.', 'error')
                response = make_response(render_template('send.html', recipient_address=recipient_address, amount=amount))
                session.pop('_flashes', None)  # Clear flashed messages
                return response
        except Exception as e:  # Capture the specific exception message
            # Log and display error message
            logging.error(f"Error sending funds from user {username}: {e}")
            flash(f'An error occurred while sending funds: {e}', 'error')
            response = make_response(render_template('send.html', recipient_address=recipient_address, amount=amount))
            session.pop('_flashes', None)  # Clear flashed messages
            return response
            # Log and display error message
            logging.error(f"Error sending funds from user {username}: {e}")
            flash(f'An error occurred while sending funds: {e}', 'error')
            response = make_response(render_template('send.html'))
            session.pop('_flashes', None)  # Clear flashed messages
            return response
    else:
        # Render the send form
        return render_template('send.html')
