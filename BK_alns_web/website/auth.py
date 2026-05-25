from functools import wraps
from flask import request, jsonify, current_app
import jwt
import os

JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
    
        auth_header = request.headers.get("Authorization")
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  
            except IndexError:
                return jsonify({"error": "Invalid token format"}), 401
        
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        
        try:
   
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
       
            request.current_user = {
                "client_id": payload["client_id"],
                "email": payload["email"]
            }
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function
