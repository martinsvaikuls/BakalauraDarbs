from flask import Blueprint, request, jsonify, current_app
import hashlib
import jwt
from datetime import datetime, timedelta
import os

bp = Blueprint("clients", __name__, url_prefix="/clients")

# Simple JWT secret key (in production, use environment variable)
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def hash_password(password: str) -> str:
    """Hash a password using SHA256 (simple for POC)"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(client_id: int, email: str) -> str:
    """Generate JWT token for authenticated user"""
    payload = {
        "client_id": client_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

@bp.post("/register")
def register():
    payload = request.get_json() or {}

    required = ["client_name", "email", "password"]
    missing = [k for k in required if k not in payload]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    # Check existing user
    existing = current_app.db.get_client_by_email(payload["email"])
    if existing:
        return jsonify({"error": "Email already registered"}), 400

    # Build DB row (STRICT schema)
    client_data = {
        "client_name": payload["client_name"],
        "email": payload["email"],
        "hash_password": hash_password(payload["password"])
    }

    # Insert into CSV (this generates client_id internally)
    client = current_app.db.create_client(client_data)

    # SAFETY: ensure key exists
    client_id = client.get("client_id")
    if not client_id:
        return jsonify({"error": "Internal error: missing client_id"}), 500

    token = generate_token(client_id, client["email"])

    return jsonify({
        "client_id": client_id,
        "client_name": client["client_name"],
        "email": client["email"],
        "token": token
    }), 201

@bp.post("/login")
def login():
    payload = request.get_json() or {}

    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    client = current_app.db.get_client_by_email(email)

    if not client:
        return jsonify({"error": "Invalid email or password"}), 401

    hashed_password = hash_password(password)

    if client.get("hash_password") != hashed_password:
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(client["client_id"], client["email"])

    return jsonify({
        "client_id": client["client_id"],
        "client_name": client["client_name"],
        "email": client["email"],
        "token": token
    }), 200

@bp.get("")
def list_clients():
    """List all clients (for admin/testing - remove auth check for POC)"""
    clients = current_app.db.list_clients()
    # Remove password hashes from response
    for client in clients:
        client.pop("hash_password", None)
    return jsonify(clients)
    