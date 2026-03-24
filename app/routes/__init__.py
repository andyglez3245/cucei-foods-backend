"""
Módulo de rutas de la API
"""
from flask_restx import Api
from app.routes.uploads import create_upload_routes
from app.routes.auth import create_auth_routes
from app.routes.places import create_places_routes
from app.routes.comments import create_comments_routes


def register_routes(api: Api):
    """
    Registra todas las rutas de la API.
    
    Args:
        api (Api): Instancia de Flask-RESTX API
    """
    create_upload_routes(api)
    create_auth_routes(api)
    create_places_routes(api)
    create_comments_routes(api)
