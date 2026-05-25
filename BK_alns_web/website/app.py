from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

#from routes.technicians import bp as technicians_bp
from routes.planning import bp as planning_bp
#from routes.restocking_locations import bp as restocking_locations_bp
from routes.clients import bp as clients_bp
#from routes.tasks import bp as tasks_bp
from routes.objects import bp as objects_bp

from csv_db import CSVDB

import json
import os

JWT_SECRET = "your-secret-key"
JWT_ALGORITHM = "HS256"

def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="")
    CORS(app)  # Enable CORS for frontend

    app.db = CSVDB(folder="csv")
    
    tables = {
        "tasks": ["id","priority","skills","duration","start_tw","end_tw","created","relevant_technician_ids","lat","long","resources","income"],
        "technicians": ["id","master_id","skills","start_tw","end_tw","home_lat","home_long","resources"],
        "shops": ["id","resources","start_tw","end_tw","lat","long"],
        "depots": ["id","resources","start_tw","end_tw","lat","long"],
        "distances_cache": ["a_nodetype","a_id","b_nodetype","b_id","distance","duration"],
        "weather_cache": ["a_nodetype","a_id","b_nodetype","b_id","time","cost_factor","slow_downFactor"],
        "users": ["client_id","client_name", "email", "hash_password"]
    }

    for table_name, fields in tables.items():
        app.db.ensure_table(table_name, fields)

    @app.get("/health")
    def health():
        return jsonify({"ok": True})
    
    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    #app.register_blueprint(technicians_bp)
    #app.register_blueprint(tasks_bp)
    app.register_blueprint(planning_bp)    
    #app.register_blueprint(restocking_locations_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(objects_bp)

    
    return app

app = create_app()

if __name__ == "__main__":

    app.run(debug=True, port=5001)
