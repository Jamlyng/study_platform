from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Явно указываем static_folder относительно корня проекта
    app.static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

    db.init_app(app)
    login_manager.init_app(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.materials import materials_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(profile_bp)

    with app.app_context():
        db.create_all()

    return app