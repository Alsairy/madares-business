from flask import Flask, request, jsonify, render_template_string
import json
from datetime import datetime

app = Flask(__name__)

# Simple in-memory data
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

# HTML template embedded in Python (to avoid file system issues)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Madares Business - Asset Management</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #d4a574, #b8860b); color: white; padding: 1rem 2rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header h1 { font-size: 1.8rem; font-weight: 600; }
        .nav-tabs { display: flex; background: white; border-bottom: 2px solid #ddd; padding: 0 2rem; }
        .nav-tab { padding: 1rem 2rem; cursor: pointer; border: none; background: none; font-size: 1rem; color: #666; border-bottom: 3px solid transparent; transition: all 0.3s; }
        .nav-tab.active { color: #d4a574; border-bottom-color: #d4a574; background: #fafafa; }
        .nav-tab:hover { background: #f9f9f9; color: #d4a574; }
        .content { padding: 2rem; max-width: 1200px; margin: 0 auto; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .login-container { max-width: 400px; margin: 100px auto; background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: #333; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 5px; font-size: 1rem; }
        .btn { padding: 0.75rem 1.5rem; border: none; border-radius: 5px; cursor: pointer; font-size: 1rem; transition: all 0.3s; }
        .btn-primary { background: #d4a574; color: white; }
        .btn-primary:hover { background: #b8860b; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 2rem; font-weight: bold; color: #d4a574; }
        .stat-label { color: #666; margin-top: 0.5rem; }
        .table { width: 100%; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .table th, .table td { padding: 1rem; text-align: left; border-bottom: 1px solid #eee; }
        .table th { background: #f8f9fa; font-weight: 600; color: #333; }
        .badge { padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.875rem; font-weight: 500; }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .hidden { display: none; }
        #map { height: 300px; width: 100%; border-radius: 5px; margin: 1rem 0; }
        .form-section { background: white; margin: 1rem 0; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .form-section h3 { color: #d4a574; margin-bottom: 1rem; cursor: pointer; }
        .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
    </style>
</head>
<body>
    <div id="loginScreen">
        <div class="login-container">
            <h2 style="text-align: center; color: #d4a574; margin-bottom: 2rem;">Madares Business Login</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" id="username" required>
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" id="password" required>
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%;">Sign In</button>
            </form>
        </div>
    </div>

    <div id="mainApp" class="hidden">
        <div class="header">
            <h1>🏢 Madares Business - Asset Management</h1>
        </div>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('dashboard')">📊 Dashboard</button>
            <button class="nav-tab" onclick="showTab('assets')">🏢 Assets</button>
            <button class="nav-tab" onclick="showTab('add-asset')">➕ Add Asset</button>
            <button class="nav-tab" onclick="showTab('workflows')">🔄 Workflows</button>
            <button class="nav-tab" onclick="showTab('users')">👥 Users</button>
            <button class="nav-tab" onclick="showTab('reports')">📊 Reports</button>
        </div>

        <div class="content">
            <div id="dashboard" class="tab-content active">
                <h2>Dashboard</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">3</div>
                        <div class="stat-label">Total Assets</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">1</div>
                        <div class="stat-label">Active Workflows</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">3</div>
                        <div class="stat-label">Regions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">3</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                </div>
            </div>

            <div id="assets" class="tab-content">
                <h2>Asset Management</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Asset ID</th>
                            <th>Building Name</th>
                            <th>Region</th>
                            <th>Status</th>
                            <th>Area</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="assetsTableBody">
                        <!-- Assets will be loaded here -->
                    </tbody>
                </table>
            </div>

            <div id="add-asset" class="tab-content">
                <h2>Add New Asset - Complete MOE Form</h2>
                <form id="assetForm">
                    <div class="form-section">
                        <h3>🏢 Asset Identification & Status</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Asset ID *</label>
                                <input type="text" name="asset_id" required>
                            </div>
                            <div class="form-group">
                                <label>Building Name *</label>
                                <input type="text" name="building_name" required>
                            </div>
                            <div class="form-group">
                                <label>Asset Condition</label>
                                <select name="condition">
                                    <option>Excellent</option>
                                    <option>Good</option>
                                    <option>Fair</option>
                                    <option>Poor</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="form-section">
                        <h3>📍 Geographic Location</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Region *</label>
                                <select name="region" required>
                                    <option>Riyadh</option>
                                    <option>Makkah</option>
                                    <option>Eastern Province</option>
                                    <option>Madinah</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>City *</label>
                                <input type="text" name="city" required>
                            </div>
                            <div class="form-group">
                                <label>Latitude</label>
                                <input type="text" name="latitude" placeholder="Click on map to select">
                            </div>
                            <div class="form-group">
                                <label>Longitude</label>
                                <input type="text" name="longitude" placeholder="Click on map to select">
                            </div>
                        </div>
                        <div id="map"></div>
                    </div>

                    <button type="submit" class="btn btn-primary">💾 Submit Asset</button>
                </form>
            </div>

            <div id="workflows" class="tab-content">
                <h2>Workflow Management</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Status</th>
                            <th>Assigned To</th>
                            <th>Due Date</th>
                            <th>Priority</th>
                        </tr>
                    </thead>
                    <tbody id="workflowsTableBody">
                        <!-- Workflows will be loaded here -->
                    </tbody>
                </table>
            </div>

            <div id="users" class="tab-content">
                <h2>User Management</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Username</th>
                            <th>Name</th>
                            <th>Role</th>
                            <th>Department</th>
                            <th>Region</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="usersTableBody">
                        <!-- Users will be loaded here -->
                    </tbody>
                </table>
            </div>

            <div id="reports" class="tab-content">
                <h2>Reports & Analytics</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>📋 Asset Summary Report</h3>
                        <p>Complete overview of all assets</p>
                    </div>
                    <div class="stat-card">
                        <h3>🗺️ Regional Distribution</h3>
                        <p>Assets by region and city</p>
                    </div>
                    <div class="stat-card">
                        <h3>🏗️ Construction Status</h3>
                        <p>Building and construction progress</p>
                    </div>
                    <div class="stat-card">
                        <h3>💰 Investment Analysis</h3>
                        <p>Financial and investment insights</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let map;

        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');

            // Initialize map if showing add-asset tab
            if (tabName === 'add-asset' && !map) {
                initMap();
            }
        }

        function initMap() {
            map = L.map('map').setView([24.7136, 46.6753], 6);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
            
            map.on('click', function(e) {
                document.querySelector('input[name="latitude"]').value = e.latlng.lat.toFixed(6);
                document.querySelector('input[name="longitude"]').value = e.latlng.lng.toFixed(6);
            });
        }

        function login(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            if (username === 'admin' && password === 'password123') {
                document.getElementById('loginScreen').classList.add('hidden');
                document.getElementById('mainApp').classList.remove('hidden');
                loadData();
            } else {
                alert('Invalid credentials. Use admin/password123');
            }
        }

        function loadData() {
            // Load assets
            fetch('/api/assets')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('assetsTableBody');
                    tbody.innerHTML = data.assets.map(asset => `
                        <tr>
                            <td>${asset.id}</td>
                            <td>${asset.building_name}</td>
                            <td>${asset.region}</td>
                            <td><span class="badge badge-success">${asset.status}</span></td>
                            <td>${asset.area}</td>
                            <td>
                                <button class="btn btn-primary" style="padding: 0.25rem 0.5rem; font-size: 0.875rem;">View</button>
                            </td>
                        </tr>
                    `).join('');
                });

            // Load workflows
            fetch('/api/workflows')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('workflowsTableBody');
                    tbody.innerHTML = data.workflows.map(workflow => `
                        <tr>
                            <td>${workflow.id}</td>
                            <td>${workflow.title}</td>
                            <td><span class="badge badge-warning">${workflow.status}</span></td>
                            <td>${workflow.assigned_to}</td>
                            <td>${workflow.due_date}</td>
                            <td><span class="badge badge-danger">${workflow.priority}</span></td>
                        </tr>
                    `).join('');
                });

            // Load users
            fetch('/api/users')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('usersTableBody');
                    tbody.innerHTML = data.users.map(user => `
                        <tr>
                            <td>${user.id}</td>
                            <td>${user.username}</td>
                            <td>${user.name}</td>
                            <td>${user.role}</td>
                            <td>${user.department}</td>
                            <td>${user.region}</td>
                            <td><span class="badge badge-success">${user.status}</span></td>
                        </tr>
                    `).join('');
                });
        }

        document.getElementById('loginForm').addEventListener('submit', login);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/assets')
def get_assets():
    return jsonify({
        'success': True,
        'assets': assets_data
    })

@app.route('/api/workflows')
def get_workflows():
    return jsonify({
        'success': True,
        'workflows': workflows_data
    })

@app.route('/api/users')
def get_users():
    return jsonify({
        'success': True,
        'users': users_data
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == 'admin' and password == 'password123':
        return jsonify({
            'success': True,
            'message': 'Login successful'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid credentials'
        }), 401

# This is the key for Vercel - simple export
if __name__ == '__main__':
    app.run(debug=True)

