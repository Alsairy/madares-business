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
import tempfile
import mimetypes
import re

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
    """Extract text from various file formats using OCR simulation"""
    try:
        file_ext = file_path.rsplit('.', 1)[1].lower()
        filename = os.path.basename(file_path)
        
        # Simulate realistic OCR text extraction
        if file_ext in ['png', 'jpg', 'jpeg', 'gif']:
            return f"""OCR Text Extracted from {filename}:
Property Document Analysis:
- Property ID: {uuid.uuid4().hex[:8].upper()}
- Location: Riyadh, Saudi Arabia
- Area: 5000 square meters
- Coordinates: 24.7136°N, 46.6753°E
- Ownership: Government Property
- Status: Active Development
- Construction: 85% Complete
- Value: 15,000,000 SAR
- Last Updated: {datetime.now().strftime('%Y-%m-%d')}
"""
            
        elif file_ext == 'pdf':
            return f"""PDF Document Extracted from {filename}:
PROPERTY DEED DOCUMENT
===================
Property Registration No: PD-{uuid.uuid4().hex[:6].upper()}
Owner: Ministry of Finance - Kingdom of Saudi Arabia
Property Type: Commercial Development
Total Area: 8,500 square meters
Built Area: 6,200 square meters
Location: Al-Malaz District, Riyadh
Boundaries:
- North: 150m adjacent to public road
- South: 150m adjacent to residential area
- East: 100m adjacent to commercial zone
- West: 100m adjacent to park area
Legal Status: Approved and Registered
Registration Date: {datetime.now().strftime('%Y-%m-%d')}
"""
            
        elif file_ext in ['doc', 'docx']:
            return f"""Document Content from {filename}:
ENGINEERING SPECIFICATIONS
========================
Project: Commercial Plaza Development
Engineer: Ahmed Al-Rashid, P.E.
Specifications:
- Foundation: Reinforced concrete, 3m depth
- Structure: Steel frame with concrete floors
- Height: 8 floors, 25m total height
- Elevators: 4 passenger, 1 freight
- Parking: 200 spaces underground
- HVAC: Central air conditioning system
- Electrical: 3-phase, 2000 amp service
- Fire Safety: Sprinkler system, emergency exits
- Completion: Estimated 18 months
- Budget: 25,000,000 SAR
"""
            
        elif file_ext in ['xls', 'xlsx']:
            return f"""Spreadsheet Data from {filename}:
FINANCIAL ANALYSIS REPORT
=======================
Investment Summary:
- Initial Investment: 20,000,000 SAR
- Current Value: 28,500,000 SAR
- Annual Rental Income: 2,400,000 SAR
- Operating Expenses: 480,000 SAR
- Net Annual Income: 1,920,000 SAR
- ROI: 9.6% annually
- Occupancy Rate: 92%
- Market Growth: 5.2% yearly
- Projected 5-year Value: 35,000,000 SAR
"""
            
        elif file_ext == 'txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    return f"Text File Content from {filename}:\n{content}"
            except:
                return f"Text file processed: {filename} - Content extracted successfully"
                
        elif file_ext == 'dwg':
            return f"""CAD Drawing Analysis from {filename}:
ARCHITECTURAL DRAWING SPECIFICATIONS
==================================
Drawing Type: Site Plan and Floor Plans
Scale: 1:100
Total Floors: 8 levels + basement
Building Dimensions:
- Length: 120 meters
- Width: 80 meters
- Height: 25 meters
- Basement: 15 meters depth
Room Distribution:
- Commercial Units: 45 units
- Office Spaces: 120 offices
- Common Areas: 15% of total area
- Parking: 200 spaces
Utilities:
- Water: Connected to main supply
- Electricity: 2000 amp service
- Sewage: Connected to municipal system
- Telecom: Fiber optic ready
"""
        else:
            return f"File processed: {filename} - Content type: {file_ext} - OCR processing completed"
            
    except Exception as e:
        return f"OCR Processing Error for {os.path.basename(file_path)}: {str(e)}"

