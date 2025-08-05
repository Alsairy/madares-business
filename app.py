import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import json
from datetime import datetime

# --- App Setup ---
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Simple in-memory storage for demo
assets_data = [
    {
        'id': 'AST-001',
        'building_name': 'Riyadh Educational Complex',
        'region': 'Riyadh',
        'city': 'Riyadh',
        'condition': 'Good',
        'status': 'Active',
        'area': '5000 m²',
        'coordinates': '24.7136, 46.6753',
        'created': '2025-01-15'
    },
    {
        'id': 'AST-002',
        'building_name': 'Jeddah Training Center',
        'region': 'Makkah',
        'city': 'Jeddah',
        'condition': 'Excellent',
        'status': 'Active',
        'area': '3500 m²',
        'coordinates': '21.4858, 39.1925',
        'created': '2025-01-10'
    },
    {
        'id': 'AST-003',
        'building_name': 'Dammam Business Hub',
        'region': 'Eastern Province',
        'city': 'Dammam',
        'condition': 'Fair',
        'status': 'Under Review',
        'area': '4200 m²',
        'coordinates': '26.4207, 50.0888',
        'created': '2025-01-05'
    }
]

workflows_data = [
    {
        'id': 'WF-001',
        'title': 'Asset Registration Review',
        'status': 'In Progress',
        'assigned_to': 'Ahmed Al-Rashid',
        'due_date': '2025-08-15',
        'priority': 'High'
    }
]

users_data = [
    {
        'id': 1,
        'username': 'admin',
        'name': 'System Administrator',
        'role': 'Central Admin',
        'department': 'IT Administration',
        'region': 'All Regions',
        'status': 'Active'
    },
    {
        'id': 2,
        'username': 'ahmed.rashid',
        'name': 'Ahmed Al-Rashid',
        'role': 'Regional Manager',
        'department': 'Asset Management',
        'region': 'Riyadh',
        'status': 'Active'
    },
    {
        'id': 3,
        'username': 'fatima.zahra',
        'name': 'Fatima Al-Zahra',
        'role': 'Investment Analyst',
        'department': 'Financial Planning',
        'region': 'Makkah',
        'status': 'Active'
    }
]

# --- API Routes ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data and data.get('username') == 'admin' and data.get('password') == 'password123':
        return jsonify({'message': 'Login successful', 'user': 'admin'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/assets', methods=['GET'])
def get_assets():
    return jsonify(assets_data)

@app.route('/api/assets/<asset_id>', methods=['GET'])
def get_asset(asset_id):
    asset = next((a for a in assets_data if a['id'] == asset_id), None)
    if asset:
        return jsonify(asset)
    return jsonify({'error': 'Asset not found'}), 404

@app.route('/api/assets', methods=['POST'])
def add_asset():
    try:
        data = request.form.to_dict() if request.form else request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create new asset
        new_asset = {
            'id': data.get('asset_id', f'AST-{len(assets_data)+1:03d}'),
            'building_name': data.get('building_name', ''),
            'region': data.get('region', ''),
            'city': data.get('city', ''),
            'condition': data.get('condition', ''),
            'status': 'Active',
            'area': data.get('area', ''),
            'coordinates': f"{data.get('latitude', '')}, {data.get('longitude', '')}",
            'created': datetime.now().strftime('%Y-%m-%d')
        }
        
        assets_data.append(new_asset)
        
        # Handle file uploads
        files = request.files
        uploaded_files = []
        for field, file in files.items():
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                uploaded_files.append(filename)
        
        return jsonify({
            'message': 'Asset added successfully',
            'asset': new_asset,
            'uploaded_files': uploaded_files
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets/<asset_id>', methods=['PUT'])
def update_asset(asset_id):
    try:
        data = request.get_json()
        asset = next((a for a in assets_data if a['id'] == asset_id), None)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
        
        # Update asset data
        for key, value in data.items():
            if key in asset:
                asset[key] = value
        
        return jsonify({'message': 'Asset updated successfully', 'asset': asset})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    return jsonify(workflows_data)

@app.route('/api/workflows', methods=['POST'])
def add_workflow():
    try:
        data = request.get_json()
        new_workflow = {
            'id': f'WF-{len(workflows_data)+1:03d}',
            'title': data.get('title', ''),
            'status': data.get('status', 'New'),
            'assigned_to': data.get('assigned_to', ''),
            'due_date': data.get('due_date', ''),
            'priority': data.get('priority', 'Medium')
        }
        workflows_data.append(new_workflow)
        return jsonify({'message': 'Workflow created successfully', 'workflow': new_workflow}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify(users_data)

@app.route('/api/users', methods=['POST'])
def add_user():
    try:
        data = request.get_json()
        new_user = {
            'id': len(users_data) + 1,
            'username': data.get('username', ''),
            'name': data.get('name', ''),
            'role': data.get('role', ''),
            'department': data.get('department', ''),
            'region': data.get('region', ''),
            'status': 'Active'
        }
        users_data.append(new_user)
        return jsonify({'message': 'User added successfully', 'user': new_user}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        user = next((u for u in users_data if u['id'] == user_id), None)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update user data
        for key, value in data.items():
            if key in user:
                user[key] = value
        
        return jsonify({'message': 'User updated successfully', 'user': user})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Simulate OCR processing
            ocr_text = f"OCR processed text from {filename} - This is simulated OCR output for demonstration."
            
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': filename,
                'ocr_text': ocr_text
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    return jsonify({
        'total_assets': len(assets_data),
        'active_workflows': len([w for w in workflows_data if w['status'] == 'In Progress']),
        'regions_covered': len(set(a['region'] for a in assets_data)),
        'total_users': len(users_data),
        'recent_activities': [
            {'icon': '🏢', 'text': 'Asset AST-001 registered in Riyadh region', 'time': '2 hours ago'},
            {'icon': '🔄', 'text': 'Workflow WF-003 completed for Dammam property', 'time': '4 hours ago'},
            {'icon': '👥', 'text': 'New user ahmed.rashid added to system', 'time': '1 day ago'},
            {'icon': '📊', 'text': 'Investment analysis report generated', 'time': '2 days ago'}
        ]
    })

# --- Serve Frontend ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Vercel will handle the server startup
# Export the app for Vercel
application = app

