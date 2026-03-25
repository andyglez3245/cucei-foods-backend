"""
Tests unitarios para app.routes.places

Prueba los endpoints:
- GET /api/places
- POST /api/places
- GET /api/places/<place_id>
- PUT /api/places/<place_id>
- DELETE /api/places/<place_id>
- GET /api/places/counts
"""
import pytest
import json
from app.db.models import db, Place, MenuItem


class TestGetPlaces:
    """Tests para GET /api/places"""

    def test_get_places_success(self, client, test_place):
        """Obtiene exitosamente una lista de lugares"""
        response = client.get("/api/places")
        
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) >= 1

    def test_get_places_empty(self, client):
        """Retorna lista vacía si no hay lugares"""
        response = client.get("/api/places")
        
        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == 0

    def test_get_places_includes_all_fields(self, client, test_place):
        """Verifica que todos los campos requeridos están presentes"""
        response = client.get("/api/places")
        
        assert response.status_code == 200
        place_data = response.json[0]
        assert 'id' in place_data
        assert 'name' in place_data
        assert 'schedule' in place_data
        assert 'category' in place_data
        assert 'image_url' in place_data
        assert 'menu' in place_data
        assert 'rating' in place_data
        assert 'num_ratings' in place_data

    def test_get_places_filter_by_category(self, client, test_multiple_places):
        """Filtra lugares por categoría"""
        response = client.get("/api/places?category=Desayunos y Comidas")
        
        assert response.status_code == 200
        assert len(response.json) >= 1
        # Todos deben ser de la categoría especificada
        for place in response.json:
            assert place['category'] == "Desayunos y Comidas"

    def test_get_places_filter_all(self, client, test_multiple_places):
        """Obtiene todos los lugares con filtro 'all'"""
        response = client.get("/api/places?category=all")
        
        assert response.status_code == 200
        # Debería retornar todos
        assert len(response.json) >= 1

    def test_get_places_case_insensitive_filter(self, client, test_multiple_places):
        """El filtro maneja caso correcto de categoría"""
        # Las categorías deben ser exactas
        response = client.get("/api/places?category=Desayunos y Comidas")
        
        assert response.status_code == 200
        # Debería encontrar al menos uno
        assert len(response.json) >= 1

    def test_get_places_invalid_category(self, client, test_place):
        """Retorna lista vacía con categoría inválida"""
        response = client.get("/api/places?category=CategoryNoExiste")
        
        assert response.status_code == 200
        assert len(response.json) == 0

    def test_get_places_with_menu(self, client, test_place_with_menu):
        """Obtiene un lugar con su menú completo"""
        response = client.get("/api/places")
        
        assert response.status_code == 200
        assert len(response.json) >= 1
        place = response.json[0]
        assert 'menu' in place
        assert isinstance(place['menu'], list)

    def test_get_places_multiple(self, client, test_multiple_places):
        """Obtiene múltiples lugares"""
        response = client.get("/api/places")
        
        assert response.status_code == 200
        assert len(response.json) >= 3


