import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file
from werkzeug.utils import secure_filename
import uuid
from io import BytesIO
import base64

# Try to import optional dependencies
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'madares_business_secret_key_2025'
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('/tmp/madares.db')
    cursor = conn.cursor()
    
    # Assets table with ALL MOE fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            -- Asset Identification & Status
            building_name TEXT NOT NULL,
            asset_type TEXT,
            condition TEXT,
            status TEXT,
            asset_purpose TEXT,
            
            -- Planning & Need Assessment
            planning_status TEXT,
            need_assessment TEXT,
            priority_level TEXT,
            expected_completion DATE,
            
            -- Location Attractiveness
            location_score INTEGER,
            accessibility TEXT,
            nearby_amenities TEXT,
            
            -- Investment Proposal & Obstacles
            investment_value REAL,
            funding_source TEXT,
            investment_obstacles TEXT,
            
            -- Financial Obligations & Covenants
            maintenance_cost REAL,
            insurance_coverage REAL,
            financial_covenants TEXT,
            
            -- Utilities Information
            electricity_provider TEXT,
            water_provider TEXT,
            telecom_provider TEXT,
            utility_status TEXT,
            
            -- Ownership Information
            ownership_type TEXT,
            owner_name TEXT,
            deed_number TEXT,
            registration_date DATE,
            
            -- Land & Plan Details
            land_area REAL,
            plot_number TEXT,
            zoning TEXT,
            
            -- Asset Area Details
            built_area REAL,
            usable_area REAL,
            floors INTEGER,
            parking_spaces INTEGER,
            green_area REAL,
            
            -- Construction Status
            construction_status TEXT,
            completion_percentage INTEGER,
            construction_start DATE,
            construction_end DATE,
            
            -- Physical Dimensions
            length REAL,
            width REAL,
            height REAL,
            perimeter REAL,
            
            -- Boundaries
            north_boundary TEXT,
            south_boundary TEXT,
            east_boundary TEXT,
            west_boundary TEXT,
            ne_coordinates TEXT,
            nw_coordinates TEXT,
            se_coordinates TEXT,
            sw_coordinates TEXT,
            
            -- Geographic Location
            region TEXT NOT NULL,
            city TEXT NOT NULL,
            district TEXT,
            street_address TEXT,
            postal_code TEXT,
            latitude REAL,
            longitude REAL,
            
            -- System fields
            created_date DATE DEFAULT CURRENT_DATE,
            updated_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Workflows table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Pending',
            assigned_to TEXT,
            due_date DATE,
            priority TEXT DEFAULT 'Medium',
            created_date DATE DEFAULT CURRENT_DATE,
            updated_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            role TEXT,
            department TEXT,
            region TEXT,
            status TEXT DEFAULT 'Active',
            created_date DATE DEFAULT CURRENT_DATE,
            updated_date DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    # Files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            asset_id TEXT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            upload_date DATE DEFAULT CURRENT_DATE,
            ocr_text TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        )
    ''')
    
    # Insert sample data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM assets')
    if cursor.fetchone()[0] == 0:
        sample_assets = [
            ('AST-001', 'Riyadh Educational Complex', 'Educational', 'Good', 'Active', 'Education',
             'Approved', 'High priority educational facility for growing population', 'High', '2025-12-31',
             9, 'Excellent', 'Metro station, shopping centers, hospitals nearby',
             15000000, 'Government', 'None identified',
             500000, 20000000, 'Standard government insurance coverage',
             'SEC', 'NWC', 'STC', 'All Connected',
             'Government', 'Ministry of Education', 'DEED-2024-001', '2024-01-15',
             5000, 'PLOT-001', 'Educational',
             3500, 3200, 3, 50, 500,
             'Completed', 100, '2023-01-01', '2024-12-31',
             100, 50, 15, 300,
             'King Fahd Road', 'Residential Area', 'Commercial District', 'Green Belt',
             '24.7200,46.6800', '24.7200,46.6750', '24.7150,46.6800', '24.7150,46.6750',
             'Riyadh', 'Riyadh', 'Al Olaya', 'King Fahd Road, Al Olaya District', '12345',
             24.7136, 46.6753),
            
            ('AST-002', 'Jeddah Training Center', 'Training', 'Excellent', 'Active', 'Professional Training',
             'In Planning', 'Advanced training facility for technical skills', 'Medium', '2025-06-30',
             8, 'Good', 'Airport nearby, business district, hotels',
             12000000, 'Government', 'Limited parking space',
             350000, 15000000, 'Comprehensive coverage including equipment',
             'SEC', 'NWC', 'STC', 'All Connected',
             'Government', 'Technical and Vocational Training Corporation', 'DEED-2024-002', '2024-02-20',
             3500, 'PLOT-002', 'Commercial',
             2800, 2500, 2, 35, 300,
             'Completed', 100, '2023-06-01', '2024-05-31',
             80, 45, 12, 250,
             'Tahlia Street', 'Commercial Area', 'Residential District', 'Main Road',
             '21.4900,39.1950', '21.4900,39.1900', '21.4850,39.1950', '21.4850,39.1900',
             'Makkah', 'Jeddah', 'Al Hamra', 'Tahlia Street, Al Hamra District', '23456',
             21.4858, 39.1925),
             
            ('AST-003', 'Dammam Business Hub', 'Commercial', 'Fair', 'Under Review', 'Business Development',
             'Pending', 'Commercial hub for eastern province business growth', 'High', '2025-09-30',
             7, 'Fair', 'Port access, industrial area, transportation hub',
             18000000, 'Mixed', 'Environmental clearance pending',
             600000, 25000000, 'Enhanced coverage for commercial activities',
             'SEC', 'NWC', 'STC', 'Partially Connected',
             'Government', 'Saudi Arabian General Investment Authority', 'DEED-2024-003', '2024-03-10',
             4200, 'PLOT-003', 'Mixed Use',
             3800, 3500, 4, 80, 400,
             'In Progress', 75, '2024-01-01', '2025-12-31',
             120, 60, 18, 360,
             'King Abdulaziz Road', 'Industrial Zone', 'Commercial Area', 'Residential District',
             '26.4250,50.0900', '26.4250,50.0850', '26.4200,50.0900', '26.4200,50.0850',
             'Eastern Province', 'Dammam', 'Al Faisaliyah', 'King Abdulaziz Road, Al Faisaliyah', '34567',
             26.4207, 50.0888)
        ]
        
        cursor.executemany('''
            INSERT INTO assets (
                id, building_name, asset_type, condition, status, asset_purpose,
                planning_status, need_assessment, priority_level, expected_completion,
                location_score, accessibility, nearby_amenities,
                investment_value, funding_source, investment_obstacles,
                maintenance_cost, insurance_coverage, financial_covenants,
                electricity_provider, water_provider, telecom_provider, utility_status,
                ownership_type, owner_name, deed_number, registration_date,
                land_area, plot_number, zoning,
                built_area, usable_area, floors, parking_spaces, green_area,
                construction_status, completion_percentage, construction_start, construction_end,
                length, width, height, perimeter,
                north_boundary, south_boundary, east_boundary, west_boundary,
                ne_coordinates, nw_coordinates, se_coordinates, sw_coordinates,
                region, city, district, street_address, postal_code,
                latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_assets)
    
    # Insert sample workflows
    cursor.execute('SELECT COUNT(*) FROM workflows')
    if cursor.fetchone()[0] == 0:
        sample_workflows = [
            ('WF-001', 'Asset Registration Review', 'Review and approve new asset registration for Riyadh complex', 'In Progress', 'Ahmed Al-Rashid', '2025-08-15', 'High'),
            ('WF-002', 'Investment Analysis', 'Conduct financial analysis for Jeddah training center expansion', 'Pending', 'Fatima Al-Zahra', '2025-08-20', 'Medium'),
            ('WF-003', 'Construction Monitoring', 'Monitor construction progress for Dammam business hub', 'In Progress', 'Mohammed Al-Qahtani', '2025-08-25', 'High')
        ]
        cursor.executemany('INSERT INTO workflows (id, title, description, status, assigned_to, due_date, priority) VALUES (?, ?, ?, ?, ?, ?, ?)', sample_workflows)
    
    # Insert sample users
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ('admin', 'System Administrator', 'admin@madares.gov.sa', 'Central Admin', 'IT Administration', 'All Regions', 'Active'),
            ('ahmed.rashid', 'Ahmed Al-Rashid', 'ahmed.rashid@madares.gov.sa', 'Regional Manager', 'Asset Management', 'Riyadh', 'Active'),
            ('fatima.zahra', 'Fatima Al-Zahra', 'fatima.zahra@madares.gov.sa', 'Investment Analyst', 'Financial Planning', 'Makkah', 'Active'),
            ('mohammed.qahtani', 'Mohammed Al-Qahtani', 'mohammed.qahtani@madares.gov.sa', 'Construction Manager', 'Operations', 'Eastern Province', 'Active')
        ]
        cursor.executemany('INSERT INTO users (username, name, email, role, department, region, status) VALUES (?, ?, ?, ?, ?, ?, ?)', sample_users)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Utility functions
