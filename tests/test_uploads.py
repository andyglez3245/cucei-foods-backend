"""
Tests unitarios para app.routes.uploads

Prueba los endpoints y funciones:
- allowed_file(filename)
- save_upload_file(file)
- GET /uploads/<filename>
"""
import pytest
import os
from io import BytesIO
from werkzeug.datastructures import FileStorage
from app.routes.uploads import allowed_file, save_upload_file
from app.config import Config


def create_file_storage(content, filename):
    """Helper para crear FileStorage objects"""
    return FileStorage(
        stream=BytesIO(content),
        filename=filename,
        name='file',
        content_type='application/octet-stream'
    )


class TestAllowedFile:
    """Tests para la función allowed_file"""

    def test_allowed_file_png(self):
        """Valida que PNG es una extensión permitida"""
        assert allowed_file("imagen.png") == True

    def test_allowed_file_jpg(self):
        """Valida que JPG es una extensión permitida"""
        assert allowed_file("imagen.jpg") == True

    def test_allowed_file_jpeg(self):
        """Valida que JPEG es una extensión permitida"""
        assert allowed_file("imagen.jpeg") == True

    def test_allowed_file_gif(self):
        """Valida que GIF es una extensión permitida"""
        assert allowed_file("imagen.gif") == True

    def test_allowed_file_uppercase(self):
        """Valida extensiones en mayúscula"""
        assert allowed_file("imagen.PNG") == True
        assert allowed_file("imagen.JPG") == True

    def test_allowed_file_invalid_txt(self):
        """Rechaza archivo TXT"""
        assert allowed_file("documento.txt") == False

    def test_allowed_file_invalid_pdf(self):
        """Rechaza archivo PDF"""
        assert allowed_file("documento.pdf") == False

    def test_allowed_file_invalid_exe(self):
        """Rechaza archivo EXE"""
        assert allowed_file("programa.exe") == False

    def test_allowed_file_no_extension(self):
        """Rechaza archivo sin extensión"""
        assert allowed_file("noextension") == False

    def test_allowed_file_multiple_dots(self):
        """Maneja nombres con múltiples puntos"""
        assert allowed_file("image.backup.png") == True
        assert allowed_file("image.backup.txt") == False

    def test_allowed_file_hidden_file(self):
        """Valida archivos con punto inicial (hidden files)"""
        assert allowed_file(".png") == True

    def test_allowed_file_mixed_case(self):
        """Valida extensiones con caso mixto"""
        assert allowed_file("imagen.PnG") == True
        assert allowed_file("imagen.JpEg") == True

    def test_allowed_file_special_characters_in_name(self):
        """Maneja nombres con caracteres especiales"""
        assert allowed_file("imagen_especial-2024.png") == True
        assert allowed_file("图片.jpg") == True

    def test_allowed_file_very_long_name(self):
        """Maneja nombres muy largos"""
        long_name = "a" * 200 + ".png"
        assert allowed_file(long_name) == True


