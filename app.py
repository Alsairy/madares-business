import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import json
from datetime import datetime

# --- App Setup for Vercel Serverless ---
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# For serverless, we don't create upload folders
# app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # Use /tmp for serverless

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
        'priority': 'High',
        'created': '2025-08-01'
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

# --- Authentication ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Simple authentication (in production, use proper password hashing)
    if username == 'admin' and password == 'password123':
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'username': username,
                'role': 'System Administrator'
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid credentials'
        }), 401

# --- Assets API ---
@app.route('/api/assets', methods=['GET'])
def get_assets():
    return jsonify({
        'success': True,
        'assets': assets_data
    })

@app.route('/api/assets', methods=['POST'])
def create_asset():
    data = request.get_json()
    
    # Generate new asset ID
    new_id = f"AST-{len(assets_data) + 1:03d}"
    
    new_asset = {
        'id': new_id,
        'building_name': data.get('building_name', ''),
        'region': data.get('region', ''),
        'city': data.get('city', ''),
        'condition': data.get('condition', ''),
        'status': data.get('status', ''),
        'area': data.get('area', ''),
        'coordinates': f"{data.get('latitude', '')}, {data.get('longitude', '')}",
        'created': datetime.now().strftime('%Y-%m-%d')
    }
    
    assets_data.append(new_asset)
    
    return jsonify({
        'success': True,
        'message': 'Asset created successfully',
        'asset': new_asset
    })

@app.route('/api/assets/<asset_id>', methods=['PUT'])
def update_asset(asset_id):
    data = request.get_json()
    
    # Find and update asset
    for asset in assets_data:
        if asset['id'] == asset_id:
            asset.update({
                'building_name': data.get('building_name', asset['building_name']),
                'region': data.get('region', asset['region']),
                'city': data.get('city', asset['city']),
                'condition': data.get('condition', asset['condition']),
                'status': data.get('status', asset['status']),
                'area': data.get('area', asset['area'])
            })
            return jsonify({
                'success': True,
                'message': 'Asset updated successfully',
                'asset': asset
            })
    
    return jsonify({
        'success': False,
        'message': 'Asset not found'
    }), 404

# --- Workflows API ---
@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    return jsonify({
        'success': True,
        'workflows': workflows_data
    })

@app.route('/api/workflows', methods=['POST'])
def create_workflow():
    data = request.get_json()
    
    new_id = f"WF-{len(workflows_data) + 1:03d}"
    
    new_workflow = {
        'id': new_id,
        'title': data.get('title', ''),
        'status': 'Pending',
        'assigned_to': data.get('assigned_to', ''),
        'due_date': data.get('due_date', ''),
        'priority': data.get('priority', 'Medium'),
        'created': datetime.now().strftime('%Y-%m-%d')
    }
    
    workflows_data.append(new_workflow)
    
    return jsonify({
        'success': True,
        'message': 'Workflow created successfully',
        'workflow': new_workflow
    })

# --- Users API ---
@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({
        'success': True,
        'users': users_data
    })

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    new_id = len(users_data) + 1
    
    new_user = {
        'id': new_id,
        'username': data.get('username', ''),
        'name': data.get('name', ''),
        'role': data.get('role', ''),
        'department': data.get('department', ''),
        'region': data.get('region', ''),
        'status': 'Active'
    }
    
    users_data.append(new_user)
    
    return jsonify({
        'success': True,
        'message': 'User created successfully',
        'user': new_user
    })

# --- File Upload API ---
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file provided'
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No file selected'
        }), 400
    
    # For serverless, we'll just return success without actually storing
    # In production, you'd upload to cloud storage (S3, etc.)
    return jsonify({
        'success': True,
        'message': f'File {file.filename} uploaded successfully',
        'filename': file.filename
    })

# --- Dashboard API ---
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    return jsonify({
        'success': True,
        'stats': {
            'total_assets': len(assets_data),
            'active_workflows': len([w for w in workflows_data if w['status'] == 'In Progress']),
            'total_regions': len(set(asset['region'] for asset in assets_data)),
            'total_users': len(users_data)
        },
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

# Vercel serverless function handler
def handler(request):
    return app(request.environ, lambda status, headers: None)

# Export the app for Vercel
app = app

