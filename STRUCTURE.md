# Estructura Modular del Backend

## Descripción

El backend de Cucei Foods ha sido refactorizado para una mejor mantenibilidad y escalabilidad. El código está organizado en módulos especializados en lugar de tener todo en un único archivo `main.py`.

## Estructura de Carpetas

```
cucei-foods-backend/
├── main.py                 # Punto de entrada principal (limpio)
├── requirements.txt
├── README.md
├── uploads/                # Directorio de archivos subidos
└── app/
    ├── __init__.py
    ├── config.py           # Configuración centralizada
    ├── models.py           # Modelos antiguos (se pueden deprecar)
    ├── utils.py            # Utilidades compartidas
    ├── db/
    │   ├── __init__.py
    │   └── models.py       # Modelos SQLAlchemy (User, Place, MenuItem, Comment)
    └── routes/             # Módulo de rutas
        ├── __init__.py     # Inicializa todas las rutas
        ├── auth.py         # Rutas de autenticación (Register, Login, Logout)
        ├── places.py       # Rutas de lugares (CRUD)
        ├── comments.py     # Rutas de comentarios (CRUD)
        └── uploads.py      # Rutas y Helper de uploads
```

## Módulos

### `main.py`
Punto de entrada de la aplicación. Contiene la factory function `create_app()` que:
- Configura Flask
- Inicializa CORS
- Configura la base de datos
- Registra todas las rutas
- Crea las tablas de base de datos

### `app/config.py`
Centraliza toda la configuración de la aplicación:
- URLs de base de datos (local y remota)
- Directorio de uploads
- Extensiones permitidas
- Secret key

### `app/routes/__init__.py`
Orquesta el registro de todas las rutas. La función `register_routes(api)` importa y registra las rutas de todos los módulos.

### `app/routes/auth.py`
Rutas de autenticación:
- **POST /api/register** - Registra un nuevo usuario
- **POST /api/login** - Inicia sesión
- **POST /api/logout** - Cierra sesión

### `app/routes/places.py`
Rutas de lugares:
- **GET /api/places** - Lista todos los lugares (con filtro de categoría)
- **POST /api/places** - Crea un nuevo lugar
- **GET /api/places/<id>** - Obtiene un lugar específico
- **PUT /api/places/<id>** - Actualiza un lugar
- **DELETE /api/places/<id>** - Elimina un lugar
- **GET /api/places/counts** - Obtiene conteo de lugares por categoría

### `app/routes/comments.py`
Rutas de comentarios:
- **GET /api/places/<place_id>/comments** - Lista comentarios de un lugar
- **POST /api/places/<place_id>/comments** - Agrega un comentario
- **PUT /api/comments/<id>** - Actualiza un comentario
- **DELETE /api/comments/<id>** - Elimina un comentario

### `app/routes/uploads.py`
Manejo de archivos:
- **GET /uploads/<filename>** - Sirve un archivo subido
- Funciones helper para validar y guardar archivos

### `app/db/models.py`
Modelos SQLAlchemy:
- `User` - Usuario del sistema
- `Place` - Lugar/Restaurante
- `MenuItem` - Artículo del menú
- `Comment` - Comentario en un lugar

### `app/utils.py`
Funciones auxiliares compartidas:
- `update_place_rating()` - Actualiza la calificación promedio de un lugar

## Ventajas de la Estructura Modular

✅ **Separación de responsabilidades** - Cada módulo tiene un propósito específico
✅ **Mantenibilidad** - Más fácil de entender y modificar
✅ **Escalabilidad** - Agregar nuevas rutas es trivial
✅ **Testabilidad** - Cada módulo se puede probar independientemente
✅ **Reutilización** - Las funciones helper se comparten fácilmente
✅ **Claridad** - El código es más legible y autodocumentado

## Cómo Agregar Nuevas Rutas

1. Crear un nuevo módulo en `app/routes/` (e.g., `app/routes/orders.py`)
2. Implementar la función `create_xxx_routes(api)` que retorna el namespace
3. Importar y registrar en `app/routes/__init__.py`:
   ```python
   from app.routes.orders import create_orders_routes
   
   def register_routes(api: Api):
       # ... otras rutas ...
       create_orders_routes(api)
   ```

## Ejecución

```bash
# Desarrollo
python main.py

# Con variables de entorno
export DATABASE_URL=postgresql://user:pass@host/db
export SECRET_KEY=tu_secret_key
python main.py
```

La API estará disponible en `http://localhost:5000` y la documentación en `http://localhost:5000/docs`.
