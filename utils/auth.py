from flask import redirect, url_for, flash, session
from flask_login import LoginManager, current_user
from functools import wraps
from models.user import User

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def setup_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def validate_password(password):
    """
    Validate password strength
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character
    """
    import re
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def generate_reset_token():
    """Generate a secure token for password reset"""
    import secrets
    return secrets.token_urlsafe(32)

def set_reset_token(user, token, expiration=3600):
    """Set password reset token with expiration time"""
    from datetime import datetime, timedelta
    session[f'reset_token_{token}'] = {
        'user_id': user.id,
        'expiration': datetime.utcnow() + timedelta(seconds=expiration)
    }

def verify_reset_token(token):
    """Verify if the reset token is valid and not expired"""
    from datetime import datetime
    token_data = session.get(f'reset_token_{token}')
    
    if not token_data:
        return None
    
    if datetime.utcnow() > token_data['expiration']:
        # Token expired, remove it
        session.pop(f'reset_token_{token}')
        return None
    
    # Valid token, return the user
    user = User.query.get(token_data['user_id'])
    return user
