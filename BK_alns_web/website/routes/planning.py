from flask import Blueprint, request, jsonify
from routes.algorithm.alns import ALNS_ALgorithm
import csv, json, threading
import os
import traceback
bp = Blueprint("planning", __name__, url_prefix="/planning")

ROUTES_FILE = "routes.csv"  # Your ALNS writes here
ITER_FILE = "iteration_info.json"
UNASIGN_FILE = "unassigned_tasks_info.json"

METRICS_FILE = "metrics.csv"

ALNS_RUNNING = False

def run_alns_background():

    global ALNS_RUNNING

    try:

        algo = ALNS_ALgorithm()
        algo.initialize()

    except Exception as e:
        print(f"ALNS background error: {e}")
        traceback.print_exc()

    finally:

        ALNS_RUNNING = False




@bp.post("/run")
def run_alns():
    global ALNS_RUNNING

    if ALNS_RUNNING:
        return jsonify({
            "ok": False,
            "error": "ALNS already running"
        })

    ALNS_RUNNING = True
    
    try:
        if os.path.exists(METRICS_FILE):
            os.remove(METRICS_FILE)
        # --- Clear old CSV ---
        if os.path.exists(ROUTES_FILE):
            os.remove(ROUTES_FILE)

        # Optionally reset iteration info
        if os.path.exists(ITER_FILE):
            os.remove(ITER_FILE)

        thread = threading.Thread(target=run_alns_background)
        thread.start()  # this will generate routes
        return jsonify({"ok": True, "message": "ALNS started in background"})

        

    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()})


# Return latest routes + iteration info
@bp.get("/routes/current")
def get_current_routes():
    routes = []
    iteration = {"current": 0, "total": 1}
    tasks = 0
    # Read current routes
    try:
        with open(ROUTES_FILE) as f:
            reader = csv.DictReader(f)
            for row in reader:
                routes.append({
                    "tech_id": row["tech_id"],
                    "coords": json.loads(row["route"])
                })
    except FileNotFoundError:
        pass

    # Read iteration info
    try:
        with open(ITER_FILE) as f:
            iteration = json.load(f)
    except FileNotFoundError:
        pass
        
        
    try:
        with open(UNASIGN_FILE) as f:
            content = f.read().strip()

            if content:
                tasks = json.loads(content)
            else:
                tasks = 0
    except FileNotFoundError:
        pass

    return jsonify({"routes": routes, "iteration": iteration, "tasks": tasks})

# Return final routes (optional)
@bp.route("/routes", methods=["GET"])
def get_routes():
    routes = []
    try:
        with open(ROUTES_FILE) as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                routes.append({
                    "tech_id": row["tech_id"],
                    "coords": json.loads(row["route"])
                })
        return jsonify(routes)
    except FileNotFoundError:
        return jsonify([])
    
@bp.get("/metrics/current")
def get_current_metrics():

    metrics = []

    try:
        with open("metrics.csv") as f:

            reader = csv.DictReader(f, delimiter=';')

            for row in reader:
                metrics.append(row)
        
    except FileNotFoundError:
        pass

    return jsonify(metrics)
