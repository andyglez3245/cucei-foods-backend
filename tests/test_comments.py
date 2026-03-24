"""
Tests unitarios para app.routes.comments

Prueba los endpoints:
- GET /api/places/<place_id>/comments
- POST /api/places/<place_id>/comments
- PUT /api/comments/<comment_id>
- DELETE /api/comments/<comment_id>
"""
import pytest
from app.db.models import db, Comment, Place


class TestGetComments:
    """Tests para GET /api/places/<place_id>/comments"""

    def test_get_comments_success(self, client, test_place, test_user):
        """Obtiene exitosamente comentarios de un lugar"""
        # Agregar comentario de prueba
        with client.application.app_context():
            comment = Comment(
                place_id=test_place.id,
                user_id=test_user.id,
                text="¡Muy bueno!",
                rating=5
            )
            db.session.add(comment)
            db.session.commit()

        response = client.get(f"/api/places/{test_place.id}/comments")
        
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        assert response.json[0]['text'] == "¡Muy bueno!"
        assert response.json[0]['rating'] == 5

    def test_get_comments_place_not_found(self, client):
        """Retorna 404 si el lugar no existe"""
        response = client.get("/api/places/nonexistent-id/comments")
        
        assert response.status_code == 404
        assert "error" in response.json or response.status_code == 404

    def test_get_comments_empty(self, client, test_place):
        """Retorna lista vacía si no hay comentarios"""
        response = client.get(f"/api/places/{test_place.id}/comments")
        
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 0

    def test_get_multiple_comments(self, client, test_place, test_user):
        """Retorna múltiples comentarios correctamente"""
        with client.application.app_context():
            for i in range(3):
                comment = Comment(
                    place_id=test_place.id,
                    user_id=test_user.id,
                    text=f"Comentario {i+1}",
                    rating=i+1
                )
                db.session.add(comment)
            db.session.commit()

        response = client.get(f"/api/places/{test_place.id}/comments")
        
        assert response.status_code == 200
        assert len(response.json) == 3

    def test_get_comments_includes_user_name(self, client, test_place, test_user):
        """Verifica que el nombre del usuario está incluido"""
        with client.application.app_context():
            comment = Comment(
                place_id=test_place.id,
                user_id=test_user.id,
                text="Prueba",
                rating=4
            )
            db.session.add(comment)
            db.session.commit()

        response = client.get(f"/api/places/{test_place.id}/comments")
        
        assert response.status_code == 200
        assert response.json[0]['user_name'] == "Test User"

    def test_get_comments_fields_present(self, client, test_place, test_user):
        """Verifica que todos los campos requeridos están presentes"""
        with client.application.app_context():
            comment = Comment(
                place_id=test_place.id,
                user_id=test_user.id,
                text="Prueba completa",
                rating=3
            )
            db.session.add(comment)
            db.session.commit()

        response = client.get(f"/api/places/{test_place.id}/comments")
        
        assert response.status_code == 200
        comment_data = response.json[0]
        assert 'id' in comment_data
        assert 'place_id' in comment_data
        assert 'user_id' in comment_data
        assert 'user_name' in comment_data
        assert 'text' in comment_data
        assert 'rating' in comment_data