class TestPostPlace:
    """Tests para POST /api/places"""

    def test_post_place_success(self, client):
        """Crea exitosamente un nuevo lugar"""
        data = {
            'name': 'Nuevo Restaurante',
            'category': 'Desayunos y Comidas',
            'schedule': json.dumps({"lunes": "10:00-22:00"}),
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        
        assert response.status_code == 201
        assert 'id' in response.json
        
        # Verificar que se creó en BD
        with client.application.app_context():
            place = db.session.get(Place, response.json['id'])
            assert place is not None
            assert place.name == 'Nuevo Restaurante'

    def test_post_place_with_menu(self, client):
        """Crea un lugar con items de menú"""
        menu_items = [
            {"category": "Desayunos", "dish_name": "Omelette", "price": 7.50},
            {"category": "Comidas", "dish_name": "Pechuga", "price": 12.00},
        ]
        
        data = {
            'name': 'Restaurante con Menú',
            'category': 'Desayunos y Comidas',
            'schedule': json.dumps({"lunes": "08:00-22:00"}),
            'menu': json.dumps(menu_items),
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        
        assert response.status_code == 201
        place_id = response.json['id']
        
        # Verificar menú
        with client.application.app_context():
            place = db.session.get(Place, place_id)
            assert len(place.menu_items) == 2
            assert place.menu_items[0].dish_name == "Omelette"

    def test_post_place_default_schedule(self, client):
        """Usa horario vacío si no se proporciona"""
        data = {
            'name': 'Lugar Simple',
            'category': 'Snacks',
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        
        assert response.status_code == 201
        place_id = response.json['id']
        
        with client.application.app_context():
            place = db.session.get(Place, place_id)
            assert place.schedule == {}

    def test_post_place_returns_id(self, client):
        """Retorna un ID válido"""
        data = {
            'name': 'Nuevo Lugar',
            'category': 'Bebidas y Cafetería',
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        
        assert response.status_code == 201
        place_id = response.json['id']
        assert isinstance(place_id, str)
        assert len(place_id) > 0

    def test_post_place_invalid_schedule_json(self, client):
        """Maneja JSON inválido en schedule"""
        data = {
            'name': 'Lugar',
            'category': 'Comida',
            'schedule': 'esto-no-es-json',
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        
        # Debe crear lugar aunque el schedule sea inválido
        assert response.status_code == 201

    def test_post_place_special_characters(self, client):
        """Maneja caracteres especiales en el nombre"""
        data = {
            'name': 'Restaurante "Fuensanta" & Ñandú',
            'category': 'Comida',
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        
        assert response.status_code == 201


class TestGetPlaceById:
    """Tests para GET /api/places/<place_id>"""

    def test_get_place_by_id_success(self, client, test_place):
        """Obtiene un lugar específico exitosamente"""
        response = client.get(f"/api/places/{test_place.id}")
        
        assert response.status_code == 200
        place_data = response.json
        assert place_data['id'] == test_place.id
        assert place_data['name'] == "Test Restaurant"

    def test_get_place_by_id_not_found(self, client):
        """Retorna 404 si el lugar no existe"""
        response = client.get("/api/places/nonexistent-id")
        
        assert response.status_code == 404

    def test_get_place_includes_all_fields(self, client, test_place):
        """Verifica que todos los campos están presentes"""
        response = client.get(f"/api/places/{test_place.id}")
        
        assert response.status_code == 200
        place_data = response.json
        assert 'id' in place_data
        assert 'name' in place_data
        assert 'schedule' in place_data
        assert 'category' in place_data
        assert 'image_url' in place_data
        assert 'menu' in place_data
        assert 'rating' in place_data
        assert 'num_ratings' in place_data

    def test_get_place_with_menu(self, client, test_place_with_menu):
        """Obtiene un lugar con su menú"""
        response = client.get(f"/api/places/{test_place_with_menu.id}")
        
        assert response.status_code == 200
        place_data = response.json
        assert len(place_data['menu']) == 3
        assert place_data['menu'][0]['dish_name'] == "Pancakes"

    def test_get_place_menu_structure(self, client, test_place_with_menu):
        """Verifica la estructura correcta del menú"""
        response = client.get(f"/api/places/{test_place_with_menu.id}")
        
        assert response.status_code == 200
        menus = response.json['menu']
        for item in menus:
            assert 'category' in item
            assert 'dish_name' in item
            assert 'price' in item


class TestPutPlace:
    """Tests para PUT /api/places/<place_id>"""

    def test_put_place_success(self, client, test_place):
        """Actualiza exitosamente un lugar"""
        update_data = {
            'name': 'Restaurante Actualizado',
            'category': 'Bebidas y Cafetería'
        }
        
        response = client.put(
            f"/api/places/{test_place.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        assert 'message' in response.json
        
        # Verificar actualización
        with client.application.app_context():
            place = db.session.get(Place, test_place.id)
            assert place.name == 'Restaurante Actualizado'
            assert place.category == 'Bebidas y Cafetería'

    def test_put_place_not_found(self, client):
        """Retorna 404 si el lugar no existe"""
        update_data = {'name': 'Nuevo Nombre'}
        
        response = client.put(
            "/api/places/nonexistent",
            json=update_data
        )
        
        assert response.status_code == 404

    def test_put_place_partial_update(self, client, test_place):
        """Actualiza solo algunos campos"""
        original_category = "Comida Rápida"
        update_data = {'name': 'Solo Nombre Nuevo'}
        
        response = client.put(
            f"/api/places/{test_place.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        
        with client.application.app_context():
            place = db.session.get(Place, test_place.id)
            assert place.name == 'Solo Nombre Nuevo'
            assert place.category == original_category

    def test_put_place_update_schedule(self, client, test_place):
        """Actualiza el horario"""
        new_schedule = {"lunes": "09:00-23:00"}
        update_data = {'schedule': new_schedule}
        
        response = client.put(
            f"/api/places/{test_place.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        
        with client.application.app_context():
            place = db.session.get(Place, test_place.id)
            assert place.schedule == new_schedule

    def test_put_place_update_schedule_as_string(self, client, test_place):
        """Maneja horario como string JSON"""
        new_schedule_str = json.dumps({"martes": "08:00-20:00"})
        update_data = {'schedule': new_schedule_str}
        
        response = client.put(
            f"/api/places/{test_place.id}",
            json=update_data
        )
        
        assert response.status_code == 200

    def test_put_place_update_menu(self, client, test_place):
        """Actualiza el menú del lugar"""
        new_menu = [
            {"category": "Bebidas", "dish_name": "Café", "price": 2.50},
            {"category": "Snacks", "dish_name": "Galletas", "price": 1.50},
        ]
        
        update_data = {'menu': new_menu}
        
        response = client.put(
            f"/api/places/{test_place.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        
        with client.application.app_context():
            place = db.session.get(Place, test_place.id)
            assert len(place.menu_items) == 2

    def test_put_place_replace_menu(self, client, test_place_with_menu):
        """Reemplaza completamente el menú"""
        new_menu = [
            {"category": "Nueva", "dish_name": "Plato", "price": 5.00},
        ]
        
        update_data = {'menu': new_menu}
        
        response = client.put(
            f"/api/places/{test_place_with_menu.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        
        with client.application.app_context():
            place = db.session.get(Place, test_place_with_menu.id)
            assert len(place.menu_items) == 1

    def test_put_place_update_image_url(self, client, test_place):
        """Actualiza la URL de la imagen"""
        new_image = "https://example.com/new-image.jpg"
        update_data = {'image_url': new_image}
        
        response = client.put(
            f"/api/places/{test_place.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        
        with client.application.app_context():
            place = db.session.get(Place, test_place.id)
            assert place.image_url == new_image


class TestDeletePlace:
    """Tests para DELETE /api/places/<place_id>"""

    def test_delete_place_success(self, client, test_place):
        """Elimina exitosamente un lugar"""
        response = client.delete(f"/api/places/{test_place.id}")
        
        assert response.status_code == 200
        assert 'message' in response.json
        
        # Verificar que se eliminó
        with client.application.app_context():
            place = db.session.get(Place, test_place.id)
            assert place is None

    def test_delete_place_not_found(self, client):
        """Retorna 404 si el lugar no existe"""
        response = client.delete("/api/places/nonexistent")
        
        assert response.status_code == 404

    def test_delete_place_cascades_menu_items(self, client, test_place_with_menu):
        """Elimina también los items de menú asociados"""
        place_id = test_place_with_menu.id
        
        # Verificar que tiene menú items
        with client.application.app_context():
            items_count = db.session.query(MenuItem).filter(MenuItem.place_id == place_id).count()
            assert items_count > 0
        
        # Eliminar lugar
        response = client.delete(f"/api/places/{place_id}")
        assert response.status_code == 200
        
        # Verificar que se eliminaron
        with client.application.app_context():
            items_count = db.session.query(MenuItem).filter(MenuItem.place_id == place_id).count()
            assert items_count == 0

    def test_delete_place_response_message(self, client, test_place):
        """Verifica el mensaje de respuesta"""
        response = client.delete(f"/api/places/{test_place.id}")
        
        assert response.status_code == 200
        assert isinstance(response.json['message'], str)


class TestPlaceCounts:
    """Tests para GET /api/places/counts"""

    def test_get_counts_empty(self, client):
        """Obtiene conteos cuando no hay lugares"""
        response = client.get("/api/places/counts")
        
        assert response.status_code == 200
        counts = response.json
        assert counts['all'] == 0
        assert counts['Desayunos y Comidas'] == 0
        assert counts['Bebidas y Cafetería'] == 0
        assert counts['Snacks'] == 0

    def test_get_counts_success(self, client, test_multiple_places):
        """Obtiene conteos correctos por categoría"""
        response = client.get("/api/places/counts")
        
        assert response.status_code == 200
        counts = response.json
        assert counts['all'] == 3
        assert counts['Desayunos y Comidas'] == 1
        assert counts['Bebidas y Cafetería'] == 1
        assert counts['Snacks'] == 1

    def test_get_counts_includes_all_categories(self, client, test_multiple_places):
        """Verifica que todos los campos de categoría están presentes"""
        response = client.get("/api/places/counts")
        
        assert response.status_code == 200
        counts = response.json
        assert 'all' in counts
        assert 'Desayunos y Comidas' in counts
        assert 'Bebidas y Cafetería' in counts
        assert 'Snacks' in counts

    def test_get_counts_are_integers(self, client, test_multiple_places):
        """Verifica que los conteos son números enteros"""
        response = client.get("/api/places/counts")
        
        assert response.status_code == 200
        counts = response.json
        for key, value in counts.items():
            assert isinstance(value, int)


class TestPlacesIntegration:
    """Tests de integración para flujos completos"""

    def test_full_place_lifecycle(self, client):
        """Prueba el ciclo completo: crear → leer → actualizar → eliminar"""
        # 1. Crear lugar
        create_data = {
            'name': 'Ciclo Completo',
            'category': 'Desayunos y Comidas',
            'schedule': json.dumps({"lunes": "10:00-22:00"}),
            'image': (None, ''),
        }
        create_response = client.post("/api/places", data=create_data)
        assert create_response.status_code == 201
        place_id = create_response.json['id']

        # 2. Obtener lugar
        get_response = client.get(f"/api/places/{place_id}")
        assert get_response.status_code == 200
        assert get_response.json['name'] == 'Ciclo Completo'

        # 3. Actualizar lugar
        update_data = {'name': 'Ciclo Completo Actualizado'}
        put_response = client.put(f"/api/places/{place_id}", json=update_data)
        assert put_response.status_code == 200

        # 4. Verificar actualización
        get_response2 = client.get(f"/api/places/{place_id}")
        assert get_response2.json['name'] == 'Ciclo Completo Actualizado'

        # 5. Eliminar lugar
        delete_response = client.delete(f"/api/places/{place_id}")
        assert delete_response.status_code == 200

        # 6. Verificar eliminación
        get_response3 = client.get(f"/api/places/{place_id}")
        assert get_response3.status_code == 404

    def test_multiple_places_filtering(self, client, test_multiple_places):
        """Prueba filtrado de múltiples lugares"""
        # Obtener todos
        all_response = client.get("/api/places")
        assert len(all_response.json) == 3

        # Filtrar por categoría
        comidas_response = client.get("/api/places?category=Desayunos y Comidas")
        assert len(comidas_response.json) == 1

        # Obtener conteos
        counts_response = client.get("/api/places/counts")
        assert counts_response.json['Desayunos y Comidas'] == 1

    def test_place_with_complete_menu_workflow(self, client):
        """Flujo completo con menú"""
        menu = [
            {"category": "Entrada", "dish_name": "Sopa", "price": 5.00},
            {"category": "Principal", "dish_name": "Pechuga", "price": 15.00},
        ]
        
        # Crear
        create_data = {
            'name': 'Restaurante Completo',
            'category': 'Desayunos y Comidas',
            'menu': json.dumps(menu),
            'image': (None, ''),
        }
        create_response = client.post("/api/places", data=create_data)
        assert create_response.status_code == 201
        place_id = create_response.json['id']

        # Obtener y verificar menú
        get_response = client.get(f"/api/places/{place_id}")
        assert len(get_response.json['menu']) == 2

        # Actualizar menú
        new_menu = [
            {"category": "Postre", "dish_name": "Flan", "price": 4.50},
        ]
        update_data = {'menu': new_menu}
        put_response = client.put(f"/api/places/{place_id}", json=update_data)
        assert put_response.status_code == 200

        # Verificar nuevo menú
        get_response2 = client.get(f"/api/places/{place_id}")
        assert len(get_response2.json['menu']) == 1
        assert get_response2.json['menu'][0]['dish_name'] == 'Flan'


class TestPlacesEdgeCases:
    """Tests de casos límite y validaciones"""

    def test_place_with_very_long_name(self, client):
        """Maneja nombres muy largos"""
        long_name = "a" * 500
        data = {
            'name': long_name,
            'category': 'Comida',
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        
        assert response.status_code == 201

    def test_place_with_unicode_name(self, client):
        """Maneja caracteres Unicode en nombre"""
        data = {
            'name': 'Restaurante 中文 العربية עברית 🍕',
            'category': 'Comida',
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        
        assert response.status_code == 201

    def test_place_id_uniqueness(self, client):
        """Verifica que cada lugar tiene ID único"""
        ids = set()
        for i in range(3):
            data = {
                'name': f'Lugar {i}',
                'category': 'Comida',
                'image': (None, ''),
            }
            response = client.post("/api/places", data=data)
            assert response.status_code == 201
            ids.add(response.json['id'])
        
        assert len(ids) == 3

    def test_place_with_empty_menu(self, client):
        """Crea lugar con menú vacío"""
        data = {
            'name': 'Sin Menú',
            'category': 'Comida',
            'menu': json.dumps([]),
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        
        assert response.status_code == 201
        place_id = response.json['id']
        
        get_response = client.get(f"/api/places/{place_id}")
        assert len(get_response.json['menu']) == 0

    def test_menu_item_price_precision(self, client):
        """Valida precisión de precios"""
        menu = [
            {"category": "Bebidas", "dish_name": "Jugo", "price": 3.75},
            {"category": "Alimentos", "dish_name": "Ensalada", "price": 12.99},
        ]
        
        data = {
            'name': 'Precios Precisos',
            'category': 'Comida',
            'menu': json.dumps(menu),
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        assert response.status_code == 201

    def test_schedule_with_complex_format(self, client):
        """Maneja horarios complejos"""
        schedule = {
            "lunes": "10:00-14:00, 18:00-23:00",
            "martes": "10:00-22:00",
            "sabado": "09:00-00:00",
            "domingo": "Cerrado"
        }
        
        data = {
            'name': 'Horario Complejo',
            'category': 'Comida',
            'schedule': json.dumps(schedule),
            'image': (None, ''),
        }
        
        response = client.post("/api/places", data=data)
        assert response.status_code == 201

    def test_place_category_variations(self, client):
        """Prueба diferentes categorías"""
        categories = [
            "Desayunos y Comidas",
            "Bebidas y Cafetería",
            "Snacks",
            "OtraCategoria"
        ]
        
        for category in categories:
            data = {
                'name': f'Lugar {category}',
                'category': category,
                'image': (None, ''),
            }
            response = client.post("/api/places", data=data)
            assert response.status_code == 201
