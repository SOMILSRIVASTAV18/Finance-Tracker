from flask import Flask
from flask_login import LoginManager
from models import db
from models.user import User
from config import Config
import os

def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.expenses import expenses_bp
    from routes.reports import reports_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(reports_bp)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # Create default categories if none exist
        from models.category import Category
        if Category.query.count() == 0:
            default_categories = [
                {'name': 'Food', 'color': '#FF5733'},
                {'name': 'Transportation', 'color': '#33FF57'},
                {'name': 'Housing', 'color': '#3357FF'},
                {'name': 'Entertainment', 'color': '#F033FF'},
                {'name': 'Utilities', 'color': '#FF9033'},
                {'name': 'Healthcare', 'color': '#33FFF0'},
                {'name': 'Education', 'color': '#FF33A8'},
                {'name': 'Shopping', 'color': '#A833FF'},
                {'name': 'Personal', 'color': '#33A8FF'},
                {'name': 'Other', 'color': '#AAAAAA'}
            ]
            
            for cat in default_categories:
                category = Category(name=cat['name'], color=cat['color'])
                db.session.add(category)
            
            db.session.commit()
    
    # Ensure export directories exist
    os.makedirs(app.config['CSV_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)
    
    return app
