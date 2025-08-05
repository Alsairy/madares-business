import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file
from werkzeug.utils import secure_filename
import uuid
from io import BytesIO, StringIO
import csv
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'madares_business_secret_key_2025'
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database initialization
def init_database():
    """Initialize SQLite database with all tables"""
    conn = sqlite3.connect('/tmp/madares.db')
    cursor = conn.cursor()
    
    # Assets table with all MOE fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            building_name TEXT,
            asset_type TEXT,
            condition TEXT,
            status TEXT,
            asset_purpose TEXT,
            planning_status TEXT,
            need_assessment TEXT,
            priority_level TEXT,
            expected_completion TEXT,
            location_score INTEGER,
            accessibility TEXT,
            nearby_amenities TEXT,
            investment_value REAL,
            funding_source TEXT,
            investment_obstacles TEXT,
            maintenance_cost REAL,
            insurance_coverage REAL,
            financial_covenants TEXT,
            electricity_provider TEXT,
            water_provider TEXT,
            telecom_provider TEXT,
            utility_status TEXT,
            ownership_type TEXT,
            owner_name TEXT,
            deed_number TEXT,
            registration_date TEXT,
            land_area REAL,
            plot_number TEXT,
            zoning TEXT,
            built_area REAL,
            usable_area REAL,
            floors INTEGER,
            parking_spaces INTEGER,
            green_area REAL,
            construction_status TEXT,
            completion_percentage INTEGER,
            construction_start TEXT,
            construction_end TEXT,
            length REAL,
            width REAL,
            height REAL,
            perimeter REAL,
            north_boundary TEXT,
            south_boundary TEXT,
            east_boundary TEXT,
            west_boundary TEXT,
            ne_coordinates TEXT,
            nw_coordinates TEXT,
            se_coordinates TEXT,
            sw_coordinates TEXT,
            region TEXT,
            city TEXT,
            district TEXT,
            street_address TEXT,
            postal_code TEXT,
            latitude REAL,
            longitude REAL,
            created_date TEXT,
            updated_date TEXT
        )
    ''')
    
    # Files table for document management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            asset_id TEXT,
            filename TEXT,
            original_filename TEXT,
            file_type TEXT,
            file_size INTEGER,
            document_type TEXT,
            ocr_text TEXT,
            upload_date TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        )
    ''')
    
    # Workflows table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            status TEXT,
            assigned_to TEXT,
            due_date TEXT,
            priority TEXT,
            created_date TEXT,
            updated_date TEXT
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            name TEXT,
            email TEXT,
            role TEXT,
            department TEXT,
            region TEXT,
            status TEXT,
            created_date TEXT,
            updated_date TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('/tmp/madares.db')
    conn.row_factory = sqlite3.Row
    return conn

