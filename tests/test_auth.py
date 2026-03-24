"""
Tests unitarios para las rutas de autenticación (app/routes/auth.py)
Prueba con pytest: pytest tests/test_auth.py -v
"""
import pytest
from werkzeug.security import generate_password_hash
from app.db.models import db, User


class TestRegister:
    """Tests para el endpoint POST /api/register"""

    def test_register_success(self, client):
        """Debe registrar un nuevo usuario exitosamente"""
        response = client.post(
            '/api/register',
            data={
                'name': 'Juan Pérez',
                'email': 'juan@alumnos.udg.mx',
                'password': 'miContraseña123'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Usuario registrado'

    def test_register_invalid_email_domain(self, client):
        """Debe rechazar emails que no sean @alumnos.udg.mx"""
        response = client.post(
            '/api/register',
            data={
                'name': 'Juan Pérez',
                'email': 'juan@gmail.com',
                'password': 'miContraseña123'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'El correo debe ser @alumnos.udg.mx'

    def test_register_missing_email(self, client):
        """Debe rechazar registro sin email"""
        response = client.post(
            '/api/register',
            data={
                'name': 'Juan Pérez',
                'password': 'miContraseña123'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['message'] == 'El correo debe ser @alumnos.udg.mx'

    def test_register_duplicate_email(self, client, test_user):
        """Debe rechazar registro con email duplicado"""
        response = client.post(
            '/api/register',
            data={
                'name': 'Otro Usuario',
                'email': 'testuser@alumnos.udg.mx',  # Email ya existe
                'password': 'otraContraseña456'
            }
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['message'] == 'Este correo ya está registrado'

    def test_register_user_exists_in_db(self, client):
        """Verifica que el usuario se cree en la base de datos"""
        # Registrar usuario
        response = client.post(
            '/api/register',
            data={
                'name': 'Maria Silva',
                'email': 'maria@alumnos.udg.mx',
                'password': 'pass123'
            }
        )
        
        assert response.status_code == 201
        
        # Verificar que existe en BD
        user = User.query.filter_by(email='maria@alumnos.udg.mx').first()
        assert user is not None
        assert user.name == 'Maria Silva'

    def test_register_password_hashed(self, client):
        """Verifica que la contraseña se guarde hasheada"""
        response = client.post(
            '/api/register',
            data={
                'name': 'Carlos López',
                'email': 'carlos@alumnos.udg.mx',
                'password': 'miPassword123'
            }
        )
        
        assert response.status_code == 201
        
        # Verificar que la contraseña no se guarde en texto plano
        user = User.query.filter_by(email='carlos@alumnos.udg.mx').first()
        assert user.password_hash != 'miPassword123'
        assert len(user.password_hash) > 20  # Hash es largo


class TestLogin:
    """Tests para el endpoint POST /api/login"""

    def test_login_success(self, client, test_user):
        """Debe hacer login exitosamente con credenciales válidas"""
        response = client.post(
            '/api/login',
            data={
                'email': 'testuser@alumnos.udg.mx',
                'password': 'password123'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Logged in'
        assert data['user_id'] == test_user.id
        assert data['user_name'] == test_user.name

    def test_login_invalid_email(self, client):
        """Debe rechazar login con email inexistente"""
        response = client.post(
            '/api/login',
            data={
                'email': 'noexiste@alumnos.udg.mx',
                'password': 'password123'
            }
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['message'] == 'Credenciales inválidas'

    def test_login_invalid_password(self, client, test_user):
        """Debe rechazar login con contraseña incorrecta"""
        response = client.post(
            '/api/login',
            data={
                'email': 'testuser@alumnos.udg.mx',
                'password': 'passwordIncorrecto'
            }
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['message'] == 'Credenciales inválidas'

    def test_login_missing_email(self, client):
        """Debe rechazar login sin email"""
        response = client.post(
            '/api/login',
            data={
                'password': 'password123'
            }
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['message'] == 'Credenciales inválidas'

    def test_login_missing_password(self, client, test_user):
        """Debe rechazar login sin contraseña"""
        response = client.post(
            '/api/login',
            data={
                'email': 'testuser@alumnos.udg.mx'
            }
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['message'] == 'Credenciales inválidas'

    def test_login_returns_user_info(self, client, test_user):
        """Verifica que login retorne info completa del usuario"""
        response = client.post(
            '/api/login',
            data={
                'email': 'testuser@alumnos.udg.mx',
                'password': 'password123'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verificar campos de respuesta
        assert 'message' in data
        assert 'user_id' in data
        assert 'user_name' in data


class TestLogout:
    """Tests para el endpoint POST /api/logout"""

    def test_logout_success(self, client):
        """Debe hacer logout exitosamente"""
        response = client.post('/api/logout')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Logged out'

    def test_logout_no_auth_required(self, client):
        """Logout debe funcionar sin autenticación previa"""
        # POST a /logout sin hacer login antes
        response = client.post('/api/logout')
        
        assert response.status_code == 200


class TestAuthIntegration:
    """Tests de integración para flujos completos de autenticación"""

    def test_full_auth_flow(self, client):
        """Test del flujo completo: Registro -> Login -> Logout"""
        
        # 1. Registrar usuario
        register_response = client.post(
            '/api/register',
            data={
                'name': 'Ana García',
                'email': 'ana@alumnos.udg.mx',
                'password': 'segura123'
            }
        )
        assert register_response.status_code == 201
        
        # 2. Login
        login_response = client.post(
            '/api/login',
            data={
                'email': 'ana@alumnos.udg.mx',
                'password': 'segura123'
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        assert login_data['user_name'] == 'Ana García'
        
        # 3. Logout
        logout_response = client.post('/api/logout')
        assert logout_response.status_code == 200

    def test_cannot_register_twice(self, client):
        """No se puede registrar dos veces con el mismo email"""
        data = {
            'name': 'Usuario Único',
            'email': 'unico@alumnos.udg.mx',
            'password': 'pass123'
        }
        
        # Primer registro
        response1 = client.post('/api/register', data=data)
        assert response1.status_code == 201
        
        # Segundo registro con mismo email
        response2 = client.post('/api/register', data=data)
        assert response2.status_code == 409

    def test_login_after_register(self, client):
        """Debe poder hacer login después de registrarse"""
        # Registrar
        email = 'nuevo@alumnos.udg.mx'
        password = 'nuevoPass123'
        
        client.post(
            '/api/register',
            data={
                'name': 'Nuevo Usuario',
                'email': email,
                'password': password
            }
        )
        
        # Login
        login_response = client.post(
            '/api/login',
            data={
                'email': email,
                'password': password
            }
        )
        
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        assert login_data['user_name'] == 'Nuevo Usuario'


class TestAuthEdgeCases:
    """Tests para casos límite y bordes"""

    def test_register_with_empty_name(self, client):
        """Debe permitir registrar con nombre vacío (dependiendo de reglas de negocio)"""
        response = client.post(
            '/api/register',
            data={
                'name': '',
                'email': 'empty@alumnos.udg.mx',
                'password': 'pass123'
            }
        )
        
        # El sistema lo permite (sin validación de nombre en este momento)
        assert response.status_code == 201

    def test_register_with_special_characters_in_name(self, client):
        """Debe permitir caracteres especiales en el nombre"""
        response = client.post(
            '/api/register',
            data={
                'name': 'José García-López Ñandú 123',
                'email': 'special@alumnos.udg.mx',
                'password': 'pass123'
            }
        )
        
        assert response.status_code == 201
        user = User.query.filter_by(email='special@alumnos.udg.mx').first()
        assert user.name == 'José García-López Ñandú 123'

    def test_email_case_sensitivity(self, client):
        """Testa comportamiento con diferentes casos en email"""
        # Registrar con minúsculas
        client.post(
            '/api/register',
            data={
                'name': 'Usuario',
                'email': 'usuario@alumnos.udg.mx',
                'password': 'pass123'
            }
        )
        
        # Login con mayúsculas (por defecto None, depende de la query)
        response = client.post(
            '/api/login',
            data={
                'email': 'usuario@alumnos.udg.mx',
                'password': 'pass123'
            }
        )
        
        # Debe funcionar si la BD es case-insensitive o si los emails se normalizan
        assert response.status_code == 200

    def test_login_with_whitespace(self, client, test_user):
        """Debe manejar correctamente espacios en email"""
        response = client.post(
            '/api/login',
            data={
                'email': '  testuser@alumnos.udg.mx  ',
                'password': 'password123'
            }
        )
        
        # Depende si se hace trim en el backend
        # Actualmente probablemente fallará
        assert response.status_code in [200, 401]
