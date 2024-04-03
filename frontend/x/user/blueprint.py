from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from plugins.user.backend.user import register_user, associate_wallet_with_user
from plugins.wallet.backend.wallet import WalletPlugin
from utilities.logging import create_main_logger

main_logger = create_main_logger()

user_blueprint = Blueprint('user', __name__, template_folder='templates', static_folder='static')

@user_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            main_logger.warning("Attempted registration with incomplete form data.")
            flash("Please fill out all fields.", 'error')
            return render_template('register.html')

        main_logger.info(f"Attempting to register user: {username}")

    try:
        registration_success = register_user(username, email, password)

        if registration_success:
            try:
                wallet_plugin = WalletPlugin()
                wallet_details, private_key_pem = wallet_plugin.create_wallet(username)
                main_logger.info(f"Wallet created for user: {username}")

                # Debugging: Print or log the session data
                main_logger.debug(f"Session after account creation: {session}")

                try:
                    associate_wallet_with_user(username, wallet_details)
                    main_logger.info(f"Wallet associated with user: {username}")
                    session['private_key'] = private_key_pem
                    return redirect(url_for('user.show_private_key'))
                except Exception as e:
                    main_logger.error(f"Error associating wallet with user {username}: {e}")
                    flash("Error during wallet association. Please contact support.", 'error')

            except Exception as e:
                main_logger.error(f"Error creating wallet for user {username}: {e}")
                flash("Error during wallet creation. Please contact support.", 'error')

        else:
            main_logger.error(f"Registration failed for user: {username}")
            flash("Registration failed. Please try again.", 'error')

    except Exception as e:
        main_logger.error(f"Unexpected error during registration process for user {username}: {e}")
        flash("An unexpected error occurred. Please try again.", 'error')


    return render_template('register.html')


@user_blueprint.route('/show_private_key')
def show_private_key():
    main_logger.info("Attempting to display the private key.")
    # Retrieve the private key from the session
    private_key_pem = session.pop('private_key', None)

    if private_key_pem:
        main_logger.info("Private key found in session; displaying to user.")
        # Render a template that shows the private key and instructs the user to save it
        return render_template('show_private_key.html', private_key=private_key_pem)
    else:
        main_logger.warning("No private key found in session; redirecting to login.")
        # If there's no private key in the session, redirect to the login page
        flash('No private key to display.', 'error')
        return redirect(url_for('user.login'))

@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        main_logger.info(f"Login attempt for username: {username}")

        try:
            if authenticate_user(username, password):
                main_logger.info(f"Authentication successful for username: {username}")
                # Authentication successful, redirect to wallet dashboard
                return redirect(url_for('wallet.dashboard'))  # Assuming wallet dashboard is implemented
            else:
                main_logger.warning(f"Authentication failed for username: {username}")
                # Authentication failed, display an error message
                error_message = 'Invalid username or password.'
                return render_template('login.html', error=error_message)
        except Exception as e:
            main_logger.error(f"Exception occurred during login for username {username}: {e}")
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('login.html')

    main_logger.info("Rendering login page.")
    return render_template('login.html')
