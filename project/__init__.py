import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.urandom(24).hex()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1mT17H75YD34@172.18.240.5/karatube_teste'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User, Room
    
    with app.app_context():
        
        # Create tables
        db.create_all()

        # add admin user to the database        
        user = User.query.filter_by(id='admin').first()
        if not user:
            new_user = User(id='admin', name='Administrator', roomid='main', password=generate_password_hash('admin', method='pbkdf2:sha256'), admin='X')
            db.session.add(new_user)
            db.session.commit()

        # add main room to the database 
        room = Room.query.filter_by(roomid='main').first()
        if not room:
            new_room = Room(roomid='main', adminid='admin', password=generate_password_hash('room', method='pbkdf2:sha256'))
            db.session.add(new_room)
            db.session.commit()

    @login_manager.user_loader
    def load_user(userid):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(userid)

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
