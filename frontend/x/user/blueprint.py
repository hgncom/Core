from flask import Blueprint, request, redirect, url_for, render_template

# Import the necessary functions
from plugins.user.backend.user import register_user, associate_wallet_with_user
from plugins.user.backend.auth import authenticate_user
from plugins.wallet.backend.wallet import WalletPlugin

user_blueprint = Blueprint('user', __name__, template_folder='templates', static_folder='static')

@user_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Call the register_user function
        registration_success = register_user(username, email, password)

        if registration_success:
            # Initialize the WalletPlugin to create a new wallet
            wallet_plugin = WalletPlugin()
            print("registration sucess - username is {username}")
            wallet_details = wallet_plugin.create_wallet(username)

            # Associate wallet with user
            associate_wallet_with_user(username, wallet_details)  # Call the function

            # Redirect to login after successful registration and wallet creation
            return redirect(url_for('user.login'))
        else:
            # Registration failed, show an error message
            error_message = 'Registration failed. Please try again.'
            return render_template('register.html', error=error_message)

    return render_template('register.html')

@user_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if authenticate_user(username, password):
            # Authentication successful, redirect to wallet dashboard
            print("Authentication successful!")
            return redirect(url_for('wallet.dashboard'))  # Assuming wallet dashboard is implemented
        else:
            # Authentication failed, display an error message
            print("Authentication invalid!")
            error_message = 'Invalid username or password.'
            return render_template('login.html', error=error_message)

    return render_template('login.html')
