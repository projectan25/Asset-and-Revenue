from flask import Flask, app
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User, Department
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'your-very-secret-key-here'
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/auth/*": {"origins": "*"}
    }, supports_credentials=True)

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    migrate = Migrate(app, db)
    csrf = CSRFProtect(app)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.user_routes import user_bp
    from routes.admin_routes import admin_bp
    from routes.depart_routes import depart_bp
    from routes.admin_user_routes import admin_user_bp
    from routes.admin_department_routes import admin_department_bp
    from routes.admin_dashboard_routes import admin_dashboard_bp
    from routes.receipt_routes import receipt_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(depart_bp, url_prefix='/departments')
    app.register_blueprint(admin_user_bp)
    app.register_blueprint(admin_department_bp)
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(receipt_bp, url_prefix='/receipts')

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize database with admin user
    with app.app_context():
        db.create_all()
        
        # Create initial admin user if none exists
        if not User.query.filter_by(is_global_admin=True).first():
            admin = User(
                username='globaladmin',
                email='admin@example.com',
                user_role='admin',
                is_global_admin=True,
                password_hash=generate_password_hash('SecureAdmin123!'),
            )
            db.session.add(admin)
            db.session.commit()
            print("Initial global admin created: username=globaladmin, password=SecureAdmin123!")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)