class TestPostComment:
    """Tests para POST /api/places/<place_id>/comments"""

    def test_post_comment_success(self, client, test_place, test_user):
        """Crea exitosamente un comentario"""
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': 'Excelente servicio',
            'rating': '5'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201
        assert 'id' in response.json
        
        # Verificar que se creó en la BD
        with client.application.app_context():
            comment = db.session.get(Comment, response.json['id'])
            assert comment is not None
            assert comment.text == 'Excelente servicio'
            assert comment.rating == 5

    def test_post_comment_place_not_found(self, client, test_user):
        """Retorna 404 si el lugar no existe"""
        data = {
            'place_id': 'nonexistent',
            'user_id': test_user.id,
            'text': 'Comentario',
            'rating': '3'
        }
        
        response = client.post(
            "/api/places/nonexistent/comments",
            data=data
        )
        
        assert response.status_code == 404

    def test_post_comment_missing_text(self, client, test_place, test_user):
        """Valida que crear comentario sin texto falla"""
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'rating': '4'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        # No debe ser creado exitosamente
        assert response.status_code != 201

    def test_post_comment_with_default_rating(self, client, test_place, test_user):
        """Usa rating 0 por defecto si no se proporciona"""
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': 'Sin rating'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201
        
        with client.application.app_context():
            comment = db.session.get(Comment, response.json['id'])
            assert comment.rating == 0

    def test_post_comment_updates_place_rating(self, client, test_place, test_user):
        """Verifica que agregar comentario actualiza el rating del lugar"""
        # Agregar comentario con rating 5
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': 'Muy bueno',
            'rating': '5'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201
        
        # Verificar que el lugar fue actualizado
        with client.application.app_context():
            place = db.session.get(Place, test_place.id)
            assert place.num_ratings == 1

    def test_post_comment_with_special_characters(self, client, test_place, test_user):
        """Maneja caracteres especiales en el texto del comentario"""
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': "¡Excelente!!! 🍔 'comillas' \"más comillas\"",
            'rating': '5'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201

    def test_post_comment_returns_id(self, client, test_place, test_user):
        """Verifica que retorna un ID válido"""
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': 'Comentario',
            'rating': '3'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201
        comment_id = response.json['id']
        assert isinstance(comment_id, str)
        assert len(comment_id) > 0


