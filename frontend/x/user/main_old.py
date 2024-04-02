from flask import Flask
from plugins.user.backend.user import db
from frontend.x.user.blueprint import user_blueprint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../hgn.db'
app.config['SECRET_KEY'] = '3?hR](#2!ul]Kq=@j=c>R).y/kHfng/jo#Sj2vbKn<tm@1Hp{DkuF"u003tt>8t'
db.init_app(app)

with app.app_context():
    db.create_all()

# Register the user management blueprint
app.register_blueprint(user_blueprint, url_prefix='/user')

if __name__ == '__main__':
    app.run(debug=True)