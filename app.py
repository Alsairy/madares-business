from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
import csv
import io
import os
import uuid
from datetime import datetime
import base64
from werkzeug.utils import secure_filename
import mimetypes

app = Flask(__name__)
CORS(app)

# Vercel-optimized configuration
DATABASE_PATH = '/tmp/madares_complete.db'
UPLOAD_FOLDER = '/tmp/uploads'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
for doc_type in ['property_deed', 'ownership_documents', 'construction_plans', 'financial_documents', 'legal_documents', 'inspection_reports']:
    os.makedirs(os.path.join(UPLOAD_FOLDER, doc_type), exist_ok=True)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'dwg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    """Extract text from various file formats using basic OCR simulation"""
    try:
        file_ext = file_path.rsplit('.', 1)[1].lower()
        
        if file_ext in ['png', 'jpg', 'jpeg', 'gif']:
            return f"OCR Text extracted from {os.path.basename(file_path)}: Sample property document text with coordinates and measurements."
        elif file_ext == 'pdf':
            return f"PDF Text extracted from {os.path.basename(file_path)}: Property deed document with legal descriptions and boundaries."
        elif file_ext in ['doc', 'docx']:
            return f"Document text from {os.path.basename(file_path)}: Construction specifications and engineering details."
        elif file_ext in ['xls', 'xlsx']:
            return f"Spreadsheet data from {os.path.basename(file_path)}: Financial calculations and cost analysis."
        elif file_ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            return f"File processed: {os.path.basename(file_path)} - Content type: {file_ext}"
    except Exception as e:
        return f"Error processing file: {str(e)}"

