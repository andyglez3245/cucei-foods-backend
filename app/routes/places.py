import json
from flask import request
from flask_restx import Resource, Api, fields, Namespace
from sqlalchemy.orm import Session
from app.db.models import db, Place, MenuItem
from app.routes.uploads import save_upload_file


def create_places_routes(api: Api) -> Namespace:
    """Crea las rutas de lugares"""
    
    api_ns = api.namespace('api', path='/api', description='API endpoints')
    
    # Modelos para la documentación
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

    id_model = api_ns.model('CreatedId', {
        'id': fields.String(description='ID creado')
    })

    message_model = api_ns.model('Message', {
        'message': fields.String(description='Mensaje informativo')
    })

    counts_model = api_ns.model('PlaceCounts', {
        'all': fields.Integer,
        'Desayunos y Comidas': fields.Integer,
        'Bebidas y Cafetería': fields.Integer,
        'Snacks': fields.Integer
    })

    @api_ns.route('/places')
    class Places(Resource):
        @api_ns.marshal_list_with(place_model)
        def get(self):
            """
            Obtiene una lista de lugares registrados.

            Returns:
                Response: Lista de lugares en formato JSON.
            """
            session_db = Session(db.engine)
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
            session_db = Session(db.engine)
            try:
                name = request.form.get("name")
                category = request.form.get("category")

                schedule_raw = request.form.get("schedule", "{}")
                try:
                    schedule = json.loads(schedule_raw)
                except:
                    schedule = {}

                image_file = request.files.get("image")
                image_url = save_upload_file(image_file)

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
            session_db = Session(db.engine)
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
            session_db = Session(db.engine)
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
            session_db = Session(db.engine)
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
            session_db = Session(db.engine)
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
    
    return api_ns
