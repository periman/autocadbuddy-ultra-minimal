from flask import Flask, request, jsonify, send_file, render_template, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sys
import json
import uuid
import shutil
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

# Configure CORS to allow requests from any origin for development
CORS(app)

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
jwt = JWTManager(app)

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'svg', 'png', 'jpg', 'jpeg', 'pdf', 'dwg', 'dxf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simulated database
USERS_DB = {}
MODELS_DB = {}
EQUIPMENT_DB = {
    'kitchen': {
        'types': ['refrigerator', 'oven', 'dishwasher', 'sink', 'counter', 'cabinet', 'island'],
        'items': [
            {
                'name': 'Commercial Refrigerator',
                'type': 'refrigerator',
                'dimensions': {'width': 120, 'depth': 80, 'height': 200},
                'regions': ['US', 'EU', 'Asia']
            },
            {
                'name': 'Convection Oven',
                'type': 'oven',
                'dimensions': {'width': 90, 'depth': 80, 'height': 60},
                'regions': ['US', 'EU', 'Asia']
            },
            {
                'name': 'Industrial Dishwasher',
                'type': 'dishwasher',
                'dimensions': {'width': 60, 'depth': 60, 'height': 85},
                'regions': ['US', 'EU']
            },
            {
                'name': 'Double Basin Sink',
                'type': 'sink',
                'dimensions': {'width': 100, 'depth': 60, 'height': 40},
                'regions': ['US', 'EU', 'Asia']
            },
            {
                'name': 'Stainless Steel Counter',
                'type': 'counter',
                'dimensions': {'width': 180, 'depth': 70, 'height': 90},
                'regions': ['US', 'EU', 'Asia']
            },
            {
                'name': 'Wall Cabinet',
                'type': 'cabinet',
                'dimensions': {'width': 60, 'depth': 35, 'height': 70},
                'regions': ['US', 'EU', 'Asia']
            },
            {
                'name': 'Kitchen Island',
                'type': 'island',
                'dimensions': {'width': 150, 'depth': 90, 'height': 90},
                'regions': ['US', 'EU']
            }
        ]
    },
    'restaurant': {
        'types': ['table', 'chair', 'booth', 'bar', 'serving_station', 'host_stand'],
        'items': [
            {
                'name': 'Dining Table',
                'type': 'table',
                'dimensions': {'width': 80, 'depth': 80, 'height': 75},
                'regions': ['US', 'EU', 'Asia']
            },
            {
                'name': 'Dining Chair',
                'type': 'chair',
                'dimensions': {'width': 45, 'depth': 50, 'height': 90},
                'regions': ['US', 'EU', 'Asia']
            },
            {
                'name': 'Corner Booth',
                'type': 'booth',
                'dimensions': {'width': 150, 'depth': 150, 'height': 110},
                'regions': ['US', 'EU']
            },
            {
                'name': 'Bar Counter',
                'type': 'bar',
                'dimensions': {'width': 200, 'depth': 60, 'height': 110},
                'regions': ['US', 'EU', 'Asia']
            },
            {
                'name': 'Serving Station',
                'type': 'serving_station',
                'dimensions': {'width': 120, 'depth': 60, 'height': 90},
                'regions': ['US', 'EU', 'Asia']
            },
            {
                'name': 'Host Stand',
                'type': 'host_stand',
                'dimensions': {'width': 60, 'depth': 40, 'height': 110},
                'regions': ['US', 'EU']
            }
        ]
    }
}

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

# Mock conversion function (since we can't import the real one in Render)
def mock_convert_2d_to_3d(input_path, output_path):
    """Mock function to simulate 2D to 3D conversion"""
    # In a real scenario, this would call the actual conversion function
    # For now, we'll just create a dummy STL file
    with open(output_path, 'w') as f:
        f.write("solid dummy\n")
        f.write("  facet normal 0 0 0\n")
        f.write("    outer loop\n")
        f.write("      vertex 0 0 0\n")
        f.write("      vertex 1 0 0\n")
        f.write("      vertex 0 1 0\n")
        f.write("    endloop\n")
        f.write("  endfacet\n")
        f.write("endsolid dummy\n")
    return True

# Routes
@app.route('/')
def index():
    return jsonify({"message": "AutoCad_Buddy API is running"}), 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

# API routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if email in USERS_DB:
            return jsonify({'error': 'Email already registered'}), 400
        
        user_id = str(uuid.uuid4())
        USERS_DB[email] = {
            'id': user_id,
            'email': email,
            'password': generate_password_hash(password),
            'name': name,
            'created_at': datetime.now().isoformat(),
            'models': []
        }
        
        access_token = create_access_token(identity=email)
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user_id,
                'email': email,
                'name': name,
                'models': []
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = USERS_DB.get(email)
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        access_token = create_access_token(identity=email)
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'models': user['models']
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_user():
    try:
        email = get_jwt_identity()
        user = USERS_DB.get(email)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        models = []
        for model_id in user['models']:
            if model_id in MODELS_DB:
                models.append(MODELS_DB[model_id])
        
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'models': models
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/convert', methods=['POST'])
@jwt_required()
def convert_file():
    try:
        email = get_jwt_identity()
        user = USERS_DB.get(email)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Convert file to 3D model
        model_id = str(uuid.uuid4())
        model_filename = f"{model_id}.stl"
        model_path = os.path.join(app.config['UPLOAD_FOLDER'], model_filename)
        
        # Call mock conversion function
        mock_convert_2d_to_3d(file_path, model_path)
        
        # Create viewer HTML
        viewer_filename = f"{model_id}.html"
        viewer_path = os.path.join(app.config['UPLOAD_FOLDER'], viewer_filename)
        
        # Create model record
        model = {
            'id': model_id,
            'user_id': user['id'],
            'filename': filename,
            'original_path': file_path,
            'model_path': model_path,
            'viewer_path': viewer_path,
            'created_at': datetime.now().isoformat(),
            'viewer_url': f"/api/viewer/{model_id}",
            'download_url': f"/api/download/{model_id}"
        }
        
        MODELS_DB[model_id] = model
        user['models'].append(model_id)
        
        return jsonify({
            'model_id': model_id,
            'filename': filename,
            'viewer_url': f"/api/viewer/{model_id}",
            'download_url': f"/api/download/{model_id}"
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Make sure the app listens on the port Render expects
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