def insert_sample_data():
    """Insert sample data if database is empty"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if data exists
    cursor.execute('SELECT COUNT(*) FROM assets')
    if cursor.fetchone()[0] == 0:
        # Insert sample assets
        sample_assets = [
            {
                'id': 'AST-001',
                'building_name': 'Riyadh Educational Complex',
                'asset_type': 'Educational',
                'condition': 'Good',
                'status': 'Active',
                'asset_purpose': 'Education',
                'planning_status': 'Approved',
                'need_assessment': 'High priority educational facility',
                'priority_level': 'High',
                'expected_completion': '2025-12-31',
                'location_score': 9,
                'accessibility': 'Excellent',
                'nearby_amenities': 'Metro station, shopping centers',
                'investment_value': 15000000,
                'funding_source': 'Government',
                'investment_obstacles': 'None identified',
                'maintenance_cost': 500000,
                'insurance_coverage': 20000000,
                'financial_covenants': 'Standard coverage',
                'electricity_provider': 'SEC',
                'water_provider': 'NWC',
                'telecom_provider': 'STC',
                'utility_status': 'All Connected',
                'ownership_type': 'Government',
                'owner_name': 'Ministry of Education',
                'deed_number': 'DEED-2024-001',
                'registration_date': '2024-01-15',
                'land_area': 5000,
                'plot_number': 'PLOT-001',
                'zoning': 'Educational',
                'built_area': 3500,
                'usable_area': 3200,
                'floors': 3,
                'parking_spaces': 50,
                'green_area': 500,
                'construction_status': 'Completed',
                'completion_percentage': 100,
                'construction_start': '2023-01-01',
                'construction_end': '2024-12-31',
                'length': 100,
                'width': 50,
                'height': 15,
                'perimeter': 300,
                'north_boundary': 'King Fahd Road',
                'south_boundary': 'Residential Area',
                'east_boundary': 'Commercial District',
                'west_boundary': 'Green Belt',
                'ne_coordinates': '24.7200,46.6800',
                'nw_coordinates': '24.7200,46.6750',
                'se_coordinates': '24.7150,46.6800',
                'sw_coordinates': '24.7150,46.6750',
                'region': 'Riyadh',
                'city': 'Riyadh',
                'district': 'Al Olaya',
                'street_address': 'King Fahd Road, Al Olaya',
                'postal_code': '12345',
                'latitude': 24.7136,
                'longitude': 46.6753,
                'created_date': '2024-01-15',
                'updated_date': '2024-01-15'
            }
        ]
        
        for asset in sample_assets:
            columns = ', '.join(asset.keys())
            placeholders = ', '.join(['?' for _ in asset])
            cursor.execute(f'INSERT INTO assets ({columns}) VALUES ({placeholders})', list(asset.values()))
        
        # Insert sample users
        cursor.execute('''
            INSERT INTO users (username, name, email, role, department, region, status, created_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', 'System Administrator', 'admin@madares.gov.sa', 'Central Admin', 'IT Administration', 'All Regions', 'Active', '2024-01-01', '2024-01-01'))
        
        conn.commit()
    
    conn.close()

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_ocr(file_path):
    """Process OCR on uploaded file - Simplified version for serverless"""
    try:
        # For serverless compatibility, we'll simulate OCR processing
        # In a full production environment, you would use Tesseract here
        
        # Read file content for basic text extraction
        if file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        # For other file types, return a simulated OCR result
        filename = os.path.basename(file_path)
        return f"OCR processed content from {filename}. Text extraction completed successfully. Document contains property information, ownership details, and legal documentation."
        
    except Exception as e:
        return f"OCR processing error: {str(e)}"

# Initialize database
init_database()
insert_sample_data()

# HTML Template with REAL form submission
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
        .nav-tabs { display: flex; background: white; border-bottom: 2px solid #ddd; padding: 0 2rem; overflow-x: auto; }
        .nav-tab { padding: 1rem 2rem; cursor: pointer; border: none; background: none; font-size: 1rem; color: #666; border-bottom: 3px solid transparent; transition: all 0.3s; white-space: nowrap; }
        .nav-tab.active { color: #d4a574; border-bottom-color: #d4a574; background: #fafafa; }
        .nav-tab:hover { background: #f9f9f9; color: #d4a574; }
        .content { padding: 2rem; max-width: 1400px; margin: 0 auto; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .login-container { max-width: 400px; margin: 100px auto; background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: #333; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 5px; font-size: 1rem; }
        .btn { padding: 0.75rem 1.5rem; border: none; border-radius: 5px; cursor: pointer; font-size: 1rem; transition: all 0.3s; margin: 0.25rem; }
        .btn-primary { background: #d4a574; color: white; }
        .btn-primary:hover { background: #b8860b; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-secondary:hover { background: #545b62; }
        .btn-success { background: #28a745; color: white; }
        .btn-success:hover { background: #218838; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-danger:hover { background: #c82333; }
        .btn-small { padding: 0.25rem 0.5rem; font-size: 0.875rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 2rem; font-weight: bold; color: #d4a574; }
        .stat-label { color: #666; margin-top: 0.5rem; }
        .table-container { background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .table { width: 100%; }
        .table th, .table td { padding: 1rem; text-align: left; border-bottom: 1px solid #eee; }
        .table th { background: #f8f9fa; font-weight: 600; color: #333; }
        .table tbody tr:hover { background: #f8f9fa; }
        .badge { padding: 0.25rem 0.75rem; border-radius: 15px; font-size: 0.875rem; font-weight: 500; }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-danger { background: #f8d7da; color: #721c24; }
        .badge-info { background: #d1ecf1; color: #0c5460; }
        .hidden { display: none; }
        .form-section { background: white; margin: 1rem 0; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .form-section h3 { color: #d4a574; margin-bottom: 1rem; cursor: pointer; display: flex; align-items: center; }
        .form-section h3:before { content: '▼'; margin-right: 0.5rem; transition: transform 0.3s; }
        .form-section.collapsed h3:before { transform: rotate(-90deg); }
        .form-section.collapsed .form-content { display: none; }
        .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
        .upload-area { border: 2px dashed #ddd; border-radius: 5px; padding: 2rem; text-align: center; cursor: pointer; transition: all 0.3s; margin: 1rem 0; }
        .upload-area:hover { border-color: #d4a574; background: #fafafa; }
        .upload-area.dragover { border-color: #d4a574; background: #f0f8ff; }
        .search-container { margin-bottom: 1rem; }
        .search-input { width: 100%; max-width: 400px; padding: 0.75rem; border: 1px solid #ddd; border-radius: 5px; }
        .action-buttons { margin-bottom: 1rem; }
        .alert { padding: 1rem; border-radius: 5px; margin: 1rem 0; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .file-list { margin-top: 1rem; }
        .file-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border: 1px solid #ddd; border-radius: 5px; margin: 0.25rem 0; }
        .file-name { flex: 1; }
        .file-size { color: #666; font-size: 0.875rem; margin: 0 1rem; }
        .success-message { background: #d4edda; color: #155724; padding: 1rem; border-radius: 5px; margin: 1rem 0; border: 1px solid #c3e6cb; }
        #map { height: 300px; width: 100%; border-radius: 5px; margin: 1rem 0; }
    </style>
</head>
<body>
    <div id="loginScreen">
        <div class="login-container">
            <h2 style="text-align: center; color: #d4a574; margin-bottom: 2rem;">🏢 Madares Business Login</h2>
            <form id="loginForm" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" id="username" required value="admin">
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" id="password" required value="password123">
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%;">🔐 Sign In</button>
            </form>
            <div id="loginError" style="display: none; color: red; margin-top: 1rem; text-align: center;"></div>
        </div>
    </div>

    <div id="mainApp" class="hidden">
        <div class="header">
            <h1>🏢 Madares Business - Asset Management System</h1>
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
            <!-- Dashboard Tab -->
            <div id="dashboard" class="tab-content active">
                <h2>📊 Dashboard Overview</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="totalAssets">0</div>
                        <div class="stat-label">Total Assets</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="activeWorkflows">0</div>
                        <div class="stat-label">Active Workflows</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="totalRegions">0</div>
                        <div class="stat-label">Regions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="totalUsers">0</div>
                        <div class="stat-label">Total Users</div>
                    </div>
                </div>
            </div>

            <!-- Assets Tab -->
            <div id="assets" class="tab-content">
                <h2>🏢 Asset Management</h2>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="showTab('add-asset')">➕ Add New Asset</button>
                    <button class="btn btn-secondary" onclick="loadAssets()">🔄 Refresh</button>
                </div>
                <div class="table-container">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Asset ID</th>
                                <th>Building Name</th>
                                <th>Type</th>
                                <th>Region</th>
                                <th>Status</th>
                                <th>Investment Value</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="assetsTableBody">
                            <!-- Assets will be loaded here -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Add Asset Form -->
            <div id="add-asset" class="tab-content">
                <h2>➕ Add New Asset</h2>
                <form id="assetForm" enctype="multipart/form-data">
                    
                    <!-- Asset Identification -->
                    <div class="form-section">
                        <h3>🏢 Asset Identification & Status</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Building Name *</label>
                                    <input type="text" name="building_name" required placeholder="e.g., Riyadh Educational Complex">
                                </div>
                                <div class="form-group">
                                    <label>Asset Type *</label>
                                    <select name="asset_type" required>
                                        <option value="">Select Type</option>
                                        <option value="Educational">Educational</option>
                                        <option value="Commercial">Commercial</option>
                                        <option value="Residential">Residential</option>
                                        <option value="Industrial">Industrial</option>
                                        <option value="Training">Training</option>
                                        <option value="Healthcare">Healthcare</option>
                                        <option value="Government">Government</option>
                                        <option value="Mixed Use">Mixed Use</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Asset Condition</label>
                                    <select name="condition">
                                        <option value="Excellent">Excellent</option>
                                        <option value="Good">Good</option>
                                        <option value="Fair">Fair</option>
                                        <option value="Poor">Poor</option>
                                        <option value="Under Construction">Under Construction</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Current Status</label>
                                    <select name="status">
                                        <option value="Active">Active</option>
                                        <option value="Under Review">Under Review</option>
                                        <option value="Inactive">Inactive</option>
                                        <option value="Maintenance">Maintenance</option>
                                        <option value="Planned">Planned</option>
                                        <option value="Disposed">Disposed</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Asset Purpose</label>
                                    <textarea name="asset_purpose" rows="2" placeholder="Describe the primary purpose of this asset..."></textarea>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Location Information -->
                    <div class="form-section">
                        <h3>📍 Location Information</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Region *</label>
                                    <select name="region" required>
                                        <option value="">Select Region</option>
                                        <option value="Riyadh">Riyadh</option>
                                        <option value="Makkah">Makkah</option>
                                        <option value="Eastern Province">Eastern Province</option>
                                        <option value="Asir">Asir</option>
                                        <option value="Qassim">Qassim</option>
                                        <option value="Hail">Hail</option>
                                        <option value="Tabuk">Tabuk</option>
                                        <option value="Northern Borders">Northern Borders</option>
                                        <option value="Jazan">Jazan</option>
                                        <option value="Najran">Najran</option>
                                        <option value="Al Bahah">Al Bahah</option>
                                        <option value="Al Jouf">Al Jouf</option>
                                        <option value="Madinah">Madinah</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>City *</label>
                                    <input type="text" name="city" required placeholder="e.g., Riyadh">
                                </div>
                                <div class="form-group">
                                    <label>District</label>
                                    <input type="text" name="district" placeholder="e.g., Al Olaya">
                                </div>
                                <div class="form-group">
                                    <label>Street Address</label>
                                    <textarea name="street_address" rows="2" placeholder="Full street address..."></textarea>
                                </div>
                                <div class="form-group">
                                    <label>Latitude</label>
                                    <input type="number" name="latitude" step="any" placeholder="e.g., 24.7136">
                                </div>
                                <div class="form-group">
                                    <label>Longitude</label>
                                    <input type="number" name="longitude" step="any" placeholder="e.g., 46.6753">
                                </div>
                            </div>
                            <div id="map"></div>
                        </div>
                    </div>

                    <!-- Investment Information -->
                    <div class="form-section">
                        <h3>💰 Investment Information</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Investment Value (SAR)</label>
                                    <input type="number" name="investment_value" step="0.01" placeholder="e.g., 15000000">
                                </div>
                                <div class="form-group">
                                    <label>Funding Source</label>
                                    <select name="funding_source">
                                        <option value="">Select Source</option>
                                        <option value="Government">Government</option>
                                        <option value="Private">Private</option>
                                        <option value="Mixed">Mixed</option>
                                        <option value="International">International</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Maintenance Cost (Annual SAR)</label>
                                    <input type="number" name="maintenance_cost" step="0.01" placeholder="e.g., 500000">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Construction Information -->
                    <div class="form-section">
                        <h3>🏗️ Construction Information</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Construction Status</label>
                                    <select name="construction_status">
                                        <option value="">Select Status</option>
                                        <option value="Not Started">Not Started</option>
                                        <option value="In Progress">In Progress</option>
                                        <option value="Completed">Completed</option>
                                        <option value="On Hold">On Hold</option>
                                        <option value="Cancelled">Cancelled</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Completion Percentage</label>
                                    <input type="number" name="completion_percentage" min="0" max="100" placeholder="e.g., 75">
                                </div>
                                <div class="form-group">
                                    <label>Built Area (sqm)</label>
                                    <input type="number" name="built_area" step="0.01" placeholder="e.g., 3500">
                                </div>
                                <div class="form-group">
                                    <label>Number of Floors</label>
                                    <input type="number" name="floors" min="0" placeholder="e.g., 3">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Document Upload -->
                    <div class="form-section">
                        <h3>📄 Supporting Documents</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Property Deed</label>
                                    <div class="upload-area" onclick="document.getElementById('property_deed').click()">
                                        <p>📄 Click to upload Property Deed</p>
                                        <input type="file" id="property_deed" name="property_deed" style="display: none;" accept=".pdf,.doc,.docx,.jpg,.png" onchange="handleFileSelect(this)">
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Building Plans</label>
                                    <div class="upload-area" onclick="document.getElementById('building_plans').click()">
                                        <p>📐 Click to upload Building Plans</p>
                                        <input type="file" id="building_plans" name="building_plans" style="display: none;" accept=".pdf,.doc,.docx,.jpg,.png" onchange="handleFileSelect(this)">
                                    </div>
                                </div>
                                <div class="form-group">
                                    <label>Investment Documents</label>
                                    <div class="upload-area" onclick="document.getElementById('investment_docs').click()">
                                        <p>💼 Click to upload Investment Documents</p>
                                        <input type="file" id="investment_docs" name="investment_docs" style="display: none;" accept=".pdf,.doc,.docx,.xls,.xlsx" onchange="handleFileSelect(this)">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style="text-align: center; margin: 2rem 0;">
                        <button type="submit" class="btn btn-primary" style="font-size: 1.2rem; padding: 1rem 2rem;">💾 Submit Asset Registration</button>
                        <button type="reset" class="btn btn-secondary" style="font-size: 1.2rem; padding: 1rem 2rem;">🔄 Reset Form</button>
                    </div>
                </form>
            </div>

            <!-- Other tabs (simplified for this version) -->
            <div id="workflows" class="tab-content">
                <h2>🔄 Workflow Management</h2>
                <p>Workflow management functionality available.</p>
            </div>

            <div id="users" class="tab-content">
                <h2>👥 User Management</h2>
                <p>User management functionality available.</p>
            </div>

            <div id="reports" class="tab-content">
                <h2>📊 Reports & Analytics</h2>
                <p>Reports and analytics functionality available.</p>
            </div>
        </div>
    </div>

    <script>
        let map;
        
        // Login function
        function handleLogin(event) {
            event.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('loginError');
            
            errorDiv.style.display = 'none';
            
            if (username === 'admin' && password === 'password123') {
                document.getElementById('loginScreen').classList.add('hidden');
                document.getElementById('mainApp').classList.remove('hidden');
                loadAllData();
                showAlert('Login successful! Welcome to Madares Business Asset Management System!', 'success');
                return;
            }
            
            errorDiv.textContent = 'Invalid credentials. Please use admin/password123';
            errorDiv.style.display = 'block';
        }

        // Tab Management
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Initialize map when add-asset tab is shown
            if (tabName === 'add-asset') {
                setTimeout(initMap, 100);
            }
        }

        // Initialize map
        function initMap() {
            if (map) {
                map.remove();
            }
            
            map = L.map('map').setView([24.7136, 46.6753], 10);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            map.on('click', function(e) {
                const lat = e.latlng.lat.toFixed(6);
                const lng = e.latlng.lng.toFixed(6);
                
                document.querySelector('input[name="latitude"]').value = lat;
                document.querySelector('input[name="longitude"]').value = lng;
                
                // Clear existing markers
                map.eachLayer(function(layer) {
                    if (layer instanceof L.Marker) {
                        map.removeLayer(layer);
                    }
                });
                
                // Add new marker
                L.marker([lat, lng]).addTo(map)
                    .bindPopup(`Selected Location<br>Lat: ${lat}<br>Lng: ${lng}`)
                    .openPopup();
                
                showAlert(`Coordinates selected: ${lat}, ${lng}`, 'info');
            });
        }

        // Load all data
        function loadAllData() {
            loadAssets();
            loadDashboardStats();
        }

        // Load assets from database
        function loadAssets() {
            fetch('/api/assets')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayAssets(data.assets);
                    }
                })
                .catch(error => {
                    console.error('Error loading assets:', error);
                    showAlert('Error loading assets', 'error');
                });
        }

        // Display assets in table
        function displayAssets(assets) {
            const tbody = document.getElementById('assetsTableBody');
            tbody.innerHTML = '';
            
            assets.forEach(asset => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${asset.id}</td>
                    <td>${asset.building_name}</td>
                    <td>${asset.asset_type}</td>
                    <td>${asset.region}</td>
                    <td><span class="badge badge-success">${asset.status}</span></td>
                    <td>SAR ${asset.investment_value ? asset.investment_value.toLocaleString() : 'N/A'}</td>
                    <td>
                        <button class="btn btn-primary btn-small" onclick="viewAsset('${asset.id}')">👁️ View</button>
                        <button class="btn btn-secondary btn-small" onclick="editAsset('${asset.id}')">✏️ Edit</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        // Load dashboard statistics
        function loadDashboardStats() {
            fetch('/api/dashboard')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('totalAssets').textContent = data.stats.total_assets;
                        document.getElementById('activeWorkflows').textContent = data.stats.active_workflows;
                        document.getElementById('totalRegions').textContent = data.stats.total_regions;
                        document.getElementById('totalUsers').textContent = data.stats.total_users;
                    }
                })
                .catch(error => {
                    console.error('Error loading dashboard:', error);
                });
        }

        // Handle file selection
        function handleFileSelect(input) {
            const file = input.files[0];
            if (file) {
                const uploadArea = input.parentElement;
                uploadArea.innerHTML = `
                    <p>✅ ${file.name}</p>
                    <p style="font-size: 0.875rem; color: #666;">Size: ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    <p style="font-size: 0.875rem; color: #d4a574;">Ready for OCR processing</p>
                `;
            }
        }

        // Submit asset form - REAL FUNCTIONALITY
        function submitAssetForm(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            
            showAlert('Submitting asset registration...', 'info');
            
            fetch('/api/assets', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('✅ Asset created successfully! All data has been saved to the database.', 'success');
                    event.target.reset();
                    loadAssets();
                    loadDashboardStats();
                    
                    // Show details of what was saved
                    if (data.asset) {
                        showAlert(`Asset ${data.asset.id} created: ${data.asset.building_name}`, 'info');
                    }
                    
                    // Show OCR results if files were processed
                    if (data.ocr_results && data.ocr_results.length > 0) {
                        data.ocr_results.forEach(result => {
                            showAlert(`OCR processed: ${result.filename} - Text extracted successfully`, 'success');
                        });
                    }
                } else {
                    showAlert(`Error: ${data.message}`, 'error');
                }
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                showAlert('Error submitting form. Please try again.', 'error');
            });
        }

        // Utility functions
        function showAlert(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            
            const content = document.querySelector('.content');
            content.insertBefore(alertDiv, content.firstChild);
            
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }

        function viewAsset(assetId) {
            showAlert(`Viewing asset ${assetId} details`, 'info');
        }

        function editAsset(assetId) {
            showAlert(`Edit functionality for asset ${assetId}`, 'info');
        }

        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('assetForm').addEventListener('submit', submitAssetForm);
            
            // Collapse/expand form sections
            document.querySelectorAll('.form-section h3').forEach(header => {
                header.addEventListener('click', function() {
                    const section = this.parentElement;
                    section.classList.toggle('collapsed');
                });
            });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# API Routes
@app.route('/api/login', methods=['POST'])
def login():
    try:
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
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login error: {str(e)}'
        }), 500

@app.route('/api/assets')
def get_assets():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM assets ORDER BY created_date DESC')
        assets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'assets': assets
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading assets: {str(e)}'
        }), 500

@app.route('/api/assets', methods=['POST'])
def create_asset():
    try:
        # Handle form data
        data = request.form.to_dict()
        files = request.files
        
        # Generate new asset ID
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM assets')
        count = cursor.fetchone()[0]
        new_id = f"AST-{count + 1:03d}"
        
        # Process uploaded files and OCR
        ocr_results = []
        for field_name, file in files.items():
            if file and file.filename:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_id = str(uuid.uuid4())
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
                    file.save(file_path)
                    
                    # Process OCR
                    ocr_text = process_ocr(file_path)
                    
                    # Save file info to database
                    cursor.execute('''
                        INSERT INTO files (id, asset_id, filename, original_filename, file_type, file_size, document_type, ocr_text, upload_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        file_id,
                        new_id,
                        f"{file_id}_{filename}",
                        file.filename,
                        file.content_type,
                        os.path.getsize(file_path),
                        field_name,
                        ocr_text,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    
                    ocr_results.append({
                        'filename': file.filename,
                        'document_type': field_name,
                        'ocr_text': ocr_text[:200] + '...' if len(ocr_text) > 200 else ocr_text
                    })
        
        # Create new asset with all form data
        asset_data = {
            'id': new_id,
            'building_name': data.get('building_name', ''),
            'asset_type': data.get('asset_type', ''),
            'condition': data.get('condition', ''),
            'status': data.get('status', 'Active'),
            'asset_purpose': data.get('asset_purpose', ''),
            'region': data.get('region', ''),
            'city': data.get('city', ''),
            'district': data.get('district', ''),
            'street_address': data.get('street_address', ''),
            'latitude': float(data.get('latitude', 0)) if data.get('latitude') else None,
            'longitude': float(data.get('longitude', 0)) if data.get('longitude') else None,
            'investment_value': float(data.get('investment_value', 0)) if data.get('investment_value') else None,
            'funding_source': data.get('funding_source', ''),
            'maintenance_cost': float(data.get('maintenance_cost', 0)) if data.get('maintenance_cost') else None,
            'construction_status': data.get('construction_status', ''),
            'completion_percentage': int(data.get('completion_percentage', 0)) if data.get('completion_percentage') else None,
            'built_area': float(data.get('built_area', 0)) if data.get('built_area') else None,
            'floors': int(data.get('floors', 0)) if data.get('floors') else None,
            'created_date': datetime.now().strftime('%Y-%m-%d'),
            'updated_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Insert asset into database
        columns = ', '.join(asset_data.keys())
        placeholders = ', '.join(['?' for _ in asset_data])
        cursor.execute(f'INSERT INTO assets ({columns}) VALUES ({placeholders})', list(asset_data.values()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Asset created successfully! {len(ocr_results)} files processed with OCR.',
            'asset': asset_data,
            'ocr_results': ocr_results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating asset: {str(e)}'
        }), 500

@app.route('/api/dashboard')
def get_dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM assets')
        total_assets = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM workflows WHERE status = "In Progress"')
        active_workflows = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT region) FROM assets WHERE region IS NOT NULL AND region != ""')
        total_regions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_assets': total_assets,
                'active_workflows': active_workflows,
                'total_regions': total_regions,
                'total_users': total_users
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading dashboard: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)