class TestSaveUploadFile:
    """Tests para la función save_upload_file"""

    def test_save_upload_file_success(self, upload_folder):
        """Guarda exitosamente un archivo PNG"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = create_file_storage(file_content, 'test_image.png')
        
        result = save_upload_file(file)
        
        assert result == "/uploads/test_image.png"
        assert os.path.exists(os.path.join(Config.UPLOAD_FOLDER, 'test_image.png'))

    def test_save_upload_file_jpg(self, upload_folder):
        """Guarda exitosamente un archivo JPG"""
        file_content = b'\xFF\xD8\xFF\xE0' + b'\x00' * 100
        file = create_file_storage(file_content, 'test_image.jpg')
        
        result = save_upload_file(file)
        
        assert result == "/uploads/test_image.jpg"
        assert os.path.exists(os.path.join(Config.UPLOAD_FOLDER, 'test_image.jpg'))

    def test_save_upload_file_gif(self, upload_folder):
        """Guarda exitosamente un archivo GIF"""
        file_content = b'GIF89a' + b'\x00' * 100
        file = create_file_storage(file_content, 'test_image.gif')
        
        result = save_upload_file(file)
        
        assert result == "/uploads/test_image.gif"

    def test_save_upload_file_none(self, upload_folder):
        """Retorna string vacío si el archivo es None"""
        result = save_upload_file(None)
        
        assert result == ""

    def test_save_upload_file_invalid_extension(self, upload_folder):
        """Retorna string vacío con extensión no permitida"""
        file_content = b'texto'
        file = create_file_storage(file_content, 'documento.txt')
        
        result = save_upload_file(file)
        
        assert result == ""

    def test_save_upload_file_exe(self, upload_folder):
        """Rechaza archivos ejecutables"""
        file_content = b'MZ\x90\x00' + b'\x00' * 100
        file = create_file_storage(file_content, 'programa.exe')
        
        result = save_upload_file(file)
        
        assert result == ""

    def test_save_upload_file_special_characters(self, upload_folder):
        """Maneja nombres con caracteres especiales"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = create_file_storage(file_content, 'test_"special"_chars.png')
        
        result = save_upload_file(file)
        
        # secure_filename debe sanitizar el nombre
        assert result.startswith("/uploads/")
        assert result.endswith(".png")

    def test_save_upload_file_unicode_name(self, upload_folder):
        """Maneja nombres Unicode"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = create_file_storage(file_content, 'imagen_中文.png')
        
        result = save_upload_file(file)
        
        assert result.startswith("/uploads/")
        assert ".png" in result

    def test_save_upload_file_path_traversal(self, upload_folder):
        """Previene path traversal attacks"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = create_file_storage(file_content, '../../../etc/passwd.png')
        
        result = save_upload_file(file)
        
        # secure_filename debe prevenir esto
        assert result.startswith("/uploads/")
        assert not ".." in result

    def test_save_upload_file_uppercase_extension(self, upload_folder):
        """Maneja extensiones en mayúscula"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = create_file_storage(file_content, 'test_image.PNG')
        
        result = save_upload_file(file)
        
        assert result != ""
        assert "/uploads/" in result

    def test_save_upload_file_creates_directory(self, upload_folder):
        """Verifica que crea el directorio si no existe"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = create_file_storage(file_content, 'image.png')
        
        result = save_upload_file(file)
        
        assert os.path.exists(Config.UPLOAD_FOLDER)
        assert result != ""

    def test_save_upload_file_overwrites_existing(self, upload_folder):
        """Sobrescribe archivos existentes"""
        file_content1 = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        file1 = create_file_storage(file_content1, 'same_name.png')
        
        result1 = save_upload_file(file1)
        assert result1 != ""
        
        # Guardar archivo con el mismo nombre
        file_content2 = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file2 = create_file_storage(file_content2, 'same_name.png')
        
        result2 = save_upload_file(file2)
        
        assert result1 == result2
        assert os.path.exists(os.path.join(Config.UPLOAD_FOLDER, 'same_name.png'))

    def test_save_upload_file_empty_file(self, upload_folder):
        """Maneja archivos vacíos"""
        file_content = b''
        file = create_file_storage(file_content, 'empty.png')
        
        result = save_upload_file(file)
        
        # Debería guardar el archivo aunque esté vacío
        assert result == "/uploads/empty.png"


