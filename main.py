"""
Cucei Foods Backend - API Principal
Punto de entrada de la aplicación Flask con CORS y RESTX
"""
from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from app.config import Config
from app.db.models import db
from app.routes import register_routes


def create_app():
    """Crea e inicializa la aplicación Flask"""
    
    app = Flask(__name__)
    
    # Configuración
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.secret_key = Config.SECRET_KEY
    
    # CORS
    CORS(app)
    
    # Base de datos
    db.init_app(app)
    
    # API REST
    api = Api(
        app,
        title="Cucei Foods API",
        version="1.0",
        description="Documentación de la API",
        doc='/docs'
    )
    
    # Registrar todas las rutas
    register_routes(api)
    
    # Crear tablas de base de datos
    with app.app_context():
        db.create_all()
    
    return app


# Crear instancia de la aplicación
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
