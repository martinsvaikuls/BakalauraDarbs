# routes/objects.py
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("objects", __name__, url_prefix="/objects")

OBJECTS = ["technicians", "tasks", "shops", "depots"]

@bp.get("/<object_type>/load")
def load_objects(object_type):
    if object_type not in OBJECTS:
        return jsonify({"error": "Unknown object type"}), 400

    items = current_app.db.load_csv(object_type)
    return jsonify({object_type: items}), 200


@bp.post("/<object_type>")
def create_object(object_type):
    if object_type not in OBJECTS:
        return jsonify({"error": "Unknown object type"}), 400

    payload = request.get_json() or {}


    # Convert lists/dicts to strings for CSV storage
    for key in payload:
        if isinstance(payload[key], (list, dict)):
            payload[key] = str(payload[key])

    current_app.db.insert(object_type, payload)
    return jsonify(payload), 201

@bp.delete("/<object_type>/<object_id>")
def delete_object(object_type, object_id):
    if object_type not in OBJECTS:
        return jsonify({"ok": False, "error": "Unknown object type"}), 400

    all_rows = current_app.db.get_all(object_type)
    new_rows = [r for r in all_rows if str(r.get("id")) != str(object_id)]

    if len(new_rows) == len(all_rows):
        return jsonify({"ok": False, "error": "Object not found"}), 404

    # Rewrite CSV
    if new_rows:
        current_app.db.update(object_type, "id", new_rows[0]["id"], new_rows[0])
        # But update rewrites only one row — better: write all rows manually
        import csv, os
        file_path = current_app.db._get_file(object_type)
        keys = new_rows[0].keys() if new_rows else all_rows[0].keys()
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys, delimiter=';')
            writer.writeheader()
            for row in new_rows:
                writer.writerow(row)
    else:
        # No rows left — just clear file
        file_path = current_app.db._get_file(object_type)
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_rows[0].keys(), delimiter=';')
            writer.writeheader()

    return jsonify({"ok": True})