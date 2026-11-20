import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'foodbridge-super-secret-key-2026')
    
    # Database Settings
    DB_TYPE = os.environ.get('DB_TYPE', 'auto').lower() # 'mysql', 'sqlite', or 'auto'
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'root')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'foodbridge')
    
    # SQLite fallback / local database file
    SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'foodbridge.db')
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max
