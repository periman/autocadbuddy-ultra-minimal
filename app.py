#!/usr/bin/env python3
"""
AutoCad_Buddy - Backend API
This script implements the backend API for the AutoCad_Buddy service.
"""

import os
import sys
import json
import time
import uuid
import logging
import tempfile
import traceback
from pathlib import Path
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AutoCad_Buddy_API')

# Import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import main as converter
    import stl_viewer
except ImportError as e:
    logger.error(f"Failed to import local modules: {e}")
    logger.error("Make sure main.py and stl_viewer.py are in the project directory.")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__, static_folder='../website', static_url_path='')
CORS(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# Configure file upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
ALLOWED_EXTENSIONS = {'svg', 'png', 'jpg', 'jpeg', 'pdf', 'dwg', 'dxf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simple in-memory database for demo purposes
# In production, this would be replaced with a proper database
users_db = {}
models_db = {}
equipment_db = {
    "kitchen": {
        "refrigerator": [
            {"name": "Commercial Refrigerator", "dimensions": {"width": 120, "depth": 80, "height": 200}, "regions": ["US", "EU", "Asia"]},
            {"name": "Compact Refrigerator", "dimensions": {"width": 60, "depth": 60, "height": 150}, "regions": ["US", "EU", "Asia"]},
        ],
        "oven": [
            {"name": "Commercial Convection Oven", "dimensions": {"width": 90, "depth": 80, "height": 60}, "regions": ["US", "EU", "Asia"]},
            {"name": "Pizza Oven", "dimensions": {"width": 120, "depth": 120, "height": 50}, "regions": ["US", "EU", "Asia"]},
        ],
        "sink": [
            {"name": "Double Basin Sink", "dimensions": {"width": 100, "depth": 60, "height": 40}, "regions": ["US", "EU", "Asia"]},
            {"name": "Triple Basin Sink", "dimensions": {"width": 150, "depth": 60, "height": 40}, "regions": ["US", "EU", "Asia"]},
        ],
        "counter": [
            {"name": "Stainless Steel Counter", "dimensions": {"width": 180, "depth": 70, "height": 90}, "regions": ["US", "EU", "Asia"]},
            {"name": "Prep Table", "dimensions": {"width": 120, "depth": 70, "height": 90}, "regions": ["US", "EU", "Asia"]},
        ],
        "stove": [
            {"name": "6-Burner Gas Range", "dimensions": {"width": 90, "depth": 80, "height": 90}, "regions": ["US", "EU", "Asia"]},
            {"name": "Induction Cooktop", "dimensions": {"width": 90, "depth": 60, "height": 10}, "regions": ["US", "EU", "Asia"]},
        ]
    },
    "restaurant": {
        "table": [
            {"name": "4-Person Table", "dimensions": {"width": 80, "depth": 80, "height": 75}, "regions": ["US", "EU", "Asia"]},
            {"name": "2-Person Table", "dimensions": {"width": 60, "depth": 60, "height": 75}, "regions": ["US", "EU", "Asia"]},
        ],
        "chair": [
            {"name": "Dining Chair", "dimensions": {"width": 45, "depth": 45, "height": 90}, "regions": ["US", "EU", "Asia"]},
            {"name": "Bar Stool", "dimensions": {"width": 40, "depth": 40, "height": 110}, "regions": ["US", "EU", "Asia"]},
        ],
        "bar": [
            {"name": "Bar Counter", "dimensions": {"width": 200, "depth": 70, "height": 110}, "regions": ["US", "EU", "Asia"]},
            {"name": "Service Station", "dimensions": {"width": 120, "depth": 60, "height": 90}, "regions": ["US", "EU", "Asia"]},
        ]
    }
}

def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the main HTML page."""
    return app.send_static_file('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
    
    email = data['email']
    
    if email in users_db:
        return jsonify({"error": "User already exists"}), 400
    
    users_db[email] = {
        "email": email,
        "password_hash": generate_password_hash(data['password']),
        "name": data.get('name', ''),
        "created_at": datetime.now().isoformat(),
        "models": []
    }
    
    access_token = create_access_token(identity=email)
    
    return jsonify({
        "message": "User registered successfully",
        "access_token": access_token,
        "user": {
            "email": email,
            "name": users_db[email]["name"]
        }
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Login a user."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
    
    email = data['email']
    
    if email not in users_db:
        return jsonify({"error": "Invalid email or password"}), 401
    
    if not check_password_hash(users_db[email]["password_hash"], data['password']):
        return jsonify({"error": "Invalid email or password"}), 401
    
    access_token = create_access_token(identity=email)
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "email": email,
            "name": users_db[email]["name"]
        }
    }), 200

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_user():
    """Get user information."""
    current_user = get_jwt_identity()
    
    if current_user not in users_db:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "email": current_user,
        "name": users_db[current_user]["name"],
        "models": users_db[current_user]["models"]
    }), 200

@app.route('/api/convert', methods=['POST'])
@jwt_required()
def convert_file():
    """Convert a 2D file to 3D."""
    current_user = get_jwt_identity()
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Check if file is allowed
    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    try:
        # Generate unique ID for the model
        model_id = str(uuid.uuid4())
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{model_id}_{filename}")
        file.save(file_path)
        
        # Convert 2D to 3D
        stl_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{model_id}.stl")
        stl_path, gltf_path = converter.convert_to_3d(file_path, stl_path)
        
        # Create 3D viewer
        viewer_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'viewers')
        os.makedirs(viewer_dir, exist_ok=True)
        viewer_path = stl_viewer.create_3d_viewer(stl_path, viewer_dir, f"{model_id}_viewer")
        
        # Store model information
        models_db[model_id] = {
            "id": model_id,
            "user_id": current_user,
            "original_filename": filename,
            "original_path": file_path,
            "stl_path": stl_path,
            "gltf_path": gltf_path if 'gltf_path' in locals() else None,
            "viewer_path": viewer_path,
            "created_at": datetime.now().isoformat()
        }
        
        # Add model to user's models
        users_db[current_user]["models"].append(model_id)
        
        # Return success response
        return jsonify({
            "success": True,
            "model_id": model_id,
            "viewer_url": f"/api/viewer/{model_id}",
            "download_url": f"/api/download/{model_id}"
        }), 200
    
    except Exception as e:
        logger.error(f"Error converting file: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/models', methods=['GET'])
@jwt_required()
def get_models():
    """Get user's models."""
    current_user = get_jwt_identity()
    
    user_models = []
    for model_id in users_db[current_user]["models"]:
        if model_id in models_db:
            model = models_db[model_id]
            user_models.append({
                "id": model["id"],
                "filename": model["original_filename"],
                "created_at": model["created_at"],
                "viewer_url": f"/api/viewer/{model_id}",
                "download_url": f"/api/download/{model_id}"
            })
    
    return jsonify(user_models), 200

@app.route('/api/viewer/<model_id>', methods=['GET'])
def get_viewer(model_id):
    """Get the 3D viewer for a model."""
    if model_id not in models_db:
        return jsonify({"error": "Model not found"}), 404
    
    viewer_path = models_db[model_id]["viewer_path"]
    viewer_dir = os.path.dirname(viewer_path)
    viewer_file = os.path.basename(viewer_path)
    
    return send_from_directory(viewer_dir, viewer_file)

@app.route('/api/download/<model_id>', methods=['GET'])
def download_model(model_id):
    """Download a 3D model."""
    if model_id not in models_db:
        return jsonify({"error": "Model not found"}), 404
    
    stl_path = models_db[model_id]["stl_path"]
    
    return send_file(
        stl_path,
        as_attachment=True,
        download_name=f"{model_id}.stl",
        mimetype='application/octet-stream'
    )

@app.route('/api/equipment/categories', methods=['GET'])
def get_equipment_categories():
    """Get equipment categories."""
    return jsonify(list(equipment_db.keys())), 200

@app.route('/api/equipment/types', methods=['GET'])
def get_equipment_types():
    """Get equipment types for a category."""
    category = request.args.get('category', 'kitchen')
    
    if category not in equipment_db:
        return jsonify({"error": "Category not found"}), 404
    
    return jsonify(list(equipment_db[category].keys())), 200

@app.route('/api/equipment/search', methods=['GET'])
def search_equipment():
    """Search for equipment."""
    category = request.args.get('category', 'kitchen')
    equipment_type = request.args.get('type')
    region = request.args.get('region', 'US')
    
    if category not in equipment_db:
        return jsonify({"error": "Category not found"}), 404
    
    if equipment_type and equipment_type not in equipment_db[category]:
        return jsonify({"error": "Equipment type not found"}), 404
    
    results = []
    
    if equipment_type:
        # Search for specific equipment type
        for item in equipment_db[category][equipment_type]:
            if region in item["regions"]:
                results.append(item)
    else:
        # Search all equipment types in category
        for eq_type, items in equipment_db[category].items():
            for item in items:
                if region in item["regions"]:
                    item_copy = item.copy()
                    item_copy["type"] = eq_type
                    results.append(item_copy)
    
    return jsonify(results), 200

@app.route('/api/location', methods=['GET'])
def get_user_location():
    """Get user's location based on IP address."""
    # In a real application, this would use a geolocation service
    # For demo purposes, we'll return a default location
    return jsonify({
        "country": "US",
        "region": "California",
        "city": "San Francisco"
    }), 200

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors by serving the index page for client-side routing."""
    return app.send_static_file('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