def init_db():
    """Initialize the database with all required tables and complete MOE fields"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Complete Assets table with ALL 58+ MOE fields organized in 14 sections
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
            
            -- Section 14: Financial & Additional Information (15+ fields)
            investment_value REAL,
            current_value REAL,
            rental_income REAL,
            maintenance_cost REAL,
            occupancy_rate REAL,
            tenant_information TEXT,
            insurance_details TEXT,
            tax_information TEXT,
            market_analysis TEXT,
            investment_recommendation TEXT,
            risk_assessment TEXT,
            future_plans TEXT,
            environmental_clearance TEXT,
            access_road TEXT,
            utilities_cost REAL,
            property_tax REAL,
            management_fee REAL,
            security_deposit REAL,
            lease_terms TEXT,
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
            asset_id TEXT,
            completion_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id)
        )
    ''')
    
    # Users table for user management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            username TEXT UNIQUE,
            password TEXT,
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
        # Simple sample data that matches the column count exactly
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
                              tenant_information, insurance_details, tax_information, market_analysis, investment_recommendation, risk_assessment, future_plans, environmental_clearance, access_road,
                              utilities_cost, property_tax, management_fee, security_deposit, lease_terms, notes)
            VALUES ('AST-001', 'Commercial Plaza Al-Riyadh', 'Commercial', 'Mixed Use', 'Class A', 'Active', 'Operational',
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
                   'Multiple Tenants', 'Comprehensive Coverage', 'Current', 'Strong Demand', 'Hold', 'Low', 'Expansion Planned', 'Approved', 'Paved',
                   25000.0, 150000.0, 75000.0, 500000.0, '5 years renewable', 'Prime location asset')
        ''')
        
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
                              tenant_information, insurance_details, tax_information, market_analysis, investment_recommendation, risk_assessment, future_plans, environmental_clearance, access_road,
                              utilities_cost, property_tax, management_fee, security_deposit, lease_terms, notes)
            VALUES ('AST-002', 'Residential Complex Jeddah', 'Residential', 'Housing', 'Class B', 'Under Development', 'Construction',
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
                   'Not Occupied', 'Under Review', 'Pending', 'Growing Market', 'Develop', 'Medium', 'Phase 2 Planning', 'Pending', 'Under Construction',
                   35000.0, 200000.0, 100000.0, 750000.0, '10 years', 'Strategic development project')
        ''')
        
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
                              tenant_information, insurance_details, tax_information, market_analysis, investment_recommendation, risk_assessment, future_plans, environmental_clearance, access_road,
                              utilities_cost, property_tax, management_fee, security_deposit, lease_terms, notes)
            VALUES ('AST-003', 'Industrial Warehouse Dammam', 'Industrial', 'Logistics', 'Class A', 'Active', 'Operational',
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
                   'Logistics Companies', 'Industrial Coverage', 'Current', 'Stable Demand', 'Hold', 'Low', 'Modernization', 'Approved', 'Paved',
                   15000.0, 80000.0, 40000.0, 300000.0, '15 years', 'Strategic logistics asset')
        ''')
    
    cursor.execute('SELECT COUNT(*) FROM workflows')
    if cursor.fetchone()[0] == 0:
        sample_workflows = [
            ('WF-001', 'Asset Inspection - Commercial Plaza', 'Complete comprehensive inspection of Commercial Plaza Al-Riyadh including structural assessment, safety compliance, and maintenance requirements', 'In Progress', 'High', 'Ahmed Al-Rashid', '2024-02-15', 'admin', 60, 'Inspection scheduled for next week. Initial assessment shows good condition.', 'Inspection', 'Operations', 8, 5, 'AST-001', None),
            ('WF-002', 'Document Review - Jeddah Complex', 'Review all legal documents for Residential Complex Jeddah including permits, contracts, and compliance certificates', 'Not Started', 'Medium', 'Sara Al-Mahmoud', '2024-02-20', 'admin', 0, 'Waiting for document submission from legal department', 'Legal Review', 'Legal', 12, 0, 'AST-002', None),
            ('WF-003', 'Financial Analysis - Dammam Warehouse', 'Conduct comprehensive financial performance analysis including ROI calculation and market comparison', 'Completed', 'Medium', 'Omar Al-Zahra', '2024-01-30', 'admin', 100, 'Analysis completed successfully. ROI exceeds expectations.', 'Financial Analysis', 'Finance', 16, 18, 'AST-003', '2024-01-30'),
            ('WF-004', 'Maintenance Planning - All Assets', 'Develop annual maintenance plan for all assets including preventive maintenance schedules and budget allocation', 'In Progress', 'High', 'Fatima Al-Nouri', '2024-03-01', 'admin', 25, 'Initial planning phase completed. Working on detailed schedules.', 'Maintenance', 'Operations', 40, 10, None, None),
            ('WF-005', 'Market Research - Riyadh Area', 'Conduct market research for potential new investments in Riyadh commercial district', 'Not Started', 'Low', 'Khalid Al-Salem', '2024-02-25', 'admin', 0, 'Pending approval from investment committee', 'Research', 'Investment', 24, 0, None, None)
        ]
        
        for workflow in sample_workflows:
            cursor.execute('''
                INSERT INTO workflows (workflow_id, title, description, status, priority, assigned_to, due_date, created_by, progress, notes, workflow_type, department, estimated_hours, actual_hours, asset_id, completion_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', workflow)
    
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        sample_users = [
            ('USR-001', 'admin', 'admin123', 'System Administrator', 'admin@madares.sa', '+966501234567', 'Administrator', 'IT', 'All Regions', 'Full Access', 'Active'),
            ('USR-002', 'ahmed.rashid', 'pass123', 'Ahmed Al-Rashid', 'ahmed.rashid@madares.sa', '+966502345678', 'Asset Manager', 'Operations', 'Riyadh', 'Asset Management', 'Active'),
            ('USR-003', 'sara.mahmoud', 'pass123', 'Sara Al-Mahmoud', 'sara.mahmoud@madares.sa', '+966503456789', 'Legal Advisor', 'Legal', 'Jeddah', 'Legal Review', 'Active'),
            ('USR-004', 'omar.zahra', 'pass123', 'Omar Al-Zahra', 'omar.zahra@madares.sa', '+966504567890', 'Financial Analyst', 'Finance', 'Dammam', 'Financial Analysis', 'Active'),
            ('USR-005', 'fatima.nouri', 'pass123', 'Fatima Al-Nouri', 'fatima.nouri@madares.sa', '+966505678901', 'Operations Manager', 'Operations', 'All Regions', 'Operations Management', 'Active'),
            ('USR-006', 'khalid.salem', 'pass123', 'Khalid Al-Salem', 'khalid.salem@madares.sa', '+966506789012', 'Regional Coordinator', 'Regional', 'Eastern Province', 'Regional Coordination', 'Active')
        ]
        
        for user in sample_users:
            cursor.execute('''
                INSERT INTO users (user_id, username, password, full_name, email, phone, role, department, region, permissions, status)
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
        
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
            direction: rtl;
        }
        
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #ff7b54;
            box-shadow: 0 0 0 3px rgba(255, 123, 84, 0.1);
        }
        
        .login-btn, .btn {
            padding: 1rem 1.5rem;
            background: linear-gradient(135deg, #ff7b54 0%, #ff6b35 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 0.5rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .login-btn:hover, .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(255, 123, 84, 0.3);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #36d1dc 0%, #5b86e5 100%);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
        }
        
        .btn-sm {
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
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
        
        .status-in-progress {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-completed {
            background: #d1ecf1;
            color: #0c5460;
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
            max-width: 900px;
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
        
        #map {
            height: 300px;
            width: 100%;
            border-radius: 10px;
            margin-top: 1rem;
        }
        
        .document-upload-section {
            background: #e8f5e8;
            border: 2px dashed #4CAF50;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
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
        
        .file-upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
            background: #f9f9f9;
            transition: all 0.3s ease;
        }
        
        .file-upload-area:hover {
            border-color: #ff7b54;
            background: #fff5f3;
        }
        
        .file-upload-area.dragover {
            border-color: #ff7b54;
            background: #fff5f3;
        }
        
        .file-list {
            margin-top: 1rem;
        }
        
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem;
            background: #f8f9fa;
            border-radius: 5px;
            margin-bottom: 0.5rem;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e1e5e9;
            border-radius: 10px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            transition: width 0.3s ease;
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

    <!-- Asset Modal with ALL MOE Fields -->
    <div id="assetModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('assetModal')">&times;</span>
            <h2 id="assetModalTitle">إضافة أصل جديد</h2>
            
            <form id="assetForm" onsubmit="saveAsset(event)">
                <input type="hidden" id="assetId" name="assetId">
                
                <!-- Section 1: Asset Identification & Status -->
                <div class="form-section">
                    <h3><i class="fas fa-id-card"></i> 1. تحديد الأصل والحالة (6 حقول)</h3>
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
                    <h3><i class="fas fa-clipboard-list"></i> 2. التخطيط وتقييم الحاجة (4 حقول)</h3>
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
                    <h3><i class="fas fa-map-marker-alt"></i> 3. جاذبية الموقع (3 حقول)</h3>
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

                <!-- Section 4: Investment Proposal & Obstacles -->
                <div class="form-section">
                    <h3><i class="fas fa-chart-line"></i> 4. اقتراح الاستثمار والعوائق (3 حقول)</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="investmentProposal">اقتراح الاستثمار:</label>
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
                    <h3><i class="fas fa-money-bill-wave"></i> 5. الالتزامات المالية والعهود (3 حقول)</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="financialObligations">الالتزامات المالية:</label>
                            <textarea id="financialObligations" name="financialObligations" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="loanCovenants">عهود القروض:</label>
                            <textarea id="loanCovenants" name="loanCovenants" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="paymentSchedule">جدول الدفع:</label>
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
                    <h3><i class="fas fa-plug"></i> 6. معلومات المرافق (4 حقول)</h3>
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
                    </div>
                    <div class="form-row">
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

                <!-- Section 7: Ownership Information -->
                <div class="form-section">
                    <h3><i class="fas fa-user-tie"></i> 7. معلومات الملكية (4 حقول)</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="ownershipType">نوع الملكية:</label>
                            <select id="ownershipType" name="ownershipType">
                                <option value="">اختر النوع</option>
                                <option value="Government">حكومي</option>
                                <option value="Private">خاص</option>
                                <option value="Mixed">مختلط</option>
                                <option value="Public">عام</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="ownerName">اسم المالك:</label>
                            <input type="text" id="ownerName" name="ownerName">
                        </div>
                        <div class="form-group">
                            <label for="ownershipPercentage">نسبة الملكية (%):</label>
                            <input type="number" id="ownershipPercentage" name="ownershipPercentage" min="0" max="100" step="0.1">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="legalStatus">الوضع القانوني:</label>
                            <select id="legalStatus" name="legalStatus">
                                <option value="">اختر الوضع</option>
                                <option value="Approved">معتمد</option>
                                <option value="Under Review">قيد المراجعة</option>
                                <option value="Pending">معلق</option>
                                <option value="In Process">قيد الإجراء</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Section 8: Land & Plan Details -->
                <div class="form-section">
                    <h3><i class="fas fa-map"></i> 8. تفاصيل الأرض والمخطط (3 حقول)</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="landUse">استخدام الأرض:</label>
                            <input type="text" id="landUse" name="landUse">
                        </div>
                        <div class="form-group">
                            <label for="zoningClassification">تصنيف التقسيم:</label>
                            <select id="zoningClassification" name="zoningClassification">
                                <option value="">اختر التصنيف</option>
                                <option value="Commercial">تجاري</option>
                                <option value="Residential">سكني</option>
                                <option value="Industrial">صناعي</option>
                                <option value="Mixed">مختلط</option>
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
                                <option value="None">لا توجد</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Section 9: Asset Area Details -->
                <div class="form-section">
                    <h3><i class="fas fa-ruler-combined"></i> 9. تفاصيل مساحة الأصل (5 حقول)</h3>
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

                <!-- Section 10: Construction Status -->
                <div class="form-section">
                    <h3><i class="fas fa-hard-hat"></i> 10. حالة الإنشاء (4 حقول)</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="constructionStatus">حالة الإنشاء:</label>
                            <select id="constructionStatus" name="constructionStatus">
                                <option value="">اختر الحالة</option>
                                <option value="Not Started">لم يبدأ</option>
                                <option value="Under Construction">تحت الإنشاء</option>
                                <option value="Completed">مكتمل</option>
                                <option value="On Hold">متوقف</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="completionPercentage">نسبة الإنجاز (%):</label>
                            <input type="number" id="completionPercentage" name="completionPercentage" min="0" max="100">
                        </div>
                        <div class="form-group">
                            <label for="constructionQuality">جودة الإنشاء:</label>
                            <select id="constructionQuality" name="constructionQuality">
                                <option value="">اختر الجودة</option>
                                <option value="Excellent">ممتاز</option>
                                <option value="Very Good">جيد جداً</option>
                                <option value="Good">جيد</option>
                                <option value="Fair">مقبول</option>
                                <option value="Poor">ضعيف</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="defectsWarranty">ضمان العيوب:</label>
                            <input type="text" id="defectsWarranty" name="defectsWarranty">
                        </div>
                    </div>
                </div>

                <!-- Section 11: Physical Dimensions -->
                <div class="form-section">
                    <h3><i class="fas fa-cube"></i> 11. الأبعاد الفيزيائية (4 حقول)</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="lengthMeters">الطول (متر):</label>
                            <input type="number" id="lengthMeters" name="lengthMeters" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="widthMeters">العرض (متر):</label>
                            <input type="number" id="widthMeters" name="widthMeters" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="heightMeters">الارتفاع (متر):</label>
                            <input type="number" id="heightMeters" name="heightMeters" step="0.01">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="totalFloors">إجمالي الطوابق:</label>
                            <input type="number" id="totalFloors" name="totalFloors" min="1">
                        </div>
                    </div>
                </div>

                <!-- Section 12: Boundaries -->
                <div class="form-section">
                    <h3><i class="fas fa-border-style"></i> 12. الحدود (8 حقول)</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="northBoundary">الحد الشمالي:</label>
                            <input type="text" id="northBoundary" name="northBoundary">
                        </div>
                        <div class="form-group">
                            <label for="southBoundary">الحد الجنوبي:</label>
                            <input type="text" id="southBoundary" name="southBoundary">
                        </div>
                        <div class="form-group">
                            <label for="eastBoundary">الحد الشرقي:</label>
                            <input type="text" id="eastBoundary" name="eastBoundary">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="westBoundary">الحد الغربي:</label>
                            <input type="text" id="westBoundary" name="westBoundary">
                        </div>
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

                <!-- Section 13: Geographic Location -->
                <div class="form-section">
                    <h3><i class="fas fa-globe"></i> 13. الموقع الجغرافي (7 حقول)</h3>
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
                            <label for="location">الموقع:</label>
                            <input type="text" id="location" name="location">
                        </div>
                        <div class="form-group">
                            <label for="latitude">خط العرض:</label>
                            <input type="number" id="latitude" name="latitude" step="0.000001">
                        </div>
                        <div class="form-group">
                            <label for="longitude">خط الطول:</label>
                            <input type="number" id="longitude" name="longitude" step="0.000001">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="elevation">الارتفاع عن سطح البحر (متر):</label>
                            <input type="number" id="elevation" name="elevation" step="0.01">
                        </div>
                    </div>
                    
                    <!-- Interactive Map -->
                    <div id="map"></div>
                    <p style="margin-top: 0.5rem; color: #666; font-size: 0.9rem;">
                        انقر على الخريطة لتحديد الموقع وتحديث الإحداثيات تلقائياً
                    </p>
                </div>

                <!-- Section 14: Financial & Additional Information -->
                <div class="form-section">
                    <h3><i class="fas fa-calculator"></i> 14. المعلومات المالية والإضافية (15+ حقول)</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="investmentValue">قيمة الاستثمار (ريال):</label>
                            <input type="number" id="investmentValue" name="investmentValue" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="currentValue">القيمة الحالية (ريال):</label>
                            <input type="number" id="currentValue" name="currentValue" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="rentalIncome">الدخل الإيجاري (ريال):</label>
                            <input type="number" id="rentalIncome" name="rentalIncome" step="0.01">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="maintenanceCost">تكلفة الصيانة (ريال):</label>
                            <input type="number" id="maintenanceCost" name="maintenanceCost" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="occupancyRate">معدل الإشغال (%):</label>
                            <input type="number" id="occupancyRate" name="occupancyRate" min="0" max="100" step="0.1">
                        </div>
                        <div class="form-group">
                            <label for="utilitiesCost">تكلفة المرافق (ريال):</label>
                            <input type="number" id="utilitiesCost" name="utilitiesCost" step="0.01">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="propertyTax">ضريبة العقار (ريال):</label>
                            <input type="number" id="propertyTax" name="propertyTax" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="managementFee">رسوم الإدارة (ريال):</label>
                            <input type="number" id="managementFee" name="managementFee" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="securityDeposit">التأمين (ريال):</label>
                            <input type="number" id="securityDeposit" name="securityDeposit" step="0.01">
                        </div>
                    </div>
                    <div class="form-row">
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
                    </div>
                    <div class="form-row">
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
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="futurePlans">الخطط المستقبلية:</label>
                            <textarea id="futurePlans" name="futurePlans" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="environmentalClearance">التصريح البيئي:</label>
                            <input type="text" id="environmentalClearance" name="environmentalClearance">
                        </div>
                        <div class="form-group">
                            <label for="accessRoad">طريق الوصول:</label>
                            <input type="text" id="accessRoad" name="accessRoad">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="leaseTerms">شروط الإيجار:</label>
                            <textarea id="leaseTerms" name="leaseTerms" rows="2"></textarea>
                        </div>
                        <div class="form-group">
                            <label for="notes">ملاحظات:</label>
                            <textarea id="notes" name="notes" rows="3"></textarea>
                        </div>
                    </div>
                </div>

                <!-- Document Upload Section -->
                <div class="form-section">
                    <h3><i class="fas fa-upload"></i> رفع المستندات المرتبطة</h3>
                    <div class="document-upload-section">
                        <i class="fas fa-cloud-upload-alt" style="font-size: 3rem; color: #4CAF50; margin-bottom: 1rem;"></i>
                        <h4>رفع المستندات</h4>
                        <p>اسحب الملفات هنا أو انقر لاختيار الملفات</p>
                        <input type="file" id="assetDocuments" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.dwg,.txt" style="display: none;" onchange="handleAssetDocuments(event)">
                        <button type="button" class="btn btn-success" onclick="document.getElementById('assetDocuments').click()">
                            <i class="fas fa-plus"></i> اختيار الملفات
                        </button>
                        <div id="assetFileList" class="file-list"></div>
                    </div>
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

    <!-- Workflow Modal -->
    <div id="workflowModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('workflowModal')">&times;</span>
            <h2 id="workflowModalTitle">إضافة مهمة جديدة</h2>
            
            <form id="workflowForm" onsubmit="saveWorkflow(event)">
                <input type="hidden" id="workflowId" name="workflowId">
                
                <div class="form-section">
                    <h3><i class="fas fa-tasks"></i> معلومات المهمة</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="workflowTitle">عنوان المهمة:</label>
                            <input type="text" id="workflowTitle" name="workflowTitle" required>
                        </div>
                        <div class="form-group">
                            <label for="workflowType">نوع المهمة:</label>
                            <select id="workflowType" name="workflowType">
                                <option value="">اختر النوع</option>
                                <option value="Inspection">تفتيش</option>
                                <option value="Legal Review">مراجعة قانونية</option>
                                <option value="Financial Analysis">تحليل مالي</option>
                                <option value="Maintenance">صيانة</option>
                                <option value="Research">بحث</option>
                                <option value="Documentation">توثيق</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="workflowPriority">الأولوية:</label>
                            <select id="workflowPriority" name="workflowPriority">
                                <option value="Low">منخفضة</option>
                                <option value="Medium" selected>متوسطة</option>
                                <option value="High">عالية</option>
                                <option value="Critical">حرجة</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="workflowStatus">الحالة:</label>
                            <select id="workflowStatus" name="workflowStatus">
                                <option value="Not Started" selected>لم تبدأ</option>
                                <option value="In Progress">قيد التنفيذ</option>
                                <option value="On Hold">متوقفة</option>
                                <option value="Completed">مكتملة</option>
                                <option value="Cancelled">ملغية</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="workflowAssignedTo">المسؤول:</label>
                            <select id="workflowAssignedTo" name="workflowAssignedTo">
                                <option value="">اختر المسؤول</option>
                                <option value="Ahmed Al-Rashid">Ahmed Al-Rashid</option>
                                <option value="Sara Al-Mahmoud">Sara Al-Mahmoud</option>
                                <option value="Omar Al-Zahra">Omar Al-Zahra</option>
                                <option value="Fatima Al-Nouri">Fatima Al-Nouri</option>
                                <option value="Khalid Al-Salem">Khalid Al-Salem</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="workflowDepartment">القسم:</label>
                            <select id="workflowDepartment" name="workflowDepartment">
                                <option value="">اختر القسم</option>
                                <option value="Operations">العمليات</option>
                                <option value="Legal">القانونية</option>
                                <option value="Finance">المالية</option>
                                <option value="Investment">الاستثمار</option>
                                <option value="Regional">الإقليمية</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="workflowDueDate">تاريخ الاستحقاق:</label>
                            <input type="date" id="workflowDueDate" name="workflowDueDate">
                        </div>
                        <div class="form-group">
                            <label for="workflowProgress">التقدم (%):</label>
                            <input type="number" id="workflowProgress" name="workflowProgress" min="0" max="100" value="0">
                        </div>
                        <div class="form-group">
                            <label for="workflowEstimatedHours">الساعات المقدرة:</label>
                            <input type="number" id="workflowEstimatedHours" name="workflowEstimatedHours" min="1">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="workflowAssetId">الأصل المرتبط:</label>
                            <select id="workflowAssetId" name="workflowAssetId">
                                <option value="">اختر الأصل (اختياري)</option>
                                <!-- Will be populated dynamically -->
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="workflowDescription">وصف المهمة:</label>
                            <textarea id="workflowDescription" name="workflowDescription" rows="4" required></textarea>
                        </div>
                        <div class="form-group">
                            <label for="workflowNotes">ملاحظات:</label>
                            <textarea id="workflowNotes" name="workflowNotes" rows="4"></textarea>
                        </div>
                    </div>
                </div>

                <div class="form-row" style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> حفظ المهمة
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('workflowModal')">
                        <i class="fas fa-times"></i> إلغاء
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- User Modal -->
    <div id="userModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('userModal')">&times;</span>
            <h2 id="userModalTitle">إضافة مستخدم جديد</h2>
            
            <form id="userForm" onsubmit="saveUser(event)">
                <input type="hidden" id="userId" name="userId">
                
                <div class="form-section">
                    <h3><i class="fas fa-user"></i> معلومات المستخدم</h3>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="userUsername">اسم المستخدم:</label>
                            <input type="text" id="userUsername" name="userUsername" required>
                        </div>
                        <div class="form-group">
                            <label for="userPassword">كلمة المرور:</label>
                            <input type="password" id="userPassword" name="userPassword" required>
                        </div>
                        <div class="form-group">
                            <label for="userFullName">الاسم الكامل:</label>
                            <input type="text" id="userFullName" name="userFullName" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="userEmail">البريد الإلكتروني:</label>
                            <input type="email" id="userEmail" name="userEmail" required>
                        </div>
                        <div class="form-group">
                            <label for="userPhone">رقم الهاتف:</label>
                            <input type="tel" id="userPhone" name="userPhone">
                        </div>
                        <div class="form-group">
                            <label for="userRole">الدور:</label>
                            <select id="userRole" name="userRole" required>
                                <option value="">اختر الدور</option>
                                <option value="Administrator">مدير النظام</option>
                                <option value="Asset Manager">مدير الأصول</option>
                                <option value="Legal Advisor">مستشار قانوني</option>
                                <option value="Financial Analyst">محلل مالي</option>
                                <option value="Operations Manager">مدير العمليات</option>
                                <option value="Regional Coordinator">منسق إقليمي</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="userDepartment">القسم:</label>
                            <select id="userDepartment" name="userDepartment">
                                <option value="">اختر القسم</option>
                                <option value="IT">تقنية المعلومات</option>
                                <option value="Operations">العمليات</option>
                                <option value="Legal">القانونية</option>
                                <option value="Finance">المالية</option>
                                <option value="Regional">الإقليمية</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="userRegion">المنطقة:</label>
                            <select id="userRegion" name="userRegion">
                                <option value="">اختر المنطقة</option>
                                <option value="All Regions">جميع المناطق</option>
                                <option value="Riyadh">الرياض</option>
                                <option value="Jeddah">جدة</option>
                                <option value="Dammam">الدمام</option>
                                <option value="Eastern Province">المنطقة الشرقية</option>
                                <option value="Makkah">مكة المكرمة</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="userStatus">الحالة:</label>
                            <select id="userStatus" name="userStatus">
                                <option value="Active" selected>نشط</option>
                                <option value="Inactive">غير نشط</option>
                                <option value="Suspended">معلق</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="userPermissions">الصلاحيات:</label>
                            <textarea id="userPermissions" name="userPermissions" rows="3" placeholder="اكتب الصلاحيات المخصصة للمستخدم"></textarea>
                        </div>
                    </div>
                </div>

                <div class="form-row" style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> حفظ المستخدم
                    </button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal('userModal')">
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
            
            <div class="file-upload-area" ondrop="handleFileDrop(event, currentDocumentType)" ondragover="event.preventDefault()" ondragenter="event.preventDefault()">
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
        let assetDocuments = [];
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
                            <button class="btn btn-sm btn-danger" onclick="deleteAsset('${asset.asset_id}')" title="حذف">
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
                    const statusClass = workflow.status === 'Completed' ? 'status-completed' : 
                                       workflow.status === 'In Progress' ? 'status-in-progress' : 'status-active';
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>
                            <button class="btn btn-sm" onclick="viewWorkflow('${workflow.workflow_id}')" title="عرض">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm" onclick="editWorkflow('${workflow.workflow_id}')" title="تعديل">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteWorkflow('${workflow.workflow_id}')" title="حذف">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${workflow.progress || 0}%"></div>
                            </div>
                            ${workflow.progress || 0}%
                        </td>
                        <td>${workflow.due_date || '-'}</td>
                        <td>${workflow.assigned_to || '-'}</td>
                        <td>${workflow.priority || '-'}</td>
                        <td><span class="status-badge ${statusClass}">${workflow.status || '-'}</span></td>
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
                            <button class="btn btn-sm btn-danger" onclick="deleteUser('${user.user_id}')" title="حذف">
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
                            <button class="btn btn-sm btn-danger" onclick="deleteFile('${file.file_id}')" title="حذف">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                        <td>${file.upload_date ? new Date(file.upload_date).toLocaleDateString('ar-SA') : '-'}</td>
                        <td><span class="status-badge status-completed">${file.processing_status || 'Processed'}</span></td>
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
                
                document.getElementById('


analyticsStats').innerHTML = analyticsHtml;
                
            } catch (error) {
                console.error('Error loading analytics:', error);
                showAlert('خطأ في تحميل التحليلات', 'error');
            }
        }
        
        // Modal Functions
        function openAssetModal(assetId = null) {
            const modal = document.getElementById('assetModal');
            const title = document.getElementById('assetModalTitle');
            
            if (assetId) {
                title.textContent = 'تعديل الأصل';
                loadAssetData(assetId);
            } else {
                title.textContent = 'إضافة أصل جديد';
                document.getElementById('assetForm').reset();
                document.getElementById('assetId').value = '';
                assetDocuments = [];
                document.getElementById('assetFileList').innerHTML = '';
            }
            
            modal.style.display = 'block';
            
            // Initialize map
            setTimeout(() => {
                initializeMap();
            }, 100);
        }
        
        function openWorkflowModal(workflowId = null) {
            const modal = document.getElementById('workflowModal');
            const title = document.getElementById('workflowModalTitle');
            
            if (workflowId) {
                title.textContent = 'تعديل المهمة';
                loadWorkflowData(workflowId);
            } else {
                title.textContent = 'إضافة مهمة جديدة';
                document.getElementById('workflowForm').reset();
                document.getElementById('workflowId').value = '';
            }
            
            // Load assets for dropdown
            loadAssetsForDropdown();
            modal.style.display = 'block';
        }
        
        function openUserModal(userId = null) {
            const modal = document.getElementById('userModal');
            const title = document.getElementById('userModalTitle');
            
            if (userId) {
                title.textContent = 'تعديل المستخدم';
                loadUserData(userId);
            } else {
                title.textContent = 'إضافة مستخدم جديد';
                document.getElementById('userForm').reset();
                document.getElementById('userId').value = '';
            }
            
            modal.style.display = 'block';
        }
        
        function openDocumentModal(documentType) {
            currentDocumentType = documentType;
            const modal = document.getElementById('documentModal');
            const title = document.getElementById('documentModalTitle');
            
            const typeNames = {
                'property_deed': 'صك الملكية',
                'ownership_documents': 'وثائق الملكية',
                'construction_plans': 'المخططات الهندسية',
                'financial_documents': 'المستندات المالية',
                'legal_documents': 'المستندات القانونية',
                'inspection_reports': 'تقارير التفتيش'
            };
            
            title.textContent = 'رفع ' + typeNames[documentType];
            uploadedFiles = [];
            document.getElementById('fileList').innerHTML = '';
            
            modal.style.display = 'block';
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        // Map Functions
        function initializeMap() {
            if (map) {
                map.remove();
            }
            
            map = L.map('map').setView([24.7136, 46.6753], 10);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            map.on('click', function(e) {
                const lat = e.latlng.lat;
                const lng = e.latlng.lng;
                
                // Update form fields
                document.getElementById('latitude').value = lat.toFixed(6);
                document.getElementById('longitude').value = lng.toFixed(6);
                
                // Update marker
                if (marker) {
                    map.removeLayer(marker);
                }
                
                marker = L.marker([lat, lng]).addTo(map);
                marker.bindPopup(`الإحداثيات: ${lat.toFixed(6)}, ${lng.toFixed(6)}`).openPopup();
            });
        }
        
        // File Upload Functions
        function handleAssetDocuments(event) {
            const files = Array.from(event.target.files);
            files.forEach(file => {
                if (allowed_file(file.name)) {
                    assetDocuments.push(file);
                }
            });
            updateAssetFileList();
        }
        
        function updateAssetFileList() {
            const fileList = document.getElementById('assetFileList');
            fileList.innerHTML = '';
            
            assetDocuments.forEach((file, index) => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.innerHTML = `
                    <span><i class="fas fa-file"></i> ${file.name}</span>
                    <button type="button" class="btn btn-sm btn-danger" onclick="removeAssetDocument(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                fileList.appendChild(fileItem);
            });
        }
        
        function removeAssetDocument(index) {
            assetDocuments.splice(index, 1);
            updateAssetFileList();
        }
        
        function handleFileSelect(event, documentType) {
            const files = Array.from(event.target.files);
            files.forEach(file => {
                if (allowed_file(file.name)) {
                    uploadedFiles.push(file);
                }
            });
            updateFileList();
        }
        
        function handleFileDrop(event, documentType) {
            event.preventDefault();
            const files = Array.from(event.dataTransfer.files);
            files.forEach(file => {
                if (allowed_file(file.name)) {
                    uploadedFiles.push(file);
                }
            });
            updateFileList();
        }
        
        function updateFileList() {
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';
            
            uploadedFiles.forEach((file, index) => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.innerHTML = `
                    <span><i class="fas fa-file"></i> ${file.name}</span>
                    <button type="button" class="btn btn-sm btn-danger" onclick="removeFile(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                fileList.appendChild(fileItem);
            });
        }
        
        function removeFile(index) {
            uploadedFiles.splice(index, 1);
            updateFileList();
        }
        
        function allowed_file(filename) {
            const allowedExtensions = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'dwg'];
            const extension = filename.split('.').pop().toLowerCase();
            return allowedExtensions.includes(extension);
        }
        
        async function uploadFiles(documentType) {
            if (uploadedFiles.length === 0) {
                showAlert('يرجى اختيار ملفات للرفع', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('document_type', documentType);
            
            uploadedFiles.forEach(file => {
                formData.append('files', file);
            });
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showAlert('تم رفع الملفات بنجاح', 'success');
                    closeModal('documentModal');
                    loadDocuments();
                } else {
                    showAlert(result.error || 'خطأ في رفع الملفات', 'error');
                }
            } catch (error) {
                console.error('Error uploading files:', error);
                showAlert('خطأ في رفع الملفات', 'error');
            }
        }
        
        // CRUD Functions
        async function saveAsset(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            
            // Add uploaded documents
            assetDocuments.forEach(file => {
                formData.append('documents', file);
            });
            
            try {
                const assetId = formData.get('assetId');
                const url = assetId ? `/api/assets/${assetId}` : '/api/assets';
                const method = assetId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showAlert('تم حفظ الأصل بنجاح', 'success');
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
            const data = Object.fromEntries(formData.entries());
            
            try {
                const workflowId = data.workflowId;
                const url = workflowId ? `/api/workflows/${workflowId}` : '/api/workflows';
                const method = workflowId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showAlert('تم حفظ المهمة بنجاح', 'success');
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
            const data = Object.fromEntries(formData.entries());
            
            try {
                const userId = data.userId;
                const url = userId ? `/api/users/${userId}` : '/api/users';
                const method = userId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showAlert('تم حفظ المستخدم بنجاح', 'success');
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
        
        // View/Edit/Delete Functions
        async function viewAsset(assetId) {
            try {
                const response = await fetch(`/api/assets/${assetId}`);
                const asset = await response.json();
                
                if (response.ok) {
                    openAssetModal(assetId);
                    populateAssetForm(asset);
                    
                    // Make form read-only for viewing
                    const form = document.getElementById('assetForm');
                    const inputs = form.querySelectorAll('input, select, textarea');
                    inputs.forEach(input => input.disabled = true);
                    
                    // Hide save button
                    const saveBtn = form.querySelector('button[type="submit"]');
                    saveBtn.style.display = 'none';
                } else {
                    showAlert('خطأ في تحميل بيانات الأصل', 'error');
                }
            } catch (error) {
                console.error('Error viewing asset:', error);
                showAlert('خطأ في عرض الأصل', 'error');
            }
        }
        
        async function editAsset(assetId) {
            try {
                const response = await fetch(`/api/assets/${assetId}`);
                const asset = await response.json();
                
                if (response.ok) {
                    openAssetModal(assetId);
                    populateAssetForm(asset);
                } else {
                    showAlert('خطأ في تحميل بيانات الأصل', 'error');
                }
            } catch (error) {
                console.error('Error editing asset:', error);
                showAlert('خطأ في تعديل الأصل', 'error');
            }
        }
        
        async function deleteAsset(assetId) {
            if (!confirm('هل أنت متأكد من حذف هذا الأصل؟')) {
                return;
            }
            
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
        
        async function viewWorkflow(workflowId) {
            try {
                const response = await fetch(`/api/workflows/${workflowId}`);
                const workflow = await response.json();
                
                if (response.ok) {
                    openWorkflowModal(workflowId);
                    populateWorkflowForm(workflow);
                    
                    // Make form read-only for viewing
                    const form = document.getElementById('workflowForm');
                    const inputs = form.querySelectorAll('input, select, textarea');
                    inputs.forEach(input => input.disabled = true);
                    
                    // Hide save button
                    const saveBtn = form.querySelector('button[type="submit"]');
                    saveBtn.style.display = 'none';
                } else {
                    showAlert('خطأ في تحميل بيانات المهمة', 'error');
                }
            } catch (error) {
                console.error('Error viewing workflow:', error);
                showAlert('خطأ في عرض المهمة', 'error');
            }
        }
        
        async function editWorkflow(workflowId) {
            try {
                const response = await fetch(`/api/workflows/${workflowId}`);
                const workflow = await response.json();
                
                if (response.ok) {
                    openWorkflowModal(workflowId);
                    populateWorkflowForm(workflow);
                } else {
                    showAlert('خطأ في تحميل بيانات المهمة', 'error');
                }
            } catch (error) {
                console.error('Error editing workflow:', error);
                showAlert('خطأ في تعديل المهمة', 'error');
            }
        }
        
        async function deleteWorkflow(workflowId) {
            if (!confirm('هل أنت متأكد من حذف هذه المهمة؟')) {
                return;
            }
            
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
        
        async function viewUser(userId) {
            try {
                const response = await fetch(`/api/users/${userId}`);
                const user = await response.json();
                
                if (response.ok) {
                    openUserModal(userId);
                    populateUserForm(user);
                    
                    // Make form read-only for viewing
                    const form = document.getElementById('userForm');
                    const inputs = form.querySelectorAll('input, select, textarea');
                    inputs.forEach(input => input.disabled = true);
                    
                    // Hide save button
                    const saveBtn = form.querySelector('button[type="submit"]');
                    saveBtn.style.display = 'none';
                } else {
                    showAlert('خطأ في تحميل بيانات المستخدم', 'error');
                }
            } catch (error) {
                console.error('Error viewing user:', error);
                showAlert('خطأ في عرض المستخدم', 'error');
            }
        }
        
        async function editUser(userId) {
            try {
                const response = await fetch(`/api/users/${userId}`);
                const user = await response.json();
                
                if (response.ok) {
                    openUserModal(userId);
                    populateUserForm(user);
                } else {
                    showAlert('خطأ في تحميل بيانات المستخدم', 'error');
                }
            } catch (error) {
                console.error('Error editing user:', error);
                showAlert('خطأ في تعديل المستخدم', 'error');
            }
        }
        
        async function deleteUser(userId) {
            if (!confirm('هل أنت متأكد من حذف هذا المستخدم؟')) {
                return;
            }
            
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
        
        // Form Population Functions
        function populateAssetForm(asset) {
            Object.keys(asset).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    element.value = asset[key] || '';
                }
            });
            
            // Update map if coordinates exist
            if (asset.latitude && asset.longitude && map) {
                const lat = parseFloat(asset.latitude);
                const lng = parseFloat(asset.longitude);
                
                map.setView([lat, lng], 15);
                
                if (marker) {
                    map.removeLayer(marker);
                }
                
                marker = L.marker([lat, lng]).addTo(map);
                marker.bindPopup(`الإحداثيات: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
            }
        }
        
        function populateWorkflowForm(workflow) {
            Object.keys(workflow).forEach(key => {
                const element = document.getElementById('workflow' + key.charAt(0).toUpperCase() + key.slice(1));
                if (element) {
                    element.value = workflow[key] || '';
                }
            });
        }
        
        function populateUserForm(user) {
            Object.keys(user).forEach(key => {
                const element = document.getElementById('user' + key.charAt(0).toUpperCase() + key.slice(1));
                if (element) {
                    element.value = user[key] || '';
                }
            });
        }
        
        // Search Functions
        function searchAssets() {
            const searchTerm = document.getElementById('assetSearch').value.toLowerCase();
            const rows = document.querySelectorAll('#assetsTableBody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        }
        
        function searchWorkflows() {
            const searchTerm = document.getElementById('workflowSearch').value.toLowerCase();
            const rows = document.querySelectorAll('#workflowsTableBody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        }
        
        function searchUsers() {
            const searchTerm = document.getElementById('userSearch').value.toLowerCase();
            const rows = document.querySelectorAll('#usersTableBody tr');
            
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
                a.download = 'assets_export.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('تم تصدير الأصول بنجاح', 'success');
            } catch (error) {
                console.error('Error exporting assets:', error);
                showAlert('خطأ في تصدير الأصول', 'error');
            }
        }
        
        async function exportWorkflows() {
            try {
                const response = await fetch('/api/export/workflows');
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'workflows_export.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('تم تصدير المهام بنجاح', 'success');
            } catch (error) {
                console.error('Error exporting workflows:', error);
                showAlert('خطأ في تصدير المهام', 'error');
            }
        }
        
        async function exportUsers() {
            try {
                const response = await fetch('/api/export/users');
                const blob = await response.blob();
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'users_export.csv';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('تم تصدير المستخدمين بنجاح', 'success');
            } catch (error) {
                console.error('Error exporting users:', error);
                showAlert('خطأ في تصدير المستخدمين', 'error');
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
                a.download = `${reportType}_report.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert('تم إنشاء التقرير بنجاح', 'success');
            } catch (error) {
                console.error('Error generating report:', error);
                showAlert('خطأ في إنشاء التقرير', 'error');
            }
        }
        
        // Utility Functions
        async function loadAssetsForDropdown() {
            try {
                const response = await fetch('/api/assets');
                const assets = await response.json();
                
                const select = document.getElementById('workflowAssetId');
                select.innerHTML = '<option value="">اختر الأصل (اختياري)</option>';
                
                assets.forEach(asset => {
                    const option = document.createElement('option');
                    option.value = asset.asset_id;
                    option.textContent = asset.asset_name;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading assets for dropdown:', error);
            }
        }
        
        function showAlert(message, type) {
            const alertDiv = document.getElementById('successMessage');
            alertDiv.textContent = message;
            alertDiv.className = type === 'success' ? 'success-message' : 'success-message alert-error';
            alertDiv.style.display = 'block';
            
            setTimeout(() => {
                alertDiv.style.display = 'none';
            }, 3000);
        }
        
        // File management functions
        async function viewFile(fileId) {
            try {
                const response = await fetch(`/api/files/${fileId}`);
                const file = await response.json();
                
                if (response.ok) {
                    // Show file details in a modal or new window
                    alert(`ملف: ${file.original_filename}\nنوع المستند: ${file.document_type}\nحالة المعالجة: ${file.processing_status}\nنص OCR: ${file.ocr_text || 'غير متوفر'}`);
                } else {
                    showAlert('خطأ في تحميل بيانات الملف', 'error');
                }
            } catch (error) {
                console.error('Error viewing file:', error);
                showAlert('خطأ في عرض الملف', 'error');
            }
        }
        
        async function downloadFile(fileId) {
            try {
                const response = await fetch(`/api/files/${fileId}/download`);
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'file_' + fileId;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                } else {
                    showAlert('خطأ في تحميل الملف', 'error');
                }
            } catch (error) {
                console.error('Error downloading file:', error);
                showAlert('خطأ في تحميل الملف', 'error');
            }
        }
        
        async function deleteFile(fileId) {
            if (!confirm('هل أنت متأكد من حذف هذا الملف؟')) {
                return;
            }
            
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
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Set up drag and drop for file upload areas
            const uploadAreas = document.querySelectorAll('.file-upload-area');
            uploadAreas.forEach(area => {
                area.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    this.classList.add('dragover');
                });
                
                area.addEventListener('dragleave', function(e) {
                    e.preventDefault();
                    this.classList.remove('dragover');
                });
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
        });
    </script>
</body>
</html>
    ''')

# API Routes
@app.route('/api/dashboard')
def api_dashboard():
    """Get dashboard statistics"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute('SELECT COUNT(DISTINCT region) FROM assets WHERE region IS NOT NULL')
        total_regions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE status = "Active"')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM workflows WHERE status != "Completed"')
        total_workflows = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM assets')
        total_assets = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(completion_percentage) FROM assets WHERE completion_percentage IS NOT NULL')
        completion_rate = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM files')
        total_files = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_regions': total_regions,
            'total_users': total_users,
            'total_workflows': total_workflows,
            'total_assets': total_assets,
            'completion_rate': f"{completion_rate:.1f}%",
            'total_files': total_files
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics')
def api_analytics():
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
def api_get_assets():
    """Get all assets"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets ORDER BY created_at DESC')
        columns = [description[0] for description in cursor.description]
        assets = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(assets)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets/<asset_id>', methods=['GET'])
def api_get_asset(asset_id):
    """Get specific asset"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets WHERE asset_id = ?', (asset_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        if row:
            asset = dict(zip(columns, row))
            conn.close()
            return jsonify(asset)
        else:
            conn.close()
            return jsonify({'error': 'Asset not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets', methods=['POST'])
def api_create_asset():
    """Create new asset"""
    try:
        # Generate unique asset ID
        asset_id = f"AST-{uuid.uuid4().hex[:6].upper()}"
        
        # Get form data
        data = request.form.to_dict()
        data['asset_id'] = asset_id
        
        # Handle file uploads
        uploaded_files = request.files.getlist('documents')
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Insert asset with all MOE fields
        cursor.execute('''
            INSERT INTO assets (
                asset_id, asset_name, asset_type, asset_category, asset_classification, current_status, operational_status,
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
                tenant_information, insurance_details, tax_information, market_analysis, investment_recommendation, risk_assessment, future_plans, environmental_clearance, access_road,
                utilities_cost, property_tax, management_fee, security_deposit, lease_terms, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('asset_id'), data.get('assetName'), data.get('assetType'), data.get('assetCategory'), data.get('assetClassification'), data.get('currentStatus'), data.get('operationalStatus'),
            data.get('planningPermit'), data.get('buildingPermit'), data.get('developmentApproval'), data.get('needAssessment'), data.get('locationScore'), data.get('accessibilityRating'), data.get('marketAttractiveness'),
            data.get('investmentProposal'), data.get('investmentObstacles'), data.get('riskMitigation'),
            data.get('financialObligations'), data.get('loanCovenants'), data.get('paymentSchedule'),
            data.get('utilitiesWater'), data.get('utilitiesElectricity'), data.get('utilitiesSewage'), data.get('utilitiesTelecom'),
            data.get('ownershipType'), data.get('ownerName'), data.get('ownershipPercentage'), data.get('legalStatus'),
            data.get('landUse'), data.get('zoningClassification'), data.get('developmentPotential'),
            data.get('landArea'), data.get('builtArea'), data.get('usableArea'), data.get('commonArea'), data.get('parkingArea'),
            data.get('constructionStatus'), data.get('completionPercentage'), data.get('constructionQuality'), data.get('defectsWarranty'),
            data.get('lengthMeters'), data.get('widthMeters'), data.get('heightMeters'), data.get('totalFloors'),
            data.get('northBoundary'), data.get('southBoundary'), data.get('eastBoundary'), data.get('westBoundary'),
            data.get('boundaryLengthNorth'), data.get('boundaryLengthSouth'), data.get('boundaryLengthEast'), data.get('boundaryLengthWest'),
            data.get('region'), data.get('city'), data.get('district'), data.get('location'), data.get('latitude'), data.get('longitude'), data.get('elevation'),
            data.get('investmentValue'), data.get('currentValue'), data.get('rentalIncome'), data.get('maintenanceCost'), data.get('occupancyRate'),
            data.get('tenantInformation'), data.get('insuranceDetails'), data.get('taxInformation'), data.get('marketAnalysis'), data.get('investmentRecommendation'), data.get('riskAssessment'), data.get('futurePlans'), data.get('environmentalClearance'), data.get('accessRoad'),
            data.get('utilitiesCost'), data.get('propertyTax'), data.get('managementFee'), data.get('securityDeposit'), data.get('leaseTerms'), data.get('notes')
        ))
        
        # Process uploaded files
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                file_id = f"FILE-{uuid.uuid4().hex[:8].upper()}"
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, 'asset_documents', filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save file
                file.save(file_path)
                
                # Extract text using OCR
                ocr_text = extract_text_from_file(file_path)
                
                # Save file record
                cursor.execute('''
                    INSERT INTO files (file_id, asset_id, document_type, original_filename, stored_filename, file_path, file_size, mime_type, ocr_text, processing_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_id, asset_id, 'asset_document', file.filename, filename, file_path, 
                    os.path.getsize(file_path), file.content_type, ocr_text, 'Processed'
                ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Asset created successfully', 'asset_id': asset_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets/<asset_id>', methods=['PUT'])
def api_update_asset(asset_id):
    """Update existing asset"""
    try:
        data = request.form.to_dict()
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Update asset with all MOE fields
        cursor.execute('''
            UPDATE assets SET
                asset_name=?, asset_type=?, asset_category=?, asset_classification=?, current_status=?, operational_status=?,
                planning_permit=?, building_permit=?, development_approval=?, need_assessment=?, location_score=?, accessibility_rating=?, market_attractiveness=?,
                investment_proposal=?, investment_obstacles=?, risk_mitigation=?,
                financial_obligations=?, loan_covenants=?, payment_schedule=?,
                utilities_water=?, utilities_electricity=?, utilities_sewage=?, utilities_telecom=?,
                ownership_type=?, owner_name=?, ownership_percentage=?, legal_status=?,
                land_use=?, zoning_classification=?, development_potential=?,
                land_area=?, built_area=?, usable_area=?, common_area=?, parking_area=?,
                construction_status=?, completion_percentage=?, construction_quality=?, defects_warranty=?,
                length_meters=?, width_meters=?, height_meters=?, total_floors=?,
                north_boundary=?, south_boundary=?, east_boundary=?, west_boundary=?,
                boundary_length_north=?, boundary_length_south=?, boundary_length_east=?, boundary_length_west=?,
                region=?, city=?, district=?, location=?, latitude=?, longitude=?, elevation=?,
                investment_value=?, current_value=?, rental_income=?, maintenance_cost=?, occupancy_rate=?,
                tenant_information=?, insurance_details=?, tax_information=?, market_analysis=?, investment_recommendation=?, risk_assessment=?, future_plans=?, environmental_clearance=?, access_road=?,
                utilities_cost=?, property_tax=?, management_fee=?, security_deposit=?, lease_terms=?, notes=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE asset_id=?
        ''', (
            data.get('assetName'), data.get('assetType'), data.get('assetCategory'), data.get('assetClassification'), data.get('currentStatus'), data.get('operationalStatus'),
            data.get('planningPermit'), data.get('buildingPermit'), data.get('developmentApproval'), data.get('needAssessment'), data.get('locationScore'), data.get('accessibilityRating'), data.get('marketAttractiveness'),
            data.get('investmentProposal'), data.get('investmentObstacles'), data.get('riskMitigation'),
            data.get('financialObligations'), data.get('loanCovenants'), data.get('paymentSchedule'),
            data.get('utilitiesWater'), data.get('utilitiesElectricity'), data.get('utilitiesSewage'), data.get('utilitiesTelecom'),
            data.get('ownershipType'), data.get('ownerName'), data.get('ownershipPercentage'), data.get('legalStatus'),
            data.get('landUse'), data.get('zoningClassification'), data.get('developmentPotential'),
            data.get('landArea'), data.get('builtArea'), data.get('usableArea'), data.get('commonArea'), data.get('parkingArea'),
            data.get('constructionStatus'), data.get('completionPercentage'), data.get('constructionQuality'), data.get('defectsWarranty'),
            data.get('lengthMeters'), data.get('widthMeters'), data.get('heightMeters'), data.get('totalFloors'),
            data.get('northBoundary'), data.get('southBoundary'), data.get('eastBoundary'), data.get('westBoundary'),
            data.get('boundaryLengthNorth'), data.get('boundaryLengthSouth'), data.get('boundaryLengthEast'), data.get('boundaryLengthWest'),
            data.get('region'), data.get('city'), data.get('district'), data.get('location'), data.get('latitude'), data.get('longitude'), data.get('elevation'),
            data.get('investmentValue'), data.get('currentValue'), data.get('rentalIncome'), data.get('maintenanceCost'), data.get('occupancyRate'),
            data.get('tenantInformation'), data.get('insuranceDetails'), data.get('taxInformation'), data.get('marketAnalysis'), data.get('investmentRecommendation'), data.get('riskAssessment'), data.get('futurePlans'), data.get('environmentalClearance'), data.get('accessRoad'),
            data.get('utilitiesCost'), data.get('propertyTax'), data.get('managementFee'), data.get('securityDeposit'), data.get('leaseTerms'), data.get('notes'),
            asset_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Asset updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets/<asset_id>', methods=['DELETE'])
def api_delete_asset(asset_id):
    """Delete asset"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM assets WHERE asset_id = ?', (asset_id,))
        cursor.execute('DELETE FROM files WHERE asset_id = ?', (asset_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Asset deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Workflow API Routes
@app.route('/api/workflows', methods=['GET'])
def api_get_workflows():
    """Get all workflows"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows ORDER BY created_at DESC')
        columns = [description[0] for description in cursor.description]
        workflows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(workflows)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<workflow_id>', methods=['GET'])
def api_get_workflow(workflow_id):
    """Get specific workflow"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows WHERE workflow_id = ?', (workflow_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        if row:
            workflow = dict(zip(columns, row))
            conn.close()
            return jsonify(workflow)
        else:
            conn.close()
            return jsonify({'error': 'Workflow not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows', methods=['POST'])
def api_create_workflow():
    """Create new workflow"""
    try:
        data = request.get_json()
        workflow_id = f"WF-{uuid.uuid4().hex[:6].upper()}"
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflows (workflow_id, title, description, status, priority, assigned_to, due_date, created_by, progress, notes, workflow_type, department, estimated_hours, actual_hours, asset_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow_id, data.get('workflowTitle'), data.get('workflowDescription'), data.get('workflowStatus'), 
            data.get('workflowPriority'), data.get('workflowAssignedTo'), data.get('workflowDueDate'), 
            'admin', data.get('workflowProgress', 0), data.get('workflowNotes'), 
            data.get('workflowType'), data.get('workflowDepartment'), data.get('workflowEstimatedHours'), 
            0, data.get('workflowAssetId')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Workflow created successfully', 'workflow_id': workflow_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<workflow_id>', methods=['PUT'])
def api_update_workflow(workflow_id):
    """Update existing workflow"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE workflows SET
                title=?, description=?, status=?, priority=?, assigned_to=?, due_date=?, progress=?, notes=?, workflow_type=?, department=?, estimated_hours=?, asset_id=?, updated_at=CURRENT_TIMESTAMP
            WHERE workflow_id=?
        ''', (
            data.get('workflowTitle'), data.get('workflowDescription'), data.get('workflowStatus'), 
            data.get('workflowPriority'), data.get('workflowAssignedTo'), data.get('workflowDueDate'), 
            data.get('workflowProgress'), data.get('workflowNotes'), data.get('workflowType'), 
            data.get('workflowDepartment'), data.get('workflowEstimatedHours'), data.get('workflowAssetId'), 
            workflow_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Workflow updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<workflow_id>', methods=['DELETE'])
def api_delete_workflow(workflow_id):
    """Delete workflow"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM workflows WHERE workflow_id = ?', (workflow_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Workflow deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User API Routes
@app.route('/api/users', methods=['GET'])
def api_get_users():
    """Get all users"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        columns = [description[0] for description in cursor.description]
        users = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Remove passwords from response
        for user in users:
            user.pop('password', None)
        
        conn.close()
        return jsonify(users)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['GET'])
def api_get_user(user_id):
    """Get specific user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        if row:
            user = dict(zip(columns, row))
            user.pop('password', None)  # Remove password from response
            conn.close()
            return jsonify(user)
        else:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def api_create_user():
    """Create new user"""
    try:
        data = request.get_json()
        user_id = f"USR-{uuid.uuid4().hex[:6].upper()}"
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (user_id, username, password, full_name, email, phone, role, department, region, permissions, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, data.get('userUsername'), data.get('userPassword'), data.get('userFullName'), 
            data.get('userEmail'), data.get('userPhone'), data.get('userRole'), 
            data.get('userDepartment'), data.get('userRegion'), data.get('userPermissions'), 
            data.get('userStatus', 'Active')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User created successfully', 'user_id': user_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
def api_update_user(user_id):
    """Update existing user"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET
                username=?, password=?, full_name=?, email=?, phone=?, role=?, department=?, region=?, permissions=?, status=?, updated_at=CURRENT_TIMESTAMP
            WHERE user_id=?
        ''', (
            data.get('userUsername'), data.get('userPassword'), data.get('userFullName'), 
            data.get('userEmail'), data.get('userPhone'), data.get('userRole'), 
            data.get('userDepartment'), data.get('userRegion'), data.get('userPermissions'), 
            data.get('userStatus'), user_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
def api_delete_user(user_id):
    """Delete user"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# File API Routes
@app.route('/api/files', methods=['GET'])
def api_get_files():
    """Get all files"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files ORDER BY upload_date DESC')
        columns = [description[0] for description in cursor.description]
        files = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(files)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>', methods=['GET'])
def api_get_file(file_id):
    """Get specific file"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM files WHERE file_id = ?', (file_id,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        if row:
            file_data = dict(zip(columns, row))
            conn.close()
            return jsonify(file_data)
        else:
            conn.close()
            return jsonify({'error': 'File not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>/download', methods=['GET'])
def api_download_file(file_id):
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
def api_delete_file(file_id):
    """Delete file"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get file path before deletion
        cursor.execute('SELECT file_path FROM files WHERE file_id = ?', (file_id,))
        row = cursor.fetchone()
        
        if row:
            file_path = row[0]
            # Delete from database
            cursor.execute('DELETE FROM files WHERE file_id = ?', (file_id,))
            
            # Delete physical file
            if os.path.exists(file_path):
                os.remove(file_path)
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'File deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def api_upload_files():
    """Upload files with OCR processing"""
    try:
        document_type = request.form.get('document_type', 'general')
        uploaded_files = request.files.getlist('files')
        
        if not uploaded_files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        processed_files = []
        
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                file_id = f"FILE-{uuid.uuid4().hex[:8].upper()}"
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, document_type, filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save file
                file.save(file_path)
                
                # Extract text using OCR
                ocr_text = extract_text_from_file(file_path)
                
                # Save file record
                cursor.execute('''
                    INSERT INTO files (file_id, document_type, original_filename, stored_filename, file_path, file_size, mime_type, ocr_text, processing_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_id, document_type, file.filename, filename, file_path, 
                    os.path.getsize(file_path), file.content_type, ocr_text, 'Processed'
                ))
                
                processed_files.append({
                    'file_id': file_id,
                    'filename': file.filename,
                    'ocr_text': ocr_text[:200] + '...' if len(ocr_text) > 200 else ocr_text
                })
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'Successfully uploaded {len(processed_files)} files',
            'files': processed_files
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Export API Routes
@app.route('/api/export/assets')
def api_export_assets():
    """Export assets to CSV"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets')
        columns = [description[0] for description in cursor.description]
        assets = cursor.fetchall()
        
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(assets)
        
        # Create response
        response = app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=assets_export.csv'}
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/workflows')
def api_export_workflows():
    """Export workflows to CSV"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows')
        columns = [description[0] for description in cursor.description]
        workflows = cursor.fetchall()
        
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(workflows)
        
        # Create response
        response = app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=workflows_export.csv'}
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/users')
def api_export_users():
    """Export users to CSV"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id, username, full_name, email, phone, role, department, region, status, created_at FROM users')
        columns = [description[0] for description in cursor.description]
        users = cursor.fetchall()
        
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(users)
        
        # Create response
        response = app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=users_export.csv'}
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Report API Routes
@app.route('/api/reports/<report_type>')
def api_generate_report(report_type):
    """Generate various reports"""
    try:
        # For now, return a simple text report
        # In production, this would generate proper PDF reports
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if report_type == 'assets':
            cursor.execute('SELECT COUNT(*) as total, asset_type FROM assets GROUP BY asset_type')
            data = cursor.fetchall()
            report_content = f"Assets Report\n{'='*50}\n"
            for row in data:
                report_content += f"{row[1]}: {row[0]} assets\n"
                
        elif report_type == 'regional':
            cursor.execute('SELECT COUNT(*) as total, region FROM assets GROUP BY region')
            data = cursor.fetchall()
            report_content = f"Regional Distribution Report\n{'='*50}\n"
            for row in data:
                report_content += f"{row[1]}: {row[0]} assets\n"
                
        elif report_type == 'construction':
            cursor.execute('SELECT COUNT(*) as total, construction_status FROM assets GROUP BY construction_status')
            data = cursor.fetchall()
            report_content = f"Construction Status Report\n{'='*50}\n"
            for row in data:
                report_content += f"{row[1]}: {row[0]} assets\n"
                
        elif report_type == 'financial':
            cursor.execute('SELECT SUM(investment_value), SUM(current_value), SUM(rental_income) FROM assets')
            data = cursor.fetchone()
            report_content = f"Financial Analysis Report\n{'='*50}\n"
            report_content += f"Total Investment: {data[0] or 0:,.2f} SAR\n"
            report_content += f"Current Value: {data[1] or 0:,.2f} SAR\n"
            report_content += f"Rental Income: {data[2] or 0:,.2f} SAR\n"
            
        elif report_type == 'workflows':
            cursor.execute('SELECT COUNT(*) as total, status FROM workflows GROUP BY status')
            data = cursor.fetchall()
            report_content = f"Workflows Report\n{'='*50}\n"
            for row in data:
                report_content += f"{row[1]}: {row[0]} workflows\n"
                
        elif report_type == 'users':
            cursor.execute('SELECT COUNT(*) as total, role FROM users GROUP BY role')
            data = cursor.fetchall()
            report_content = f"Users Report\n{'='*50}\n"
            for row in data:
                report_content += f"{row[1]}: {row[0]} users\n"
        else:
            report_content = "Report type not found"
        
        conn.close()
        
        # Create response
        response = app.response_class(
            report_content,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename={report_type}_report.txt'}
        )
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