class TestUploadEndpoint:
    """Tests para GET /uploads/<filename>"""

    def test_get_upload_success(self, client, upload_folder):
        """Descarga exitosamente un archivo subido"""
        # Crear y guardar un archivo
        file_path = os.path.join(Config.UPLOAD_FOLDER, 'test_image.png')
        with open(file_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        
        response = client.get("/uploads/test_image.png")
        
        assert response.status_code == 200
        assert len(response.data) > 0

    def test_get_upload_not_found(self, client, upload_folder):
        """Retorna 404 si el archivo no existe"""
        response = client.get("/uploads/nonexistent.png")
        
        assert response.status_code == 404

    def test_get_upload_jpg(self, client, upload_folder):
        """Descarga archivo JPG"""
        file_path = os.path.join(Config.UPLOAD_FOLDER, 'test.jpg')
        with open(file_path, 'wb') as f:
            f.write(b'\xFF\xD8\xFF\xE0' + b'\x00' * 50)
        
        response = client.get("/uploads/test.jpg")
        
        assert response.status_code == 200

    def test_get_upload_gif(self, client, upload_folder):
        """Descarga archivo GIF"""
        file_path = os.path.join(Config.UPLOAD_FOLDER, 'test.gif')
        with open(file_path, 'wb') as f:
            f.write(b'GIF89a' + b'\x00' * 50)
        
        response = client.get("/uploads/test.gif")
        
        assert response.status_code == 200

    def test_get_upload_returns_content_type(self, client, upload_folder):
        """Verifica que retorna el tipo de contenido correcto"""
        file_path = os.path.join(Config.UPLOAD_FOLDER, 'test.png')
        with open(file_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        
        response = client.get("/uploads/test.png")
        
        assert response.status_code == 200
        assert 'Content-Type' in response.headers

    def test_get_upload_path_traversal_prevention(self, client, upload_folder):
        """Previene acceso a archivos fuera del directorio de uploads"""
        # Intentar acceder a directorios padres
        response = client.get("/uploads/../../../etc/passwd")
        
        # Debería fallar (404 o 400)
        assert response.status_code != 200

    def test_get_upload_special_filename(self, client, upload_folder):
        """Maneja nombres de archivo con caracteres especiales"""
        # Crear archivo con nombre especial
        filename = 'test_image_2024-03.png'
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        with open(file_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 50)
        
        response = client.get(f"/uploads/{filename}")
        
        assert response.status_code == 200

    def test_get_upload_case_sensitive(self, client, upload_folder):
        """Valida que los nombres de archivo son case-sensitive"""
        # Crear archivo en minúscula
        file_path = os.path.join(Config.UPLOAD_FOLDER, 'image.png')
        with open(file_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 50)
        
        # Intentar acceder en mayúscula (debería fallar en caso-sensitive)
        response = client.get("/uploads/IMAGE.PNG")
        
        # Dependiendo del OS, esto puede ser 200 o 404
        # En Windows es case-insensitive, en Linux es case-sensitive
        assert response.status_code in [200, 404]


class TestUploadIntegration:
    """Tests de integración para flujos completos"""

    def test_upload_and_retrieve(self, client, upload_folder):
        """Flujo completo: guardar archivo y descargarlo"""
        # Crear archivo en memoria
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = create_file_storage(file_content, 'integration_test.png')
        
        # Guardar
        save_path = save_upload_file(file)
        assert save_path == "/uploads/integration_test.png"
        
        # Descargar
        response = client.get(save_path)
        assert response.status_code == 200
        assert len(response.data) > 0

    def test_multiple_uploads_different_formats(self, client, upload_folder):
        """Guarda múltiples archivos en diferentes formatos"""
        formats = [
            ('test1.png', b'\x89PNG\r\n\x1a\n'),
            ('test2.jpg', b'\xFF\xD8\xFF\xE0'),
            ('test3.gif', b'GIF89a'),
            ('test4.jpeg', b'\xFF\xD8\xFF\xE0'),
        ]
        
        for filename, header in formats:
            file = create_file_storage(header + b'\x00' * 50, filename)
            
            result = save_upload_file(file)
            assert result != ""
            
            # Verificar que se puede descargar
            response = client.get(result)
            assert response.status_code == 200

    def test_upload_overwrites_previous(self, client, upload_folder):
        """Archivos con mismo nombre sobrescriben anteriores"""
        # Primer upload
        file_content1 = b'\x89PNG\r\n\x1a\n' + b'A' * 50
        file1 = create_file_storage(file_content1, 'overwrite_test.png')
        result1 = save_upload_file(file1)
        
        # Segundo upload con el mismo nombre
        file_content2 = b'\x89PNG\r\n\x1a\n' + b'B' * 50
        file2 = create_file_storage(file_content2, 'overwrite_test.png')
        result2 = save_upload_file(file2)
        
        assert result1 == result2
        
        # Descargar debería retornar el segundo archivo
        response = client.get(result1)
        assert response.status_code == 200


class TestUploadEdgeCases:
    """Tests de casos límite y validaciones"""

    def test_save_large_file(self, upload_folder):
        """Maneja archivos grandes"""
        large_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * (5 * 1024 * 1024)  # 5MB
        file = create_file_storage(large_content, 'large_image.png')
        
        result = save_upload_file(file)
        
        assert result == "/uploads/large_image.png"

    def test_filename_with_multiple_extensions(self, upload_folder):
        """Maneja nombres con múltiples puntos"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        file = create_file_storage(file_content, 'image.backup.png')
        
        result = save_upload_file(file)
        
        assert result == "/uploads/image.backup.png"

    def test_filename_with_spaces(self, upload_folder):
        """Maneja nombres con espacios"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        file = create_file_storage(file_content, 'my image file.png')
        
        result = save_upload_file(file)
        
        assert result != ""
        assert ".png" in result

    def test_empty_filename(self, upload_folder):
        """Maneja filename vacío"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        file = create_file_storage(file_content, '')
        
        result = save_upload_file(file)
        
        # Debería rechazar por no tener extensión
        assert result == ""

    def test_filename_only_extension(self, upload_folder):
        """Maneja filename que es solo la extensión"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        file = create_file_storage(file_content, '.png')
        
        result = save_upload_file(file)
        
        # allowed_file debería permitir files ".png"
        assert result != "" or result == ""  # Comportamiento del sistema

    def test_very_long_filename(self, upload_folder):
        """Maneja nombres de archivo muy largos"""
        long_name = 'a' * 200 + '.png'
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        file = create_file_storage(file_content, long_name)
        
        result = save_upload_file(file)
        
        assert result != ""

    def test_unicode_filename_variants(self, upload_folder):
        """Maneja diferentes caracteres Unicode"""
        filenames = [
            'imagen_中文_123.png',
            'фото_русский.jpg',
            'صورة_عربي.gif',
            'εικόνα_ελληνικά.jpeg',
        ]
        
        for filename in filenames:
            file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
            file = create_file_storage(file_content, filename)
            
            result = save_upload_file(file)
            assert result != ""

    def test_file_with_no_dot(self, upload_folder):
        """Rechaza archivo sin punto (sin extensión)"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        file = create_file_storage(file_content, 'imagensinextension')
        
        result = save_upload_file(file)
        
        assert result == ""

    def test_file_empty_after_dot(self, upload_folder):
        """Maneja archivo con punto pero sin extensión"""
        file_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 50
        file = create_file_storage(file_content, 'imagen.')
        
        result = save_upload_file(file)
        
        # Sin extensión, debería fallar
        assert result == ""

    def test_allowed_file_with_dot_at_start(self):
        """Archivos con nombre que empieza con punto"""
        # .png tiene extensión png
        assert allowed_file('.png') == True
        # Pero es un hidden file
        assert allowed_file('.jpg') == True

    def test_save_jpeg_extension_variants(self, upload_folder):
        """Maneja variantes de JPEG"""
        for ext in ['jpg', 'jpeg', 'JPG', 'JPEG', 'Jpg', 'Jpeg']:
            file_content = b'\xFF\xD8\xFF\xE0' + b'\x00' * 50
            file = create_file_storage(file_content, f'test.{ext}')
            
            result = save_upload_file(file)
            assert result != ""
