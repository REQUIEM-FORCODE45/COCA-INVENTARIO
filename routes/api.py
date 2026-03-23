import os
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from services.excel_service import excel_service

api_bp = Blueprint("api", __name__, url_prefix="/api")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "public", "uploads")
ALLOWED_EXTENSIONS = {"xlsx"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@api_bp.route("/files/status", methods=["GET"])
def files_status():
    inventario = os.path.join(UPLOAD_FOLDER, "inventario.xlsx")
    plantilla = os.path.join(UPLOAD_FOLDER, "plantilla.xlsx")
    
    has_files = os.path.exists(inventario) and os.path.exists(plantilla)
    fecha = None
    
    if has_files:
        mtime = os.path.getmtime(inventario)
        from datetime import datetime
        fecha = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
    
    return jsonify({
        "success": True,
        "has_files": has_files,
        "fecha": fecha
    })


@api_bp.route("/files/upload", methods=["POST"])
def upload_files():
    if "inventario" not in request.files or "plantilla" not in request.files:
        return jsonify({"success": False, "error": "Faltan archivos"}), 400
    
    inventario = request.files["inventario"]
    plantilla = request.files["plantilla"]
    
    if inventario.filename == "" or plantilla.filename == "":
        return jsonify({"success": False, "error": "Archivos vacíos"}), 400
    
    inventario_path = os.path.join(UPLOAD_FOLDER, "inventario.xlsx")
    plantilla_path = os.path.join(UPLOAD_FOLDER, "plantilla.xlsx")
    
    inventario.save(inventario_path)
    plantilla.save(plantilla_path)
    
    excel_service.clear_cache()
    
    return jsonify({"success": True})


@api_bp.route("/files/clear", methods=["POST"])
def clear_files():
    inventario = os.path.join(UPLOAD_FOLDER, "inventario.xlsx")
    plantilla = os.path.join(UPLOAD_FOLDER, "plantilla.xlsx")
    
    if os.path.exists(inventario):
        os.remove(inventario)
    if os.path.exists(plantilla):
        os.remove(plantilla)
    
    excel_service.clear_cache()
    
    return jsonify({"success": True})


@api_bp.route("/inventario", methods=["GET"])
def get_inventario():
    inventario = os.path.join(UPLOAD_FOLDER, "inventario.xlsx")
    plantilla = os.path.join(UPLOAD_FOLDER, "plantilla.xlsx")
    
    if not (os.path.exists(inventario) and os.path.exists(plantilla)):
        return jsonify({"success": False, "error": "Archivos no encontrados"}), 404
    
    excel_service.set_paths(inventario, plantilla)
    data = excel_service.get_inventario_data()
    return jsonify({"success": True, "data": data, "total": len(data)})
