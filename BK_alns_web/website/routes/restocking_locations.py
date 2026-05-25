from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("technicians", __name__, url_prefix="/technicians")

@bp.get("")
def list_printers():

    printers = current_app.db.list_printers()
    return jsonify(printers)

@bp.post("")
def create_printer():

    payload = request.get_json() or {}
    required_fields = ["model", "base_speed"]
    missing_fields = [field for field in required_fields if field not in payload]

    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400
    
    row = current_app.db.create_printer(payload)
    return jsonify(row), 201