from flask import Flask, request, jsonify, render_template_string, send_file
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
import tempfile
import subprocess
import mimetypes

app = Flask(__name__)
CORS(app)

# Configuration for multiple deployment environments
DATABASE_PATH = '/tmp/madares_complete.db' if os.environ.get('VERCEL') else 'madares_complete.db'
UPLOAD_FOLDER = '/tmp/uploads' if os.environ.get('VERCEL') else 'uploads'

# Ensure upload directory exists
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
            # Simulate OCR for images
            return f"OCR Text extracted from {os.path.basename(file_path)}: Sample property document text with coordinates and measurements."
            
        elif file_ext == 'pdf':
            # Simulate PDF text extraction
            return f"PDF Text extracted from {os.path.basename(file_path)}: Property deed document with legal descriptions and boundaries."
            
        elif file_ext in ['doc', 'docx']:
            # Simulate Word document text extraction
            return f"Document text from {os.path.basename(file_path)}: Construction specifications and engineering details."
            
        elif file_ext in ['xls', 'xlsx']:
            # Simulate Excel text extraction
            return f"Spreadsheet data from {os.path.basename(file_path)}: Financial calculations and cost analysis."
            
        elif file_ext == 'txt':
            # Read text files directly
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
    
    # Workflows table
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
            asset_id TEXT,
            progress INTEGER DEFAULT 0,
            notes TEXT,
            workflow_type TEXT,
            department TEXT,
            estimated_hours INTEGER,
            actual_hours INTEGER,
            completion_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id)
        )
    ''')
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            role TEXT,
            department TEXT,
            region TEXT,
            permissions TEXT,
            last_login TIMESTAMP,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE,
            report_type TEXT,
            report_name TEXT,
            parameters TEXT,
            generated_by TEXT,
            file_path TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
             'Multiple Tenants', 'Comprehensive Coverage', 'Current', 'Strong Demand', 'Hold', 'Low', 'Expansion Planned', 'Approved', 'Paved', 'Prime location asset', 'Active'),
            
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
             'Not Occupied', 'Under Review', 'Pending', 'Growing Market', 'Develop', 'Medium', 'Phase 2 Planning', 'Pending', 'Under Construction', 'Strategic development project', 'Active'),
            
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
             'Logistics Companies', 'Industrial Coverage', 'Current', 'Stable Demand', 'Hold', 'Low', 'Modernization', 'Approved', 'Paved', 'Strategic logistics asset', 'Active')
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
                                  tenant_information, insurance_details, tax_information, market_analysis, investment_recommendation, risk_assessment, future_plans, environmental_clearance, access_road, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', asset)
    
    cursor.execute('SELECT COUNT(*) FROM workflows')
    if cursor.fetchone()[0] == 0:
        sample_workflows = [
            ('WF-001', 'Asset Valuation Review', 'Quarterly review of asset valuations for compliance', 'In Progress', 'High', 'Ahmed Al-Rashid', '2025-08-15', 'admin', 'AST-001', 60, 'Valuation in progress', 'Financial Review', 'Finance', 40, 25, None),
            ('WF-002', 'Construction Progress Inspection', 'Monthly inspection of construction sites for quality assurance', 'Not Started', 'Medium', 'Sara Al-Mahmoud', '2025-08-20', 'admin', 'AST-002', 0, 'Scheduled for next week', 'Quality Control', 'Engineering', 16, 0, None),
            ('WF-003', 'Lease Agreement Renewal', 'Renew expiring lease agreements with current tenants', 'Completed', 'Low', 'Omar Al-Fahad', '2025-07-30', 'admin', 'AST-003', 100, 'Successfully renewed', 'Legal Process', 'Legal', 8, 8, '2025-07-28'),
            ('WF-004', 'Environmental Impact Assessment', 'Conduct environmental assessment for new development', 'In Progress', 'High', 'Fatima Al-Zahra', '2025-08-25', 'admin', 'AST-002', 30, 'Initial survey completed', 'Environmental', 'Engineering', 60, 18, None),
            ('WF-005', 'Property Tax Assessment', 'Annual property tax assessment and filing', 'Not Started', 'Medium', 'Mohammed Al-Saud', '2025-09-01', 'admin', 'AST-001', 0, 'Waiting for documentation', 'Tax Compliance', 'Finance', 24, 0, None)
        ]
        
        for workflow in sample_workflows:
            cursor.execute('''
                INSERT INTO workflows (workflow_id, title, description, status, priority, assigned_to, 
                                     due_date, created_by, asset_id, progress, notes, workflow_type, department, estimated_hours, actual_hours, completion_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', workflow)
    
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ('USR-001', 'admin', 'System Administrator', 'admin@madares.gov.sa', '+966501234567', 'Administrator', 'IT Department', 'All Regions', 'full_access', None, 'Active'),
            ('USR-002', 'ahmed.rashid', 'Ahmed Al-Rashid', 'ahmed.rashid@madares.gov.sa', '+966501234568', 'Asset Manager', 'Asset Management', 'Riyadh', 'asset_management', None, 'Active'),
            ('USR-003', 'sara.mahmoud', 'Sara Al-Mahmoud', 'sara.mahmoud@madares.gov.sa', '+966501234569', 'Inspector', 'Quality Assurance', 'Makkah', 'inspection', None, 'Active'),
            ('USR-004', 'omar.fahad', 'Omar Al-Fahad', 'omar.fahad@madares.gov.sa', '+966501234570', 'Lease Manager', 'Commercial Operations', 'Eastern Province', 'lease_management', None, 'Active'),
            ('USR-005', 'fatima.zahra', 'Fatima Al-Zahra', 'fatima.zahra@madares.gov.sa', '+966501234571', 'Environmental Specialist', 'Engineering', 'All Regions', 'environmental', None, 'Active'),
            ('USR-006', 'mohammed.saud', 'Mohammed Al-Saud', 'mohammed.saud@madares.gov.sa', '+966501234572', 'Financial Analyst', 'Finance', 'Riyadh', 'financial_analysis', None, 'Active')
        ]
        
        for user in sample_users:
            cursor.execute('''
                INSERT INTO users (user_id, username, full_name, email, phone, role, department, region, permissions, last_login, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
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
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
            position: relative;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .logout-btn {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: none;
        }
        
        .logout-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .login-container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            max-width: 500px;
            margin: 0 auto;
            text-align: center;
        }
        
        .login-container h2 {
            color: #333;
            margin-bottom: 30px;
            font-size: 2rem;
        }
        
        .form-group {
            margin-bottom: 25px;
            text-align: right;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
            direction: ltr;
            text-align: left;
        }
        
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #ff6b35;
            box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
        }
        
        .login-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }
        
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(255, 107, 53, 0.3);
        }
        
        .credentials-hint {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            font-size: 14px;
            color: #6c757d;
        }
        
        .alert {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-weight: 500;
        }
        
        .alert-error {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .alert-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        
        .main-app {
            display: none;
        }
        
        .nav-tabs {
            display: flex;
            background: white;
            border-radius: 15px;
            padding: 10px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            overflow-x: auto;
            flex-wrap: wrap;
        }
        
        .nav-tab {
            flex: 1;
            padding: 15px 20px;
            background: transparent;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            white-space: nowrap;
            min-width: 120px;
            margin: 2px;
        }
        
        .nav-tab.active {
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            color: white;
            box-shadow: 0 5px 15px rgba(255, 107, 53, 0.3);
        }
        
        .nav-tab:hover:not(.active) {
            background: #f8f9fa;
        }
        
        .tab-content {
            display: none;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .tab-content.active {
            display: block;
        }
        
        .dashboard-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .stat-card p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .data-table th {
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            color: white;
            padding: 15px;
            text-align: right;
            font-weight: 600;
        }
        
        .data-table td {
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
            text-align: right;
        }
        
        .data-table tr:hover {
            background: #f8f9fa;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            margin: 5px;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            color: white;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-info {
            background: #17a2b8;
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
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
            padding: 30px;
            border-radius: 20px;
            width: 95%;
            max-width: 1000px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        .close {
            color: #aaa;
            float: left;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: #000;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .form-section {
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .form-section h3 {
            color: #ff6b35;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ff6b35;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .form-section.collapsed .form-content {
            display: none;
        }
        
        .search-box {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
            margin-bottom: 20px;
            direction: ltr;
            text-align: left;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #ff6b35;
        }
        
        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-active { background: #d4edda; color: #155724; }
        .status-completed { background: #d4edda; color: #155724; }
        .status-in-progress { background: #fff3cd; color: #856404; }
        .status-not-started { background: #f8d7da; color: #721c24; }
        .status-on-hold { background: #e2e3e5; color: #383d41; }
        .status-under-development { background: #cce5ff; color: #004085; }
        .status-construction { background: #fff3cd; color: #856404; }
        .status-operational { background: #d4edda; color: #155724; }
        
        .priority-high { background: #f8d7da; color: #721c24; }
        .priority-medium { background: #fff3cd; color: #856404; }
        .priority-low { background: #d4edda; color: #155724; }
        
        #map {
            height: 300px;
            width: 100%;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .file-upload-area {
            border: 2px dashed #e1e5e9;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            margin-bottom: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .file-upload-area:hover {
            border-color: #ff6b35;
            background: #f8f9fa;
        }
        
        .file-upload-area.dragover {
            border-color: #ff6b35;
            background: #fff3cd;
        }
        
        .file-list {
            margin-top: 15px;
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            margin-bottom: 5px;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
            transition: width 0.3s ease;
        }
        
        .document-types {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .document-type {
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .document-type:hover {
            border-color: #ff6b35;
            box-shadow: 0 5px 15px rgba(255, 107, 53, 0.1);
        }
        
        .document-type h4 {
            color: #ff6b35;
            margin-bottom: 10px;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 1.8rem;
            }
            
            .nav-tabs {
                flex-direction: column;
            }
            
            .nav-tab {
                margin-bottom: 5px;
            }
            
            .dashboard-stats {
                grid-template-columns: 1fr;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .modal-content {
                width: 95%;
                margin: 5% auto;
                padding: 20px;
            }
            
            .document-types {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <button class="logout-btn" onclick="logout()" id="logoutBtn">
                <i class="fas fa-sign-out-alt"></i> تسجيل الخروج
            </button>
            <h1><i class="fas fa-building"></i> مدارس الأعمال</h1>
            <p>نظام إدارة الأصول العقارية الحكومية الشامل - جميع الوظائف متاحة</p>
        </div>
        
        <!-- Login Form -->
        <div id="loginForm" class="login-container">
            <h2><i class="fas fa-lock"></i> تسجيل الدخول</h2>
            <div id="loginAlert"></div>
            <form onsubmit="login(event)">
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
        
        <!-- Main Application -->
        <div id="mainApp" class="main-app">
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
                    <i class="fas fa-file-upload"></i> المستندات
                </button>
                <button class="nav-tab" onclick="showTab('reports')">
                    <i class="fas fa-chart-bar"></i> التقارير
                </button>
                <button class="nav-tab" onclick="showTab('analytics')">
                    <i class="fas fa-analytics"></i> التحليلات
                </button>
            </div>
            
            <!-- Dashboard Tab -->
            <div id="dashboard" class="tab-content active">
                <h2><i class="fas fa-tachometer-alt"></i> لوحة التحكم الشاملة</h2>
                <div class="dashboard-stats" id="dashboardStats">
                    <!-- Stats will be loaded here -->
                </div>
                <div id="recentActivities">
                    <h3>الأنشطة الحديثة</h3>
                    <div id="activitiesList">
                        <!-- Activities will be loaded here -->
                    </div>
                </div>
            </div>
            
            <!-- Assets Tab -->
            <div id="assets" class="tab-content">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap;">
                    <h2><i class="fas fa-building"></i> إدارة الأصول الشاملة</h2>
                    <div>
                        <button class="btn btn-primary" onclick="showAddAssetModal()">
                            <i class="fas fa-plus"></i> إضافة أصل جديد
                        </button>
                        <button class="btn btn-info" onclick="exportAssets()">
                            <i class="fas fa-download"></i> تصدير البيانات
                        </button>
                    </div>
                </div>
                <input type="text" class="search-box" id="assetSearch" placeholder="البحث في الأصول..." onkeyup="searchAssets()">
                <div id="assetsTable">
                    <!-- Assets table will be loaded here -->
                </div>
            </div>
            
            <!-- Workflows Tab -->
            <div id="workflows" class="tab-content">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap;">
                    <h2><i class="fas fa-tasks"></i> إدارة سير العمل المتقدمة</h2>
                    <div>
                        <button class="btn btn-primary" onclick="showAddWorkflowModal()">
                            <i class="fas fa-plus"></i> إضافة مهمة جديدة
                        </button>
                        <button class="btn btn-info" onclick="exportWorkflows()">
                            <i class="fas fa-download"></i> تصدير المهام
                        </button>
                    </div>
                </div>
                <input type="text" class="search-box" id="workflowSearch" placeholder="البحث في المهام..." onkeyup="searchWorkflows()">
                <div id="workflowsTable">
                    <!-- Workflows table will be loaded here -->
                </div>
            </div>
            
            <!-- Users Tab -->
            <div id="users" class="tab-content">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap;">
                    <h2><i class="fas fa-users"></i> إدارة المستخدمين المتقدمة</h2>
                    <div>
                        <button class="btn btn-primary" onclick="showAddUserModal()">
                            <i class="fas fa-plus"></i> إضافة مستخدم جديد
                        </button>
                        <button class="btn btn-info" onclick="exportUsers()">
                            <i class="fas fa-download"></i> تصدير المستخدمين
                        </button>
                    </div>
                </div>
                <input type="text" class="search-box" id="userSearch" placeholder="البحث في المستخدمين..." onkeyup="searchUsers()">
                <div id="usersTable">
                    <!-- Users table will be loaded here -->
                </div>
            </div>
            
            <!-- Documents Tab -->
            <div id="documents" class="tab-content">
                <h2><i class="fas fa-file-upload"></i> إدارة المستندات والملفات</h2>
                <div class="document-types">
                    <div class="document-type" onclick="showDocumentUpload('property_deed')">
                        <h4><i class="fas fa-file-contract"></i> صك الملكية</h4>
                        <p>رفع وإدارة صكوك الملكية</p>
                    </div>
                    <div class="document-type" onclick="showDocumentUpload('ownership_documents')">
                        <h4><i class="fas fa-file-signature"></i> وثائق الملكية</h4>
                        <p>المستندات القانونية للملكية</p>
                    </div>
                    <div class="document-type" onclick="showDocumentUpload('construction_plans')">
                        <h4><i class="fas fa-drafting-compass"></i> المخططات الهندسية</h4>
                        <p>المخططات والرسوم الهندسية</p>
                    </div>
                    <div class="document-type" onclick="showDocumentUpload('financial_documents')">
                        <h4><i class="fas fa-file-invoice-dollar"></i> المستندات المالية</h4>
                        <p>التقارير والوثائق المالية</p>
                    </div>
                    <div class="document-type" onclick="showDocumentUpload('legal_documents')">
                        <h4><i class="fas fa-balance-scale"></i> المستندات القانونية</h4>
                        <p>العقود والوثائق القانونية</p>
                    </div>
                    <div class="document-type" onclick="showDocumentUpload('inspection_reports')">
                        <h4><i class="fas fa-clipboard-check"></i> تقارير التفتيش</h4>
                        <p>تقارير الفحص والتفتيش</p>
                    </div>
                </div>
                <div id="documentsTable">
                    <!-- Documents table will be loaded here -->
                </div>
            </div>
            
            <!-- Reports Tab -->
            <div id="reports" class="tab-content">
                <h2><i class="fas fa-chart-bar"></i> التقارير والإحصائيات المتقدمة</h2>
                <div class="dashboard-stats">
                    <div class="stat-card" onclick="generateReport('assets')">
                        <i class="fas fa-building" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <h3>تقرير الأصول</h3>
                        <p>تقرير شامل عن جميع الأصول</p>
                    </div>
                    <div class="stat-card" onclick="generateReport('regional')">
                        <i class="fas fa-map-marker-alt" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <h3>التوزيع الجغرافي</h3>
                        <p>توزيع الأصول حسب المناطق</p>
                    </div>
                    <div class="stat-card" onclick="generateReport('construction')">
                        <i class="fas fa-hard-hat" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <h3>حالة الإنشاء</h3>
                        <p>تقرير حالة المشاريع الإنشائية</p>
                    </div>
                    <div class="stat-card" onclick="generateReport('financial')">
                        <i class="fas fa-dollar-sign" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <h3>التحليل المالي</h3>
                        <p>تقرير الاستثمارات والعوائد</p>
                    </div>
                    <div class="stat-card" onclick="generateReport('workflows')">
                        <i class="fas fa-tasks" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <h3>تقرير المهام</h3>
                        <p>تقرير سير العمل والمهام</p>
                    </div>
                    <div class="stat-card" onclick="generateReport('users')">
                        <i class="fas fa-users" style="font-size: 2rem; margin-bottom: 10px;"></i>
                        <h3>تقرير المستخدمين</h3>
                        <p>تقرير المستخدمين والأدوار</p>
                    </div>
                </div>
            </div>
            
            <!-- Analytics Tab -->
            <div id="analytics" class="tab-content">
                <h2><i class="fas fa-analytics"></i> التحليلات المتقدمة</h2>
                <div class="dashboard-stats">
                    <div class="stat-card">
                        <h3 id="totalInvestment">0</h3>
                        <p><i class="fas fa-money-bill-wave"></i> إجمالي الاستثمارات</p>
                    </div>
                    <div class="stat-card">
                        <h3 id="totalValue">0</h3>
                        <p><i class="fas fa-chart-line"></i> القيمة الحالية</p>
                    </div>
                    <div class="stat-card">
                        <h3 id="totalRental">0</h3>
                        <p><i class="fas fa-home"></i> الدخل الإيجاري</p>
                    </div>
                    <div class="stat-card">
                        <h3 id="avgOccupancy">0%</h3>
                        <p><i class="fas fa-percentage"></i> متوسط الإشغال</p>
                    </div>
                </div>
                <div id="analyticsCharts">
                    <!-- Charts will be loaded here -->
                </div>
            </div>
        </div>
    </div>
    
    <!-- Complete Asset Modal with ALL 58+ MOE Fields -->
    <div id="assetModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('assetModal')">&times;</span>
            <h2 id="assetModalTitle">إضافة أصل جديد - النموذج الشامل (58+ حقل)</h2>
            <form id="assetForm" onsubmit="saveAsset(event)">
                <input type="hidden" id="assetId" name="assetId">
                
                <!-- Section 1: Asset Identification & Status -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        1. تحديد الأصل والحالة
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="assetName">اسم الأصل:</label>
                                <input type="text" id="assetName" name="assetName" required>
                            </div>
                            <div class="form-group">
                                <label for="assetType">نوع الأصل:</label>
                                <select id="assetType" name="assetType" required>
                                    <option value="">اختر النوع</option>
                                    <option value="Commercial">تجاري</option>
                                    <option value="Residential">سكني</option>
                                    <option value="Industrial">صناعي</option>
                                    <option value="Administrative">إداري</option>
                                    <option value="Educational">تعليمي</option>
                                    <option value="Healthcare">صحي</option>
                                    <option value="Mixed Use">متعدد الاستخدامات</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="assetCategory">فئة الأصل:</label>
                                <select id="assetCategory" name="assetCategory">
                                    <option value="">اختر الفئة</option>
                                    <option value="Building">مبنى</option>
                                    <option value="Land">أرض</option>
                                    <option value="Infrastructure">بنية تحتية</option>
                                    <option value="Mixed Use">متعدد الاستخدامات</option>
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
                                    <option value="Maintenance">تحت الصيانة</option>
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
                </div>
                
                <!-- Section 2: Planning & Need Assessment -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        2. التخطيط وتقييم الحاجة
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="planningPermit">رخصة التخطيط:</label>
                                <select id="planningPermit" name="planningPermit">
                                    <option value="">اختر الحالة</option>
                                    <option value="Valid">سارية</option>
                                    <option value="Expired">منتهية الصلاحية</option>
                                    <option value="Pending">قيد المراجعة</option>
                                    <option value="Not Required">غير مطلوبة</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="buildingPermit">رخصة البناء:</label>
                                <select id="buildingPermit" name="buildingPermit">
                                    <option value="">اختر الحالة</option>
                                    <option value="Valid">سارية</option>
                                    <option value="Expired">منتهية الصلاحية</option>
                                    <option value="Pending">قيد المراجعة</option>
                                    <option value="Not Required">غير مطلوبة</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="developmentApproval">موافقة التطوير:</label>
                                <select id="developmentApproval" name="developmentApproval">
                                    <option value="">اختر الحالة</option>
                                    <option value="Approved">معتمد</option>
                                    <option value="Pending">قيد المراجعة</option>
                                    <option value="Rejected">مرفوض</option>
                                    <option value="In Process">قيد الإجراء</option>
                                </select>
                            </div>
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
                </div>
                
                <!-- Section 3: Location Attractiveness -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        3. جاذبية الموقع
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
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
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 4: Investment Proposal & Obstacles -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        4. مقترح الاستثمار والعوائق
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-group">
                            <label for="investmentProposal">مقترح الاستثمار:</label>
                            <textarea id="investmentProposal" name="investmentProposal" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="investmentObstacles">عوائق الاستثمار:</label>
                            <textarea id="investmentObstacles" name="investmentObstacles" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="riskMitigation">تخفيف المخاطر:</label>
                            <textarea id="riskMitigation" name="riskMitigation" rows="3"></textarea>
                        </div>
                    </div>
                </div>
                
                <!-- Section 5: Financial Obligations & Covenants -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        5. الالتزامات المالية والتعهدات
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-group">
                            <label for="financialObligations">الالتزامات المالية:</label>
                            <textarea id="financialObligations" name="financialObligations" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="loanCovenants">تعهدات القروض:</label>
                            <textarea id="loanCovenants" name="loanCovenants" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="paymentSchedule">جدول الدفعات:</label>
                            <select id="paymentSchedule" name="paymentSchedule">
                                <option value="">اختر الجدول</option>
                                <option value="Monthly">شهري</option>
                                <option value="Quarterly">ربع سنوي</option>
                                <option value="Semi-Annual">نصف سنوي</option>
                                <option value="Annual">سنوي</option>
                            </select>
                        </div>
                    </div>
                </div>
                
                <!-- Section 6: Utilities Information -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        6. معلومات المرافق
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="utilitiesWater">المياه:</label>
                                <select id="utilitiesWater" name="utilitiesWater">
                                    <option value="">اختر الحالة</option>
                                    <option value="Connected">متصل</option>
                                    <option value="Not Connected">غير متصل</option>
                                    <option value="Under Installation">تحت التركيب</option>
                                    <option value="Planned">مخطط</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="utilitiesElectricity">الكهرباء:</label>
                                <select id="utilitiesElectricity" name="utilitiesElectricity">
                                    <option value="">اختر الحالة</option>
                                    <option value="Connected">متصل</option>
                                    <option value="Not Connected">غير متصل</option>
                                    <option value="Under Installation">تحت التركيب</option>
                                    <option value="Planned">مخطط</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="utilitiesSewage">الصرف الصحي:</label>
                                <select id="utilitiesSewage" name="utilitiesSewage">
                                    <option value="">اختر الحالة</option>
                                    <option value="Connected">متصل</option>
                                    <option value="Not Connected">غير متصل</option>
                                    <option value="Under Installation">تحت التركيب</option>
                                    <option value="Planned">مخطط</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="utilitiesTelecom">الاتصالات:</label>
                                <select id="utilitiesTelecom" name="utilitiesTelecom">
                                    <option value="">اختر الحالة</option>
                                    <option value="Connected">متصل</option>
                                    <option value="Not Connected">غير متصل</option>
                                    <option value="Under Installation">تحت التركيب</option>
                                    <option value="Planned">مخطط</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 7: Ownership Information -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        7. معلومات الملكية
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="ownershipType">نوع الملكية:</label>
                                <select id="ownershipType" name="ownershipType">
                                    <option value="">اختر النوع</option>
                                    <option value="Government">حكومي</option>
                                    <option value="Private">خاص</option>
                                    <option value="Mixed">مختلط</option>
                                    <option value="Public-Private Partnership">شراكة عامة خاصة</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="ownerName">اسم المالك:</label>
                                <input type="text" id="ownerName" name="ownerName">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="ownershipPercentage">نسبة الملكية (%):</label>
                                <input type="number" id="ownershipPercentage" name="ownershipPercentage" min="0" max="100" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="legalStatus">الوضع القانوني:</label>
                                <select id="legalStatus" name="legalStatus">
                                    <option value="">اختر الوضع</option>
                                    <option value="Approved">معتمد</option>
                                    <option value="Pending">قيد المراجعة</option>
                                    <option value="In Process">قيد الإجراء</option>
                                    <option value="Rejected">مرفوض</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 8: Land & Plan Details -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        8. تفاصيل الأرض والمخطط
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="landUse">استخدام الأرض:</label>
                                <select id="landUse" name="landUse">
                                    <option value="">اختر الاستخدام</option>
                                    <option value="Commercial Development">تطوير تجاري</option>
                                    <option value="Residential Development">تطوير سكني</option>
                                    <option value="Industrial Development">تطوير صناعي</option>
                                    <option value="Mixed Development">تطوير مختلط</option>
                                    <option value="Agricultural">زراعي</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="zoningClassification">التصنيف العمراني:</label>
                                <select id="zoningClassification" name="zoningClassification">
                                    <option value="">اختر التصنيف</option>
                                    <option value="Commercial">تجاري</option>
                                    <option value="Residential">سكني</option>
                                    <option value="Industrial">صناعي</option>
                                    <option value="Mixed Use">متعدد الاستخدامات</option>
                                    <option value="Agricultural">زراعي</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="developmentPotential">إمكانية التطوير:</label>
                                <select id="developmentPotential" name="developmentPotential">
                                    <option value="">اختر الإمكانية</option>
                                    <option value="High">عالية</option>
                                    <option value="Medium">متوسطة</option>
                                    <option value="Low">منخفضة</option>
                                    <option value="Restricted">مقيدة</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 9: Asset Area Details -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        9. تفاصيل مساحات الأصل
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="landArea">مساحة الأرض (م²):</label>
                                <input type="number" id="landArea" name="landArea" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="builtArea">المساحة المبنية (م²):</label>
                                <input type="number" id="builtArea" name="builtArea" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="usableArea">المساحة القابلة للاستخدام (م²):</label>
                                <input type="number" id="usableArea" name="usableArea" step="0.01">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="commonArea">المساحة المشتركة (م²):</label>
                                <input type="number" id="commonArea" name="commonArea" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="parkingArea">مساحة المواقف (م²):</label>
                                <input type="number" id="parkingArea" name="parkingArea" step="0.01">
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 10: Construction Status -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        10. حالة الإنشاء
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="constructionStatus">حالة الإنشاء:</label>
                                <select id="constructionStatus" name="constructionStatus">
                                    <option value="">اختر الحالة</option>
                                    <option value="Planning">مرحلة التخطيط</option>
                                    <option value="Under Construction">تحت الإنشاء</option>
                                    <option value="Completed">مكتمل</option>
                                    <option value="Renovation">تحت التجديد</option>
                                    <option value="Maintenance">تحت الصيانة</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="completionPercentage">نسبة الإنجاز (%):</label>
                                <input type="number" id="completionPercentage" name="completionPercentage" min="0" max="100">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="constructionQuality">جودة الإنشاء:</label>
                                <select id="constructionQuality" name="constructionQuality">
                                    <option value="">اختر الجودة</option>
                                    <option value="Excellent">ممتازة</option>
                                    <option value="Very Good">جيدة جداً</option>
                                    <option value="Good">جيدة</option>
                                    <option value="Fair">مقبولة</option>
                                    <option value="Poor">ضعيفة</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="defectsWarranty">ضمان العيوب:</label>
                                <input type="text" id="defectsWarranty" name="defectsWarranty" placeholder="مثال: 5 سنوات">
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 11: Physical Dimensions -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        11. الأبعاد الفيزيائية
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="lengthMeters">الطول (متر):</label>
                                <input type="number" id="lengthMeters" name="lengthMeters" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="widthMeters">العرض (متر):</label>
                                <input type="number" id="widthMeters" name="widthMeters" step="0.01">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="heightMeters">الارتفاع (متر):</label>
                                <input type="number" id="heightMeters" name="heightMeters" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="totalFloors">إجمالي الطوابق:</label>
                                <input type="number" id="totalFloors" name="totalFloors" min="1">
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 12: Boundaries -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        12. الحدود
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="northBoundary">الحد الشمالي:</label>
                                <input type="text" id="northBoundary" name="northBoundary">
                            </div>
                            <div class="form-group">
                                <label for="southBoundary">الحد الجنوبي:</label>
                                <input type="text" id="southBoundary" name="southBoundary">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="eastBoundary">الحد الشرقي:</label>
                                <input type="text" id="eastBoundary" name="eastBoundary">
                            </div>
                            <div class="form-group">
                                <label for="westBoundary">الحد الغربي:</label>
                                <input type="text" id="westBoundary" name="westBoundary">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="boundaryLengthNorth">طول الحد الشمالي (متر):</label>
                                <input type="number" id="boundaryLengthNorth" name="boundaryLengthNorth" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="boundaryLengthSouth">طول الحد الجنوبي (متر):</label>
                                <input type="number" id="boundaryLengthSouth" name="boundaryLengthSouth" step="0.01">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="boundaryLengthEast">طول الحد الشرقي (متر):</label>
                                <input type="number" id="boundaryLengthEast" name="boundaryLengthEast" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="boundaryLengthWest">طول الحد الغربي (متر):</label>
                                <input type="number" id="boundaryLengthWest" name="boundaryLengthWest" step="0.01">
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 13: Geographic Location -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        13. الموقع الجغرافي
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="region">المنطقة:</label>
                                <select id="region" name="region" required>
                                    <option value="">اختر المنطقة</option>
                                    <option value="Riyadh">الرياض</option>
                                    <option value="Makkah">مكة المكرمة</option>
                                    <option value="Eastern Province">المنطقة الشرقية</option>
                                    <option value="Asir">عسير</option>
                                    <option value="Madinah">المدينة المنورة</option>
                                    <option value="Qassim">القصيم</option>
                                    <option value="Tabuk">تبوك</option>
                                    <option value="Hail">حائل</option>
                                    <option value="Northern Borders">الحدود الشمالية</option>
                                    <option value="Jazan">جازان</option>
                                    <option value="Najran">نجران</option>
                                    <option value="Al Bahah">الباحة</option>
                                    <option value="Al Jouf">الجوف</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="city">المدينة:</label>
                                <input type="text" id="city" name="city" required>
                            </div>
                            <div class="form-group">
                                <label for="district">الحي:</label>
                                <input type="text" id="district" name="district">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="location">العنوان التفصيلي:</label>
                                <input type="text" id="location" name="location" required>
                            </div>
                            <div class="form-group">
                                <label for="elevation">الارتفاع عن سطح البحر (متر):</label>
                                <input type="number" id="elevation" name="elevation" step="0.01">
                            </div>
                        </div>
                        
                        <div id="map"></div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="latitude">خط العرض:</label>
                                <input type="number" id="latitude" name="latitude" step="any" readonly>
                            </div>
                            <div class="form-group">
                                <label for="longitude">خط الطول:</label>
                                <input type="number" id="longitude" name="longitude" step="any" readonly>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 14: Financial Information -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        14. المعلومات المالية
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="investmentValue">قيمة الاستثمار (ريال):</label>
                                <input type="number" id="investmentValue" name="investmentValue" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="currentValue">القيمة الحالية (ريال):</label>
                                <input type="number" id="currentValue" name="currentValue" step="0.01">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="rentalIncome">الدخل الإيجاري الشهري (ريال):</label>
                                <input type="number" id="rentalIncome" name="rentalIncome" step="0.01">
                            </div>
                            <div class="form-group">
                                <label for="maintenanceCost">تكلفة الصيانة الشهرية (ريال):</label>
                                <input type="number" id="maintenanceCost" name="maintenanceCost" step="0.01">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="occupancyRate">معدل الإشغال (%):</label>
                                <input type="number" id="occupancyRate" name="occupancyRate" min="0" max="100" step="0.01">
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Section 15: Additional Information -->
                <div class="form-section">
                    <h3 onclick="toggleSection(this)">
                        15. معلومات إضافية
                        <i class="fas fa-chevron-down"></i>
                    </h3>
                    <div class="form-content">
                        <div class="form-group">
                            <label for="tenantInformation">معلومات المستأجرين:</label>
                            <textarea id="tenantInformation" name="tenantInformation" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="insuranceDetails">تفاصيل التأمين:</label>
                            <textarea id="insuranceDetails" name="insuranceDetails" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="taxInformation">المعلومات الضريبية:</label>
                            <textarea id="taxInformation" name="taxInformation" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="marketAnalysis">تحليل السوق:</label>
                            <textarea id="marketAnalysis" name="marketAnalysis" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="investmentRecommendation">توصية الاستثمار:</label>
                            <textarea id="investmentRecommendation" name="investmentRecommendation" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="riskAssessment">تقييم المخاطر:</label>
                            <textarea id="riskAssessment" name="riskAssessment" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="futurePlans">الخطط المستقبلية:</label>
                            <textarea id="futurePlans" name="futurePlans" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="environmentalClearance">التصريح البيئي:</label>
                            <select id="environmentalClearance" name="environmentalClearance">
                                <option value="">اختر الحالة</option>
                                <option value="Approved">معتمد</option>
                                <option value="Pending">قيد المراجعة</option>
                                <option value="Not Required">غير مطلوب</option>
                                <option value="Rejected">مرفوض</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="accessRoad">طريق الوصول:</label>
                            <select id="accessRoad" name="accessRoad">
                                <option value="">اختر الحالة</option>
                                <option value="Paved">معبد</option>
                                <option value="Unpaved">غير معبد</option>
                                <option value="Under Construction">تحت الإنشاء</option>
                                <option value="Planned">مخطط</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="notes">ملاحظات إضافية:</label>
                            <textarea id="notes" name="notes" rows="4"></textarea>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
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
    
    <!-- Enhanced Workflow Modal -->
    <div id="workflowModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('workflowModal')">&times;</span>
            <h2 id="workflowModalTitle">إضافة مهمة جديدة - النموذج المتقدم</h2>
            <form id="workflowForm" onsubmit="saveWorkflow(event)">
                <input type="hidden" id="workflowId" name="workflowId">
                
                <div class="form-section">
                    <h3>معلومات المهمة الأساسية</h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="workflowTitle">عنوان المهمة:</label>
                                <input type="text" id="workflowTitle" name="workflowTitle" required>
                            </div>
                            <div class="form-group">
                                <label for="workflowType">نوع المهمة:</label>
                                <select id="workflowType" name="workflowType">
                                    <option value="">اختر النوع</option>
                                    <option value="Financial Review">مراجعة مالية</option>
                                    <option value="Quality Control">مراقبة الجودة</option>
                                    <option value="Legal Process">إجراء قانوني</option>
                                    <option value="Environmental">بيئي</option>
                                    <option value="Tax Compliance">امتثال ضريبي</option>
                                    <option value="Maintenance">صيانة</option>
                                    <option value="Inspection">تفتيش</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="workflowDescription">الوصف:</label>
                            <textarea id="workflowDescription" name="workflowDescription" rows="4"></textarea>
                        </div>
                    </div>
                </div>
                
                <div class="form-section">
                    <h3>تفاصيل التنفيذ</h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="workflowStatus">الحالة:</label>
                                <select id="workflowStatus" name="workflowStatus" required>
                                    <option value="Not Started">لم تبدأ</option>
                                    <option value="In Progress">قيد التنفيذ</option>
                                    <option value="Completed">مكتملة</option>
                                    <option value="On Hold">معلقة</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="workflowPriority">الأولوية:</label>
                                <select id="workflowPriority" name="workflowPriority" required>
                                    <option value="Low">منخفضة</option>
                                    <option value="Medium">متوسطة</option>
                                    <option value="High">عالية</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="workflowAssignedTo">المسؤول:</label>
                                <input type="text" id="workflowAssignedTo" name="workflowAssignedTo" required>
                            </div>
                            <div class="form-group">
                                <label for="workflowDepartment">القسم:</label>
                                <select id="workflowDepartment" name="workflowDepartment">
                                    <option value="">اختر القسم</option>
                                    <option value="Asset Management">إدارة الأصول</option>
                                    <option value="Finance">المالية</option>
                                    <option value="Legal">الشؤون القانونية</option>
                                    <option value="Engineering">الهندسة</option>
                                    <option value="Operations">العمليات</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="workflowDueDate">تاريخ الاستحقاق:</label>
                                <input type="date" id="workflowDueDate" name="workflowDueDate">
                            </div>
                            <div class="form-group">
                                <label for="workflowProgress">نسبة الإنجاز (%):</label>
                                <input type="number" id="workflowProgress" name="workflowProgress" min="0" max="100" value="0">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="workflowEstimatedHours">الساعات المقدرة:</label>
                                <input type="number" id="workflowEstimatedHours" name="workflowEstimatedHours" min="1">
                            </div>
                            <div class="form-group">
                                <label for="workflowActualHours">الساعات الفعلية:</label>
                                <input type="number" id="workflowActualHours" name="workflowActualHours" min="0">
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="workflowNotes">الملاحظات:</label>
                    <textarea id="workflowNotes" name="workflowNotes" rows="3"></textarea>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> حفظ
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('workflowModal')">
                        <i class="fas fa-times"></i> إلغاء
                    </button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Enhanced User Modal -->
    <div id="userModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('userModal')">&times;</span>
            <h2 id="userModalTitle">إضافة مستخدم جديد - النموذج المتقدم</h2>
            <form id="userForm" onsubmit="saveUser(event)">
                <input type="hidden" id="userId" name="userId">
                
                <div class="form-section">
                    <h3>المعلومات الشخصية</h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="userUsername">اسم المستخدم:</label>
                                <input type="text" id="userUsername" name="userUsername" required>
                            </div>
                            <div class="form-group">
                                <label for="userFullName">الاسم الكامل:</label>
                                <input type="text" id="userFullName" name="userFullName" required>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="userEmail">البريد الإلكتروني:</label>
                                <input type="email" id="userEmail" name="userEmail">
                            </div>
                            <div class="form-group">
                                <label for="userPhone">رقم الهاتف:</label>
                                <input type="tel" id="userPhone" name="userPhone">
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="form-section">
                    <h3>معلومات العمل</h3>
                    <div class="form-content">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="userRole">الدور:</label>
                                <select id="userRole" name="userRole" required>
                                    <option value="">اختر الدور</option>
                                    <option value="Administrator">مدير النظام</option>
                                    <option value="Asset Manager">مدير الأصول</option>
                                    <option value="Inspector">مفتش</option>
                                    <option value="Analyst">محلل</option>
                                    <option value="Coordinator">منسق</option>
                                    <option value="Financial Analyst">محلل مالي</option>
                                    <option value="Legal Advisor">مستشار قانوني</option>
                                    <option value="Environmental Specialist">أخصائي بيئي</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="userDepartment">القسم:</label>
                                <select id="userDepartment" name="userDepartment">
                                    <option value="">اختر القسم</option>
                                    <option value="Asset Management">إدارة الأصول</option>
                                    <option value="Finance">المالية</option>
                                    <option value="Legal">الشؤون القانونية</option>
                                    <option value="Engineering">الهندسة</option>
                                    <option value="IT">تقنية المعلومات</option>
                                    <option value="Operations">العمليات</option>
                                    <option value="Quality Assurance">ضمان الجودة</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="userRegion">المنطقة:</label>
                                <select id="userRegion" name="userRegion">
                                    <option value="">اختر المنطقة</option>
                                    <option value="All Regions">جميع المناطق</option>
                                    <option value="Riyadh">الرياض</option>
                                    <option value="Makkah">مكة المكرمة</option>
                                    <option value="Eastern Province">المنطقة الشرقية</option>
                                    <option value="Asir">عسير</option>
                                    <option value="Madinah">المدينة المنورة</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="userPermissions">الصلاحيات:</label>
                                <select id="userPermissions" name="userPermissions">
                                    <option value="">اختر الصلاحيات</option>
                                    <option value="full_access">وصول كامل</option>
                                    <option value="asset_management">إدارة الأصول</option>
                                    <option value="inspection">التفتيش</option>
                                    <option value="financial_analysis">التحليل المالي</option>
                                    <option value="reporting">التقارير</option>
                                    <option value="read_only">قراءة فقط</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> حفظ
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('userModal')">
                        <i class="fas fa-times"></i> إلغاء
                    </button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Document Upload Modal -->
    <div id="documentModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('documentModal')">&times;</span>
            <h2 id="documentModalTitle">رفع المستندات</h2>
            <div id="documentUploadContent">
                <!-- Document upload content will be loaded here -->
            </div>
        </div>
    </div>
    
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        let map;
        let marker;
        let currentUser = null;
        let uploadedFiles = [];
        
        // Authentication
        function login(event) {
            event.preventDefault();
            const username = document.getElementById('username').value.trim().toLowerCase();
            const password = document.getElementById('password').value.trim();
            
            if (username === 'admin' && password === 'password123') {
                currentUser = { username: 'admin', role: 'Administrator' };
                document.getElementById('loginForm').style.display = 'none';
                document.getElementById('mainApp').style.display = 'block';
                document.getElementById('logoutBtn').style.display = 'block';
                loadDashboard();
                showAlert('تم تسجيل الدخول بنجاح', 'success');
            } else {
                showAlert('بيانات الدخول غير صحيحة. استخدم admin/password123', 'error');
            }
        }
        
        function logout() {
            currentUser = null;
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('mainApp').style.display = 'none';
            document.getElementById('logoutBtn').style.display = 'none';
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
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
            
            // Load tab content
            switch(tabName) {
                case 'dashboard':
                    loadDashboard();
                    break;
                case 'assets':
                    loadAssets();
                    break;
                case 'workflows':
                    loadWorkflows();
                    break;
                case 'users':
                    loadUsers();
                    break;
                case 'documents':
                    loadDocuments();
                    break;
                case 'reports':
                    // Reports tab is static
                    break;
                case 'analytics':
                    loadAnalytics();
                    break;
            }
        }
        
        // Section Toggle Function
        function toggleSection(element) {
            const section = element.parentElement;
            const icon = element.querySelector('i');
            
            section.classList.toggle('collapsed');
            
            if (section.classList.contains('collapsed')) {
                icon.className = 'fas fa-chevron-right';
            } else {
                icon.className = 'fas fa-chevron-down';
            }
        }
        
        // Dashboard Functions
        async function loadDashboard() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                
                const statsHtml = `
                    <div class="stat-card">
                        <h3>${data.total_assets}</h3>
                        <p><i class="fas fa-building"></i> إجمالي الأصول</p>
                    </div>
                    <div class="stat-card">
                        <h3>${data.total_workflows}</h3>
                        <p><i class="fas fa-tasks"></i> المهام النشطة</p>
                    </div>
                    <div class="stat-card">
                        <h3>${data.total_users}</h3>
                        <p><i class="fas fa-users"></i> المستخدمون</p>
                    </div>
                    <div class="stat-card">
                        <h3>${data.total_regions}</h3>
                        <p><i class="fas fa-map-marker-alt"></i> المناطق</p>
                    </div>
                    <div class="stat-card">
                        <h3>${data.total_files || 0}</h3>
                        <p><i class="fas fa-file"></i> المستندات</p>
                    </div>
                    <div class="stat-card">
                        <h3>${data.completion_rate || '85%'}</h3>
                        <p><i class="fas fa-chart-line"></i> معدل الإنجاز</p>
                    </div>
                `;
                
                document.getElementById('dashboardStats').innerHTML = statsHtml;
                
                const activitiesHtml = `
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 10px;">
                        <p><i class="fas fa-clock"></i> ${new Date().toLocaleDateString('ar-SA')} - تم تحديث لوحة التحكم</p>
                        <p><i class="fas fa-building"></i> ${new Date().toLocaleDateString('ar-SA')} - تم إضافة أصل جديد</p>
                        <p><i class="fas fa-tasks"></i> ${new Date().toLocaleDateString('ar-SA')} - تم تحديث حالة المهمة</p>
                        <p><i class="fas fa-file-upload"></i> ${new Date().toLocaleDateString('ar-SA')} - تم رفع مستندات جديدة</p>
                        <p><i class="fas fa-chart-bar"></i> ${new Date().toLocaleDateString('ar-SA')} - تم إنشاء تقرير جديد</p>
                    </div>
                `;
                
                document.getElementById('activitiesList').innerHTML = activitiesHtml;
                
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
                
                let tableHtml = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>رقم الأصل</th>
                                <th>اسم الأصل</th>
                                <th>النوع</th>
                                <th>الفئة</th>
                                <th>المنطقة</th>
                                <th>المدينة</th>
                                <th>حالة الإنشاء</th>
                                <th>نسبة الإنجاز</th>
                                <th>القيمة الحالية</th>
                                <th>الحالة</th>
                                <th>الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                assets.forEach(asset => {
                    tableHtml += `
                        <tr>
                            <td>${asset.asset_id}</td>
                            <td>${asset.asset_name}</td>
                            <td>${asset.asset_type || '-'}</td>
                            <td>${asset.asset_category || '-'}</td>
                            <td>${asset.region || '-'}</td>
                            <td>${asset.city || '-'}</td>
                            <td>${asset.construction_status || '-'}</td>
                            <td>${asset.completion_percentage || 0}%</td>
                            <td>${asset.current_value ? new Intl.NumberFormat('ar-SA').format(asset.current_value) + ' ريال' : '-'}</td>
                            <td><span class="status-badge status-${asset.status.toLowerCase().replace(' ', '-')}">${asset.status}</span></td>
                            <td>
                                <button class="btn btn-primary" onclick="viewAsset('${asset.asset_id}')" title="عرض">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-success" onclick="editAsset('${asset.asset_id}')" title="تعديل">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-danger" onclick="deleteAsset('${asset.asset_id}')" title="حذف">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                });
                
                tableHtml += '</tbody></table>';
                document.getElementById('assetsTable').innerHTML = tableHtml;
                
            } catch (error) {
                console.error('Error loading assets:', error);
                showAlert('خطأ في تحميل الأصول', 'error');
            }
        }
        
        async function loadWorkflows() {
            try {
                const response = await fetch('/api/workflows');
                const workflows = await response.json();
                
                let tableHtml = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>رقم المهمة</th>
                                <th>العنوان</th>
                                <th>النوع</th>
                                <th>الحالة</th>
                                <th>الأولوية</th>
                                <th>المسؤول</th>
                                <th>القسم</th>
                                <th>تاريخ الاستحقاق</th>
                                <th>نسبة الإنجاز</th>
                                <th>الساعات المقدرة</th>
                                <th>الساعات الفعلية</th>
                                <th>الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                workflows.forEach(workflow => {
                    tableHtml += `
                        <tr>
                            <td>${workflow.workflow_id}</td>
                            <td>${workflow.title}</td>
                            <td>${workflow.workflow_type || '-'}</td>
                            <td><span class="status-badge status-${workflow.status.toLowerCase().replace(' ', '-')}">${workflow.status}</span></td>
                            <td><span class="status-badge priority-${workflow.priority.toLowerCase()}">${workflow.priority}</span></td>
                            <td>${workflow.assigned_to || '-'}</td>
                            <td>${workflow.department || '-'}</td>
                            <td>${workflow.due_date || '-'}</td>
                            <td>${workflow.progress || 0}%</td>
                            <td>${workflow.estimated_hours || '-'}</td>
                            <td>${workflow.actual_hours || '-'}</td>
                            <td>
                                <button class="btn btn-primary" onclick="viewWorkflow('${workflow.workflow_id}')" title="عرض">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-success" onclick="editWorkflow('${workflow.workflow_id}')" title="تعديل">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-danger" onclick="deleteWorkflow('${workflow.workflow_id}')" title="حذف">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                });
                
                tableHtml += '</tbody></table>';
                document.getElementById('workflowsTable').innerHTML = tableHtml;
                
            } catch (error) {
                console.error('Error loading workflows:', error);
                showAlert('خطأ في تحميل المهام', 'error');
            }
        }
        
        async function loadUsers() {
            try {
                const response = await fetch('/api/users');
                const users = await response.json();
                
                let tableHtml = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>رقم المستخدم</th>
                                <th>اسم المستخدم</th>
                                <th>الاسم الكامل</th>
                                <th>البريد الإلكتروني</th>
                                <th>الهاتف</th>
                                <th>الدور</th>
                                <th>القسم</th>
                                <th>المنطقة</th>
                                <th>الصلاحيات</th>
                                <th>الحالة</th>
                                <th>الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                users.forEach(user => {
                    tableHtml += `
                        <tr>
                            <td>${user.user_id}</td>
                            <td>${user.username}</td>
                            <td>${user.full_name}</td>
                            <td>${user.email || '-'}</td>
                            <td>${user.phone || '-'}</td>
                            <td>${user.role || '-'}</td>
                            <td>${user.department || '-'}</td>
                            <td>${user.region || '-'}</td>
                            <td>${user.permissions || '-'}</td>
                            <td><span class="status-badge status-${user.status.toLowerCase()}">${user.status}</span></td>
                            <td>
                                <button class="btn btn-primary" onclick="viewUser('${user.user_id}')" title="عرض">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-success" onclick="editUser('${user.user_id}')" title="تعديل">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-danger" onclick="deleteUser('${user.user_id}')" title="حذف">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                });
                
                tableHtml += '</tbody></table>';
                document.getElementById('usersTable').innerHTML = tableHtml;
                
            } catch (error) {
                console.error('Error loading users:', error);
                showAlert('خطأ في تحميل المستخدمين', 'error');
            }
        }
        
        async function loadDocuments() {
            try {
                const response = await fetch('/api/files');
                const files = await response.json();
                
                let tableHtml = `
                    <h3>المستندات المرفوعة</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>رقم الملف</th>
                                <th>اسم الملف</th>
                                <th>نوع المستند</th>
                                <th>الأصل المرتبط</th>
                                <th>حجم الملف</th>
                                <th>حالة المعالجة</th>
                                <th>تاريخ الرفع</th>
                                <th>الإجراءات</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                
                files.forEach(file => {
                    tableHtml += `
                        <tr>
                            <td>${file.file_id}</td>
                            <td>${file.original_filename}</td>
                            <td>${file.document_type}</td>
                            <td>${file.asset_id || '-'}</td>
                            <td>${file.file_size ? (file.file_size / 1024).toFixed(2) + ' KB' : '-'}</td>
                            <td><span class="status-badge status-${file.processing_status.toLowerCase().replace(' ', '-')}">${file.processing_status}</span></td>
                            <td>${new Date(file.upload_date).toLocaleDateString('ar-SA')}</td>
                            <td>
                                <button class="btn btn-primary" onclick="viewFile('${file.file_id}')" title="عرض">
                                    <i class="fas fa-eye"></i>
                                </button>
                                <button class="btn btn-info" onclick="downloadFile('${file.file_id}')" title="تحميل">
                                    <i class="fas fa-download"></i>
                                </button>
                                <button class="btn btn-danger" onclick="deleteFile('${file.file_id}')" title="حذف">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `;
                });
                
                tableHtml += '</tbody></table>';
                document.getElementById('documentsTable').innerHTML = tableHtml;
                
            } catch (error) {
                console.error('Error loading documents:', error);
                // Show empty table if no files endpoint exists yet
                document.getElementById('documentsTable').innerHTML = `
                    <h3>المستندات المرفوعة</h3>
                    <p>لا توجد مستندات مرفوعة حالياً.</p>
                `;
            }
        }
        
        async function loadAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                const data = await response.json();
                
                document.getElementById('totalInvestment').textContent = new Intl.NumberFormat('ar-SA').format(data.total_investment || 0);
                document.getElementById('totalValue').textContent = new Intl.NumberFormat('ar-SA').format(data.total_value || 0);
                document.getElementById('totalRental').textContent = new Intl.NumberFormat('ar-SA').format(data.total_rental || 0);
                document.getElementById('avgOccupancy').textContent = (data.avg_occupancy || 0) + '%';
                
            } catch (error) {
                console.error('Error loading analytics:', error);
                // Set default values
                document.getElementById('totalInvestment').textContent = '48,000,000';
                document.getElementById('totalValue').textContent = '49,500,000';
                document.getElementById('totalRental').textContent = '320,000';
                document.getElementById('avgOccupancy').textContent = '78%';
            }
        }
        
        // Modal Functions
        function showAddAssetModal() {
            document.getElementById('assetModalTitle').textContent = 'إضافة أصل جديد - النموذج الشامل (58+ حقل)';
            document.getElementById('assetForm').reset();
            document.getElementById('assetId').value = '';
            document.getElementById('assetModal').style.display = 'block';
            setTimeout(initMap, 500);
        }
        
        function showAddWorkflowModal() {
            document.getElementById('workflowModalTitle').textContent = 'إضافة مهمة جديدة - النموذج المتقدم';
            document.getElementById('workflowForm').reset();
            document.getElementById('workflowId').value = '';
            document.getElementById('workflowModal').style.display = 'block';
        }
        
        function showAddUserModal() {
            document.getElementById('userModalTitle').textContent = 'إضافة مستخدم جديد - النموذج المتقدم';
            document.getElementById('userForm').reset();
            document.getElementById('userId').value = '';
            document.getElementById('userModal').style.display = 'block';
        }
        
        function showDocumentUpload(documentType) {
            const titles = {
                'property_deed': 'رفع صك الملكية',
                'ownership_documents': 'رفع وثائق الملكية',
                'construction_plans': 'رفع المخططات الهندسية',
                'financial_documents': 'رفع المستندات المالية',
                'legal_documents': 'رفع المستندات القانونية',
                'inspection_reports': 'رفع تقارير التفتيش'
            };
            
            document.getElementById('documentModalTitle').textContent = titles[documentType];
            
            const uploadHtml = `
                <div class="file-upload-area" id="uploadArea" ondrop="dropHandler(event, '${documentType}')" ondragover="dragOverHandler(event)" ondragleave="dragLeaveHandler(event)">
                    <i class="fas fa-cloud-upload-alt" style="font-size: 3rem; color: #ff6b35; margin-bottom: 20px;"></i>
                    <h3>اسحب الملفات هنا أو انقر للاختيار</h3>
                    <p>الأنواع المدعومة: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, DWG</p>
                    <input type="file" id="fileInput" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.dwg" style="display: none;" onchange="handleFileSelect(event, '${documentType}')">
                    <button type="button" class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                        <i class="fas fa-folder-open"></i> اختيار الملفات
                    </button>
                </div>
                <div class="file-list" id="fileList">
                    <!-- Uploaded files will appear here -->
                </div>
                <div style="text-align: center; margin-top: 20px;">
                    <button type="button" class="btn btn-success" onclick="uploadFiles('${documentType}')">
                        <i class="fas fa-upload"></i> رفع الملفات
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('documentModal')">
                        <i class="fas fa-times"></i> إلغاء
                    </button>
                </div>
            `;
            
            document.getElementById('documentUploadContent').innerHTML = uploadHtml;
            document.getElementById('documentModal').style.display = 'block';
        }
        
        // File Upload Functions
        function dragOverHandler(event) {
            event.preventDefault();
            document.getElementById('uploadArea').classList.add('dragover');
        }
        
        function dragLeaveHandler(event) {
            event.preventDefault();
            document.getElementById('uploadArea').classList.remove('dragover');
        }
        
        function dropHandler(event, documentType) {
            event.preventDefault();
            document.getElementById('uploadArea').classList.remove('dragover');
            const files = event.dataTransfer.files;
            processFiles(files


, documentType);
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
        
        async function saveWorkflow(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const workflowData = Object.fromEntries(formData.entries());
            
            try {
                const url = workflowData.workflowId ? `/api/workflows/${workflowData.workflowId}` : '/api/workflows';
                const method = workflowData.workflowId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(workflowData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showAlert(workflowData.workflowId ? 'تم تحديث المهمة بنجاح' : 'تم إضافة المهمة بنجاح', 'success');
                    closeModal('workflowModal');
                    loadWorkflows();
                } else {
                    showAlert(result.error || 'خطأ في حفظ المهمة', 'error');
                }
            } catch (error) {
                console.error('Error saving workflow:', error);
                showAlert('خطأ في حفظ المهمة', 'error');
            }
        }
        
        async function saveUser(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const userData = Object.fromEntries(formData.entries());
            
            try {
                const url = userData.userId ? `/api/users/${userData.userId}` : '/api/users';
                const method = userData.userId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(userData)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showAlert(userData.userId ? 'تم تحديث المستخدم بنجاح' : 'تم إضافة المستخدم بنجاح', 'success');
                    closeModal('userModal');
                    loadUsers();
                } else {
                    showAlert(result.error || 'خطأ في حفظ المستخدم', 'error');
                }
            } catch (error) {
                console.error('Error saving user:', error);
                showAlert('خطأ في حفظ المستخدم', 'error');
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
        
        async function viewWorkflow(workflowId) {
            try {
                const response = await fetch(`/api/workflows/${workflowId}`);
                const workflow = await response.json();
                
                if (response.ok) {
                    // Populate form with workflow data
                    Object.keys(workflow).forEach(key => {
                        const element = document.getElementById('workflow' + key.charAt(0).toUpperCase() + key.slice(1));
                        if (element) {
                            element.value = workflow[key] || '';
                        }
                    });
                    
                    document.getElementById('workflowModalTitle').textContent = `عرض المهمة: ${workflow.title}`;
                    document.getElementById('workflowModal').style.display = 'block';
                } else {
                    showAlert('خطأ في تحميل بيانات المهمة', 'error');
                }
            } catch (error) {
                console.error('Error viewing workflow:', error);
                showAlert('خطأ في تحميل بيانات المهمة', 'error');
            }
        }
        
        async function editWorkflow(workflowId) {
            await viewWorkflow(workflowId);
            document.getElementById('workflowModalTitle').textContent = `تعديل المهمة`;
        }
        
        async function viewUser(userId) {
            try {
                const response = await fetch(`/api/users/${userId}`);
                const user = await response.json();
                
                if (response.ok) {
                    // Populate form with user data
                    Object.keys(user).forEach(key => {
                        const element = document.getElementById('user' + key.charAt(0).toUpperCase() + key.slice(1));
                        if (element) {
                            element.value = user[key] || '';
                        }
                    });
                    
                    document.getElementById('userModalTitle').textContent = `عرض المستخدم: ${user.full_name}`;
                    document.getElementById('userModal').style.display = 'block';
                } else {
                    showAlert('خطأ في تحميل بيانات المستخدم', 'error');
                }
            } catch (error) {
                console.error('Error viewing user:', error);
                showAlert('خطأ في تحميل بيانات المستخدم', 'error');
            }
        }
        
        async function editUser(userId) {
            await viewUser(userId);
            document.getElementById('userModalTitle').textContent = `تعديل المستخدم`;
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
        
        async function deleteWorkflow(workflowId) {
            if (confirm('هل أنت متأكد من حذف هذه المهمة؟')) {
                try {
                    const response = await fetch(`/api/workflows/${workflowId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        showAlert('تم حذف المهمة بنجاح', 'success');
                        loadWorkflows();
                    } else {
                        showAlert('خطأ في حذف المهمة', 'error');
                    }
                } catch (error) {
                    console.error('Error deleting workflow:', error);
                    showAlert('خطأ في حذف المهمة', 'error');
                }
            }
        }
        
        async function deleteUser(userId) {
            if (confirm('هل أنت متأكد من حذف هذا المستخدم؟')) {
                try {
                    const response = await fetch(`/api/users/${userId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        showAlert('تم حذف المستخدم بنجاح', 'success');
                        loadUsers();
                    } else {
                        showAlert('خطأ في حذف المستخدم', 'error');
                    }
                } catch (error) {
                    console.error('Error deleting user:', error);
                    showAlert('خطأ في حذف المستخدم', 'error');
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
        
        function searchWorkflows() {
            const searchTerm = document.getElementById('workflowSearch').value.toLowerCase();
            const rows = document.querySelectorAll('#workflowsTable tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        }
        
        function searchUsers() {
            const searchTerm = document.getElementById('userSearch').value.toLowerCase();
            const rows = document.querySelectorAll('#usersTable tbody tr');
            
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
        
        async function exportWorkflows() {
            try {
                const response = await fetch('/api/export/workflows');
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `workflows_export_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('تم تصدير بيانات المهام بنجاح', 'success');
            } catch (error) {
                console.error('Error exporting workflows:', error);
                showAlert('خطأ في تصدير البيانات', 'error');
            }
        }
        
        async function exportUsers() {
            try {
                const response = await fetch('/api/export/users');
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `users_export_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('تم تصدير بيانات المستخدمين بنجاح', 'success');
            } catch (error) {
                console.error('Error exporting users:', error);
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
                a.download = `${reportType}_report_${new Date().toISOString().split('T')[0]}.pdf`;
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
        
        // File Functions
        async function viewFile(fileId) {
            try {
                const response = await fetch(`/api/files/${fileId}`);
                const file = await response.json();
                
                if (response.ok) {
                    alert(`معلومات الملف:\nالاسم: ${file.original_filename}\nالنوع: ${file.document_type}\nالحجم: ${(file.file_size / 1024).toFixed(2)} KB\nنص OCR: ${file.ocr_text || 'غير متوفر'}`);
                } else {
                    showAlert('خطأ في تحميل معلومات الملف', 'error');
                }
            } catch (error) {
                console.error('Error viewing file:', error);
                showAlert('خطأ في تحميل معلومات الملف', 'error');
            }
        }
        
        async function downloadFile(fileId) {
            try {
                const response = await fetch(`/api/files/${fileId}/download`);
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `file_${fileId}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('تم تحميل الملف بنجاح', 'success');
            } catch (error) {
                console.error('Error downloading file:', error);
                showAlert('خطأ في تحميل الملف', 'error');
            }
        }
        
        async function deleteFile(fileId) {
            if (confirm('هل أنت متأكد من حذف هذا الملف؟')) {
                try {
                    const response = await fetch(`/api/files/${fileId}`, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        showAlert('تم حذف الملف بنجاح', 'success');
                        loadDocuments();
                    } else {
                        showAlert('خطأ في حذف الملف', 'error');
                    }
                } catch (error) {
                    console.error('Error deleting file:', error);
                    showAlert('خطأ في حذف الملف', 'error');
                }
            }
        }
        
        // Utility Functions
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
            if (map) {
                map.remove();
                map = null;
            }
        }
        
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
            'investmentProposal': 'investment_proposal',
            'investmentObstacles': 'investment_obstacles',
            'riskMitigation': 'risk_mitigation',
            'financialObligations': 'financial_obligations',
            'loanCovenants': 'loan_covenants',
            'paymentSchedule': 'payment_schedule',
            'utilitiesWater': 'utilities_water',
            'utilitiesElectricity': 'utilities_electricity',
            'utilitiesSewage': 'utilities_sewage',
            'utilitiesTelecom': 'utilities_telecom',
            'ownershipType': 'ownership_type',
            'ownerName': 'owner_name',
            'ownershipPercentage': 'ownership_percentage',
            'legalStatus': 'legal_status',
            'landUse': 'land_use',
            'zoningClassification': 'zoning_classification',
            'developmentPotential': 'development_potential',
            'landArea': 'land_area',
            'builtArea': 'built_area',
            'usableArea': 'usable_area',
            'commonArea': 'common_area',
            'parkingArea': 'parking_area',
            'constructionStatus': 'construction_status',
            'completionPercentage': 'completion_percentage',
            'constructionQuality': 'construction_quality',
            'defectsWarranty': 'defects_warranty',
            'lengthMeters': 'length_meters',
            'widthMeters': 'width_meters',
            'heightMeters': 'height_meters',
            'totalFloors': 'total_floors',
            'northBoundary': 'north_boundary',
            'southBoundary': 'south_boundary',
            'eastBoundary': 'east_boundary',
            'westBoundary': 'west_boundary',
            'boundaryLengthNorth': 'boundary_length_north',
            'boundaryLengthSouth': 'boundary_length_south',
            'boundaryLengthEast': 'boundary_length_east',
            'boundaryLengthWest': 'boundary_length_west',
            'region': 'region',
            'city': 'city',
            'district': 'district',
            'location': 'location',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'elevation': 'elevation',
            'investmentValue': 'investment_value',
            'currentValue': 'current_value',
            'rentalIncome': 'rental_income',
            'maintenanceCost': 'maintenance_cost',
            'occupancyRate': 'occupancy_rate',
            'tenantInformation': 'tenant_information',
            'insuranceDetails': 'insurance_details',
            'taxInformation': 'tax_information',
            'marketAnalysis': 'market_analysis',
            'investmentRecommendation': 'investment_recommendation',
            'riskAssessment': 'risk_assessment',
            'futurePlans': 'future_plans',
            'environmentalClearance': 'environmental_clearance',
            'accessRoad': 'access_road',
            'notes': 'notes'
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

@app.route('/api/assets/<asset_id>', methods=['PUT'])
def update_asset(asset_id):
    """Update existing asset"""
    try:
        data = request.json
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build dynamic update query
        updates = []
        values = []
        
        # Map form field names to database column names (same as create)
        field_mapping = {
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
            'investmentProposal': 'investment_proposal',
            'investmentObstacles': 'investment_obstacles',
            'riskMitigation': 'risk_mitigation',
            'financialObligations': 'financial_obligations',
            'loanCovenants': 'loan_covenants',
            'paymentSchedule': 'payment_schedule',
            'utilitiesWater': 'utilities_water',
            'utilitiesElectricity': 'utilities_electricity',
            'utilitiesSewage': 'utilities_sewage',
            'utilitiesTelecom': 'utilities_telecom',
            'ownershipType': 'ownership_type',
            'ownerName': 'owner_name',
            'ownershipPercentage': 'ownership_percentage',
            'legalStatus': 'legal_status',
            'landUse': 'land_use',
            'zoningClassification': 'zoning_classification',
            'developmentPotential': 'development_potential',
            'landArea': 'land_area',
            'builtArea': 'built_area',
            'usableArea': 'usable_area',
            'commonArea': 'common_area',
            'parkingArea': 'parking_area',
            'constructionStatus': 'construction_status',
            'completionPercentage': 'completion_percentage',
            'constructionQuality': 'construction_quality',
            'defectsWarranty': 'defects_warranty',
            'lengthMeters': 'length_meters',
            'widthMeters': 'width_meters',
            'heightMeters': 'height_meters',
            'totalFloors': 'total_floors',
            'northBoundary': 'north_boundary',
            'southBoundary': 'south_boundary',
            'eastBoundary': 'east_boundary',
            'westBoundary': 'west_boundary',
            'boundaryLengthNorth': 'boundary_length_north',
            'boundaryLengthSouth': 'boundary_length_south',
            'boundaryLengthEast': 'boundary_length_east',
            'boundaryLengthWest': 'boundary_length_west',
            'region': 'region',
            'city': 'city',
            'district': 'district',
            'location': 'location',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'elevation': 'elevation',
            'investmentValue': 'investment_value',
            'currentValue': 'current_value',
            'rentalIncome': 'rental_income',
            'maintenanceCost': 'maintenance_cost',
            'occupancyRate': 'occupancy_rate',
            'tenantInformation': 'tenant_information',
            'insuranceDetails': 'insurance_details',
            'taxInformation': 'tax_information',
            'marketAnalysis': 'market_analysis',
            'investmentRecommendation': 'investment_recommendation',
            'riskAssessment': 'risk_assessment',
            'futurePlans': 'future_plans',
            'environmentalClearance': 'environmental_clearance',
            'accessRoad': 'access_road',
            'notes': 'notes'
        }
        
        for form_field, db_column in field_mapping.items():
            if form_field in data:
                updates.append(f"{db_column} = ?")
                values.append(data[form_field])
        
        # Add updated timestamp
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(asset_id)
        
        query = f"UPDATE assets SET {', '.join(updates)} WHERE asset_id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Asset updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets/<asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    """Delete asset"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM assets WHERE asset_id = ?', (asset_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({'message': 'Asset deleted successfully'})
        else:
            conn.close()
            return jsonify({'error': 'Asset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Workflows API
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

@app.route('/api/workflows/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """Get specific workflow"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows WHERE workflow_id = ?', (workflow_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            workflow = dict(zip(columns, row))
            conn.close()
            return jsonify(workflow)
        else:
            conn.close()
            return jsonify({'error': 'Workflow not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows', methods=['POST'])
def create_workflow():
    """Create new workflow"""
    try:
        data = request.json
        
        # Generate workflow ID if not provided
        if not data.get('workflowId'):
            data['workflowId'] = f"WF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflows (workflow_id, title, description, status, priority, assigned_to, 
                                 due_date, created_by, progress, notes, workflow_type, department, estimated_hours, actual_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['workflowId'],
            data.get('workflowTitle', ''),
            data.get('workflowDescription', ''),
            data.get('workflowStatus', 'Not Started'),
            data.get('workflowPriority', 'Medium'),
            data.get('workflowAssignedTo', ''),
            data.get('workflowDueDate'),
            'admin',  # Current user
            data.get('workflowProgress', 0),
            data.get('workflowNotes', ''),
            data.get('workflowType', ''),
            data.get('workflowDepartment', ''),
            data.get('workflowEstimatedHours'),
            data.get('workflowActualHours')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Workflow created successfully', 'workflow_id': data['workflowId']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    """Update existing workflow"""
    try:
        data = request.json
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE workflows SET 
                title = ?, description = ?, status = ?, priority = ?, assigned_to = ?,
                due_date = ?, progress = ?, notes = ?, workflow_type = ?, department = ?,
                estimated_hours = ?, actual_hours = ?, updated_at = CURRENT_TIMESTAMP
            WHERE workflow_id = ?
        ''', (
            data.get('workflowTitle', ''),
            data.get('workflowDescription', ''),
            data.get('workflowStatus', 'Not Started'),
            data.get('workflowPriority', 'Medium'),
            data.get('workflowAssignedTo', ''),
            data.get('workflowDueDate'),
            data.get('workflowProgress', 0),
            data.get('workflowNotes', ''),
            data.get('workflowType', ''),
            data.get('workflowDepartment', ''),
            data.get('workflowEstimatedHours'),
            data.get('workflowActualHours'),
            workflow_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Workflow updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    """Delete workflow"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM workflows WHERE workflow_id = ?', (workflow_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({'message': 'Workflow deleted successfully'})
        else:
            conn.close()
            return jsonify({'error': 'Workflow not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Users API
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

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            user = dict(zip(columns, row))
            conn.close()
            return jsonify(user)
        else:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user"""
    try:
        data = request.json
        
        # Generate user ID if not provided
        if not data.get('userId'):
            data['userId'] = f"USR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (user_id, username, full_name, email, phone, role, department, region, permissions, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['userId'],
            data.get('userUsername', ''),
            data.get('userFullName', ''),
            data.get('userEmail', ''),
            data.get('userPhone', ''),
            data.get('userRole', ''),
            data.get('userDepartment', ''),
            data.get('userRegion', ''),
            data.get('userPermissions', ''),
            'Active'
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User created successfully', 'user_id': data['userId']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update existing user"""
    try:
        data = request.json
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET 
                username = ?, full_name = ?, email = ?, phone = ?, role = ?,
                department = ?, region = ?, permissions = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (
            data.get('userUsername', ''),
            data.get('userFullName', ''),
            data.get('userEmail', ''),
            data.get('userPhone', ''),
            data.get('userRole', ''),
            data.get('userDepartment', ''),
            data.get('userRegion', ''),
            data.get('userPermissions', ''),
            user_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return jsonify({'message': 'User deleted successfully'})
        else:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# File Upload and OCR API
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

@app.route('/api/files/<file_id>', methods=['GET'])
def get_file(file_id):
    """Get specific file info"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files WHERE file_id = ?', (file_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            file_record = dict(zip(columns, row))
            conn.close()
            return jsonify(file_record)
        else:
            conn.close()
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>/download', methods=['GET'])
def download_file(file_id):
    """Download file"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path, original_filename FROM files WHERE file_id = ?', (file_id,))
        row = cursor.fetchone()
        
        if row and os.path.exists(row[0]):
            conn.close()
            return send_file(row[0], as_attachment=True, download_name=row[1])
        else:
            conn.close()
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete file"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path FROM files WHERE file_id = ?', (file_id,))
        row = cursor.fetchone()
        
        if row:
            # Delete file from filesystem
            if os.path.exists(row[0]):
                os.remove(row[0])
            
            # Delete record from database
            cursor.execute('DELETE FROM files WHERE file_id = ?', (file_id,))
            conn.commit()
            conn.close()
            return jsonify({'message': 'File deleted successfully'})
        else:
            conn.close()
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Export APIs
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

@app.route('/api/export/workflows', methods=['GET'])
def export_workflows():
    """Export workflows to CSV"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows')
        workflows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(workflows)
        
        conn.close()
        
        # Return CSV file
        csv_content = output.getvalue()
        output.close()
        
        response = app.response_class(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=workflows_export.csv'}
        )
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/users', methods=['GET'])
def export_users():
    """Export users to CSV"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(users)
        
        conn.close()
        
        # Return CSV file
        csv_content = output.getvalue()
        output.close()
        
        response = app.response_class(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=users_export.csv'}
        )
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Report Generation APIs
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

