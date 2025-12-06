import os
import json
import secrets
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sqlalchemy.orm import Session
from app.db.models import db, Place, MenuItem, Comment, User
from app.utils import update_place_rating
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restx import Api, Resource, fields


UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
CORS(app)
# Exponer la UI de Swagger en /docs (doc='/') por defecto; aquí la configuramos explícitamente
api = Api(app, title="Cucei Foods API", version="1.0", description="Documentación de la API", doc='/docs')

# --- INICIO DE LA CONFIGURACIÓN DE BASE DE DATOS HÍBRIDA ---

database_url = os.environ.get('DATABASE_URL')

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

local_db_uri = f'postgresql://postgres:{os.environ.get("DB_PASSWORD", "contraseña_local_aqui")}@localhost:5432/cuceifoods'

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or local_db_uri

# --- FIN DE LA CONFIGURACIÓN ---
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Secret key for sessions
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

db.init_app(app)

# -------------------
# Helpers
# -------------------

def get_session():
    return Session(db.engine)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------
# UPLOADS
# -------------------


@api.route("/uploads/<filename>")
class UploadResource(Resource):
    def get(self, filename):
        """
        Sirve un archivo subido desde el directorio de uploads.

        Args:
            filename (str): Nombre del archivo a servir.

        Returns:
            Response: Archivo solicitado.
        """
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------------------
# AUTH ENDPOINTS
# -------------------

api_ns = api.namespace('api', path='/api', description='API endpoints')

# Models para la documentación (Flask-RESTx)
menu_item_model = api_ns.model('MenuItem', {
    'category': fields.String(required=False, description='Categoría del plato'),
    'dish_name': fields.String(required=True, description='Nombre del platillo'),
    'price': fields.Float(required=True, description='Precio')
})

place_model = api_ns.model('Place', {
    'id': fields.String(readOnly=True, description='ID del lugar'),
    'name': fields.String(required=True, description='Nombre del lugar'),
    'schedule': fields.Raw(required=False, description='Horario (objeto JSON)'),
    'category': fields.String(required=False, description='Categoría'),
    'image_url': fields.String(required=False, description='URL de la imagen'),
    'menu': fields.List(fields.Nested(menu_item_model), description='Lista de elementos del menú'),
    'rating': fields.Float(description='Calificación promedio'),
    'num_ratings': fields.Integer(description='Número de calificaciones'),
    'latest_comment': fields.String(description='Último comentario')
})

comment_model = api_ns.model('Comment', {
    'id': fields.String(readOnly=True, description='ID del comentario'),
    'place_id': fields.String(required=True, description='ID del lugar'),
    'user_id': fields.String(required=False, description='ID del usuario'),
    'user_name': fields.String(required=False, description='Nombre del usuario'),
    'text': fields.String(required=True, description='Texto del comentario'),
    'rating': fields.Integer(required=False, description='Calificación')
})

id_model = api_ns.model('CreatedId', {
    'id': fields.String(description='ID creado')
})

message_model = api_ns.model('Message', {
    'message': fields.String(description='Mensaje informativo')
})

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