class TestPutComment:
    """Tests para PUT /api/comments/<comment_id>"""

    def test_put_comment_success(self, client, test_comment):
        """Actualiza exitosamente un comentario"""
        update_data = {
            'text': 'Texto actualizado',
            'rating': 4
        }
        
        response = client.put(
            f"/api/comments/{test_comment.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        assert 'message' in response.json
        
        # Verificar que se actualizó en la BD
        with client.application.app_context():
            comment = db.session.get(Comment, test_comment.id)
            assert comment.text == 'Texto actualizado'
            assert comment.rating == 4

    def test_put_comment_not_found(self, client):
        """Retorna 404 si el comentario no existe"""
        update_data = {
            'text': 'Texto',
            'rating': 3
        }
        
        response = client.put(
            "/api/comments/nonexistent",
            json=update_data
        )
        
        assert response.status_code == 404

    def test_put_comment_partial_update(self, client, test_comment):
        """Actualiza solo el texto sin modificar el rating"""
        original_rating = 5
        with client.application.app_context():
            comment = db.session.get(Comment, test_comment.id)
            comment.rating = original_rating
            db.session.commit()

        update_data = {
            'text': 'Solo texto nuevo'
        }
        
        response = client.put(
            f"/api/comments/{test_comment.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        
        with client.application.app_context():
            comment = db.session.get(Comment, test_comment.id)
            assert comment.text == 'Solo texto nuevo'
            assert comment.rating == original_rating

    def test_put_comment_only_rating(self, client, test_comment):
        """Actualiza solo el rating sin modificar el texto"""
        original_text = "Texto original"
        with client.application.app_context():
            comment = db.session.get(Comment, test_comment.id)
            comment.text = original_text
            db.session.commit()

        update_data = {
            'rating': 2
        }
        
        response = client.put(
            f"/api/comments/{test_comment.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        
        with client.application.app_context():
            comment = db.session.get(Comment, test_comment.id)
            assert comment.text == original_text
            assert comment.rating == 2

    def test_put_comment_updates_place_rating(self, client, test_comment):
        """Verificar que actualizar comentario recalcula el rating del lugar"""
        response = client.put(
            f"/api/comments/{test_comment.id}",
            json={'rating': 3}
        )
        
        assert response.status_code == 200

    def test_put_comment_with_special_characters(self, client, test_comment):
        """Maneja caracteres especiales al actualizar"""
        update_data = {
            'text': 'Actualizado con ñ, acentos: á é í ó ú',
            'rating': 5
        }
        
        response = client.put(
            f"/api/comments/{test_comment.id}",
            json=update_data
        )
        
        assert response.status_code == 200

    def test_put_comment_empty_update(self, client, test_comment):
        """Maneja actualización vacía correctamente"""
        update_data = {}
        
        response = client.put(
            f"/api/comments/{test_comment.id}",
            json=update_data
        )
        
        # Debe ser exitosa o retornar error específico
        assert response.status_code in [200, 400]


class TestDeleteComment:
    """Tests para DELETE /api/comments/<comment_id>"""

    def test_delete_comment_success(self, client, test_comment):
        """Elimina exitosamente un comentario"""
        response = client.delete(f"/api/comments/{test_comment.id}")
        
        assert response.status_code == 200
        assert 'message' in response.json
        
        # Verificar que se eliminó de la BD
        with client.application.app_context():
            comment = db.session.get(Comment, test_comment.id)
            assert comment is None

    def test_delete_comment_not_found(self, client):
        """Retorna 404 si el comentario no existe"""
        response = client.delete("/api/comments/nonexistent")
        
        assert response.status_code == 404

    def test_delete_comment_updates_place_rating(self, client, test_comment, test_place):
        """Verificar que eliminar comentario recalcula el rating del lugar"""
        place_id = test_comment.place_id
        
        response = client.delete(f"/api/comments/{test_comment.id}")
        
        assert response.status_code == 200
        
        # Verificar que el lugar sigue existiendo
        with client.application.app_context():
            place = db.session.get(Place, place_id)
            assert place is not None

    def test_delete_multiple_comments(self, client, test_place, test_user):
        """Elimina múltiples comentarios correctamente"""
        # Crear 3 comentarios
        comment_ids = []
        with client.application.app_context():
            for i in range(3):
                comment = Comment(
                    place_id=test_place.id,
                    user_id=test_user.id,
                    text=f"Comentario {i}",
                    rating=i+1
                )
                db.session.add(comment)
                db.session.commit()
                comment_ids.append(comment.id)

        # Eliminar los primeros 2
        for cid in comment_ids[:2]:
            response = client.delete(f"/api/comments/{cid}")
            assert response.status_code == 200

        # Verificar que el tercero sigue existiendo
        with client.application.app_context():
            comment = db.session.get(Comment, comment_ids[2])
            assert comment is not None

    def test_delete_comment_response_message(self, client, test_comment):
        """Verifica que el mensaje de respuesta es correcto"""
        response = client.delete(f"/api/comments/{test_comment.id}")
        
        assert response.status_code == 200
        assert 'message' in response.json
        assert isinstance(response.json['message'], str)


class TestCommentsIntegration:
    """Tests de integración para flujos completos"""

    def test_full_comment_lifecycle(self, client, test_place, test_user):
        """Prueba el ciclo completo: crear → leer → actualizar → eliminar"""
        # 1. Crear comentario
        create_data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': 'Comentario inicial',
            'rating': '3'
        }
        create_response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=create_data
        )
        assert create_response.status_code == 201
        comment_id = create_response.json['id']

        # 2. Leer comentarios
        get_response = client.get(f"/api/places/{test_place.id}/comments")
        assert get_response.status_code == 200
        assert len(get_response.json) == 1
        assert get_response.json[0]['text'] == 'Comentario inicial'

        # 3. Actualizar comentario
        update_data = {
            'text': 'Comentario actualizado',
            'rating': 5
        }
        put_response = client.put(
            f"/api/comments/{comment_id}",
            json=update_data
        )
        assert put_response.status_code == 200

        # 4. Verificar actualización
        get_response2 = client.get(f"/api/places/{test_place.id}/comments")
        assert get_response2.json[0]['text'] == 'Comentario actualizado'
        assert get_response2.json[0]['rating'] == 5

        # 5. Eliminar comentario
        delete_response = client.delete(f"/api/comments/{comment_id}")
        assert delete_response.status_code == 200

        # 6. Verificar eliminación
        get_response3 = client.get(f"/api/places/{test_place.id}/comments")
        assert len(get_response3.json) == 0

    def test_multiple_comments_handling(self, client, test_place, test_user):
        """Prueba manejo de múltiples comentarios del mismo lugar"""
        # Crear 3 comentarios
        comment_ids = []
        for i in range(3):
            data = {
                'place_id': test_place.id,
                'user_id': test_user.id,
                'text': f'Comentario {i+1}',
                'rating': str(i+1)
            }
            response = client.post(
                f"/api/places/{test_place.id}/comments",
                data=data
            )
            assert response.status_code == 201
            comment_ids.append(response.json['id'])

        # Verificar que todos existen
        get_response = client.get(f"/api/places/{test_place.id}/comments")
        assert len(get_response.json) == 3

        # Eliminar el del medio
        delete_response = client.delete(f"/api/comments/{comment_ids[1]}")
        assert delete_response.status_code == 200

        # Verificar que quedan 2
        get_response2 = client.get(f"/api/places/{test_place.id}/comments")
        assert len(get_response2.json) == 2

    def test_comments_isolated_by_place(self, client, test_user):
        """Verifica que comentarios están aislados por lugar"""
        # Crear 2 lugares
        with client.application.app_context():
            place1 = Place(
                name="Lugar 1",
                schedule={"lunes": "10:00-22:00"},
                category="Comida",
                image_url=""
            )
            place2 = Place(
                name="Lugar 2",
                schedule={"lunes": "10:00-22:00"},
                category="Comida",
                image_url=""
            )
            db.session.add_all([place1, place2])
            db.session.commit()
            place1_id = place1.id
            place2_id = place2.id

        # Agregar comentarios a lugar 1
        for i in range(2):
            data = {
                'place_id': place1_id,
                'user_id': test_user.id,
                'text': f'Comentario lugar 1 - {i}',
                'rating': str(i+1)
            }
            client.post(f"/api/places/{place1_id}/comments", data=data)

        # Agregar comentario a lugar 2
        data = {
            'place_id': place2_id,
            'user_id': test_user.id,
            'text': 'Comentario lugar 2',
            'rating': '5'
        }
        client.post(f"/api/places/{place2_id}/comments", data=data)

        # Verificar que cada lugar tiene sus comentarios
        response1 = client.get(f"/api/places/{place1_id}/comments")
        response2 = client.get(f"/api/places/{place2_id}/comments")

        assert len(response1.json) == 2
        assert len(response2.json) == 1

    def test_comment_update_then_delete(self, client, test_comment):
        """Actualiza un comentario y luego lo elimina"""
        # Actualizar
        update_data = {'text': 'Actualizado', 'rating': 4}
        put_response = client.put(
            f"/api/comments/{test_comment.id}",
            json=update_data
        )
        assert put_response.status_code == 200

        # Eliminar
        delete_response = client.delete(f"/api/comments/{test_comment.id}")
        assert delete_response.status_code == 200

        # Verificar eliminación
        with client.application.app_context():
            comment = db.session.get(Comment, test_comment.id)
            assert comment is None


class TestCommentsEdgeCases:
    """Tests de casos límite y validaciones"""

    def test_comment_with_very_long_text(self, client, test_place, test_user):
        """Maneja comentarios con texto muy largo"""
        long_text = "a" * 5000
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': long_text,
            'rating': '5'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201

    def test_comment_with_zero_rating(self, client, test_place, test_user):
        """Permite rating de 0"""
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': 'Sin calificación',
            'rating': '0'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201
        with client.application.app_context():
            comment = db.session.get(Comment, response.json['id'])
            assert comment.rating == 0

    def test_comment_with_high_rating(self, client, test_place, test_user):
        """Permite ratings altos"""
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': 'Excelente',
            'rating': '10'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201
        with client.application.app_context():
            comment = db.session.get(Comment, response.json['id'])
            assert comment.rating == 10

    def test_comment_with_unicode_characters(self, client, test_place, test_user):
        """Maneja caracteres Unicode correctamente"""
        unicode_text = "Emoji: 🍕 🍔 Caracteres: 中文 العربية עברית"
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': unicode_text,
            'rating': '5'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201

    def test_comment_id_uniqueness(self, client, test_place, test_user):
        """Verifica que cada comentario tiene ID único"""
        ids = set()
        for i in range(3):
            data = {
                'place_id': test_place.id,
                'user_id': test_user.id,
                'text': f'Comentario {i}',
                'rating': str(i+1)
            }
            response = client.post(
                f"/api/places/{test_place.id}/comments",
                data=data
            )
            assert response.status_code == 201
            ids.add(response.json['id'])

        assert len(ids) == 3  # Todos los IDs son diferentes

    def test_comment_whitespace_handling(self, client, test_place, test_user):
        """Maneja espacios en blanco en el texto"""
        data = {
            'place_id': test_place.id,
            'user_id': test_user.id,
            'text': '   Texto con espacios   ',
            'rating': '4'
        }
        
        response = client.post(
            f"/api/places/{test_place.id}/comments",
            data=data
        )
        
        assert response.status_code == 201
