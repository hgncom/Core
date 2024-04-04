import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from flask import make_response
from models.transaction import TransactionModel

from utilities.logging import create_main_logger
from dag_core.node import Transaction

wallet_blueprint = Blueprint('wallet', __name__, template_folder='templates', static_folder='static')
def get_wallet_plugin():
    with current_app.app_context():
        from plugins.wallet.backend.wallet import WalletPlugin
        return WalletPlugin()

wallet_plugin = get_wallet_plugin()

@wallet_blueprint.route('/dashboard')
def dashboard():
    def get_wallet_plugin():
        with current_app.app_context():
            from plugins.wallet.backend.wallet import WalletPlugin
            return WalletPlugin()

@wallet_blueprint.route('/dashboard')
def dashboard():
    # Retrieve the username from the session
    username = session.get('username')
    main_logger.info(f"Dashboard accessed by user: {username}")
    # Ensure that the NODE_URL is set in the application's configuration
    if 'NODE_URL' not in current_app.config:
        main_logger.error("NODE_URL is not set in the application's configuration.")
        flash("Configuration error. Please contact the administrator.", 'error')
        return render_template('error.html', message="Configuration error.")


    # Ensure that the NODE_URL is set in the application's configuration
    if 'NODE_URL' not in current_app.config:
        main_logger.error("NODE_URL is not set in the application's configuration.")
        flash("Configuration error. Please contact the administrator.", 'error')
        return render_template('error.html', message="Configuration error.")

    # Create an instance of WalletPlugin within the application context
    wallet_plugin = get_wallet_plugin()


    # Redirect to login if user is not logged in
    if not username:
        return redirect(url_for('user.login'))

    try:
        # Fetch wallet data for the user
        wallet_data = wallet_plugin.fetch_wallet_data(username)
        main_logger.info("Fetched wallet data for user %s: %s", username, wallet_data)
        return render_template('dashboard.html', wallet=wallet_data if wallet_data else {})
    except Exception as e:
        # Log and render error message
        main_logger.error("Error fetching wallet data for user %s: %s", username, str(e))
        flash("An error occurred while fetching wallet data.", 'error')
        return render_template('error.html', message=str(e))

@wallet_blueprint.route('/send', methods=['GET', 'POST'])
def send():
    if 'username' not in session or not session['username']:
        return redirect(url_for('user.login'))

    # Create an instance of WalletPlugin within the application context
    try:
        wallet_plugin = get_wallet_plugin()
    except RuntimeError as e:
        main_logger.error(f"Failed to get WalletPlugin: {e}")
        flash("An error occurred while accessing the wallet service.", 'error')
        return render_template('error.html', message="Wallet service error.")


    if request.method == 'POST':
        recipient_address = request.form.get('recipient_address')
        amount = request.form.get('amount', type=float)
        main_logger.debug(f"Send funds form submitted with recipient_address: {recipient_address}, amount: {amount}")

        if not recipient_address or not amount or amount <= 0:
            flash('Invalid recipient address or amount', 'error')
            return render_template('send.html')

        username = session['username']
        try:
            sender_user = UserModel.query.filter_by(username=username).first()
            if not sender_user or not sender_user.wallet:
                main_logger.error(f"Sender user {username} or wallet not found.")
                flash('Sender user or wallet not found.', 'error')
                return render_template('send.html')

            if sender_user.wallet.amount < amount:
                flash('Insufficient funds.', 'error')
                return render_template('send.html')

            if sender_user.wallet.amount < amount:
                flash('Insufficient funds or invalid recipient address.', 'error')
                return render_template('send.html')

            new_transaction = Transaction(
                sender=sender_user.wallet.wallet_address,
                receiver=recipient_address,
                amount=amount,
                signature=''  # Placeholder for actual signature
            )  # Assuming Transaction has the appropriate constructor

            # Retrieve the actual private key for the sender
            sender_private_key_pem = wallet_plugin.get_private_key_for_user(sender_user.id)
            if not sender_private_key_pem:
                flash('Private key not found.', 'error')
                return render_template('send.html')

            # Sign the transaction with the sender's private key (retrieved securely)
            new_transaction = wallet_plugin.sign_transaction(new_transaction, sender_private_key_pem)
            main_logger.debug(f"Transaction signed: {new_transaction.signature}")

            # Add the transaction to the database or ledger
            success, message = wallet_plugin.add_transaction_to_ledger(new_transaction)
            if not success:
                main_logger.error(f"Failed to add transaction to ledger: {message}")
                flash('Failed to send funds. ' + message, 'error')
                return render_template('send.html')

            main_logger.info(f"Transaction {new_transaction.transaction_id} added to ledger successfully.")
            flash('Funds successfully sent.', 'success')
            return redirect(url_for('.dashboard'))

        except Exception as e:
            main_logger.exception(f"Exception occurred during transaction process: {e}")
            flash(f'An error occurred while sending funds: {e}', 'error')
            return render_template('send.html')

    return render_template('send.html')