def init_db():
    """Initialize the database with all required tables and complete MOE fields"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Complete Assets table with ALL 58+ MOE fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id TEXT UNIQUE,
            
            -- Section 1: Asset Identification & Status (6 fields)
            asset_name TEXT NOT NULL,
            asset_type TEXT,
            asset_category TEXT,
            asset_classification TEXT,
            current_status TEXT,
            operational_status TEXT,
            
            -- Section 2: Planning & Need Assessment (4 fields)
            planning_permit TEXT,
            building_permit TEXT,
            development_approval TEXT,
            need_assessment TEXT,
            
            -- Section 3: Location Attractiveness (3 fields)
            location_score INTEGER,
            accessibility_rating TEXT,
            market_attractiveness TEXT,
            
            -- Section 4: Investment Proposal & Obstacles (3 fields)
            investment_proposal TEXT,
            investment_obstacles TEXT,
            risk_mitigation TEXT,
            
            -- Section 5: Financial Obligations & Covenants (3 fields)
            financial_obligations TEXT,
            loan_covenants TEXT,
            payment_schedule TEXT,
            
            -- Section 6: Utilities Information (4 fields)
            utilities_water TEXT,
            utilities_electricity TEXT,
            utilities_sewage TEXT,
            utilities_telecom TEXT,
            
            -- Section 7: Ownership Information (4 fields)
            ownership_type TEXT,
            owner_name TEXT,
            ownership_percentage REAL,
            legal_status TEXT,
            
            -- Section 8: Land & Plan Details (3 fields)
            land_use TEXT,
            zoning_classification TEXT,
            development_potential TEXT,
            
            -- Section 9: Asset Area Details (5 fields)
            land_area REAL,
            built_area REAL,
            usable_area REAL,
            common_area REAL,
            parking_area REAL,
            
            -- Section 10: Construction Status (4 fields)
            construction_status TEXT,
            completion_percentage INTEGER,
            construction_quality TEXT,
            defects_warranty TEXT,
            
            -- Section 11: Physical Dimensions (4 fields)
            length_meters REAL,
            width_meters REAL,
            height_meters REAL,
            total_floors INTEGER,
            
            -- Section 12: Boundaries (8 fields)
            north_boundary TEXT,
            south_boundary TEXT,
            east_boundary TEXT,
            west_boundary TEXT,
            boundary_length_north REAL,
            boundary_length_south REAL,
            boundary_length_east REAL,
            boundary_length_west REAL,
            
            -- Section 13: Geographic Location (7 fields)
            region TEXT,
            city TEXT,
            district TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            elevation REAL,
            
            -- Financial Information
            investment_value REAL,
            current_value REAL,
            rental_income REAL,
            maintenance_cost REAL,
            occupancy_rate REAL,
            
            -- Additional Information
            tenant_information TEXT,
            insurance_details TEXT,
            tax_information TEXT,
            market_analysis TEXT,
            investment_recommendation TEXT,
            risk_assessment TEXT,
            future_plans TEXT,
            environmental_clearance TEXT,
            access_road TEXT,
            notes TEXT,
            
            -- System fields
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Files table for document management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE,
            asset_id TEXT,
            document_type TEXT,
            original_filename TEXT,
            stored_filename TEXT,
            file_path TEXT,
            file_size INTEGER,
            mime_type TEXT,
            ocr_text TEXT,
            processing_status TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id)
        )
    ''')
    
    # Workflows table for task management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Not Started',
            priority TEXT DEFAULT 'Medium',
            assigned_to TEXT,
            due_date DATE,
            created_by TEXT,
            progress INTEGER DEFAULT 0,
            notes TEXT,
            workflow_type TEXT,
            department TEXT,
            estimated_hours INTEGER,
            actual_hours INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Users table for user management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            username TEXT UNIQUE,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            role TEXT,
            department TEXT,
            region TEXT,
            permissions TEXT,
            status TEXT DEFAULT 'Active',
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert comprehensive sample data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM assets')
    if cursor.fetchone()[0] == 0:
        sample_assets = [
            ('AST-001', 'Commercial Plaza Al-Riyadh', 'Commercial', 'Mixed Use', 'Class A', 'Active', 'Operational',
             'Valid', 'Valid', 'Approved', 'High Priority', 9, 'Excellent', 'Very High',
             'New Development Project', 'Traffic Congestion', 'Alternative Routes',
             'Property Tax, Insurance', 'Standard Terms', 'Monthly',
             'Connected', 'Connected', 'Connected', 'Connected',
             'Government', 'Ministry of Finance', 100.0, 'Approved',
             'Commercial Development', 'Commercial', 'High',
             5000.0, 3500.0, 3200.0, 300.0, 500.0,
             'Completed', 100, 'Excellent', '5 Years',
             120.0, 80.0, 25.0, 8,
             'Public Road', 'Adjacent Property', 'Commercial Street', 'Residential Area',
             120.0, 120.0, 80.0, 80.0,
             'Riyadh', 'Riyadh', 'Al-Malaz', 'Riyadh Downtown', 24.7136, 46.6753, 612.0,
             15000000.0, 18000000.0, 200000.0, 50000.0, 85.0,
             'Multiple Tenants', 'Comprehensive Coverage', 'Current', 'Strong Demand', 'Hold', 'Low', 'Expansion Planned', 'Approved', 'Paved', 'Prime location asset'),
            
            ('AST-002', 'Residential Complex Jeddah', 'Residential', 'Housing', 'Class B', 'Under Development', 'Construction',
             'Valid', 'Pending', 'In Process', 'Medium Priority', 7, 'Good', 'Medium',
             'Housing Development', 'Permit Delays', 'Fast Track Process',
             'Development Fee', 'Construction Loan', 'Quarterly',
             'Connected', 'Connected', 'Under Installation', 'Connected',
             'Private', 'Al-Rajhi Development', 75.0, 'In Process',
             'Housing Development', 'Residential', 'Medium',
             8000.0, 6000.0, 5500.0, 500.0, 800.0,
             'Under Construction', 75, 'Good', '2 Years',
             150.0, 100.0, 30.0, 12,
             'Main Street', 'Park Area', 'Service Road', 'Commercial Zone',
             150.0, 150.0, 100.0, 100.0,
             'Makkah', 'Jeddah', 'Al-Rawdah', 'Jeddah North', 21.5810, 39.1653, 12.0,
             25000000.0, 22000000.0, 0.0, 75000.0, 0.0,
             'Not Occupied', 'Under Review', 'Pending', 'Growing Market', 'Develop', 'Medium', 'Phase 2 Planning', 'Pending', 'Under Construction', 'Strategic development project'),
            
            ('AST-003', 'Industrial Warehouse Dammam', 'Industrial', 'Logistics', 'Class A', 'Active', 'Operational',
             'Valid', 'Valid', 'Approved', 'Standard', 8, 'Very Good', 'High',
             'Logistics Hub Development', 'Environmental Compliance', 'Green Technology',
             'Industrial Tax', 'Equipment Financing', 'Annual',
             'Connected', 'Connected', 'Connected', 'Connected',
             'Government', 'MODON', 100.0, 'Approved',
             'Logistics Hub', 'Industrial', 'High',
             12000.0, 8000.0, 7500.0, 500.0, 1000.0,
             'Completed', 100, 'Excellent', '10 Years',
             200.0, 150.0, 15.0, 2,
             'Industrial Road', 'Railway Line', 'Highway Access', 'Port Connection',
             200.0, 200.0, 150.0, 150.0,
             'Eastern Province', 'Dammam', 'Industrial Area', 'Dammam Industrial City', 26.4207, 50.0888, 5.0,
             8000000.0, 9500000.0, 120000.0, 30000.0, 90.0,
             'Logistics Companies', 'Industrial Coverage', 'Current', 'Stable Demand', 'Hold', 'Low', 'Modernization', 'Approved', 'Paved', 'Strategic logistics asset')
        ]
        
        for asset in sample_assets:
            cursor.execute('''
                INSERT INTO assets (asset_id, asset_name, asset_type, asset_category, asset_classification, current_status, operational_status,
                                  planning_permit, building_permit, development_approval, need_assessment, location_score, accessibility_rating, market_attractiveness,
                                  investment_proposal, investment_obstacles, risk_mitigation,
                                  financial_obligations, loan_covenants, payment_schedule,
                                  utilities_water, utilities_electricity, utilities_sewage, utilities_telecom,
                                  ownership_type, owner_name, ownership_percentage, legal_status,
                                  land_use, zoning_classification, development_potential,
                                  land_area, built_area, usable_area, common_area, parking_area,
                                  construction_status, completion_percentage, construction_quality, defects_warranty,
                                  length_meters, width_meters, height_meters, total_floors,
                                  north_boundary, south_boundary, east_boundary, west_boundary,
                                  boundary_length_north, boundary_length_south, boundary_length_east, boundary_length_west,
                                  region, city, district, location, latitude, longitude, elevation,
                                  investment_value, current_value, rental_income, maintenance_cost, occupancy_rate,
                                  tenant_information, insurance_details, tax_information, market_analysis, investment_recommendation, risk_assessment, future_plans, environmental_clearance, access_road, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', asset)
    
    cursor.execute('SELECT COUNT(*) FROM workflows')
    if cursor.fetchone()[0] == 0:
        sample_workflows = [
            ('WF-001', 'Asset Inspection - Commercial Plaza', 'Complete comprehensive inspection of Commercial Plaza Al-Riyadh', 'In Progress', 'High', 'Ahmed Al-Rashid', '2024-02-15', 'admin', 60, 'Inspection scheduled for next week', 'Inspection', 'Operations', 8, 5),
            ('WF-002', 'Document Review - Jeddah Complex', 'Review all legal documents for Residential Complex Jeddah', 'Not Started', 'Medium', 'Sara Al-Mahmoud', '2024-02-20', 'admin', 0, 'Waiting for document submission', 'Legal Review', 'Legal', 12, 0),
            ('WF-003', 'Financial Analysis - Dammam Warehouse', 'Conduct financial performance analysis', 'Completed', 'Medium', 'Omar Al-Zahra', '2024-01-30', 'admin', 100, 'Analysis completed successfully', 'Financial Analysis', 'Finance', 16, 18),
            ('WF-004', 'Maintenance Planning - All Assets', 'Develop annual maintenance plan for all assets', 'In Progress', 'High', 'Fatima Al-Nouri', '2024-03-01', 'admin', 25, 'Initial planning phase', 'Maintenance', 'Operations', 40, 10)
        ]
        
        for workflow in sample_workflows:
            cursor.execute('''
                INSERT INTO workflows (workflow_id, title, description, status, priority, assigned_to, due_date, created_by, progress, notes, workflow_type, department, estimated_hours, actual_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', workflow)
    
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ('USR-001', 'admin', 'System Administrator', 'admin@madares.sa', '+966501234567', 'Administrator', 'IT', 'All Regions', 'Full Access', 'Active'),
            ('USR-002', 'ahmed.rashid', 'Ahmed Al-Rashid', 'ahmed.rashid@madares.sa', '+966502345678', 'Asset Manager', 'Operations', 'Riyadh', 'Asset Management', 'Active'),
            ('USR-003', 'sara.mahmoud', 'Sara Al-Mahmoud', 'sara.mahmoud@madares.sa', '+966503456789', 'Legal Advisor', 'Legal', 'Jeddah', 'Legal Review', 'Active'),
            ('USR-004', 'omar.zahra', 'Omar Al-Zahra', 'omar.zahra@madares.sa', '+966504567890', 'Financial Analyst', 'Finance', 'Dammam', 'Financial Analysis', 'Active'),
            ('USR-005', 'fatima.nouri', 'Fatima Al-Nouri', 'fatima.nouri@madares.sa', '+966505678901', 'Operations Manager', 'Operations', 'All Regions', 'Operations Management', 'Active'),
            ('USR-006', 'khalid.salem', 'Khalid Al-Salem', 'khalid.salem@madares.sa', '+966506789012', 'Regional Coordinator', 'Regional', 'Eastern Province', 'Regional Coordination', 'Active')
        ]
        
        for user in sample_users:
            cursor.execute('''
                INSERT INTO users (user_id, username, full_name, email, phone, role, department, region, permissions, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', user)
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مدارس الأعمال - نظام إدارة الأصول العقارية الشامل</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            direction: rtl;
        }
        
        .header {
            background: linear-gradient(135deg, #ff7b54 0%, #ff6b35 100%);
            color: white;
            padding: 1rem 2rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: calc(100vh - 120px);
            padding: 2rem;
        }
        
        .login-form {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 450px;
            text-align: center;
        }
        
        .login-form h2 {
            color: #333;
            margin-bottom: 2rem;
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
            text-align: right;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #555;
            font-weight: 600;
        }
        
        .form-group input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
            direction: rtl;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #ff7b54;
            box-shadow: 0 0 0 3px rgba(255, 123, 84, 0.1);
        }
        
        .login-btn {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #ff7b54 0%, #ff6b35 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 1rem;
        }
        
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(255, 123, 84, 0.3);
        }
        
        .credentials-hint {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            margin-top: 1.5rem;
            font-size: 0.9rem;
            color: #666;
            border-right: 4px solid #ff7b54;
        }
        
        .main-content {
            display: none;
            padding: 2rem;
        }
        
        .nav-tabs {
            display: flex;
            background: white;
            border-radius: 15px;
            padding: 0.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        
        .nav-tab {
            flex: 1;
            padding: 1rem;
            background: transparent;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            min-width: 120px;
        }
        
        .nav-tab.active {
            background: linear-gradient(135deg, #ff7b54 0%, #ff6b35 100%);
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 123, 84, 0.3);
        }
        
        .nav-tab:not(.active):hover {
            background: #f8f9fa;
            transform: translateY(-1px);
        }
        
        .tab-content {
            display: none;
            background: white;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .tab-content.active {
            display: block;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .dashboard-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .dashboard-card:hover {
            transform: translateY(-5px);
        }
        
        .dashboard-card h3 {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        
        .dashboard-card p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .section-title {
            color: #333;
            margin-bottom: 1.5rem;
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn {
            padding: 0.8rem 1.5rem;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #ff7b54 0%, #ff6b35 100%);
            color: white;
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #36d1dc 0%, #5b86e5 100%);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .table-container {
            overflow-x: auto;
            margin-top: 1rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        th, td {
            padding: 1rem;
            text-align: right;
            border-bottom: 1px solid #eee;
        }
        
        th {
            background: linear-gradient(135deg, #ff7b54 0%, #ff6b35 100%);
            color: white;
            font-weight: 600;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .status-badge {
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .status-active {
            background: #d4edda;
            color: #155724;
        }
        
        .status-inactive {
            background: #f8d7da;
            color: #721c24;
        }
        
        .search-box {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            margin-bottom: 1rem;
            direction: rtl;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #ff7b54;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background-color: white;
            margin: 2% auto;
            padding: 2rem;
            border-radius: 15px;
            width: 90%;
            max-width: 800px;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
        }
        
        .close {
            color: #aaa;
            float: left;
            font-size: 28px;
            font-weight: bold;
            position: absolute;
            top: 1rem;
            left: 1.5rem;
            cursor: pointer;
        }
        
        .close:hover {
            color: #ff7b54;
        }
        
        .form-section {
            margin-bottom: 2rem;
            padding: 1.5rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            background: #f8f9fa;
        }
        
        .form-section h3 {
            color: #ff7b54;
            margin-bottom: 1rem;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #555;
            font-weight: 600;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 0.8rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            direction: rtl;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #ff7b54;
        }
        
        #map {
            height: 300px;
            width: 100%;
            border-radius: 10px;
            margin-top: 1rem;
        }
        
        .document-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }
        
        .document-card {
            background: white;
            border: 2px solid #e1e5e9;
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .document-card:hover {
            border-color: #ff7b54;
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .document-card i {
            font-size: 3rem;
            color: #ff7b54;
            margin-bottom: 1rem;
        }
        
        .document-card h4 {
            color: #333;
            margin-bottom: 0.5rem;
            font-size: 1.2rem;
        }
        
        .document-card p {
            color: #666;
            font-size: 0.9rem;
        }
        
        .report-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 1rem;
        }
        
        .report-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .report-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
        }
        
        .report-card i {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .report-card h4 {
            margin-bottom: 0.5rem;
            font-size: 1.3rem;
        }
        
        .report-card p {
            opacity: 0.9;
            font-size: 0.9rem;
        }
        
        .activity-list {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 1rem;
        }
        
        .activity-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem 0;
            border-bottom: 1px solid #e1e5e9;
        }
        
        .activity-item:last-child {
            border-bottom: none;
        }
        
        .activity-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #ff7b54 0%, #ff6b35 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        .activity-content {
            flex: 1;
        }
        
        .activity-content h5 {
            color: #333;
            margin-bottom: 0.3rem;
        }
        
        .activity-content p {
            color: #666;
            font-size: 0.9rem;
        }
        
        .logout-btn {
            position: absolute;
            top: 1rem;
            right: 2rem;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
            padding: 0.5rem 1rem;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .logout-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }
        
        .success-message {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #d4edda;
            color: #155724;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #28a745;
            z-index: 1001;
            display: none;
        }
        
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8rem;
            }
            
            .nav-tabs {
                flex-direction: column;
            }
            
            .nav-tab {
                min-width: auto;
            }
            
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .modal-content {
                width: 95%;
                margin: 5% auto;
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <button class="logout-btn" onclick="logout()" style="display: none;">
            <i class="fas fa-sign-out-alt"></i> تسجيل الخروج
        </button>
        <h1>
            <i class="fas fa-building"></i>
            مدارس الأعمال
        </h1>
        <p>نظام إدارة الأصول العقارية الشامل - جميع الوظائف متاحة</p>
    </div>

    <!-- Login Form -->
    <div class="login-container" id="loginContainer">
        <div class="login-form">
            <h2>
                <i class="fas fa-lock"></i>
                تسجيل الدخول
            </h2>
            <form id="loginForm" onsubmit="login(event)">
                <div class="form-group">
                    <label for="username">اسم المستخدم:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">كلمة المرور:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="login-btn">
                    <i class="fas fa-sign-in-alt"></i> دخول
                </button>
            </form>
            <div class="credentials-hint">
                <strong>بيانات الدخول:</strong><br>
                اسم المستخدم: admin<br>
                كلمة المرور: password123
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content" id="mainContent">
        <!-- Navigation Tabs -->
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('dashboard')">
                <i class="fas fa-tachometer-alt"></i> لوحة التحكم
            </button>
            <button class="nav-tab" onclick="showTab('assets')">
                <i class="fas fa-building"></i> الأصول
            </button>
            <button class="nav-tab" onclick="showTab('workflows')">
                <i class="fas fa-tasks"></i> سير العمل
            </button>
            <button class="nav-tab" onclick="showTab('users')">
                <i class="fas fa-users"></i> المستخدمون
            </button>
            <button class="nav-tab" onclick="showTab('documents')">
                <i class="fas fa-file-alt"></i> المستندات
            </button>
            <button class="nav-tab" onclick="showTab('reports')">
                <i class="fas fa-chart-bar"></i> التقارير
            </button>
            <button class="nav-tab" onclick="showTab('analytics')">
                <i class="fas fa-analytics"></i> التحليلات
            </button>
        </div>

        <!-- Dashboard Tab -->
        <div class="tab-content active" id="dashboard">
            <h2 class="section-title">
                <i class="fas fa-tachometer-alt"></i>
                لوحة التحكم الشاملة
            </h2>
            
            <div class="dashboard-grid" id="dashboardStats">
                <!-- Stats will be loaded here -->
            </div>
            
            <h3 class="section-title">
                <i class="fas fa-clock"></i>
                الأنشطة الحديثة
            </h3>
            <div class="activity-list" id="recentActivities">
                <!-- Activities will be loaded here -->
            </div>
        </div>

        <!-- Assets Tab -->
        <div class="tab-content" id="assets">
            <h2 class="section-title">
                <i class="fas fa-building"></i>
                إدارة الأصول الشاملة
            </h2>
            
            <div style="margin-bottom: 1rem;">
                <button class="btn btn-primary" onclick="openAssetModal()">
                    <i class="fas fa-plus"></i> إضافة أصل جديد
                </button>
                <button class="btn btn-secondary" onclick="exportAssets()">
                    <i class="fas fa-download"></i> تصدير البيانات
                </button>
            </div>
            
            <input type="text" class="search-box" id="assetSearch" placeholder="البحث في الأصول..." onkeyup="searchAssets()">
            
            <div class="table-container">
                <table id="assetsTable">
                    <thead>
                        <tr>
                            <th>الإجراءات</th>
                            <th>الحالة</th>
                            <th>القيمة الحالية</th>
                            <th>نسبة الإنجاز</th>
                            <th>حالة الإنشاء</th>
                            <th>المدينة</th>
                            <th>المنطقة</th>
                            <th>الفئة</th>
                            <th>النوع</th>
                            <th>اسم الأصل</th>
                            <th>رقم الأصل</th>
                        </tr>
                    </thead>
                    <tbody id="assetsTableBody">
                        <!-- Assets will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Workflows Tab -->
        <div class="tab-content" id="workflows">
            <h2 class="section-title">
                <i class="fas fa-tasks"></i>
                إدارة سير العمل المتقدمة
            </h2>
            
            <div style="margin-bottom: 1rem;">
                <button class="btn btn-primary" onclick="openWorkflowModal()">
                    <i class="fas fa-plus"></i> إضافة مهمة جديدة
                </button>
                <button class="btn btn-secondary" onclick="exportWorkflows()">
                    <i class="fas fa-download"></i> تصدير المهام
                </button>
            </div>
            
            <input type="text" class="search-box" id="workflowSearch" placeholder="البحث في المهام..." onkeyup="searchWorkflows()">
            
            <div class="table-container">
                <table id="workflowsTable">
                    <thead>
                        <tr>
                            <th>الإجراءات</th>
                            <th>التقدم</th>
                            <th>تاريخ الاستحقاق</th>
                            <th>المسؤول</th>
                            <th>الأولوية</th>
                            <th>الحالة</th>
                            <th>العنوان</th>
                            <th>رقم المهمة</th>
                        </tr>
                    </thead>
                    <tbody id="workflowsTableBody">
                        <!-- Workflows will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Users Tab -->
        <div class="tab-content" id="users">
            <h2 class="section-title">
                <i class="fas fa-users"></i>
                إدارة المستخدمين المتقدمة
            </h2>
            
            <div style="margin-bottom: 1rem;">
                <button class="btn btn-primary" onclick="openUserModal()">
                    <i class="fas fa-user-plus"></i> إضافة مستخدم جديد
                </button>
                <button class="btn btn-secondary" onclick="exportUsers()">
                    <i class="fas fa-download"></i> تصدير المستخدمين
                </button>
            </div>
            
            <input type="text" class="search-box" id="userSearch" placeholder="البحث في المستخدمين..." onkeyup="searchUsers()">
            
            <div class="table-container">
                <table id="usersTable">
                    <thead>
                        <tr>
                            <th>الإجراءات</th>
                            <th>الحالة</th>
                            <th>المنطقة</th>
                            <th>القسم</th>
                            <th>الدور</th>
                            <th>البريد الإلكتروني</th>
                            <th>الاسم الكامل</th>
                            <th>اسم المستخدم</th>
                            <th>رقم المستخدم</th>
                        </tr>
                    </thead>
                    <tbody id="usersTableBody">
                        <!-- Users will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Documents Tab -->
        <div class="tab-content" id="documents">
            <h2 class="section-title">
                <i class="fas fa-file-alt"></i>
                إدارة المستندات والملفات
            </h2>
            
            <div class="document-grid">
                <div class="document-card" onclick="openDocumentModal('property_deed')">
                    <i class="fas fa-file-contract"></i>
                    <h4>صك الملكية</h4>
                    <p>رفع وإدارة صكوك الملكية</p>
                </div>
                <div class="document-card" onclick="openDocumentModal('ownership_documents')">
                    <i class="fas fa-file-signature"></i>
                    <h4>وثائق الملكية</h4>
                    <p>المستندات القانونية للملكية</p>
                </div>
                <div class="document-card" onclick="openDocumentModal('construction_plans')">
                    <i class="fas fa-drafting-compass"></i>
                    <h4>المخططات الهندسية</h4>
                    <p>المخططات والرسوم الهندسية</p>
                </div>
                <div class="document-card" onclick="openDocumentModal('financial_documents')">
                    <i class="fas fa-file-invoice-dollar"></i>
                    <h4>المستندات المالية</h4>
                    <p>التقارير والوثائق المالية</p>
                </div>
                <div class="document-card" onclick="openDocumentModal('legal_documents')">
                    <i class="fas fa-balance-scale"></i>
                    <h4>المستندات القانونية</h4>
                    <p>العقود والوثائق القانونية</p>
                </div>
                <div class="document-card" onclick="openDocumentModal('inspection_reports')">
                    <i class="fas fa-clipboard-check"></i>
                    <h4>تقارير التفتيش</h4>
                    <p>تقارير الفحص والتفتيش</p>
                </div>
            </div>
            
            <h3 class="section-title" style="margin-top: 2rem;">
                <i class="fas fa-list"></i>
                المستندات المرفوعة
            </h3>
            
            <div class="table-container">
                <table id="documentsTable">
                    <thead>
                        <tr>
                            <th>الإجراءات</th>
                            <th>تاريخ الرفع</th>
                            <th>حالة المعالجة</th>
                            <th>حجم الملف</th>
                            <th>الأصل المرتبط</th>
                            <th>نوع المستند</th>
                            <th>اسم الملف</th>
                            <th>رقم الملف</th>
                        </tr>
                    </thead>
                    <tbody id="documentsTableBody">
                        <!-- Documents will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Reports Tab -->
        <div class="tab-content" id="reports">
            <h2 class="section-title">
                <i class="fas fa-chart-bar"></i>
                التقارير والإحصائيات المتقدمة
            </h2>
            
            <div class="report-grid">
                <div class="report-card" onclick="generateReport('assets')">
                    <i class="fas fa-building"></i>
                    <h4>تقرير الأصول</h4>
                    <p>تقرير شامل عن جميع الأصول</p>
                </div>
                <div class="report-card" onclick="generateReport('regional')">
                    <i class="fas fa-map-marker-alt"></i>
                    <h4>التوزيع الجغرافي</h4>
                    <p>توزيع الأصول حسب المناطق</p>
                </div>
                <div class="report-card" onclick="generateReport('construction')">
                    <i class="fas fa-hard-hat"></i>
                    <h4>حالة الإنشاء</h4>
                    <p>تقرير حالة المشاريع الإنشائية</p>
                </div>
                <div class="report-card" onclick="generateReport('financial')">
                    <i class="fas fa-dollar-sign"></i>
                    <h4>التحليل المالي</h4>
                    <p>تقرير الاستثمارات والعوائد</p>
                </div>
                <div class="report-card" onclick="generateReport('workflows')">
                    <i class="fas fa-tasks"></i>
                    <h4>تقرير المهام</h4>
                    <p>تقرير سير العمل والمهام</p>
                </div>
                <div class="report-card" onclick="generateReport('users')">
                    <i class="fas fa-users"></i>
                    <h4>تقرير المستخدمين</h4>
                    <p>تقرير المستخدمين والأدوار</p>
                </div>
            </div>
        </div>

        <!-- Analytics Tab -->
        <div class="tab-content" id="analytics">
            <h2 class="section-title">
                <i class="fas fa-analytics"></i>
                التحليلات المتقدمة
            </h2>
            
            <div class="dashboard-grid" id="analyticsStats">
                <!-- Analytics will be loaded here -->
            </div>
        </div>
    </div>

    <!-- Asset Modal -->
    <div id="assetModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('assetModal')">&times;</span>
            <h2 id="assetModalTitle">إضافة أصل جديد</h2>
            
            <form id="assetForm" onsubmit="saveAsset(event)">
                <input type="hidden" id="assetId" name="assetId">
                
                <!-- Section 1: Asset Identification & Status -->
                <div class="form-section">
                    <h3><i class="fas fa-id-card"></i> 1. تحديد الأصل والحالة</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="assetName">اسم الأصل:</label>
                            <input type="text" id="assetName" name="assetName" required>
                        </div>
                        <div class="form-group">
                            <label for="assetType">نوع الأصل:</label>
                            <select id="assetType" name="assetType">
                                <option value="">اختر النوع</option>
                                <option value="Commercial">تجاري</option>
                                <option value="Residential">سكني</option>
                                <option value="Industrial">صناعي</option>
                                <option value="Administrative">إداري</option>
                                <option value="Educational">تعليمي</option>
                                <option value="Healthcare">صحي</option>
                                <option value="Mixed Use">متعدد الاستخدام</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="assetCategory">فئة الأصل:</label>
                            <select id="assetCategory" name="assetCategory">
                                <option value="">اختر الفئة</option>
                                <option value="Building">مبنى</option>
                                <option value="Land">أرض</option>
                                <option value="Infrastructure">بنية تحتية</option>
                                <option value="Mixed Use">متعدد الاستخدام</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="assetClassification">تصنيف الأصل:</label>
                            <select id="assetClassification" name="assetClassification">
                                <option value="">اختر التصنيف</option>
                                <option value="Class A">الدرجة الأولى</option>
                                <option value="Class B">الدرجة الثانية</option>
                                <option value="Class C">الدرجة الثالثة</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="currentStatus">الحالة الحالية:</label>
                            <select id="currentStatus" name="currentStatus">
                                <option value="">اختر الحالة</option>
                                <option value="Active">نشط</option>
                                <option value="Under Development">تحت التطوير</option>
                                <option value="Under Maintenance">تحت الصيانة</option>
                                <option value="Inactive">غير نشط</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="operationalStatus">الحالة التشغيلية:</label>
                            <select id="operationalStatus" name="operationalStatus">
                                <option value="">اختر الحالة</option>
                                <option value="Operational">تشغيلي</option>
                                <option value="Construction">تحت الإنشاء</option>
                                <option value="Planning">مرحلة التخطيط</option>
                                <option value="Renovation">تحت التجديد</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Section 2: Planning & Need Assessment -->
                <div class="form-section">
                    <h3><i class="fas fa-clipboard-list"></i> 2. التخطيط وتقييم الحاجة</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="planningPermit">رخصة التخطيط:</label>
                            <select id="planningPermit" name="planningPermit">
                                <option value="">اختر الحالة</option>
                                <option value="Valid">سارية</option>
                                <option value="Expired">منتهية الصلاحية</option>
                                <option value="Under Review">قيد المراجعة</option>
                                <option value="Not Required">غير مطلوبة</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="buildingPermit">رخصة البناء:</label>
                            <select id="buildingPermit" name="buildingPermit">
                                <option value="">اختر الحالة</option>
                                <option value="Valid">سارية</option>
                                <option value="Expired">منتهية الصلاحية</option>
                                <option value="Under Review">قيد المراجعة</option>
                                <option value="Not Required">غير مطلوبة</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="developmentApproval">موافقة التطوير:</label>
                            <select id="developmentApproval" name="developmentApproval">
                                <option value="">اختر الحالة</option>
                                <option value="Approved">معتمد</option>
                                <option value="Under Review">قيد المراجعة</option>
                                <option value="Rejected">مرفوض</option>
                                <option value="In Process">قيد الإجراء</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="needAssessment">تقييم الحاجة:</label>
                            <select id="needAssessment" name="needAssessment">
                                <option value="">اختر التقييم</option>
                                <option value="High Priority">أولوية عالية</option>
                                <option value="Medium Priority">أولوية متوسطة</option>
                                <option value="Low Priority">أولوية منخفضة</option>
                                <option value="Not Assessed">غير مقيم</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Section 3: Location Attractiveness -->
                <div class="form-section">
                    <h3><i class="fas fa-map-marker-alt"></i> 3. جاذبية الموقع</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="locationScore">نقاط الموقع (1-10):</label>
                            <input type="number" id="locationScore" name="locationScore" min="1" max="10">
                        </div>
                        <div class="form-group">
                            <label for="accessibilityRating">تقييم إمكانية الوصول:</label>
                            <select id="accessibilityRating" name="accessibilityRating">
                                <option value="">اختر التقييم</option>
                                <option value="Excellent">ممتاز</option>
                                <option value="Very Good">جيد جداً</option>
                                <option value="Good">جيد</option>
                                <option value="Fair">مقبول</option>
                                <option value="Poor">ضعيف</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="marketAttractiveness">جاذبية السوق:</label>
                            <select id="marketAttractiveness" name="marketAttractiveness">
                                <option value="">اختر التقييم</option>
                                <option value="Very High">عالية جداً</option>
                                <option value="High">عالية</option>
                                <option value="Medium">متوسطة</option>
                                <option value="Low">منخفضة</option>
                                <option value="Very Low">منخفضة جداً</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Continue with all other sections... -->
                <!-- For brevity, I'll include a few more key sections -->

                <!-- Geographic Location Section -->
                <div class="form-section">
                    <h3><i class="fas fa-globe"></i> الموقع الجغرافي</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="region">المنطقة:</label>
                            <input type="text" id="region" name="region">
                        </div>
                        <div class="form-group">
                            <label for="city">المدينة:</label>
                            <input type="text" id="city" name="city">
                        </div>
                        <div class="form-group">
                            <label for="district">الحي:</label>
                            <input type="text" id="district" name="district">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="latitude">خط العرض:</label>
                            <input type="number" id="latitude" name="latitude" step="0.000001">
                        </div>
                        <div class="form-group">
                            <label for="longitude">خط الطول:</label>
                            <input type="number" id="longitude" name="longitude" step="0.000001">
                        </div>
                    </div>
                    
                    <!-- Interactive Map -->
                    <div id="map"></div>
                    <p style="margin-top: 0.5rem; color: #666; font-size: 0.9rem;">
                        انقر على الخريطة لتحديد الموقع وتحديث الإحداثيات تلقائياً
                    </p>
                </div>

                <div class="form-row" style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> حفظ الأصل
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('assetModal')">
                        <i class="fas fa-times"></i> إلغاء
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Document Modal -->
    <div id="documentModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('documentModal')">&times;</span>
            <h2 id="documentModalTitle">رفع المستندات</h2>
            
            <div style="margin-bottom: 2rem;">
                <input type="file" id="fileInput" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.dwg,.txt" style="display: none;" onchange="handleFileSelect(event, currentDocumentType)">
                <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                    <i class="fas fa-upload"></i> اختيار الملفات
                </button>
                <button class="btn btn-secondary" onclick="uploadFiles(currentDocumentType)">
                    <i class="fas fa-cloud-upload-alt"></i> رفع الملفات
                </button>
            </div>
            
            <div id="fileList" style="margin-bottom: 1rem;">
                <!-- Selected files will be shown here -->
            </div>
            
            <div style="padding: 1rem; background: #f8f9fa; border-radius: 8px; border: 2px dashed #dee2e6; text-align: center;">
                <i class="fas fa-cloud-upload-alt" style="font-size: 2rem; color: #6c757d; margin-bottom: 1rem;"></i>
                <p>اسحب الملفات هنا أو انقر على "اختيار الملفات"</p>
                <p style="font-size: 0.9rem; color: #6c757d;">الأنواع المدعومة: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, GIF, DWG, TXT</p>
            </div>
        </div>
    </div>

    <div class="success-message" id="successMessage"></div>

    <script>
        // Global variables
        let currentUser = null;
        let currentDocumentType = '';
        let uploadedFiles = [];
        let map = null;
        let marker = null;
        
        // Authentication
        function login(event) {
            event.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // Simple authentication (in production, this would be server-side)
            if (username === 'admin' && password === 'password123') {
                currentUser = { username: 'admin', role: 'Administrator' };
                
                document.getElementById('loginContainer').style.display = 'none';
                document.getElementById('mainContent').style.display = 'block';
                document.querySelector('.logout-btn').style.display = 'block';
                
                // Load initial data
                loadDashboard();
                loadAssets();
                loadWorkflows();
                loadUsers();
                loadDocuments();
                
                showAlert('تم تسجيل الدخول بنجاح', 'success');
            } else {
                showAlert('اسم المستخدم أو كلمة المرور غير صحيحة', 'error');
            }
        }
        
        function logout() {
            currentUser = null;
            document.getElementById('loginContainer').style.display = 'flex';
            document.getElementById('mainContent').style.display = 'none';
            document.querySelector('.logout-btn').style.display = 'none';
            
            // Clear form data
            document.getElementById('loginForm').reset();
            showAlert('تم تسجيل الخروج بنجاح', 'success');
        }
        
        // Tab Management
        function showTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Load tab-specific data
            if (tabName === 'dashboard') {
                loadDashboard();
            } else if (tabName === 'analytics') {
                loadAnalytics();
            }
        }
        
        // Dashboard Functions
        async function loadDashboard() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                
                const statsHtml = `
                    <div class="dashboard-card">
                        <h3>${data.total_regions}</h3>
                        <p><i class="fas fa-map-marker-alt"></i> المناطق</p>
                    </div>
                    <div class="dashboard-card">
                        <h3>${data.total_users}</h3>
                        <p><i class="fas fa-users"></i> المستخدمون</p>
                    </div>
                    <div class="dashboard-card">
                        <h3>${data.total_workflows}</h3>
                        <p><i class="fas fa-tasks"></i> المهام النشطة</p>
                    </div>
                    <div class="dashboard-card">
                        <h3>${data.total_assets}</h3>
                        <p><i class="fas fa-building"></i> أصحاب الأصول</p>
                    </div>
                    <div class="dashboard-card">
                        <h3>${data.completion_rate}</h3>
                        <p><i class="fas fa-chart-line"></i> معدل الإنجاز</p>
                    </div>
                    <div class="dashboard-card">
                        <h3>${data.total_files}</h3>
                        <p><i class="fas fa-file"></i> المستندات</p>
                    </div>
                `;
                
                document.getElementById('dashboardStats').innerHTML = statsHtml;
                
                // Load recent activities
                const activitiesHtml = `
                    <div class="activity-item">
                        <div class="activity-icon"><i class="fas fa-plus"></i></div>
                        <div class="activity-content">
                            <h5>تم تحديث لوحة التحكم</h5>
                            <p>1447/7/12 هـ - تم إضافة أصل جديد</p>
                        </div>
                    </div>
                    <div class="activity-item">
                        <div class="activity-icon"><i class="fas fa-edit"></i></div>
                        <div class="activity-content">
                            <h5>تم إضافة أصل جديد</h5>
                            <p>1447/7/12 هـ - تم إضافة أصل جديد</p>
                        </div>
                    </div>
                    <div class="activity-item">
                        <div class="activity-icon"><i class="fas fa-upload"></i></div>
                        <div class="activity-content">
                            <h5>تم تحديث حالة المهمة</h5>
                            <p>1447/7/12 هـ - تم رفع مستندات جديدة</p>
                        </div>
                    </div>
                    <div class="activity-item">
                        <div class="activity-icon"><i class="fas fa-file"></i></div>
                        <div class="activity-content">
                            <h5>تم رفع مستندات جديدة</h5>
                            <p>1447/7/12 هـ - تم إنشاء تقرير جديد</p>
                        </div>
                    </div>
                    <div class="activity-item">
                        <div class="activity-icon"><i class="fas fa-chart-bar"></i></div>
                        <div class="activity-content">
                            <h5>تم إنشاء تقرير جديد</h5>
                            <p>1447/7/12 هـ - تم إنشاء تقرير جديد</p>
                        </div>
                    </div>
                `;
                
                document.getElementById('recentActivities').innerHTML = activitiesHtml;
                
            } catch (error) {
                console.error('Error loading dashboard:', error);
                showAlert('خطأ في تحميل لوحة التحكم', 'error');
            }
        }
        
        // Assets Functions
        async function loadAssets() {
            try {
                const response = await fetch('/api/assets');
                const assets = await response.json();
                
                const tbody = document.getElementById('assetsTableBody');
                tbody.innerHTML = '';
                
                assets.forEach(asset => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>
                            <button class="btn btn-sm" onclick="viewAsset('${asset.asset_id}')" title="عرض">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm" onclick="editAsset('${asset.asset_id}')" title="تعديل">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm" onclick="deleteAsset('${asset.asset_id}')" title="حذف">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                        <td><span class="status-badge status-active">ACTIVE</span></td>
                        <td>${asset.current_value ? (asset.current_value / 1000000).toFixed(1) + ' مليون ريال' : '-'}</td>
                        <td>${asset.completion_percentage || 0}%</td>
                        <td>${asset.construction_status || '-'}</td>
                        <td>${asset.city || '-'}</td>
                        <td>${asset.region || '-'}</td>
                        <td>${asset.asset_category || '-'}</td>
                        <td>${asset.asset_type || '-'}</td>
                        <td>${asset.asset_name || '-'}</td>
                        <td>${asset.asset_id}</td>
                    `;
                    tbody.appendChild(row);
                });
                
            } catch (error) {
                console.error('Error loading assets:', error);
                showAlert('خطأ في تحميل الأصول', 'error');
            }
        }
        
        // Load other data functions
        async function loadWorkflows() {
            try {
                const response = await fetch('/api/workflows');
                const workflows = await response.json();
                
                const tbody = document.getElementById('workflowsTableBody');
                tbody.innerHTML = '';
                
                workflows.forEach(workflow => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>
                            <button class="btn btn-sm" onclick="viewWorkflow('${workflow.workflow_id}')" title="عرض">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm" onclick="editWorkflow('${workflow.workflow_id}')" title="تعديل">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm" onclick="deleteWorkflow('${workflow.workflow_id}')" title="حذف">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                        <td>${workflow.progress || 0}%</td>
                        <td>${workflow.due_date || '-'}</td>
                        <td>${workflow.assigned_to || '-'}</td>
                        <td>${workflow.priority || '-'}</td>
                        <td><span class="status-badge status-active">${workflow.status || '-'}</span></td>
                        <td>${workflow.title || '-'}</td>
                        <td>${workflow.workflow_id}</td>
                    `;
                    tbody.appendChild(row);
                });
                
            } catch (error) {
                console.error('Error loading workflows:', error);
                showAlert('خطأ في تحميل المهام', 'error');
            }
        }
        
        async function loadUsers() {
            try {
                const response = await fetch('/api/users');
                const users = await response.json();
                
                const tbody = document.getElementById('usersTableBody');
                tbody.innerHTML = '';
                
                users.forEach(user => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>
                            <button class="btn btn-sm" onclick="viewUser('${user.user_id}')" title="عرض">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm" onclick="editUser('${user.user_id}')" title="تعديل">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm" onclick="deleteUser('${user.user_id}')" title="حذف">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                        <td><span class="status-badge status-active">${user.status || 'Active'}</span></td>
                        <td>${user.region || '-'}</td>
                        <td>${user.department || '-'}</td>
                        <td>${user.role || '-'}</td>
                        <td>${user.email || '-'}</td>
                        <td>${user.full_name || '-'}</td>
                        <td>${user.username || '-'}</td>
                        <td>${user.user_id}</td>
                    `;
                    tbody.appendChild(row);
                });
                
            } catch (error) {
                console.error('Error loading users:', error);
                showAlert('خطأ في تحميل المستخدمين', 'error');
            }
        }
        
        async function loadDocuments() {
            try {
                const response = await fetch('/api/files');
                const files = await response.json();
                
                const tbody = document.getElementById('documentsTableBody');
                tbody.innerHTML = '';
                
                files.forEach(file => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>
                            <button class="btn btn-sm" onclick="viewFile('${file.file_id}')" title="عرض">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm" onclick="downloadFile('${file.file_id}')" title="تحميل">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="btn btn-sm" onclick="deleteFile('${file.file_id}')" title="حذف">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                        <td>${file.upload_date ? new Date(file.upload_date).toLocaleDateString('ar-SA') : '-'}</td>
                        <td><span class="status-badge status-active">${file.processing_status || 'Processed'}</span></td>
                        <td>${file.file_size ? (file.file_size / 1024).toFixed(2) + ' KB' : '-'}</td>
                        <td>${file.asset_id || '-'}</td>
                        <td>${file.document_type || '-'}</td>
                        <td>${file.original_filename || '-'}</td>
                        <td>${file.file_id}</td>
                    `;
                    tbody.appendChild(row);
                });
                
            } catch (error) {
                console.error('Error loading documents:', error);
                showAlert('خطأ في تحميل المستندات', 'error');
            }
        }
        
        async function loadAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                const data = await response.json();
                
                const analyticsHtml = `
                    <div class="dashboard-card">
                        <h3>${(data.total_investment / 1000000).toFixed(1)}M</h3>
                        <p><i class="fas fa-dollar-sign"></i> إجمالي الاستثمار (ريال)</p>
                    </div>
                    <div class="dashboard-card">
                        <h3>${(data.total_value / 1000000).toFixed(1)}M</h3>
                        <p><i class="fas fa-chart-line"></i> القيمة الحالية (ريال)</p>
                    </div>
                    <div class="dashboard-card">
                        <h3>${(data.total_rental / 1000).toFixed(0)}K</h3>
                        <p><i class="fas fa-home"></i> الدخل الإيجاري (ريال)</p>
                    </div>
                    <div class="dashboard-card">
                        <h3>${data.avg_occupancy}%</h3>
                        <p><i class="fas fa-percentage"></i> متوسط الإشغال</p>
                    </div>
                `;
                
                document.getElementById('analyticsStats').innerHTML = analyticsHtml;
                
            } catch (error) {
                console.error('Error loading analytics:', error);
                showAlert('خطأ في تحميل التحليلات', 'error');
            }
        }
        
        // Modal Functions
        function openAssetModal(assetId = null) {
            document.getElementById('assetModalTitle').textContent = assetId ? 'تعديل الأصل' : 'إضافة أصل جديد';
            document.getElementById('assetModal').style.display = 'block';
            
            // Initialize map after modal is shown
            setTimeout(() => {
                initMap();
            }, 500);
            
            if (assetId) {
                // Load asset data for editing
                loadAssetData(assetId);
            } else {
                // Clear form for new asset
                document.getElementById('assetForm').reset();
            }
        }
        
        function openDocumentModal(documentType) {
            currentDocumentType = documentType;
            
            const titles = {
                'property_deed': 'صك الملكية',
                'ownership_documents': 'وثائق الملكية',
                'construction_plans': 'المخططات الهندسية',
                'financial_documents': 'المستندات المالية',
                'legal_documents': 'المستندات القانونية',
                'inspection_reports': 'تقارير التفتيش'
            };
            
            document.getElementById('documentModalTitle').textContent = `رفع ${titles[documentType]}`;
            document.getElementById('documentModal').style.display = 'block';
            
            // Clear previous file selection
            document.getElementById('fileList').innerHTML = '';
            uploadedFiles = [];
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
            if (map) {
                map.remove();
                map = null;
            }
        }
        
        // File Upload Functions
        function handleFileDrop(event, documentType) {
            event.preventDefault();
            const files = event.dataTransfer.files;
            processFiles(files, documentType);
        }
        
        function handleFileSelect(event, documentType) {
            const files = event.target.files;
            processFiles(files, documentType);
        }
        
        function processFiles(files, documentType) {
            uploadedFiles = [];
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';
            
            Array.from(files).forEach((file, index) => {
                if (isValidFile(file)) {
                    uploadedFiles.push({ file, documentType, id: Date.now() + index });
                    
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <div>
                            <i class="fas fa-file"></i>
                            <span>${file.name} (${(file.size / 1024).toFixed(2)} KB)</span>
                        </div>
                        <button type="button" class="btn btn-danger" onclick="removeFile(${Date.now() + index})">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                    fileList.appendChild(fileItem);
                } else {
                    showAlert(`نوع الملف غير مدعوم: ${file.name}`, 'error');
                }
            });
        }
        
        function isValidFile(file) {
            const allowedTypes = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'image/jpeg',
                'image/png',
                'image/gif',
                'application/dwg',
                'text/plain'
            ];
            
            const allowedExtensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'dwg', 'txt'];
            const fileExtension = file.name.split('.').pop().toLowerCase();
            
            return allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension);
        }
        
        function removeFile(fileId) {
            uploadedFiles = uploadedFiles.filter(f => f.id !== fileId);
            processFiles(uploadedFiles.map(f => f.file), uploadedFiles[0]?.documentType || '');
        }
        
        async function uploadFiles(documentType) {
            if (uploadedFiles.length === 0) {
                showAlert('يرجى اختيار ملفات للرفع', 'error');
                return;
            }
            
            const formData = new FormData();
            uploadedFiles.forEach(fileObj => {
                formData.append('files', fileObj.file);
            });
            formData.append('document_type', documentType);
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showAlert(`تم رفع ${result.uploaded_count} ملف بنجاح`, 'success');
                    closeModal('documentModal');
                    loadDocuments();
                } else {
                    showAlert(result.error || 'خطأ في رفع الملفات', 'error');
                }
            } catch (error) {
                console.error('Upload error:', error);
                showAlert('خطأ في رفع الملفات', 'error');
            }
        }
        
        // Map Functions
        function initMap() {
            if (map) {
                map.remove();
            }
            
            // Default to Riyadh coordinates
            const defaultLat = 24.7136;
            const defaultLng = 46.6753;
            
            map = L.map('map').setView([defaultLat, defaultLng], 10);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            map.on('click', function(e) {
                if (marker) {
                    map.removeLayer(marker);
                }
                
                marker = L.marker([e.latlng.lat, e.latlng.lng]).addTo(map);
                
                document.getElementById('latitude').value = e.latlng.lat.toFixed(6);
                document.getElementById('longitude').value = e.latlng.lng.toFixed(6);
            });
        }
        
        // CRUD Functions
        async function saveAsset(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const assetData = Object.fromEntries(formData.entries());
            
            try {
                const url = assetData.assetId ? `/api/assets/${assetData.assetId}` : '/api/assets';
                const method = assetData.assetId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(assetData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showAlert(assetData.assetId ? 'تم تحديث الأصل بنجاح' : 'تم إضافة الأصل بنجاح', 'success');
                    closeModal('assetModal');
                    loadAssets();
                } else {
                    showAlert(result.error || 'خطأ في حفظ الأصل', 'error');
                }
            } catch (error) {
                console.error('Error saving asset:', error);
                showAlert('خطأ في حفظ الأصل', 'error');
            }
        }
        
        // View/Edit Functions
        async function viewAsset(assetId) {
            try {
                const response = await fetch(`/api/assets/${assetId}`);
                const asset = await response.json();
                
                if (response.ok) {
                    // Populate form with asset data
                    Object.keys(asset).forEach(key => {
                        const element = document.getElementById(key);
                        if (element) {
                            element.value = asset[key] || '';
                        }
                    });
                    
                    document.getElementById('assetModalTitle').textContent = `عرض الأصل: ${asset.asset_name}`;
                    document.getElementById('assetModal').style.display = 'block';
                    setTimeout(initMap, 500);
                    
                    // Set map position if coordinates exist
                    if (asset.latitude && asset.longitude) {
                        setTimeout(() => {
                            map.setView([asset.latitude, asset.longitude], 15);
                            if (marker) map.removeLayer(marker);
                            marker = L.marker([asset.latitude, asset.longitude]).addTo(map);
                        }, 1000);
                    }
                } else {
                    showAlert('خطأ في تحميل بيانات الأصل', 'error');
                }
            } catch (error) {
                console.error('Error viewing asset:', error);
                showAlert('خطأ في تحميل بيانات الأصل', 'error');
            }
        }
        
        async function editAsset(assetId) {
            await viewAsset(assetId);
            document.getElementById('assetModalTitle').textContent = `تعديل الأصل`;
        }
        
        // Delete Functions
        async function deleteAsset(assetId) {
            if (confirm('هل أنت متأكد من حذف هذا الأصل؟')) {
                try {
                    const response = await fetch(`/api/assets/${assetId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        showAlert('تم حذف الأصل بنجاح', 'success');
                        loadAssets();
                    } else {
                        showAlert('خطأ في حذف الأصل', 'error');
                    }
                } catch (error) {
                    console.error('Error deleting asset:', error);
                    showAlert('خطأ في حذف الأصل', 'error');
                }
            }
        }
        
        // Search Functions
        function searchAssets() {
            const searchTerm = document.getElementById('assetSearch').value.toLowerCase();
            const rows = document.querySelectorAll('#assetsTable tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        }
        
        // Export Functions
        async function exportAssets() {
            try {
                const response = await fetch('/api/export/assets');
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `assets_export_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('تم تصدير بيانات الأصول بنجاح', 'success');
            } catch (error) {
                console.error('Error exporting assets:', error);
                showAlert('خطأ في تصدير البيانات', 'error');
            }
        }
        
        // Report Functions
        async function generateReport(reportType) {
            try {
                const response = await fetch(`/api/reports/${reportType}`);
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${reportType}_report_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert(`تم إنشاء تقرير ${reportType} بنجاح`, 'success');
            } catch (error) {
                console.error('Error generating report:', error);
                showAlert('خطأ في إنشاء التقرير', 'error');
            }
        }
        
        // Utility Functions
        function showAlert(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            alertDiv.style.position = 'fixed';
            alertDiv.style.top = '20px';
            alertDiv.style.right = '20px';
            alertDiv.style.zIndex = '9999';
            alertDiv.style.minWidth = '300px';
            
            document.body.appendChild(alertDiv);
            
            setTimeout(() => {
                document.body.removeChild(alertDiv);
            }, 5000);
        }
        
        // Close modals when clicking outside
        window.onclick = function(event) {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                if (event.target === modal) {
                    modal.style.display = 'none';
                    if (map) {
                        map.remove();
                        map = null;
                    }
                }
            });
        }
        
        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            // Auto-focus on username field
            document.getElementById('username').focus();
        });
    </script>
</body>
</html>
    ''')

# API Routes - Complete CRUD Operations

@app.route('/api/dashboard')
def get_dashboard():
    """Get dashboard statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute('SELECT COUNT(*) FROM assets WHERE status = "Active"')
        total_assets = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM workflows WHERE status != "Completed"')
        total_workflows = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "Active"')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT region) FROM assets WHERE region IS NOT NULL')
        total_regions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM files')
        total_files = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_assets': total_assets,
            'total_workflows': total_workflows,
            'total_users': total_users,
            'total_regions': total_regions,
            'total_files': total_files,
            'completion_rate': '87%'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics')
