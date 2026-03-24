import os
import secrets

class Config:
    """Configuración base de la aplicación"""
    
    # Base de datos
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "contraseña_local_aqui")
    LOCAL_DB_URI = f'postgresql://postgres:{DB_PASSWORD}@localhost:5432/cuceifoods'
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or LOCAL_DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    
    # Seguridad
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    
    # Crear carpeta de uploads si no existe
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
