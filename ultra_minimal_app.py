from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import uuid
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configure CORS to allow requests from any origin
CORS(app)

# Simulated in-memory database
USERS_DB = {}

# Routes
@app.route('/')
def index():
    return jsonify({"message": "AutoCad_Buddy API is running"}), 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

# API routes
@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
        
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
            'password': password,  # In a real app, hash this password
            'name': name,
            'created_at': datetime.now().isoformat(),
            'models': []
        }
        
        # Create a simple token
        access_token = str(uuid.uuid4())
        
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

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def login():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
        
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = USERS_DB.get(email)
        if not user or user['password'] != password:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create a simple token
        access_token = str(uuid.uuid4())
        
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

# For testing purposes
@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"message": "API test endpoint is working"}), 200

# Make sure the app listens on the port Render expects
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
