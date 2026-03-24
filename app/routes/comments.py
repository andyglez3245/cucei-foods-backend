from flask import request
from flask_restx import Resource, Api, fields, Namespace
from sqlalchemy.orm import Session
from app.db.models import db, Place, Comment
from app.utils import update_place_rating


def create_comments_routes(api: Api) -> Namespace:
    """Crea las rutas de comentarios"""
    
    api_ns = api.namespace('api', path='/api', description='API endpoints')
    
    # Modelos para la documentación
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
            session_db = Session(db.engine)
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
            session_db = Session(db.engine)
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
            session_db = Session(db.engine)
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
            session_db = Session(db.engine)
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
    
    return api_ns