def get_db_connection():
    conn = sqlite3.connect('/tmp/madares.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_ocr(file_path):
    """Process OCR on uploaded file"""
    if not OCR_AVAILABLE:
        return "OCR processing not available - install pytesseract and PIL"
    
    try:
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='eng+ara')
            return text
        else:
            return "OCR only supported for image files"
    except Exception as e:
        return f"OCR processing error: {str(e)}"

def generate_pdf_report(report_type, data):
    """Generate PDF report"""
    if not PDF_AVAILABLE:
        return None, "PDF generation not available - install reportlab"
    
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(f"Madares Business - {report_type.replace('-', ' ').title()} Report", title_style))
        story.append(Spacer(1, 12))
        
        # Date
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        if report_type == 'asset-summary':
            # Asset summary table
            table_data = [['Asset ID', 'Building Name', 'Region', 'Status', 'Investment Value']]
            for asset in data:
                table_data.append([
                    asset['id'],
                    asset['building_name'],
                    asset['region'],
                    asset['status'],
                    f"SAR {asset['investment_value']:,.0f}" if asset['investment_value'] else 'N/A'
                ])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer, None
    except Exception as e:
        return None, f"PDF generation error: {str(e)}"

# Complete HTML template with ALL MOE fields
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
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: white; margin: 2% auto; padding: 2rem; border-radius: 10px; width: 95%; max-width: 1000px; max-height: 90vh; overflow-y: auto; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .modal-title { font-size: 1.5rem; color: #d4a574; }
        .close { font-size: 2rem; cursor: pointer; color: #999; }
        .close:hover { color: #333; }
        #map { height: 300px; width: 100%; border-radius: 5px; margin: 1rem 0; }
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
        .recent-activities { background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .activity-item { display: flex; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid #eee; }
        .activity-item:last-child { border-bottom: none; }
        .activity-icon { font-size: 1.5rem; margin-right: 1rem; }
        .activity-text { flex: 1; }
        .activity-time { color: #666; font-size: 0.875rem; }
        .reports-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
        .report-card { background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; cursor: pointer; transition: all 0.3s; }
        .report-card:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,0,0,0.15); }
        .report-icon { font-size: 3rem; margin-bottom: 1rem; }
        .alert { padding: 1rem; border-radius: 5px; margin: 1rem 0; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .file-list { margin-top: 1rem; }
        .file-item { display: flex; justify-content: between; align-items: center; padding: 0.5rem; border: 1px solid #ddd; border-radius: 5px; margin: 0.25rem 0; }
        .file-name { flex: 1; }
        .file-size { color: #666; font-size: 0.875rem; margin: 0 1rem; }
    </style>
</head>
<body>
    <div id="loginScreen">
        <div class="login-container">
            <h2 style="text-align: center; color: #d4a574; margin-bottom: 2rem;">🏢 Madares Business Login</h2>
            <form id="loginForm">
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
        </div>
    </div>

    <div id="mainApp" class="hidden">
        <div class="header">
            <h1>🏢 Madares Business - Complete Asset Management System</h1>
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
                    <div class="stat-card">
                        <div class="stat-number" id="totalInvestment">0</div>
                        <div class="stat-label">Total Investment (SAR)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="completedAssets">0</div>
                        <div class="stat-label">Completed Assets</div>
                    </div>
                </div>

                <div class="recent-activities">
                    <h3>🕒 Recent Activities</h3>
                    <div id="recentActivities">
                        <!-- Activities will be loaded here -->
                    </div>
                </div>
            </div>

            <!-- Assets Tab -->
            <div id="assets" class="tab-content">
                <h2>🏢 Asset Management</h2>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="showTab('add-asset')">➕ Add New Asset</button>
                    <button class="btn btn-secondary" onclick="refreshAssets()">🔄 Refresh</button>
                    <button class="btn btn-success" onclick="exportAssets()">📊 Export</button>
                </div>
                <div class="search-container">
                    <input type="text" class="search-input" placeholder="🔍 Search assets..." onkeyup="searchAssets(this.value)">
                </div>
                <div class="table-container">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Asset ID</th>
                                <th>Building Name</th>
                                <th>Type</th>
                                <th>Region</th>
                                <th>City</th>
                                <th>Status</th>
                                <th>Investment Value</th>
                                <th>Construction</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="assetsTableBody">
                            <!-- Assets will be loaded here -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Complete MOE Add Asset Form -->
            <div id="add-asset" class="tab-content">
                <h2>➕ Add New Asset - Complete MOE Form (All Fields)</h2>
                <form id="assetForm" enctype="multipart/form-data">
                    
                    <!-- 1. Asset Identification & Status -->
                    <div class="form-section">
                        <h3>🏢 1. Asset Identification & Status (5 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Asset ID *</label>
                                    <input type="text" name="asset_id" required placeholder="e.g., AST-004">
                                </div>
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

                    <!-- 2. Planning & Need Assessment -->
                    <div class="form-section">
                        <h3>📋 2. Planning & Need Assessment (4 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Planning Status</label>
                                    <select name="planning_status">
                                        <option value="Planned">Planned</option>
                                        <option value="In Planning">In Planning</option>
                                        <option value="Approved">Approved</option>
                                        <option value="Rejected">Rejected</option>
                                        <option value="Under Review">Under Review</option>
                                        <option value="Pending">Pending</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Need Assessment</label>
                                    <textarea name="need_assessment" rows="3" placeholder="Describe the need assessment and justification for this asset..."></textarea>
                                </div>
                                <div class="form-group">
                                    <label>Priority Level</label>
                                    <select name="priority_level">
                                        <option value="Critical">Critical</option>
                                        <option value="High">High</option>
                                        <option value="Medium">Medium</option>
                                        <option value="Low">Low</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Expected Completion Date</label>
                                    <input type="date" name="expected_completion">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 3. Location Attractiveness -->
                    <div class="form-section">
                        <h3>📍 3. Location Attractiveness (3 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Location Score (1-10)</label>
                                    <input type="number" name="location_score" min="1" max="10" placeholder="Rate location attractiveness (1-10)">
                                </div>
                                <div class="form-group">
                                    <label>Accessibility</label>
                                    <select name="accessibility">
                                        <option value="Excellent">Excellent</option>
                                        <option value="Good">Good</option>
                                        <option value="Fair">Fair</option>
                                        <option value="Poor">Poor</option>
                                        <option value="Limited">Limited</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Nearby Amenities</label>
                                    <textarea name="nearby_amenities" rows="2" placeholder="List nearby amenities (schools, hospitals, shopping centers, etc.)..."></textarea>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 4. Investment Proposal & Obstacles -->
                    <div class="form-section">
                        <h3>💰 4. Investment Proposal & Obstacles (3 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Investment Value (SAR)</label>
                                    <input type="number" name="investment_value" placeholder="e.g., 15000000" step="1000">
                                </div>
                                <div class="form-group">
                                    <label>Funding Source</label>
                                    <select name="funding_source">
                                        <option value="Government">Government</option>
                                        <option value="Private">Private</option>
                                        <option value="Mixed">Mixed (Public-Private)</option>
                                        <option value="International">International</option>
                                        <option value="Islamic Development Bank">Islamic Development Bank</option>
                                        <option value="Other">Other</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Investment Obstacles</label>
                                    <textarea name="investment_obstacles" rows="3" placeholder="Describe any obstacles or challenges for investment..."></textarea>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 5. Financial Obligations & Covenants -->
                    <div class="form-section">
                        <h3>💳 5. Financial Obligations & Covenants (3 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Annual Maintenance Cost (SAR)</label>
                                    <input type="number" name="maintenance_cost" placeholder="e.g., 500000" step="1000">
                                </div>
                                <div class="form-group">
                                    <label>Insurance Coverage (SAR)</label>
                                    <input type="number" name="insurance_coverage" placeholder="e.g., 20000000" step="1000">
                                </div>
                                <div class="form-group">
                                    <label>Financial Covenants</label>
                                    <textarea name="financial_covenants" rows="3" placeholder="Describe financial obligations, covenants, and commitments..."></textarea>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 6. Utilities Information -->
                    <div class="form-section">
                        <h3>⚡ 6. Utilities Information (4 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Electricity Provider</label>
                                    <input type="text" name="electricity_provider" placeholder="e.g., Saudi Electricity Company (SEC)">
                                </div>
                                <div class="form-group">
                                    <label>Water Provider</label>
                                    <input type="text" name="water_provider" placeholder="e.g., National Water Company (NWC)">
                                </div>
                                <div class="form-group">
                                    <label>Internet/Telecom Provider</label>
                                    <input type="text" name="telecom_provider" placeholder="e.g., Saudi Telecom Company (STC)">
                                </div>
                                <div class="form-group">
                                    <label>Utility Connection Status</label>
                                    <select name="utility_status">
                                        <option value="All Connected">All Connected</option>
                                        <option value="Partially Connected">Partially Connected</option>
                                        <option value="Not Connected">Not Connected</option>
                                        <option value="Under Installation">Under Installation</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 7. Ownership Information -->
                    <div class="form-section">
                        <h3>📋 7. Ownership Information (4 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Ownership Type</label>
                                    <select name="ownership_type">
                                        <option value="Government">Government</option>
                                        <option value="Private">Private</option>
                                        <option value="Leased">Leased</option>
                                        <option value="Joint Venture">Joint Venture</option>
                                        <option value="Waqf">Waqf (Religious Endowment)</option>
                                        <option value="Cooperative">Cooperative</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Owner Name</label>
                                    <input type="text" name="owner_name" placeholder="Name of owner/entity">
                                </div>
                                <div class="form-group">
                                    <label>Property Deed Number</label>
                                    <input type="text" name="deed_number" placeholder="Property deed/title number">
                                </div>
                                <div class="form-group">
                                    <label>Registration Date</label>
                                    <input type="date" name="registration_date">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 8. Land & Plan Details -->
                    <div class="form-section">
                        <h3>🗺️ 8. Land & Plan Details (3 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Land Area (m²)</label>
                                    <input type="number" name="land_area" placeholder="e.g., 5000" step="0.01">
                                </div>
                                <div class="form-group">
                                    <label>Plot Number</label>
                                    <input type="text" name="plot_number" placeholder="Plot/parcel number">
                                </div>
                                <div class="form-group">
                                    <label>Zoning Classification</label>
                                    <select name="zoning">
                                        <option value="Residential">Residential</option>
                                        <option value="Commercial">Commercial</option>
                                        <option value="Industrial">Industrial</option>
                                        <option value="Mixed Use">Mixed Use</option>
                                        <option value="Educational">Educational</option>
                                        <option value="Healthcare">Healthcare</option>
                                        <option value="Government">Government</option>
                                        <option value="Agricultural">Agricultural</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 9. Asset Area Details -->
                    <div class="form-section">
                        <h3>📐 9. Asset Area Details (5 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Built-up Area (m²)</label>
                                    <input type="number" name="built_area" placeholder="e.g., 3500" step="0.01">
                                </div>
                                <div class="form-group">
                                    <label>Usable Area (m²)</label>
                                    <input type="number" name="usable_area" placeholder="e.g., 3200" step="0.01">
                                </div>
                                <div class="form-group">
                                    <label>Number of Floors</label>
                                    <input type="number" name="floors" placeholder="e.g., 3" min="0">
                                </div>
                                <div class="form-group">
                                    <label>Parking Spaces</label>
                                    <input type="number" name="parking_spaces" placeholder="e.g., 50" min="0">
                                </div>
                                <div class="form-group">
                                    <label>Green Area (m²)</label>
                                    <input type="number" name="green_area" placeholder="e.g., 500" step="0.01" min="0">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 10. Construction Status -->
                    <div class="form-section">
                        <h3>🏗️ 10. Construction Status (4 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Construction Status</label>
                                    <select name="construction_status">
                                        <option value="Completed">Completed</option>
                                        <option value="In Progress">In Progress</option>
                                        <option value="Planned">Planned</option>
                                        <option value="On Hold">On Hold</option>
                                        <option value="Cancelled">Cancelled</option>
                                        <option value="Under Design">Under Design</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>Completion Percentage (%)</label>
                                    <input type="number" name="completion_percentage" min="0" max="100" placeholder="e.g., 85">
                                </div>
                                <div class="form-group">
                                    <label>Construction Start Date</label>
                                    <input type="date" name="construction_start">
                                </div>
                                <div class="form-group">
                                    <label>Expected/Actual Completion Date</label>
                                    <input type="date" name="construction_end">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 11. Physical Dimensions -->
                    <div class="form-section">
                        <h3>📏 11. Physical Dimensions (4 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Length (m)</label>
                                    <input type="number" name="length" placeholder="e.g., 100" step="0.01">
                                </div>
                                <div class="form-group">
                                    <label>Width (m)</label>
                                    <input type="number" name="width" placeholder="e.g., 50" step="0.01">
                                </div>
                                <div class="form-group">
                                    <label>Height (m)</label>
                                    <input type="number" name="height" placeholder="e.g., 15" step="0.01">
                                </div>
                                <div class="form-group">
                                    <label>Perimeter (m)</label>
                                    <input type="number" name="perimeter" placeholder="e.g., 300" step="0.01">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 12. Boundaries -->
                    <div class="form-section">
                        <h3>🧭 12. Boundaries (8 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>North Boundary</label>
                                    <input type="text" name="north_boundary" placeholder="What borders the north side">
                                </div>
                                <div class="form-group">
                                    <label>South Boundary</label>
                                    <input type="text" name="south_boundary" placeholder="What borders the south side">
                                </div>
                                <div class="form-group">
                                    <label>East Boundary</label>
                                    <input type="text" name="east_boundary" placeholder="What borders the east side">
                                </div>
                                <div class="form-group">
                                    <label>West Boundary</label>
                                    <input type="text" name="west_boundary" placeholder="What borders the west side">
                                </div>
                                <div class="form-group">
                                    <label>Northeast Corner Coordinates</label>
                                    <input type="text" name="ne_coordinates" placeholder="Lat, Lng (e.g., 24.7200, 46.6800)">
                                </div>
                                <div class="form-group">
                                    <label>Northwest Corner Coordinates</label>
                                    <input type="text" name="nw_coordinates" placeholder="Lat, Lng (e.g., 24.7200, 46.6750)">
                                </div>
                                <div class="form-group">
                                    <label>Southeast Corner Coordinates</label>
                                    <input type="text" name="se_coordinates" placeholder="Lat, Lng (e.g., 24.7150, 46.6800)">
                                </div>
                                <div class="form-group">
                                    <label>Southwest Corner Coordinates</label>
                                    <input type="text" name="sw_coordinates" placeholder="Lat, Lng (e.g., 24.7150, 46.6750)">
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 13. Geographic Location -->
                    <div class="form-section">
                        <h3>🌍 13. Geographic Location (7 Fields)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Region *</label>
                                    <select name="region" required>
                                        <option value="">Select Region</option>
                                        <option value="Riyadh">Riyadh</option>
                                        <option value="Makkah">Makkah</option>
                                        <option value="Eastern Province">Eastern Province</option>
                                        <option value="Madinah">Madinah</option>
                                        <option value="Qassim">Qassim</option>
                                        <option value="Hail">Hail</option>
                                        <option value="Tabuk">Tabuk</option>
                                        <option value="Northern Borders">Northern Borders</option>
                                        <option value="Jazan">Jazan</option>
                                        <option value="Najran">Najran</option>
                                        <option value="Al Bahah">Al Bahah</option>
                                        <option value="Al Jouf">Al Jouf</option>
                                        <option value="Asir">Asir</option>
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
                                    <input type="text" name="street_address" placeholder="Full street address">
                                </div>
                                <div class="form-group">
                                    <label>Postal Code</label>
                                    <input type="text" name="postal_code" placeholder="e.g., 12345">
                                </div>
                                <div class="form-group">
                                    <label>Latitude</label>
                                    <input type="number" name="latitude" step="0.000001" placeholder="Click on map to select">
                                </div>
                                <div class="form-group">
                                    <label>Longitude</label>
                                    <input type="number" name="longitude" step="0.000001" placeholder="Click on map to select">
                                </div>
                            </div>
                            <div id="map"></div>
                        </div>
                    </div>

                    <!-- 14. Supporting Documents -->
                    <div class="form-section">
                        <h3>📄 14. Supporting Documents (6 File Upload Areas)</h3>
                        <div class="form-content">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Property Deed</label>
                                    <div class="upload-area" onclick="triggerFileUpload('property_deed')">
                                        <p>📄 Click to upload or drag and drop</p>
                                        <p style="font-size: 12px; color: #666;">PDF, DOC, JPG, PNG (Max 16MB)</p>
                                    </div>
                                    <input type="file" id="property_deed" name="property_deed" style="display: none;" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png">
                                    <div id="property_deed_list" class="file-list"></div>
                                </div>
                                <div class="form-group">
                                    <label>Survey Report</label>
                                    <div class="upload-area" onclick="triggerFileUpload('survey_report')">
                                        <p>📊 Click to upload or drag and drop</p>
                                        <p style="font-size: 12px; color: #666;">PDF, DOC, JPG, PNG (Max 16MB)</p>
                                    </div>
                                    <input type="file" id="survey_report" name="survey_report" style="display: none;" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png">
                                    <div id="survey_report_list" class="file-list"></div>
                                </div>
                                <div class="form-group">
                                    <label>Investment Proposal</label>
                                    <div class="upload-area" onclick="triggerFileUpload('investment_proposal')">
                                        <p>💰 Click to upload or drag and drop</p>
                                        <p style="font-size: 12px; color: #666;">PDF, DOC, XLS, XLSX (Max 16MB)</p>
                                    </div>
                                    <input type="file" id="investment_proposal" name="investment_proposal" style="display: none;" accept=".pdf,.doc,.docx,.xls,.xlsx">
                                    <div id="investment_proposal_list" class="file-list"></div>
                                </div>
                                <div class="form-group">
                                    <label>Financial Documents</label>
                                    <div class="upload-area" onclick="triggerFileUpload('financial_docs')">
                                        <p>💳 Click to upload or drag and drop</p>
                                        <p style="font-size: 12px; color: #666;">PDF, DOC, XLS, XLSX (Max 16MB)</p>
                                    </div>
                                    <input type="file" id="financial_docs" name="financial_docs" style="display: none;" accept=".pdf,.doc,.docx,.xls,.xlsx">
                                    <div id="financial_docs_list" class="file-list"></div>
                                </div>
                                <div class="form-group">
                                    <label>Engineering Reports</label>
                                    <div class="upload-area" onclick="triggerFileUpload('engineering_reports')">
                                        <p>🏗️ Click to upload or drag and drop</p>
                                        <p style="font-size: 12px; color: #666;">PDF, DOC, JPG, PNG (Max 16MB)</p>
                                    </div>
                                    <input type="file" id="engineering_reports" name="engineering_reports" style="display: none;" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png">
                                    <div id="engineering_reports_list" class="file-list"></div>
                                </div>
                                <div class="form-group">
                                    <label>Other Documents</label>
                                    <div class="upload-area" onclick="triggerFileUpload('other_docs')">
                                        <p>📋 Click to upload or drag and drop</p>
                                        <p style="font-size: 12px; color: #666;">PDF, DOC, JPG, PNG (Max 16MB)</p>
                                    </div>
                                    <input type="file" id="other_docs" name="other_docs" style="display: none;" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png">
                                    <div id="other_docs_list" class="file-list"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div style="text-align: center; margin: 2rem 0;">
                        <button type="submit" class="btn btn-primary" style="font-size: 1.2rem; padding: 1rem 2rem;">💾 Submit Complete Asset Registration</button>
                        <button type="reset" class="btn btn-secondary" style="font-size: 1.2rem; padding: 1rem 2rem;">🔄 Reset Form</button>
                    </div>
                </form>
            </div>

            <!-- Workflows Tab -->
            <div id="workflows" class="tab-content">
                <h2>🔄 Workflow Management</h2>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="openCreateWorkflowModal()">➕ Create New Workflow</button>
                    <button class="btn btn-secondary" onclick="refreshWorkflows()">🔄 Refresh</button>
                </div>
                <div class="table-container">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Title</th>
                                <th>Description</th>
                                <th>Status</th>
                                <th>Assigned To</th>
                                <th>Due Date</th>
                                <th>Priority</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="workflowsTableBody">
                            <!-- Workflows will be loaded here -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Users Tab -->
            <div id="users" class="tab-content">
                <h2>👥 User Management</h2>
                <div class="action-buttons">
                    <button class="btn btn-primary" onclick="openCreateUserModal()">➕ Add New User</button>
                    <button class="btn btn-secondary" onclick="refreshUsers()">🔄 Refresh</button>
                </div>
                <div class="table-container">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Username</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Department</th>
                                <th>Region</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="usersTableBody">
                            <!-- Users will be loaded here -->
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Reports Tab -->
            <div id="reports" class="tab-content">
                <h2>📊 Reports & Analytics</h2>
                <div class="reports-grid">
                    <div class="report-card" onclick="generateReport('asset-summary')">
                        <div class="report-icon">📋</div>
                        <h3>Asset Summary Report</h3>
                        <p>Complete overview of all assets with statistics and details</p>
                    </div>
                    <div class="report-card" onclick="generateReport('regional-distribution')">
                        <div class="report-icon">🗺️</div>
                        <h3>Regional Distribution</h3>
                        <p>Assets distribution across different regions and cities</p>
                    </div>
                    <div class="report-card" onclick="generateReport('construction-status')">
                        <div class="report-icon">🏗️</div>
                        <h3>Construction Status</h3>
                        <p>Building and construction progress across all projects</p>
                    </div>
                    <div class="report-card" onclick="generateReport('investment-analysis')">
                        <div class="report-icon">💰</div>
                        <h3>Investment Analysis</h3>
                        <p>Financial insights and investment performance metrics</p>
                    </div>
                    <div class="report-card" onclick="generateReport('workflow-performance')">
                        <div class="report-icon">⚡</div>
                        <h3>Workflow Performance</h3>
                        <p>Task completion rates and workflow efficiency metrics</p>
                    </div>
                    <div class="report-card" onclick="generateReport('user-activity')">
                        <div class="report-icon">👥</div>
                        <h3>User Activity Report</h3>
                        <p>User engagement and system usage statistics</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modals -->
    <!-- Asset View/Edit Modal -->
    <div id="assetModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title" id="assetModalTitle">Asset Details</h2>
                <span class="close" onclick="closeModal('assetModal')">&times;</span>
            </div>
            <div id="assetModalContent">
                <!-- Asset details will be loaded here -->
            </div>
        </div>
    </div>

    <!-- Workflow Create/Edit Modal -->
    <div id="workflowModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title" id="workflowModalTitle">Create New Workflow</h2>
                <span class="close" onclick="closeModal('workflowModal')">&times;</span>
            </div>
            <form id="workflowForm">
                <div class="form-group">
                    <label>Workflow Title *</label>
                    <input type="text" name="title" required placeholder="e.g., Asset Registration Review">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea name="description" rows="3" placeholder="Describe the workflow..."></textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Assigned To</label>
                        <select name="assigned_to">
                            <option value="Ahmed Al-Rashid">Ahmed Al-Rashid</option>
                            <option value="Fatima Al-Zahra">Fatima Al-Zahra</option>
                            <option value="Mohammed Al-Qahtani">Mohammed Al-Qahtani</option>
                            <option value="System Administrator">System Administrator</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Priority</label>
                        <select name="priority">
                            <option value="Critical">Critical</option>
                            <option value="High">High</option>
                            <option value="Medium">Medium</option>
                            <option value="Low">Low</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Due Date</label>
                        <input type="date" name="due_date">
                    </div>
                </div>
                <div style="text-align: center; margin-top: 1rem;">
                    <button type="submit" class="btn btn-primary">💾 Save Workflow</button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('workflowModal')">❌ Cancel</button>
                </div>
            </form>
        </div>
    </div>

    <!-- User Create/Edit Modal -->
    <div id="userModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title" id="userModalTitle">Add New User</h2>
                <span class="close" onclick="closeModal('userModal')">&times;</span>
            </div>
            <form id="userForm">
                <div class="form-row">
                    <div class="form-group">
                        <label>Username *</label>
                        <input type="text" name="username" required placeholder="e.g., john.doe">
                    </div>
                    <div class="form-group">
                        <label>Full Name *</label>
                        <input type="text" name="name" required placeholder="e.g., John Doe">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" placeholder="e.g., john.doe@madares.gov.sa">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Role</label>
                        <select name="role">
                            <option value="Regional Manager">Regional Manager</option>
                            <option value="Investment Analyst">Investment Analyst</option>
                            <option value="Asset Coordinator">Asset Coordinator</option>
                            <option value="Financial Analyst">Financial Analyst</option>
                            <option value="Construction Manager">Construction Manager</option>
                            <option value="System Administrator">System Administrator</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Department</label>
                        <select name="department">
                            <option value="Asset Management">Asset Management</option>
                            <option value="Financial Planning">Financial Planning</option>
                            <option value="IT Administration">IT Administration</option>
                            <option value="Operations">Operations</option>
                            <option value="Legal Affairs">Legal Affairs</option>
                            <option value="Construction">Construction</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Region</label>
                        <select name="region">
                            <option value="All Regions">All Regions</option>
                            <option value="Riyadh">Riyadh</option>
                            <option value="Makkah">Makkah</option>
                            <option value="Eastern Province">Eastern Province</option>
                            <option value="Madinah">Madinah</option>
                        </select>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 1rem;">
                    <button type="submit" class="btn btn-primary">💾 Save User</button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('userModal')">❌ Cancel</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let map;
        let currentEditingAsset = null;
        let currentEditingWorkflow = null;
        let currentEditingUser = null;

        // Tab Management
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
                setTimeout(initMap, 100);
            }
        }

        // Map Initialization
        function initMap() {
            if (document.getElementById('map')) {
                map = L.map('map').setView([24.7136, 46.6753], 6);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);
                
                map.on('click', function(e) {
                    document.querySelector('input[name="latitude"]').value = e.latlng.lat.toFixed(6);
                    document.querySelector('input[name="longitude"]').value = e.latlng.lng.toFixed(6);
                    
                    // Remove existing marker
                    map.eachLayer(function(layer) {
                        if (layer instanceof L.Marker) {
                            map.removeLayer(layer);
                        }
                    });
                    
                    // Add new marker
                    L.marker([e.latlng.lat, e.latlng.lng]).addTo(map);
                });
            }
        }

        // Login Function
        function login(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('loginScreen').classList.add('hidden');
                    document.getElementById('mainApp').classList.remove('hidden');
                    loadAllData();
                    showAlert('Login successful! Welcome to Madares Business.', 'success');
                } else {
                    showAlert('Invalid credentials. Please use admin/password123', 'error');
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                showAlert('Login error occurred', 'error');
            });
        }

        // Load All Data
        function loadAllData() {
            loadAssets();
            loadWorkflows();
            loadUsers();
            updateDashboardStats();
        }

        // Load Assets
        function loadAssets() {
            fetch('/api/assets')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const tbody = document.getElementById('assetsTableBody');
                        tbody.innerHTML = data.assets.map(asset => `
                            <tr>
                                <td>${asset.id}</td>
                                <td>${asset.building_name}</td>
                                <td>${asset.asset_type || 'N/A'}</td>
                                <td>${asset.region}</td>
                                <td>${asset.city}</td>
                                <td><span class="badge badge-${asset.status === 'Active' ? 'success' : asset.status === 'Under Review' ? 'warning' : 'info'}">${asset.status}</span></td>
                                <td>${asset.investment_value ? 'SAR ' + parseInt(asset.investment_value).toLocaleString() : 'N/A'}</td>
                                <td><span class="badge badge-${asset.construction_status === 'Completed' ? 'success' : asset.construction_status === 'In Progress' ? 'warning' : 'info'}">${asset.construction_status || 'N/A'}</span></td>
                                <td>
                                    <button class="btn btn-primary btn-small" onclick="viewAsset('${asset.id}')">👁️ View</button>
                                    <button class="btn btn-secondary btn-small" onclick="editAsset('${asset.id}')">✏️ Edit</button>
                                    <button class="btn btn-danger btn-small" onclick="deleteAsset('${asset.id}')">🗑️ Delete</button>
                                </td>
                            </tr>
                        `).join('');
                    }
                })
                .catch(error => {
                    console.error('Error loading assets:', error);
                    showAlert('Error loading assets', 'error');
                });
        }

        // Load Workflows
        function loadWorkflows() {
            fetch('/api/workflows')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const tbody = document.getElementById('workflowsTableBody');
                        tbody.innerHTML = data.workflows.map(workflow => `
                            <tr>
                                <td>${workflow.id}</td>
                                <td>${workflow.title}</td>
                                <td>${workflow.description || 'N/A'}</td>
                                <td><span class="badge badge-${workflow.status === 'In Progress' ? 'warning' : workflow.status === 'Completed' ? 'success' : 'info'}">${workflow.status}</span></td>
                                <td>${workflow.assigned_to}</td>
                                <td>${workflow.due_date || 'N/A'}</td>
                                <td><span class="badge badge-${workflow.priority === 'Critical' || workflow.priority === 'High' ? 'danger' : workflow.priority === 'Medium' ? 'warning' : 'info'}">${workflow.priority}</span></td>
                                <td>
                                    <button class="btn btn-primary btn-small" onclick="viewWorkflow('${workflow.id}')">👁️ View</button>
                                    <button class="btn btn-secondary btn-small" onclick="editWorkflow('${workflow.id}')">✏️ Edit</button>
                                    <button class="btn btn-danger btn-small" onclick="deleteWorkflow('${workflow.id}')">🗑️ Delete</button>
                                </td>
                            </tr>
                        `).join('');
                    }
                })
                .catch(error => {
                    console.error('Error loading workflows:', error);
                    showAlert('Error loading workflows', 'error');
                });
        }

        // Load Users
        function loadUsers() {
            fetch('/api/users')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const tbody = document.getElementById('usersTableBody');
                        tbody.innerHTML = data.users.map(user => `
                            <tr>
                                <td>${user.id}</td>
                                <td>${user.username}</td>
                                <td>${user.name}</td>
                                <td>${user.email || 'N/A'}</td>
                                <td>${user.role}</td>
                                <td>${user.department}</td>
                                <td>${user.region}</td>
                                <td><span class="badge badge-success">${user.status}</span></td>
                                <td>
                                    <button class="btn btn-primary btn-small" onclick="viewUser(${user.id})">👁️ View</button>
                                    <button class="btn btn-secondary btn-small" onclick="editUser(${user.id})">✏️ Edit</button>
                                    <button class="btn btn-danger btn-small" onclick="deleteUser(${user.id})">🗑️ Delete</button>
                                </td>
                            </tr>
                        `).join('');
                    }
                })
                .catch(error => {
                    console.error('Error loading users:', error);
                    showAlert('Error loading users', 'error');
                });
        }

        // Update Dashboard Stats
        function updateDashboardStats() {
            fetch('/api/dashboard')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('totalAssets').textContent = data.stats.total_assets;
                        document.getElementById('activeWorkflows').textContent = data.stats.active_workflows;
                        document.getElementById('totalRegions').textContent = data.stats.total_regions;
                        document.getElementById('totalUsers').textContent = data.stats.total_users;
                        document.getElementById('totalInvestment').textContent = data.stats.total_investment ? (data.stats.total_investment / 1000000).toFixed(1) + 'M' : '0';
                        document.getElementById('completedAssets').textContent = data.stats.completed_assets;
                        
                        // Update recent activities
                        const activitiesContainer = document.getElementById('recentActivities');
                        activitiesContainer.innerHTML = data.recent_activities.map(activity => `
                            <div class="activity-item">
                                <div class="activity-icon">${activity.icon}</div>
                                <div class="activity-text">${activity.text}</div>
                                <div class="activity-time">${activity.time}</div>
                            </div>
                        `).join('');
                    }
                })
                .catch(error => {
                    console.error('Error loading dashboard stats:', error);
                });
        }

        // Asset Functions
        function viewAsset(assetId) {
            fetch(`/api/assets/${assetId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const asset = data.asset;
                        document.getElementById('assetModalTitle').textContent = `Asset Details - ${asset.id}`;
                        document.getElementById('assetModalContent').innerHTML = `
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Asset ID:</label>
                                    <p>${asset.id}</p>
                                </div>
                                <div class="form-group">
                                    <label>Building Name:</label>
                                    <p>${asset.building_name}</p>
                                </div>
                                <div class="form-group">
                                    <label>Asset Type:</label>
                                    <p>${asset.asset_type || 'N/A'}</p>
                                </div>
                                <div class="form-group">
                                    <label>Region:</label>
                                    <p>${asset.region}</p>
                                </div>
                                <div class="form-group">
                                    <label>City:</label>
                                    <p>${asset.city}</p>
                                </div>
                                <div class="form-group">
                                    <label>Status:</label>
                                    <p><span class="badge badge-${asset.status === 'Active' ? 'success' : 'warning'}">${asset.status}</span></p>
                                </div>
                                <div class="form-group">
                                    <label>Condition:</label>
                                    <p>${asset.condition}</p>
                                </div>
                                <div class="form-group">
                                    <label>Investment Value:</label>
                                    <p>${asset.investment_value ? 'SAR ' + parseInt(asset.investment_value).toLocaleString() : 'N/A'}</p>
                                </div>
                                <div class="form-group">
                                    <label>Built Area:</label>
                                    <p>${asset.built_area ? asset.built_area + ' m²' : 'N/A'}</p>
                                </div>
                                <div class="form-group">
                                    <label>Construction Status:</label>
                                    <p>${asset.construction_status || 'N/A'}</p>
                                </div>
                                <div class="form-group">
                                    <label>Coordinates:</label>
                                    <p>${asset.latitude && asset.longitude ? asset.latitude + ', ' + asset.longitude : 'N/A'}</p>
                                </div>
                                <div class="form-group">
                                    <label>Created:</label>
                                    <p>${asset.created_date}</p>
                                </div>
                            </div>
                            <div style="text-align: center; margin-top: 1rem;">
                                <button class="btn btn-primary" onclick="editAsset('${asset.id}')">✏️ Edit Asset</button>
                                <button class="btn btn-secondary" onclick="closeModal('assetModal')">❌ Close</button>
                            </div>
                        `;
                        document.getElementById('assetModal').style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Error loading asset:', error);
                    showAlert('Error loading asset details', 'error');
                });
        }

        function editAsset(assetId) {
            showAlert(`Edit functionality for asset ${assetId} - Full edit form would open here`, 'info');
        }

        function deleteAsset(assetId) {
            if (confirm(`Are you sure you want to delete asset ${assetId}?`)) {
                fetch(`/api/assets/${assetId}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showAlert('Asset deleted successfully', 'success');
                            loadAssets();
                            updateDashboardStats();
                        } else {
                            showAlert('Error deleting asset', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error deleting asset:', error);
                        showAlert('Error deleting asset', 'error');
                    });
            }
        }

        // Workflow Functions
        function openCreateWorkflowModal() {
            currentEditingWorkflow = null;
            document.getElementById('workflowModalTitle').textContent = 'Create New Workflow';
            document.getElementById('workflowForm').reset();
            document.getElementById('workflowModal').style.display = 'block';
        }

        function viewWorkflow(workflowId) {
            showAlert(`View workflow ${workflowId} details - Full workflow details would open here`, 'info');
        }

        function editWorkflow(workflowId) {
            showAlert(`Edit workflow ${workflowId} - Full edit form would open here`, 'info');
        }

        function deleteWorkflow(workflowId) {
            if (confirm(`Are you sure you want to delete workflow ${workflowId}?`)) {
                fetch(`/api/workflows/${workflowId}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showAlert('Workflow deleted successfully', 'success');
                            loadWorkflows();
                            updateDashboardStats();
                        } else {
                            showAlert('Error deleting workflow', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error deleting workflow:', error);
                        showAlert('Error deleting workflow', 'error');
                    });
            }
        }

        // User Functions
        function openCreateUserModal() {
            currentEditingUser = null;
            document.getElementById('userModalTitle').textContent = 'Add New User';
            document.getElementById('userForm').reset();
            document.getElementById('userModal').style.display = 'block';
        }

        function viewUser(userId) {
            showAlert(`View user ${userId} details - Full user profile would open here`, 'info');
        }

        function editUser(userId) {
            showAlert(`Edit user ${userId} - Full edit form would open here`, 'info');
        }

        function deleteUser(userId) {
            if (confirm(`Are you sure you want to delete user ${userId}?`)) {
                fetch(`/api/users/${userId}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showAlert('User deleted successfully', 'success');
                            loadUsers();
                            updateDashboardStats();
                        } else {
                            showAlert('Error deleting user', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error deleting user:', error);
                        showAlert('Error deleting user', 'error');
                    });
            }
        }

        // Form Submissions
        function submitAsset(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            // Show loading
            showAlert('Submitting asset registration...', 'info');
            
            fetch('/api/assets', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Asset created successfully with all MOE fields!', 'success');
                    e.target.reset();
                    loadAssets();
                    updateDashboardStats();
                    showTab('assets');
                } else {
                    showAlert('Error creating asset: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error creating asset:', error);
                showAlert('Error creating asset', 'error');
            });
        }

        function submitWorkflow(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const workflowData = Object.fromEntries(formData.entries());

            fetch('/api/workflows', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(workflowData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Workflow created successfully!', 'success');
                    closeModal('workflowModal');
                    loadWorkflows();
                    updateDashboardStats();
                } else {
                    showAlert('Error creating workflow: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error creating workflow:', error);
                showAlert('Error creating workflow', 'error');
            });
        }

        function submitUser(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const userData = Object.fromEntries(formData.entries());

            fetch('/api/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('User created successfully!', 'success');
                    closeModal('userModal');
                    loadUsers();
                    updateDashboardStats();
                } else {
                    showAlert('Error creating user: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error creating user:', error);
                showAlert('Error creating user', 'error');
            });
        }

        // Utility Functions
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }

        function showAlert(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            
            // Insert at the top of the content area
            const content = document.querySelector('.content');
            content.insertBefore(alertDiv, content.firstChild);
            
            // Remove after 5 seconds
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }

        function refreshAssets() {
            loadAssets();
            showAlert('Assets refreshed', 'success');
        }

        function refreshWorkflows() {
            loadWorkflows();
            showAlert('Workflows refreshed', 'success');
        }

        function refreshUsers() {
            loadUsers();
            showAlert('Users refreshed', 'success');
        }

        function exportAssets() {
            window.open('/api/assets/export', '_blank');
        }

        function searchAssets(query) {
            const rows = document.querySelectorAll('#assetsTableBody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query.toLowerCase()) ? '' : 'none';
            });
        }

        function triggerFileUpload(inputId) {
            document.getElementById(inputId).click();
        }

        function generateReport(reportType) {
            showAlert(`Generating ${reportType} report...`, 'info');
            
            fetch(`/api/reports/${reportType}`)
                .then(response => {
                    if (response.ok) {
                        return response.blob();
                    }
                    throw new Error('Report generation failed');
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = `${reportType}-report.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    showAlert(`${reportType} report downloaded successfully!`, 'success');
                })
                .catch(error => {
                    console.error('Report generation error:', error);
                    showAlert(`Error generating ${reportType} report`, 'error');
                });
        }

        // Form Section Toggle
        function toggleFormSection(element) {
            const section = element.closest('.form-section');
            section.classList.toggle('collapsed');
        }

        // Event Listeners
        document.addEventListener('DOMContentLoaded', function() {
            // Login form
            document.getElementById('loginForm').addEventListener('submit', login);
            
            // Asset form
            document.getElementById('assetForm').addEventListener('submit', submitAsset);
            
            // Workflow form
            document.getElementById('workflowForm').addEventListener('submit', submitWorkflow);
            
            // User form
            document.getElementById('userForm').addEventListener('submit', submitUser);
            
            // Form section toggles
            document.querySelectorAll('.form-section h3').forEach(header => {
                header.addEventListener('click', () => toggleFormSection(header));
            });
            
            // Close modals when clicking outside
            window.addEventListener('click', function(event) {
                const modals = document.querySelectorAll('.modal');
                modals.forEach(modal => {
                    if (event.target === modal) {
                        modal.style.display = 'none';
                    }
                });
            });

            // File upload handlers
            document.querySelectorAll('input[type="file"]').forEach(input => {
                input.addEventListener('change', function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        const uploadArea = e.target.previousElementSibling;
                        const fileList = e.target.nextElementSibling;
                        
                        uploadArea.innerHTML = `
                            <p>✅ ${file.name}</p>
                            <p style="font-size: 12px; color: #666;">File selected successfully (${(file.size / 1024 / 1024).toFixed(2)} MB)</p>
                        `;
                        
                        if (fileList) {
                            fileList.innerHTML = `
                                <div class="file-item">
                                    <span class="file-name">${file.name}</span>
                                    <span class="file-size">${(file.size / 1024 / 1024).toFixed(2)} MB</span>
                                    <button type="button" class="btn btn-danger btn-small" onclick="removeFile('${e.target.id}')">Remove</button>
                                </div>
                            `;
                        }
                        
                        showAlert(`File ${file.name} selected for upload`, 'success');
                    }
                });
            });
        });

        function removeFile(inputId) {
            const input = document.getElementById(inputId);
            const uploadArea = input.previousElementSibling;
            const fileList = input.nextElementSibling;
            
            input.value = '';
            
            const label = uploadArea.parentElement.querySelector('label').textContent;
            let icon = '📄';
            let fileTypes = 'PDF, DOC, JPG, PNG (Max 16MB)';
            
            if (label.includes('Survey')) {
                icon = '📊';
            } else if (label.includes('Investment')) {
                icon = '💰';
                fileTypes = 'PDF, DOC, XLS, XLSX (Max 16MB)';
            } else if (label.includes('Financial')) {
                icon = '💳';
                fileTypes = 'PDF, DOC, XLS, XLSX (Max 16MB)';
            } else if (label.includes('Engineering')) {
                icon = '🏗️';
            } else if (label.includes('Other')) {
                icon = '📋';
            }
            
            uploadArea.innerHTML = `
                <p>${icon} Click to upload or drag and drop</p>
                <p style="font-size: 12px; color: #666;">${fileTypes}</p>
            `;
            
            if (fileList) {
                fileList.innerHTML = '';
            }
        }
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

@app.route('/api/assets')
def get_assets():
    conn = get_db_connection()
    assets = conn.execute('SELECT * FROM assets ORDER BY created_date DESC').fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'assets': [dict(asset) for asset in assets]
    })

@app.route('/api/assets/<asset_id>')
def get_asset(asset_id):
    conn = get_db_connection()
    asset = conn.execute('SELECT * FROM assets WHERE id = ?', (asset_id,)).fetchone()
    conn.close()
    
    if asset:
        return jsonify({
            'success': True,
            'asset': dict(asset)
        })
    return jsonify({
        'success': False,
        'message': 'Asset not found'
    }), 404

@app.route('/api/assets', methods=['POST'])
def create_asset():
    try:
        # Handle both form data and JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            files = request.files
        else:
            data = request.get_json() or {}
            files = {}
        
        # Generate new asset ID
        conn = get_db_connection()
        result = conn.execute('SELECT COUNT(*) as count FROM assets').fetchone()
        new_id = f"AST-{result['count'] + 1:03d}"
        
        # Insert asset with all MOE fields
        conn.execute('''
            INSERT INTO assets (
                id, building_name, asset_type, condition, status, asset_purpose,
                planning_status, need_assessment, priority_level, expected_completion,
                location_score, accessibility, nearby_amenities,
                investment_value, funding_source, investment_obstacles,
                maintenance_cost, insurance_coverage, financial_covenants,
                electricity_provider, water_provider, telecom_provider, utility_status,
                ownership_type, owner_name, deed_number, registration_date,
                land_area, plot_number, zoning,
                built_area, usable_area, floors, parking_spaces, green_area,
                construction_status, completion_percentage, construction_start, construction_end,
                length, width, height, perimeter,
                north_boundary, south_boundary, east_boundary, west_boundary,
                ne_coordinates, nw_coordinates, se_coordinates, sw_coordinates,
                region, city, district, street_address, postal_code,
                latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_id,
            data.get('building_name', ''),
            data.get('asset_type', ''),
            data.get('condition', ''),
            data.get('status', 'Active'),
            data.get('asset_purpose', ''),
            data.get('planning_status', ''),
            data.get('need_assessment', ''),
            data.get('priority_level', ''),
            data.get('expected_completion', ''),
            data.get('location_score', ''),
            data.get('accessibility', ''),
            data.get('nearby_amenities', ''),
            data.get('investment_value', ''),
            data.get('funding_source', ''),
            data.get('investment_obstacles', ''),
            data.get('maintenance_cost', ''),
            data.get('insurance_coverage', ''),
            data.get('financial_covenants', ''),
            data.get('electricity_provider', ''),
            data.get('water_provider', ''),
            data.get('telecom_provider', ''),
            data.get('utility_status', ''),
            data.get('ownership_type', ''),
            data.get('owner_name', ''),
            data.get('deed_number', ''),
            data.get('registration_date', ''),
            data.get('land_area', ''),
            data.get('plot_number', ''),
            data.get('zoning', ''),
            data.get('built_area', ''),
            data.get('usable_area', ''),
            data.get('floors', ''),
            data.get('parking_spaces', ''),
            data.get('green_area', ''),
            data.get('construction_status', ''),
            data.get('completion_percentage', ''),
            data.get('construction_start', ''),
            data.get('construction_end', ''),
            data.get('length', ''),
            data.get('width', ''),
            data.get('height', ''),
            data.get('perimeter', ''),
            data.get('north_boundary', ''),
            data.get('south_boundary', ''),
            data.get('east_boundary', ''),
            data.get('west_boundary', ''),
            data.get('ne_coordinates', ''),
            data.get('nw_coordinates', ''),
            data.get('se_coordinates', ''),
            data.get('sw_coordinates', ''),
            data.get('region', ''),
            data.get('city', ''),
            data.get('district', ''),
            data.get('street_address', ''),
            data.get('postal_code', ''),
            data.get('latitude', ''),
            data.get('longitude', '')
        ))
        
        # Handle file uploads
        uploaded_files = []
        for file_key, file in files.items():
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_id = str(uuid.uuid4())
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
                file.save(file_path)
                
                # Process OCR if it's an image
                ocr_text = ""
                if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    ocr_text = process_ocr(file_path)
                
                # Save file info to database
                conn.execute('''
                    INSERT INTO files (id, asset_id, filename, original_filename, file_type, file_size, ocr_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (file_id, new_id, f"{file_id}_{filename}", filename, file_key, file.content_length or 0, ocr_text))
                
                uploaded_files.append({
                    'id': file_id,
                    'filename': filename,
                    'type': file_key,
                    'ocr_text': ocr_text[:100] + '...' if len(ocr_text) > 100 else ocr_text
                })
        
        conn.commit()
        
        # Get the created asset
        new_asset = conn.execute('SELECT * FROM assets WHERE id = ?', (new_id,)).fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Asset created successfully with {len(uploaded_files)} files uploaded',
            'asset': dict(new_asset),
            'uploaded_files': uploaded_files
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error creating asset: {str(e)}'
        }), 500

@app.route('/api/assets/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    conn = get_db_connection()
    
    # Delete associated files first
    files = conn.execute('SELECT filename FROM files WHERE asset_id = ?', (asset_id,)).fetchall()
    for file_row in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_row['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
    
    conn.execute('DELETE FROM files WHERE asset_id = ?', (asset_id,))
    conn.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Asset deleted successfully'
    })

@app.route('/api/workflows')
def get_workflows():
    conn = get_db_connection()
    workflows = conn.execute('SELECT * FROM workflows ORDER BY created_date DESC').fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'workflows': [dict(workflow) for workflow in workflows]
    })

@app.route('/api/workflows', methods=['POST'])
def create_workflow():
    data = request.get_json()
    
    conn = get_db_connection()
    result = conn.execute('SELECT COUNT(*) as count FROM workflows').fetchone()
    new_id = f"WF-{result['count'] + 1:03d}"
    
    conn.execute('''
        INSERT INTO workflows (id, title, description, assigned_to, due_date, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        new_id,
        data.get('title', ''),
        data.get('description', ''),
        data.get('assigned_to', ''),
        data.get('due_date', ''),
        data.get('priority', 'Medium')
    ))
    
    conn.commit()
    new_workflow = conn.execute('SELECT * FROM workflows WHERE id = ?', (new_id,)).fetchone()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Workflow created successfully',
        'workflow': dict(new_workflow)
    })

@app.route('/api/workflows/<workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM workflows WHERE id = ?', (workflow_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Workflow deleted successfully'
    })

@app.route('/api/users')
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY created_date DESC').fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'users': [dict(user) for user in users]
    })

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO users (username, name, email, role, department, region)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.get('username', ''),
        data.get('name', ''),
        data.get('email', ''),
        data.get('role', ''),
        data.get('department', ''),
        data.get('region', '')
    ))
    
    conn.commit()
    new_user = conn.execute('SELECT * FROM users WHERE username = ?', (data.get('username'),)).fetchone()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'User created successfully',
        'user': dict(new_user)
    })

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'User deleted successfully'
    })

@app.route('/api/dashboard')
def get_dashboard():
    conn = get_db_connection()
    
    # Get statistics
    total_assets = conn.execute('SELECT COUNT(*) as count FROM assets').fetchone()['count']
    active_workflows = conn.execute('SELECT COUNT(*) as count FROM workflows WHERE status = "In Progress"').fetchone()['count']
    total_regions = conn.execute('SELECT COUNT(DISTINCT region) as count FROM assets').fetchone()['count']
    total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    total_investment = conn.execute('SELECT SUM(investment_value) as total FROM assets WHERE investment_value IS NOT NULL').fetchone()['total'] or 0
    completed_assets = conn.execute('SELECT COUNT(*) as count FROM assets WHERE construction_status = "Completed"').fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_assets': total_assets,
            'active_workflows': active_workflows,
            'total_regions': total_regions,
            'total_users': total_users,
            'total_investment': total_investment,
            'completed_assets': completed_assets
        },
        'recent_activities': [
            {'icon': '🏢', 'text': f'Total of {total_assets} assets registered in system', 'time': 'Current'},
            {'icon': '🔄', 'text': f'{active_workflows} workflows currently in progress', 'time': 'Current'},
            {'icon': '👥', 'text': f'{total_users} users active in system', 'time': 'Current'},
            {'icon': '💰', 'text': f'Total investment value: SAR {total_investment:,.0f}', 'time': 'Current'},
            {'icon': '✅', 'text': f'{completed_assets} assets completed construction', 'time': 'Current'}
        ]
    })

@app.route('/api/reports/<report_type>')
def generate_report_endpoint(report_type):
    try:
        conn = get_db_connection()
        
        if report_type == 'asset-summary':
            assets = conn.execute('SELECT * FROM assets ORDER BY created_date DESC').fetchall()
            data = [dict(asset) for asset in assets]
        else:
            data = []
        
        conn.close()
        
        pdf_buffer, error = generate_pdf_report(report_type, data)
        
        if error:
            return jsonify({'success': False, 'message': error}), 500
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'{report_type}-report.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/assets/export')
def export_assets():
    try:
        conn = get_db_connection()
        assets = conn.execute('SELECT * FROM assets ORDER BY created_date DESC').fetchall()
        conn.close()
        
        # Create CSV export
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        if assets:
            writer.writerow(assets[0].keys())
            
            # Write data
            for asset in assets:
                writer.writerow([str(value) if value is not None else '' for value in asset])
        
        output.seek(0)
        
        return send_file(
            BytesIO(output.getvalue().encode('utf-8')),
            as_attachment=True,
            download_name='assets_export.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

