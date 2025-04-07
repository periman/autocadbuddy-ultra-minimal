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
# Configure CORS to allow requests from our frontend domain
CORS(app, resources={r"/api/*": {"origins": os.environ.get('CORS_ALLOWED_ORIGINS', 'https://bbydsufg.manus.space')}})

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

# API routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
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

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
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

@app.route('/api/user', methods=['GET'])
@jwt_required()
def get_user():
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

@app.route('/api/convert', methods=['POST'])
@jwt_required()
def convert_file():
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
    
    try:
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

@app.route('/api/models', methods=['GET'])
@jwt_required()
def get_models():
    email = get_jwt_identity()
    user = USERS_DB.get(email)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    models = []
    for model_id in user['models']:
        if model_id in MODELS_DB:
            model = MODELS_DB[model_id]
            models.append({
                'id': model['id'],
                'filename': model['filename'],
                'created_at': model['created_at'],
                'viewer_url': model['viewer_url'],
                'download_url': model['download_url']
            })
    
    return jsonify(models), 200

@app.route('/api/viewer/<model_id>', methods=['GET'])
def view_model(model_id):
    if model_id not in MODELS_DB:
        return jsonify({'error': 'Model not found'}), 404
    
    model = MODELS_DB[model_id]
    
    # Create viewer HTML if it doesn't exist
    if not os.path.exists(model['viewer_path']):
        with open(model['viewer_path'], 'w') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>3D Model Viewer - {model['filename']}</title>
                <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/build/three.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/controls/OrbitControls.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/three@0.132.2/examples/js/loaders/STLLoader.js"></script>
                <style>
                    body {{ margin: 0; overflow: hidden; }}
                    canvas {{ width: 100%; height: 100%; display: block; }}
                    .info {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="info">
                    <h3>{model['filename']}</h3>
                    <p>Use mouse to rotate, scroll to zoom, and right-click to pan.</p>
                </div>
                <script>
                    // Set up scene
                    const scene = new THREE.Scene();
                    scene.background = new THREE.Color(0xf0f0f0);
                    
                    // Set up camera
                    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                    camera.position.z = 5;
                    
                    // Set up renderer
                    const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                    renderer.setSize(window.innerWidth, window.innerHeight);
                    document.body.appendChild(renderer.domElement);
                    
                    // Add lights
                    const ambientLight = new THREE.AmbientLight(0x404040);
                    scene.add(ambientLight);
                    
                    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.5);
                    directionalLight1.position.set(1, 1, 1);
                    scene.add(directionalLight1);
                    
                    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.5);
                    directionalLight2.position.set(-1, -1, -1);
                    scene.add(directionalLight2);
                    
                    // Add controls
                    const controls = new THREE.OrbitControls(camera, renderer.domElement);
                    controls.enableDamping = true;
                    controls.dampingFactor = 0.25;
                    
                    // Load STL model
                    const loader = new THREE.STLLoader();
                    loader.load('/api/download/{model_id}', function(geometry) {{
                        const material = new THREE.MeshPhongMaterial({{ color: 0x3498db, specular: 0x111111, shininess: 200 }});
                        const mesh = new THREE.Mesh(geometry, material);
                        
                        // Center model
                        geometry.computeBoundingBox();
                        const center = geometry.boundingBox.getCenter(new THREE.Vector3());
                        mesh.position.x = -center.x;
                        mesh.position.y = -center.y;
                        mesh.position.z = -center.z;
                        
                        scene.add(mesh);
                        
                        // Adjust camera to fit model
                        const box = new THREE.Box3().setFromObject(mesh);
                        const size = box.getSize(new THREE.Vector3());
                        const maxDim = Math.max(size.x, size.y, size.z);
                        camera.position.z = maxDim * 2.5;
                    }});
                    
                    // Handle window resize
                    window.addEventListener('resize', function() {{
                        camera.aspect = window.innerWidth / window.innerHeight;
                        camera.updateProjectionMatrix();
                        renderer.setSize(window.innerWidth, window.innerHeight);
                    }});
                    
                    // Animation loop
                    function animate() {{
                        requestAnimationFrame(animate);
                        controls.update();
                        renderer.render(scene, camera);
                    }}
                    
                    animate();
                </script>
            </body>
            </html>
            """)
    
    return send_file(model['viewer_path'])

@app.route('/api/download/<model_id>', methods=['GET'])
def download_model(model_id):
    if model_id not in MODELS_DB:
        return jsonify({'error': 'Model not found'}), 404
    
    model = MODELS_DB[model_id]
    
    return send_file(model['model_path'], as_attachment=True, download_name=f"{model['filename']}.stl")

@app.route('/api/equipment/categories', methods=['GET'])
def get_equipment_categories():
    return jsonify(list(EQUIPMENT_DB.keys())), 200

@app.route('/api/equipment/types', methods=['GET'])
def get_equipment_types():
    category = request.args.get('category', 'kitchen')
    
    if category not in EQUIPMENT_DB:
        return jsonify({'error': 'Category not found'}), 404
    
    return jsonify(EQUIPMENT_DB[category]['types']), 200

@app.route('/api/equipment/search', methods=['GET'])
def search_equipment():
    category = request.args.get('category', 'kitchen')
    type_filter = request.args.get('type', '')
    region = request.args.get('region', 'US')
    
    if category not in EQUIPMENT_DB:
        return jsonify({'error': 'Category not found'}), 404
    
    results = []
    for item in EQUIPMENT_DB[category]['items']:
        if (not type_filter or item['type'] == type_filter) and region in item['regions']:
            results.append(item)
    
    return jsonify(results), 200

@app.route('/api/location', methods=['GET'])
def get_user_location():
    # In a real app, this would use geolocation or IP-based location
    return jsonify({
        'country': 'US',
        'region': 'West',
        'city': 'San Francisco'
    }), 200

# Health check endpoint for Render
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
