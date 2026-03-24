import os
from flask import send_from_directory
from flask_restx import Resource, Api
from werkzeug.utils import secure_filename
from app.config import Config


def create_upload_routes(api: Api):
    """Crea las rutas de uploads"""
    
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
            return send_from_directory(Config.UPLOAD_FOLDER, filename)


def allowed_file(filename: str) -> bool:
    """Verifica si el archivo tiene una extensión permitida"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def save_upload_file(file) -> str:
    """
    Guarda un archivo subido y retorna su URL.
    
    Args:
        file: Objeto de archivo de Flask
        
    Returns:
        str: URL del archivo guardado o string vacío si falla
    """
    if not file or not allowed_file(file.filename):
        return ""
    
    filename = secure_filename(file.filename)
    image_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(image_path)
    return f"/uploads/{filename}"