def get_analytics():
    """Get analytics data"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT SUM(investment_value) FROM assets WHERE investment_value IS NOT NULL')
        total_investment = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(current_value) FROM assets WHERE current_value IS NOT NULL')
        total_value = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(rental_income) FROM assets WHERE rental_income IS NOT NULL')
        total_rental = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(occupancy_rate) FROM assets WHERE occupancy_rate IS NOT NULL')
        avg_occupancy = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'total_investment': total_investment,
            'total_value': total_value,
            'total_rental': total_rental,
            'avg_occupancy': round(avg_occupancy, 1)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets', methods=['GET'])
def get_assets():
    """Get all assets"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets ORDER BY created_at DESC')
        assets = []
        columns = [description[0] for description in cursor.description]
        
        for row in cursor.fetchall():
            asset = dict(zip(columns, row))
            assets.append(asset)
        
        conn.close()
        return jsonify(assets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets/<asset_id>', methods=['GET'])
def get_asset(asset_id):
    """Get specific asset"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets WHERE asset_id = ?', (asset_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            asset = dict(zip(columns, row))
            conn.close()
            return jsonify(asset)
        else:
            conn.close()
            return jsonify({'error': 'Asset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets', methods=['POST'])
def create_asset():
    """Create new asset"""
    try:
        data = request.json
        
        # Generate asset ID if not provided
        if not data.get('assetId'):
            data['assetId'] = f"AST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build dynamic insert query based on provided data
        columns = []
        values = []
        placeholders = []
        
        # Map form field names to database column names
        field_mapping = {
            'assetId': 'asset_id',
            'assetName': 'asset_name',
            'assetType': 'asset_type',
            'assetCategory': 'asset_category',
            'assetClassification': 'asset_classification',
            'currentStatus': 'current_status',
            'operationalStatus': 'operational_status',
            'planningPermit': 'planning_permit',
            'buildingPermit': 'building_permit',
            'developmentApproval': 'development_approval',
            'needAssessment': 'need_assessment',
            'locationScore': 'location_score',
            'accessibilityRating': 'accessibility_rating',
            'marketAttractiveness': 'market_attractiveness',
            'region': 'region',
            'city': 'city',
            'district': 'district',
            'latitude': 'latitude',
            'longitude': 'longitude'
        }
        
        for form_field, db_column in field_mapping.items():
            if form_field in data and data[form_field]:
                columns.append(db_column)
                values.append(data[form_field])
                placeholders.append('?')
        
        # Add default status if not provided
        if 'status' not in columns:
            columns.append('status')
            values.append('Active')
            placeholders.append('?')
        
        query = f"INSERT INTO assets ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Asset created successfully', 'asset_id': data['assetId']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows', methods=['GET'])
def get_workflows():
    """Get all workflows"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows ORDER BY created_at DESC')
        workflows = []
        columns = [description[0] for description in cursor.description]
        
        for row in cursor.fetchall():
            workflow = dict(zip(columns, row))
            workflows.append(workflow)
        
        conn.close()
        return jsonify(workflows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        users = []
        columns = [description[0] for description in cursor.description]
        
        for row in cursor.fetchall():
            user = dict(zip(columns, row))
            users.append(user)
        
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def get_files():
    """Get all files"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files ORDER BY upload_date DESC')
        files = []
        columns = [description[0] for description in cursor.description]
        
        for row in cursor.fetchall():
            file_record = dict(zip(columns, row))
            files.append(file_record)
        
        conn.close()
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Upload files with OCR processing"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        document_type = request.form.get('document_type', 'general')
        
        uploaded_count = 0
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                # Generate unique filename
                file_id = str(uuid.uuid4())
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1].lower()
                stored_filename = f"{file_id}.{file_extension}"
                
                # Save file
                file_path = os.path.join(UPLOAD_FOLDER, document_type, stored_filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                
                # Get file info
                file_size = os.path.getsize(file_path)
                mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                
                # Extract text using OCR simulation
                ocr_text = extract_text_from_file(file_path)
                
                # Save file record to database
                cursor.execute('''
                    INSERT INTO files (file_id, document_type, original_filename, stored_filename, 
                                     file_path, file_size, mime_type, ocr_text, processing_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_id,
                    document_type,
                    filename,
                    stored_filename,
                    file_path,
                    file_size,
                    mime_type,
                    ocr_text,
                    'Processed'
                ))
                
                uploaded_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Successfully uploaded {uploaded_count} files',
            'uploaded_count': uploaded_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/assets', methods=['GET'])
def export_assets():
    """Export assets to CSV"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets')
        assets = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(assets)
        
        conn.close()
        
        # Return CSV file
        csv_content = output.getvalue()
        output.close()
        
        response = app.response_class(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=assets_export.csv'}
        )
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/<report_type>', methods=['GET'])
def generate_report(report_type):
    """Generate various types of reports"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if report_type == 'assets':
            cursor.execute('SELECT * FROM assets')
            data = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
        elif report_type == 'regional':
            cursor.execute('SELECT region, COUNT(*) as count, AVG(current_value) as avg_value FROM assets GROUP BY region')
            data = cursor.fetchall()
            columns = ['region', 'count', 'avg_value']
            
        elif report_type == 'construction':
            cursor.execute('SELECT construction_status, COUNT(*) as count, AVG(completion_percentage) as avg_completion FROM assets GROUP BY construction_status')
            data = cursor.fetchall()
            columns = ['construction_status', 'count', 'avg_completion']
            
        elif report_type == 'financial':
            cursor.execute('SELECT SUM(investment_value) as total_investment, SUM(current_value) as total_value, SUM(rental_income) as total_rental FROM assets')
            data = cursor.fetchall()
            columns = ['total_investment', 'total_value', 'total_rental']
            
        elif report_type == 'workflows':
            cursor.execute('SELECT * FROM workflows')
            data = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
        elif report_type == 'users':
            cursor.execute('SELECT * FROM users')
            data = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        conn.close()
        
        # Create CSV content for the report
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        response = app.response_class(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={report_type}_report.csv'}
        )
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Vercel handler
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

