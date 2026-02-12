import os
from urllib.parse import quote_plus

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # MySQL configuration
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'somil@25'
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = os.environ.get('DB_PORT') or '3306'
    DB_NAME = os.environ.get('DB_NAME') or 'finance_tracker'
    
    # Construct MySQL connection string
    # Format: mysql://username:password@host:port/database_name
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"mysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXPORT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports')
    CSV_FOLDER = os.path.join(EXPORT_FOLDER, 'csv')
    PDF_FOLDER = os.path.join(EXPORT_FOLDER, 'pdf')
    
    # Create export directories if they don't exist
    os.makedirs(CSV_FOLDER, exist_ok=True)
    os.makedirs(PDF_FOLDER, exist_ok=True)
