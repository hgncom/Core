# auth.py

class User:
    def __init__(self, username, roles=None):
        self.username = username
        self.roles = roles if roles is not None else []

class AuthenticationService:
    def authenticate_user(self, username, password):
        """
        Authenticate a user based on username and password.
        This is a placeholder for actual authentication logic,
        which might involve checking a user database or an external authentication service.
        """
        # Placeholder authentication logic
        if username == "admin" and password == "secret":
            return User(username, roles=["admin"])
        return None

class AuthorizationService:
    def __init__(self):
        self.permissions = {
            "admin": ["create", "read", "update", "delete"],
            "user": ["read"]
        }

    def authorize_user(self, user, action):
        """
        Check if a user is authorized to perform a given action.
        """
        if user is None:
            return False
        return any(action in self.permissions[role] for role in user.roles)

# Example usage
if __name__ == "__main__":
    auth_service = AuthenticationService()
    user = auth_service.authenticate_user("admin", "secret")

    authz_service = AuthorizationService()
    if authz_service.authorize_user(user, "read"):
        print(f"User {user.username} is authorized to read.")
    else:
        print(f"User {user.username} is not authorized to read.")
