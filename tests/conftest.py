"""
Configuración de fixtures para tests con pytest
Usa PostgreSQL en memoria si está disponible, sino SQLite
"""
import pytest
import os
from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from app.db.models import db, User
from app.routes import register_routes


@pytest.fixture(scope="function")
def app():
    """Crea una instancia de aplicación Flask para testing"""
    
    app = Flask(__name__)
    
    # Usar PostgreSQL si está disponible en tests, sino SQLite
    # Para desarrollo rápido, usamos SQLite con JSON en lugar de JSONB
    db_url = os.environ.get('TEST_DATABASE_URL', 'sqlite:///test.db')
    
    # Forzar JSON en SQLite para compatibilidad
    if 'sqlite' in db_url:
        from sqlalchemy.dialects.sqlite import base
        from sqlalchemy import JSON, TypeDecorator
        
        class CompatibleJSONB(TypeDecorator):
            impl = JSON
            cache_ok = True
        
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    app.secret_key = 'test-secret-key-for-testing-only'
    
    # Inicializar extensiones
    CORS(app)
    db.init_app(app)
    
    # Crear API
    api = Api(app, doc='/docs')
    register_routes(api)
    
    # Crear tablas usando SQL directo para evitar problemas con JSONB
    with app.app_context():
        with db.engine.begin() as conn:
            # Opción 1: Usar create_all (puede fallar con JSONB en SQLite)
            # Opción 2: Usar SQL directo específico
            if 'sqlite' in str(db.engine.url):
                # Para SQLite, usar JSON en lugar de JSONB
                conn.exec_driver_sql("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(150) NOT NULL,
                        email VARCHAR(150) NOT NULL UNIQUE,
                        password_hash VARCHAR(200) NOT NULL
                    )
                """)
                conn.exec_driver_sql("""
                    CREATE TABLE IF NOT EXISTS places (
                        id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(200) NOT NULL,
                        schedule JSON,
                        category VARCHAR(100) NOT NULL,
                        image_url VARCHAR(300),
                        rating REAL DEFAULT 0.0,
                        num_ratings INTEGER DEFAULT 0
                    )
                """)
                conn.exec_driver_sql("""
                    CREATE TABLE IF NOT EXISTS menu_items (
                        id VARCHAR(36) PRIMARY KEY,
                        place_id VARCHAR(36) NOT NULL,
                        category VARCHAR(100) NOT NULL,
                        dish_name VARCHAR(200) NOT NULL,
                        price REAL NOT NULL,
                        FOREIGN KEY (place_id) REFERENCES places (id)
                    )
                """)
                conn.exec_driver_sql("""
                    CREATE TABLE IF NOT EXISTS comments (
                        id VARCHAR(36) PRIMARY KEY,
                        place_id VARCHAR(36) NOT NULL,
                        user_id VARCHAR(36) NOT NULL,
                        text TEXT NOT NULL,
                        rating INTEGER DEFAULT 0,
                        FOREIGN KEY (place_id) REFERENCES places (id),
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
            else:
                db.create_all()
        
        yield app
        
        # Limpiar
        with db.engine.begin() as conn:
            if 'postgres' in str(db.engine.url):
                db.drop_all()
            else:
                # Para SQLite, eliminar tablas manualmente
                for table in ['comments', 'menu_items', 'places', 'users']:
                    try:
                        conn.exec_driver_sql(f"DROP TABLE IF EXISTS {table}")
                    except:
                        pass
        
        db.session.remove()


@pytest.fixture(scope="function")
def client(app):
    """Crea un cliente de prueba para la aplicación"""
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """Crea un test CLI runner para la aplicación"""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def test_user(app):
    """Crea un usuario de prueba en la base de datos"""
    from werkzeug.security import generate_password_hash
    
    with app.app_context():
        user = User(
            name="Test User",
            email="testuser@alumnos.udg.mx"
        )
        user.password_hash = generate_password_hash("password123")
        
        db.session.add(user)
        db.session.commit()
        
        # Retornar IDs en un diccionario para que sean accesibles fuera del contexto
        user_id = user.id
        user_name = user.name
    
    # Crear un objeto simple que contenga los datos (no la instancia SQLAlchemy)
    class TestUserInfo:
        def __init__(self, uid, uname):
            self.id = uid
            self.name = uname
    
    return TestUserInfo(user_id, user_name)


@pytest.fixture(scope="function")
def test_place(app, test_user):
    """Crea un lugar de prueba en la base de datos"""
    from app.db.models import Place
    
    with app.app_context():
        place = Place(
            name="Test Restaurant",
            schedule={"lunes": "10:00-22:00", "martes": "10:00-22:00"},
            category="Comida Rápida",
            image_url="https://example.com/image.jpg",
            rating=0.0,
            num_ratings=0
        )
        
        db.session.add(place)
        db.session.commit()
        
        place_id = place.id
    
    # Retornar objeto simple con los datos
    class TestPlaceInfo:
        def __init__(self, pid):
            self.id = pid
    
    return TestPlaceInfo(place_id)


@pytest.fixture(scope="function")
def test_comment(app, test_user, test_place):
    """Crea un comentario de prueba en la base de datos"""
    from app.db.models import Comment
    
    with app.app_context():
        comment = Comment(
            place_id=test_place.id,
            user_id=test_user.id,
            text="Excelente comida",
            rating=5
        )
        
        db.session.add(comment)
        db.session.commit()
        
        comment_id = comment.id
    
    # Retornar objeto simple con los datos
    class TestCommentInfo:
        def __init__(self, cid, pid, uid):
            self.id = cid
            self.place_id = pid
            self.user_id = uid
    
    return TestCommentInfo(comment_id, test_place.id, test_user.id)


@pytest.fixture(scope="function")
def test_place_with_menu(app):
    """Crea un lugar con items de menú"""
    from app.db.models import Place, MenuItem
    
    with app.app_context():
        place = Place(
            name="Restaurant Menú Completo",
            schedule={"lunes": "08:00-22:00"},
            category="Desayunos y Comidas",
            image_url="https://example.com/menu.jpg",
            rating=0.0,
            num_ratings=0
        )
        
        db.session.add(place)
        db.session.commit()
        
        # Agregar items de menú
        menu_items = [
            MenuItem(place_id=place.id, category="Desayunos", dish_name="Pancakes", price=8.50),
            MenuItem(place_id=place.id, category="Comidas", dish_name="Tacos", price=6.00),
            MenuItem(place_id=place.id, category="Bebidas", dish_name="Jugo", price=3.00),
        ]
        
        db.session.add_all(menu_items)
        db.session.commit()
        
        place_id = place.id
    
    # Retornar objeto simple con los datos
    class TestPlaceMenuInfo:
        def __init__(self, pid):
            self.id = pid
    
    return TestPlaceMenuInfo(place_id)


@pytest.fixture(scope="function")
def test_multiple_places(app):
    """Crea varios lugares en diferentes categorías"""
    from app.db.models import Place
    
    with app.app_context():
        places = [
            Place(
                name="Restaurante Comidas",
                schedule={"lunes": "10:00-22:00"},
                category="Desayunos y Comidas",
                image_url="https://example.com/comidas.jpg"
            ),
            Place(
                name="Cafetería Bebidas",
                schedule={"lunes": "07:00-20:00"},
                category="Bebidas y Cafetería",
                image_url="https://example.com/cafe.jpg"
            ),
            Place(
                name="Snack Bar",
                schedule={"lunes": "09:00-21:00"},
                category="Snacks",
                image_url="https://example.com/snacks.jpg"
            ),
        ]
        
        db.session.add_all(places)
        db.session.commit()
        
        place_ids = [p.id for p in places]
    
    # Retornar objeto simple con los IDs
    class TestMultiplePlacesInfo:
        def __init__(self, pids):
            self.ids = pids
    
    return TestMultiplePlacesInfo(place_ids)
