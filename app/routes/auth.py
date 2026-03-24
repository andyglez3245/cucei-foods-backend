from flask import request
from flask_restx import Resource, Api, fields, Namespace
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from app.db.models import db, User


def create_auth_routes(api: Api) -> Namespace:
    """Crea las rutas de autenticación"""
    
    api_ns = api.namespace('api', path='/api', description='API endpoints')
    
    # Modelos para la documentación
    register_model = api_ns.model('Register', {
        'name': fields.String(required=True, description='Nombre del usuario'),
        'email': fields.String(required=True, description='Correo electrónico'),
        'password': fields.String(required=True, description='Contraseña')
    })

    login_model = api_ns.model('Login', {
        'email': fields.String(required=True, description='Correo electrónico'),
        'password': fields.String(required=True, description='Contraseña')
    })

    login_response_model = api_ns.model('LoginResponse', {
        'message': fields.String(description='Mensaje de respuesta'),
        'user_id': fields.String(description='ID del usuario'),
        'user_name': fields.String(description='Nombre del usuario')
    })

    message_model = api_ns.model('Message', {
        'message': fields.String(description='Mensaje informativo')
    })

    @api_ns.route('/register')
    class Register(Resource):
        @api_ns.expect(register_model, validate=False)
        @api_ns.marshal_with(message_model, code=201)
        def post(self):
            """
            Registra un nuevo usuario en el sistema.

            Returns:
                Response: Mensaje de éxito o error.
            """
            session_db = Session(db.engine)
            try:
                name = request.form.get("name")
                email = request.form.get("email")
                password = request.form.get("password")

                if not email or not email.endswith("@alumnos.udg.mx"):
                    return {"message": "El correo debe ser @alumnos.udg.mx"}, 400

                # Email already exists?
                if session_db.query(User).filter(User.email == email).first():
                    return {"message": "Este correo ya está registrado"}, 409

                user = User(name=name, email=email)
                user.password_hash = generate_password_hash(password)

                session_db.add(user)
                session_db.commit()

                return {"message": "Usuario registrado"}, 201

            finally:
                session_db.close()


    @api_ns.route('/login')
    class Login(Resource):
        @api_ns.expect(login_model, validate=False)
        @api_ns.marshal_with(login_response_model)
        def post(self):
            """
            Inicia sesión para un usuario existente.

            Returns:
                Response: Mensaje de éxito o error con información del usuario.
            """
            session_db = Session(db.engine)
            try:
                email = request.form.get("email")
                password = request.form.get("password")

                user = session_db.query(User).filter(User.email == email).first()

                if not user or not check_password_hash(user.password_hash, password):
                    return {"message": "Credenciales inválidas"}, 401

                return {
                    "message": "Logged in",
                    "user_id": user.id,
                    "user_name": user.name
                }, 200

            finally:
                session_db.close()


    @api_ns.route('/logout')
    class Logout(Resource):
        @api_ns.marshal_with(message_model)
        def post(self):
            """
            Finaliza la sesión del usuario.

            Returns:
                Response: Mensaje de éxito.
            """
            return {"message": "Logged out"}, 200
    
    return api_ns