counts_model = api_ns.model('PlaceCounts', {
    'all': fields.Integer,
    'Desayunos y Comidas': fields.Integer,
    'Bebidas y Cafetería': fields.Integer,
    'Snacks': fields.Integer
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
        session_db = get_session()
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
        session_db = get_session()
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

# -------------------
# PLACES ENDPOINTS
# -------------------

@api_ns.route('/places')
class Places(Resource):
    @api_ns.marshal_list_with(place_model)
    def get(self):
        """
        Obtiene una lista de lugares registrados.

        Returns:
            Response: Lista de lugares en formato JSON.
        """
        session_db = get_session()
        try:
            category = request.args.get("category")

            query = session_db.query(Place)
            if category and category.lower() != "all":
                query = query.filter(Place.category == category)

            places = query.all()

            result = []
            for p in places:
                result.append({
                    "id": p.id,
                    "name": p.name,
                    "schedule": p.schedule,
                    "category": p.category,
                    "image_url": p.image_url,
                    "menu": [{"category": m.category, "dish_name": m.dish_name, "price": m.price} for m in p.menu_items],
                    "rating": p.rating,
                    "num_ratings": p.num_ratings,
                    "latest_comment": p.comments[-1].text if p.comments else ""
                })

            return result
        finally:
            session_db.close()

    @api_ns.expect(place_model, validate=False)
    @api_ns.marshal_with(id_model, code=201)
    def post(self):
        """
        Crea un nuevo lugar en el sistema.

        Returns:
            Response: ID del lugar creado o mensaje de error.
        """
        session_db = get_session()
        try:
            name = request.form.get("name")
            category = request.form.get("category")

            schedule_raw = request.form.get("schedule", "{}")
            try:
                schedule = json.loads(schedule_raw)
            except:
                schedule = {}

            image_file = request.files.get("image")
            image_url = ""
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)
                image_url = f"/uploads/{filename}"

            new_place = Place(
                name=name,
                schedule=schedule,
                category=category,
                image_url=image_url
            )

            session_db.add(new_place)
            session_db.commit()

            # Menu items
            menu_json = request.form.get("menu", "[]")
            menu_items = json.loads(menu_json)
            for m in menu_items:
                menu_item = MenuItem(
                    place_id=new_place.id,
                    category=m.get("category"),
                    dish_name=m.get("dish_name"),
                    price=m.get("price")
                )
                session_db.add(menu_item)

            session_db.commit()
            return {"id": new_place.id}, 201
        finally:
            session_db.close()


@api_ns.route('/places/<string:place_id>')
class PlaceResource(Resource):
    @api_ns.marshal_with(place_model)
    def get(self, place_id):
        """
        Obtiene información detallada de un lugar específico.

        Args:
            place_id (str): ID del lugar.

        Returns:
            Response: Información del lugar o error si no se encuentra.
        """
        session_db = get_session()
        try:
            p = session_db.get(Place, place_id)
            if not p:
                return {"error": "Place not found"}, 404

            return {
                "id": p.id,
                "name": p.name,
                "schedule": p.schedule,
                "category": p.category,
                "image_url": p.image_url,
                "menu": [{"category": m.category, "dish_name": m.dish_name, "price": m.price} for m in p.menu_items],
                "rating": p.rating,
                "num_ratings": p.num_ratings
            }
        finally:
            session_db.close()

    @api_ns.expect(place_model, validate=False)
    @api_ns.marshal_with(message_model)
    def put(self, place_id):
        """
        Actualiza la información de un lugar existente.

        Args:
            place_id (str): ID del lugar a actualizar.

        Returns:
            Response: Mensaje de éxito o error.
        """
        session_db = get_session()
        try:
            p = session_db.get(Place, place_id)
            if not p:
                return {"error": "Place not found"}, 404

            data = request.json
            p.name = data.get("name", p.name)
            p.category = data.get("category", p.category)
            p.image_url = data.get("image_url", p.image_url)

            if "schedule" in data:
                s = data["schedule"]
                if isinstance(s, str):
                    try:
                        s = json.loads(s)
                    except:
                        s = {}
                p.schedule = s

            # Delete old menu items
            session_db.query(MenuItem).filter(MenuItem.place_id == p.id).delete(synchronize_session=False)

            for m in data.get("menu", []):
                menu_item = MenuItem(
                    place_id=p.id,
                    category=m.get("category"),
                    dish_name=m.get("dish_name"),
                    price=m.get("price")
                )
                session_db.add(menu_item)

            session_db.commit()
            return {"message": "Updated"}
        finally:
            session_db.close()

    @api_ns.marshal_with(message_model)
    def delete(self, place_id):
        """
        Elimina un lugar del sistema.

        Args:
            place_id (str): ID del lugar a eliminar.

        Returns:
            Response: Mensaje de éxito o error.
        """
        session_db = get_session()
        try:
            p = session_db.get(Place, place_id)
            if not p:
                return {"error": "Place not found"}, 404

            session_db.delete(p)
            session_db.commit()

            return {"message": "Deleted"}
        finally:
            session_db.close()











@api_ns.route('/places/counts')
class PlaceCounts(Resource):
    @api_ns.marshal_with(counts_model)
    def get(self):
        """
        Obtiene el conteo de lugares por categoría.

        Returns:
            Response: Conteo de lugares en formato JSON.
        """
        session_db = get_session()
        try:
            counts = {
                "all": session_db.query(Place).count(),
                "Desayunos y Comidas": session_db.query(Place).filter(Place.category == "Desayunos y Comidas").count(),
                "Bebidas y Cafetería": session_db.query(Place).filter(Place.category == "Bebidas y Cafetería").count(),
                "Snacks": session_db.query(Place).filter(Place.category == "Snacks").count()
            }
            return counts
        finally:
            session_db.close()

# -------------------
# COMMENTS
# -------------------

@api_ns.route('/places/<string:place_id>/comments')
class Comments(Resource):
    @api_ns.marshal_list_with(comment_model)
    def get(self, place_id):
        """
        Obtiene los comentarios de un lugar específico.

        Args:
            place_id (str): ID del lugar.

        Returns:
            Response: Lista de comentarios en formato JSON.
        """
        session_db = get_session()
        try:
            place = session_db.get(Place, place_id)
            if not place:
                return {"error": "Place not found"}, 404

            return [
                {
                    "id": c.id,
                    "place_id": c.place_id,
                    "user_id": c.user_id,
                    "user_name": c.user.name,
                    "text": c.text,
                    "rating": c.rating
                }
                for c in place.comments
            ]
        finally:
            session_db.close()

    @api_ns.expect(comment_model, validate=False)
    @api_ns.marshal_with(id_model, code=201)
    def post(self, place_id):
        """
        Agrega un comentario a un lugar específico.

        Args:
            place_id (str): ID del lugar.

        Returns:
            Response: ID del comentario creado o mensaje de error.
        """
        session_db = get_session()
        try:
            place = session_db.get(Place, place_id)
            if not place:
                return {"error": "Local no encontrado"}, 404

            new_comment = Comment(
                place_id=place_id,
                user_id=request.form.get("user_id"),
                text=request.form.get("text"),
                rating=int(request.form.get("rating", 0))
            )

            session_db.add(new_comment)
            session_db.commit()

            update_place_rating(session_db, place)
            session_db.commit()

            return {"id": new_comment.id}, 201

        finally:
            session_db.close()





@api_ns.route('/comments/<string:comment_id>')
class CommentResource(Resource):
    @api_ns.expect(comment_model, validate=False)
    @api_ns.marshal_with(message_model)
    def put(self, comment_id):
        """
        Actualiza un comentario existente.

        Args:
            comment_id (str): ID del comentario a actualizar.

        Returns:
            Response: Mensaje de éxito o error.
        """
        session_db = get_session()
        try:
            c = session_db.get(Comment, comment_id)
            if not c:
                return {"error": "Comentario no encontrado"}, 404

            data = request.json
            c.text = data.get("text", c.text)
            c.rating = data.get("rating", c.rating)

            session_db.commit()
            update_place_rating(session_db, c.place)
            session_db.commit()

            return {"message": "Comentario editado correctamente"}
        finally:
            session_db.close()

    @api_ns.marshal_with(message_model)
    def delete(self, comment_id):
        """
        Elimina un comentario del sistema.

        Args:
            comment_id (str): ID del comentario a eliminar.

        Returns:
            Response: Mensaje de éxito o error.
        """
        session_db = get_session()
        try:
            c = session_db.get(Comment, comment_id)
            if not c:
                return {"error": "Comment not found"}, 404

            place = c.place

            session_db.delete(c)
            session_db.commit()

            update_place_rating(session_db, place)
            session_db.commit()

            return {"message": "Comentario eliminado correctamente"}
        finally:
            session_db.close()


# -------------------
# RUN SERVER
# -------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
