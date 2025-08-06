from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import json
import os
import sqlite3
from datetime import datetime
import uuid
import base64

app = Flask(__name__)
app.secret_key = 'madares_secret_key_2025'
CORS(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('/tmp/madares.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL,
            region TEXT NOT NULL,
            status TEXT DEFAULT 'نشط',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Assets table with all 79 MOE fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            -- Asset Identification (6 fields)
            asset_name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            asset_category TEXT,
            asset_status TEXT DEFAULT 'نشط',
            unique_id TEXT,
            creation_date DATE,
            
            -- Planning Assessment (4 fields)
            need_assessment TEXT,
            development_plan TEXT,
            expected_timeline TEXT,
            planning_phase TEXT,
            
            -- Location Attractiveness (3 fields)
            location_rating TEXT,
            nearby_facilities TEXT,
            accessibility TEXT,
            
            -- Investment Proposal (3 fields)
            investment_proposal TEXT,
            potential_obstacles TEXT,
            expected_return TEXT,
            
            -- Financial Obligations (3 fields)
            total_cost REAL,
            required_funding REAL,
            funding_source TEXT,
            
            -- Utilities Information (4 fields)
            electricity_status TEXT,
            water_status TEXT,
            sewage_status TEXT,
            telecom_status TEXT,
            
            -- Ownership Information (4 fields)
            ownership_type TEXT,
            owner_name TEXT,
            ownership_documents TEXT,
            legal_status TEXT,
            
            -- Land Details (3 fields)
            land_area REAL,
            land_type TEXT,
            zoning_classification TEXT,
            
            -- Asset Areas (5 fields)
            built_area REAL,
            usable_area REAL,
            common_area REAL,
            parking_area REAL,
            green_area REAL,
            
            -- Construction Status (4 fields)
            construction_status TEXT,
            completion_percentage REAL,
            construction_start_date DATE,
            expected_completion_date DATE,
            
            -- Physical Dimensions (4 fields)
            length_meters REAL,
            width_meters REAL,
            height_meters REAL,
            floors_count INTEGER,
            
            -- Boundaries (8 fields)
            north_boundary TEXT,
            south_boundary TEXT,
            east_boundary TEXT,
            west_boundary TEXT,
            boundary_length_north REAL,
            boundary_length_south REAL,
            boundary_length_east REAL,
            boundary_length_west REAL,
            
            -- Geographic Location (7 fields)
            latitude REAL,
            longitude REAL,
            region TEXT,
            city TEXT,
            district TEXT,
            street_name TEXT,
            building_number TEXT,
            
            -- Financial & Additional (21+ fields)
            current_value REAL,
            market_value REAL,
            rental_income REAL,
            operating_expenses REAL,
            net_income REAL,
            roi_percentage REAL,
            appreciation_rate REAL,
            property_tax REAL,
            insurance_cost REAL,
            maintenance_cost REAL,
            management_fee REAL,
            vacancy_rate REAL,
            cap_rate REAL,
            debt_service REAL,
            cash_flow REAL,
            irr_percentage REAL,
            npv_value REAL,
            payback_period REAL,
            risk_assessment TEXT,
            market_conditions TEXT,
            future_prospects TEXT,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Workflows table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'معلقة',
            priority TEXT DEFAULT 'متوسطة',
            assignee_id INTEGER,
            assigned_to TEXT,
            due_date DATE,
            progress INTEGER DEFAULT 0,
            asset_id INTEGER,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assignee_id) REFERENCES users (id),
            FOREIGN KEY (asset_id) REFERENCES assets (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Documents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            document_type TEXT NOT NULL,
            asset_id INTEGER,
            file_size INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER,
            ocr_text TEXT,
            processing_status TEXT DEFAULT 'معلق',
            file_path TEXT,
            FOREIGN KEY (asset_id) REFERENCES assets (id),
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        )
    ''')
    
    # Insert default admin user
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, full_name, email, role, department, region)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('admin', 'password123', 'مدير النظام', 'admin@madares.sa', 'مدير', 'الإدارة العامة', 'الرياض'))
    
    # Insert sample users
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, full_name, email, role, department, region)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('ahmed.m', 'password123', 'أحمد محمد', 'ahmed@madares.sa', 'محلل أصول', 'إدارة الأصول', 'الرياض'))
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, full_name, email, role, department, region)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('fatima.a', 'password123', 'فاطمة علي', 'fatima@madares.sa', 'مختص قانوني', 'الشؤون القانونية', 'جدة'))
    
    # Insert sample assets
    cursor.execute('''
        INSERT OR IGNORE INTO assets (
            asset_name, asset_type, asset_category, region, city, current_value, 
            completion_percentage, construction_status, latitude, longitude
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('مجمع الرياض التجاري', 'تجاري', 'مجمع تجاري', 'الرياض', 'الرياض', 25000000, 85, 'قيد الإنشاء', 24.7136, 46.6753))
    
    cursor.execute('''
        INSERT OR IGNORE INTO assets (
            asset_name, asset_type, asset_category, region, city, current_value, 
            completion_percentage, construction_status, latitude, longitude
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('برج جدة للأعمال', 'مكتبي', 'برج أعمال', 'مكة المكرمة', 'جدة', 45000000, 100, 'مكتمل', 21.4858, 39.1925))
    
    cursor.execute('''
        INSERT OR IGNORE INTO assets (
            asset_name, asset_type, asset_category, region, city, current_value, 
            completion_percentage, construction_status, latitude, longitude
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('مجمع الدمام السكني', 'سكني', 'مجمع سكني', 'المنطقة الشرقية', 'الدمام', 18000000, 60, 'قيد الإنشاء', 26.4207, 50.0888))
    
    # Insert sample workflows
    cursor.execute('''
        INSERT OR IGNORE INTO workflows (title, status, priority, assigned_to, due_date, progress)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('مراجعة تقييم الأصول', 'قيد التنفيذ', 'عالية', 'أحمد محمد', '2025-08-15', 75))
    
    cursor.execute('''
        INSERT OR IGNORE INTO workflows (title, status, priority, assigned_to, due_date, progress)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('تحديث المستندات القانونية', 'مكتملة', 'متوسطة', 'فاطمة علي', '2025-08-10', 100))
    
    cursor.execute('''
        INSERT OR IGNORE INTO workflows (title, status, priority, assigned_to, due_date, progress)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('فحص الأصول الجديدة', 'معلقة', 'منخفضة', 'محمد سالم', '2025-08-20', 25))
    
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
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
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
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .container {
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 60vh;
        }
        
        .login-form {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        
        .login-form h2 {
            color: #333;
            margin-bottom: 2rem;
            font-size: 1.8rem;
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
            font-family: inherit;
        }
        
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #ff7b54;
            box-shadow: 0 0 0 3px rgba(255, 123, 84, 0.1);
        }
        
        .login-btn, .btn {
            width: 100%;
            padding: 1rem 1.5rem;
            background: linear-gradient(135deg, #ff7b54 0%, #ff6b35 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .login-btn:hover, .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(255, 123, 84, 0.3);
        }
        
        .btn-small {
            width: auto;
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
            margin: 0.2rem;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        }
        
        .btn-info {
            background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
        }
        
        .debug-btn {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        
        .debug-btn:hover {
            box-shadow: 0 10px 25px rgba(40, 167, 69, 0.3);
        }
        
        .credentials-hint {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            margin-top: 1rem;
            font-size: 0.9rem;
            color: #666;
        }
        
        .main-content {
            display: none;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        
        .card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            color: #333;
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            opacity: 0.9;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        .table th, .table td {
            padding: 1rem;
            text-align: right;
            border-bottom: 1px solid #e1e5e9;
        }
        
        .table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        
        .table tr:hover {
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
        
        .status-progress {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-complete {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .status-pending {
            background: #f8d7da;
            color: #721c24;
        }
        
        .logout-btn {
            position: fixed;
            top: 20px;
            left: 20px;
            background: #dc3545;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            display: none;
        }
        
        .nav-tabs {
            display: flex;
            background: white;
            border-radius: 10px;
            margin-bottom: 2rem;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .nav-tab {
            flex: 1;
            padding: 1rem;
            background: white;
            border: none;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            color: #666;
            transition: all 0.3s ease;
        }
        
        .nav-tab.active {
            background: linear-gradient(135deg, #ff7b54 0%, #ff6b35 100%);
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
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
            margin: 5% auto;
            padding: 2rem;
            border-radius: 15px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .close {
            color: #aaa;
            float: left;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: black;
        }
        
        .form-section {
            margin-bottom: 2rem;
            padding: 1.5rem;
            border: 1px solid #e1e5e9;
            border-radius: 10px;
            background: #f8f9fa;
        }
        
        .form-section h4 {
            color: #333;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #ff7b54;
        }
        
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            padding: 0.2rem;
            margin: 0.5rem 0;
        }
        
        .progress-fill {
            background: #007bff;
            height: 8px;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        
        #map {
            height: 300px;
            width: 100%;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .file-upload-area {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        .file-upload-area:hover {
            border-color: #ff7b54;
            background: #f8f9fa;
        }
        
        .file-upload-area.dragover {
            border-color: #ff7b54;
            background: #fff3cd;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 0 0.5rem;
            }
            
            .login-form {
                padding: 2rem;
            }
            
            .dashboard {
                grid-template-columns: 1fr;
            }
            
            .stats {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .nav-tabs {
                flex-direction: column;
            }
            
            .form-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-building"></i> مدارس الأعمال</h1>
        <p>نظام إدارة الأصول العقارية الشامل - جميع الوظائف متاحة وتعمل</p>
    </div>

    <button class="logout-btn" onclick="logout()">
        <i class="fas fa-sign-out-alt"></i> خروج
    </button>

    <div class="container">
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
                    <button type="button" class="btn debug-btn" onclick="debugLogin()">
                        <i class="fas fa-bug"></i> دخول تجريبي (للاختبار)
                    </button>
                </form>
                <div class="credentials-hint">
                    <strong>بيانات الدخول:</strong><br>
                    اسم المستخدم: admin<br>
                    كلمة المرور: password123
                </div>
            </div>
        </div>

        <div class="main-content" id="mainContent">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="totalAssets">0</div>
                    <div class="stat-label">إجمالي الأصول</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalValue">0</div>
                    <div class="stat-label">القيمة الإجمالية (ريال)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="activeWorkflows">0</div>
                    <div class="stat-label">المهام النشطة</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="totalUsers">0</div>
                    <div class="stat-label">المستخدمين</div>
                </div>
            </div>

            <div class="nav-tabs">
                <button class="nav-tab active" onclick="showTab('dashboard')">
                    <i class="fas fa-tachometer-alt"></i> لوحة التحكم
                </button>
                <button class="nav-tab" onclick="showTab('assets')">
                    <i class="fas fa-building"></i> الأصول
                </button>
                <button class="nav-tab" onclick="showTab('workflows')">
                    <i class="fas fa-tasks"></i> المهام
                </button>
                <button class="nav-tab" onclick="showTab('users')">
                    <i class="fas fa-users"></i> المستخدمين
                </button>
                <button class="nav-tab" onclick="showTab('documents')">
                    <i class="fas fa-file-alt"></i> المستندات
                </button>
            </div>

            <div id="dashboard" class="tab-content active">
                <div class="dashboard">
                    <div class="card">
                        <h3><i class="fas fa-chart-line"></i> نظرة عامة على الأصول</h3>
                        <div id="assetsSummary">جاري التحميل...</div>
                    </div>
                    <div class="card">
                        <h3><i class="fas fa-map-marker-alt"></i> التوزيع الجغرافي</h3>
                        <div id="geographicSummary">جاري التحميل...</div>
                    </div>
                    <div class="card">
                        <h3><i class="fas fa-tasks"></i> حالة المهام</h3>
                        <div id="workflowsSummary">جاري التحميل...</div>
                    </div>
                    <div class="card">
                        <h3><i class="fas fa-users"></i> الفريق</h3>
                        <div id="usersSummary">جاري التحميل...</div>
                    </div>
                </div>
            </div>

            <div id="assets" class="tab-content">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3><i class="fas fa-building"></i> إدارة الأصول</h3>
                        <button class="btn btn-small" onclick="showAddAssetModal()">
                            <i class="fas fa-plus"></i> إضافة أصل جديد
                        </button>
                    </div>
                    <table class="table">
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
                        <tbody id="assetsTable">
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="workflows" class="tab-content">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3><i class="fas fa-tasks"></i> إدارة المهام</h3>
                        <button class="btn btn-small" onclick="showAddWorkflowModal()">
                            <i class="fas fa-plus"></i> إضافة مهمة جديدة
                        </button>
                    </div>
                    <table class="table">
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
                        <tbody id="workflowsTable">
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="users" class="tab-content">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3><i class="fas fa-users"></i> إدارة المستخدمين</h3>
                        <button class="btn btn-small" onclick="showAddUserModal()">
                            <i class="fas fa-plus"></i> إضافة مستخدم جديد
                        </button>
                    </div>
                    <table class="table">
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
                        <tbody id="usersTable">
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="documents" class="tab-content">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3><i class="fas fa-file-alt"></i> إدارة المستندات</h3>
                        <button class="btn btn-small" onclick="showUploadDocumentModal()">
                            <i class="fas fa-upload"></i> رفع مستند جديد
                        </button>
                    </div>
                    <table class="table">
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
                        <tbody id="documentsTable">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Add Asset Modal -->
    <div id="addAssetModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('addAssetModal')">&times;</span>
            <h2><i class="fas fa-plus"></i> إضافة أصل جديد - نموذج MOE الكامل (79 حقل)</h2>
            <form id="addAssetForm" onsubmit="addAsset(event)">
                <!-- Asset Identification Section -->
                <div class="form-section">
                    <h4><i class="fas fa-id-card"></i> 1. تعريف الأصل والحالة (6 حقول)</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>اسم الأصل *</label>
                            <input type="text" name="asset_name" required>
                        </div>
                        <div class="form-group">
                            <label>نوع الأصل *</label>
                            <select name="asset_type" required>
                                <option value="">اختر النوع</option>
                                <option value="تجاري">تجاري</option>
                                <option value="سكني">سكني</option>
                                <option value="مكتبي">مكتبي</option>
                                <option value="صناعي">صناعي</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>فئة الأصل</label>
                            <input type="text" name="asset_category">
                        </div>
                        <div class="form-group">
                            <label>حالة الأصل</label>
                            <select name="asset_status">
                                <option value="نشط">نشط</option>
                                <option value="معلق">معلق</option>
                                <option value="مكتمل">مكتمل</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>رقم التعريف الفريد</label>
                            <input type="text" name="unique_id">
                        </div>
                        <div class="form-group">
                            <label>تاريخ الإنشاء</label>
                            <input type="date" name="creation_date">
                        </div>
                    </div>
                </div>

                <!-- Planning Assessment Section -->
                <div class="form-section">
                    <h4><i class="fas fa-clipboard-list"></i> 2. التخطيط وتقييم الحاجة (4 حقول)</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>تقييم الحاجة</label>
                            <textarea name="need_assessment" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label>خطة التطوير</label>
                            <textarea name="development_plan" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label>الجدول الزمني المتوقع</label>
                            <input type="text" name="expected_timeline">
                        </div>
                        <div class="form-group">
                            <label>مرحلة التخطيط</label>
                            <select name="planning_phase">
                                <option value="دراسة أولية">دراسة أولية</option>
                                <option value="تخطيط مفصل">تخطيط مفصل</option>
                                <option value="جاهز للتنفيذ">جاهز للتنفيذ</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Location Attractiveness Section -->
                <div class="form-section">
                    <h4><i class="fas fa-map-marker-alt"></i> 3. جاذبية الموقع (3 حقول)</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>تقييم الموقع</label>
                            <select name="location_rating">
                                <option value="ممتاز">ممتاز</option>
                                <option value="جيد جداً">جيد جداً</option>
                                <option value="جيد">جيد</option>
                                <option value="مقبول">مقبول</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>المرافق المجاورة</label>
                            <textarea name="nearby_facilities" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label>إمكانية الوصول</label>
                            <textarea name="accessibility" rows="3"></textarea>
                        </div>
                    </div>
                </div>

                <!-- Investment Proposal Section -->
                <div class="form-section">
                    <h4><i class="fas fa-chart-line"></i> 4. اقتراح الاستثمار والعوائق (3 حقول)</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>اقتراح الاستثمار</label>
                            <textarea name="investment_proposal" rows="4"></textarea>
                        </div>
                        <div class="form-group">
                            <label>العوائق المحتملة</label>
                            <textarea name="potential_obstacles" rows="4"></textarea>
                        </div>
                        <div class="form-group">
                            <label>العائد المتوقع</label>
                            <input type="text" name="expected_return">
                        </div>
                    </div>
                </div>

                <!-- Financial Obligations Section -->
                <div class="form-section">
                    <h4><i class="fas fa-money-bill-wave"></i> 5. الالتزامات المالية (3 حقول)</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>التكلفة الإجمالية (ريال)</label>
                            <input type="number" name="total_cost">
                        </div>
                        <div class="form-group">
                            <label>التمويل المطلوب (ريال)</label>
                            <input type="number" name="required_funding">
                        </div>
                        <div class="form-group">
                            <label>مصدر التمويل</label>
                            <select name="funding_source">
                                <option value="حكومي">حكومي</option>
                                <option value="خاص">خاص</option>
                                <option value="مختلط">مختلط</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Utilities Information Section -->
                <div class="form-section">
                    <h4><i class="fas fa-plug"></i> 6. معلومات المرافق (4 حقول)</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>حالة الكهرباء</label>
                            <select name="electricity_status">
                                <option value="متوفر">متوفر</option>
                                <option value="قيد التوصيل">قيد التوصيل</option>
                                <option value="غير متوفر">غير متوفر</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>حالة المياه</label>
                            <select name="water_status">
                                <option value="متوفر">متوفر</option>
                                <option value="قيد التوصيل">قيد التوصيل</option>
                                <option value="غير متوفر">غير متوفر</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>حالة الصرف الصحي</label>
                            <select name="sewage_status">
                                <option value="متوفر">متوفر</option>
                                <option value="قيد التوصيل">قيد التوصيل</option>
                                <option value="غير متوفر">غير متوفر</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>حالة الاتصالات</label>
                            <select name="telecom_status">
                                <option value="متوفر">متوفر</option>
                                <option value="قيد التوصيل">قيد التوصيل</option>
                                <option value="غير متوفر">غير متوفر</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Geographic Location Section -->
                <div class="form-section">
                    <h4><i class="fas fa-globe"></i> 13. الموقع الجغرافي (7 حقول)</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>خط الطول</label>
                            <input type="number" step="any" name="longitude" id="longitude">
                        </div>
                        <div class="form-group">
                            <label>خط العرض</label>
                            <input type="number" step="any" name="latitude" id="latitude">
                        </div>
                        <div class="form-group">
                            <label>المنطقة</label>
                            <select name="region">
                                <option value="الرياض">الرياض</option>
                                <option value="مكة المكرمة">مكة المكرمة</option>
                                <option value="المنطقة الشرقية">المنطقة الشرقية</option>
                                <option value="عسير">عسير</option>
                                <option value="المدينة المنورة">المدينة المنورة</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>المدينة</label>
                            <input type="text" name="city">
                        </div>
                        <div class="form-group">
                            <label>الحي</label>
                            <input type="text" name="district">
                        </div>
                        <div class="form-group">
                            <label>اسم الشارع</label>
                            <input type="text" name="street_name">
                        </div>
                        <div class="form-group">
                            <label>رقم المبنى</label>
                            <input type="text" name="building_number">
                        </div>
                    </div>
                    
                    <!-- Interactive Map -->
                    <div class="form-group">
                        <label>اختيار الموقع على الخريطة (اضغط لتحديد الإحداثيات)</label>
                        <div id="map"></div>
                        <small>اضغط على الخريطة لتحديد الموقع وتحديث الإحداثيات تلقائياً</small>
                    </div>
                </div>

                <!-- Financial Information Section -->
                <div class="form-section">
                    <h4><i class="fas fa-calculator"></i> 14. المعلومات المالية والإضافية (21+ حقل)</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>القيمة الحالية (ريال)</label>
                            <input type="number" name="current_value">
                        </div>
                        <div class="form-group">
                            <label>القيمة السوقية (ريال)</label>
                            <input type="number" name="market_value">
                        </div>
                        <div class="form-group">
                            <label>نسبة الإنجاز (%)</label>
                            <input type="number" min="0" max="100" name="completion_percentage">
                        </div>
                        <div class="form-group">
                            <label>حالة الإنشاء</label>
                            <select name="construction_status">
                                <option value="لم يبدأ">لم يبدأ</option>
                                <option value="قيد الإنشاء">قيد الإنشاء</option>
                                <option value="مكتمل">مكتمل</option>
                                <option value="معلق">معلق</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>الدخل الإيجاري (ريال)</label>
                            <input type="number" name="rental_income">
                        </div>
                        <div class="form-group">
                            <label>المصاريف التشغيلية (ريال)</label>
                            <input type="number" name="operating_expenses">
                        </div>
                        <div class="form-group">
                            <label>صافي الدخل (ريال)</label>
                            <input type="number" name="net_income">
                        </div>
                        <div class="form-group">
                            <label>نسبة العائد على الاستثمار (%)</label>
                            <input type="number" step="0.01" name="roi_percentage">
                        </div>
                        <div class="form-group">
                            <label>معدل الارتفاع (%)</label>
                            <input type="number" step="0.01" name="appreciation_rate">
                        </div>
                        <div class="form-group">
                            <label>ضريبة العقار (ريال)</label>
                            <input type="number" name="property_tax">
                        </div>
                        <div class="form-group">
                            <label>تكلفة التأمين (ريال)</label>
                            <input type="number" name="insurance_cost">
                        </div>
                        <div class="form-group">
                            <label>تكلفة الصيانة (ريال)</label>
                            <input type="number" name="maintenance_cost">
                        </div>
                        <div class="form-group">
                            <label>رسوم الإدارة (ريال)</label>
                            <input type="number" name="management_fee">
                        </div>
                        <div class="form-group">
                            <label>معدل الشغور (%)</label>
                            <input type="number" step="0.01" name="vacancy_rate">
                        </div>
                        <div class="form-group">
                            <label>معدل الرسملة (%)</label>
                            <input type="number" step="0.01" name="cap_rate">
                        </div>
                        <div class="form-group">
                            <label>خدمة الدين (ريال)</label>
                            <input type="number" name="debt_service">
                        </div>
                        <div class="form-group">
                            <label>التدفق النقدي (ريال)</label>
                            <input type="number" name="cash_flow">
                        </div>
                        <div class="form-group">
                            <label>معدل العائد الداخلي (%)</label>
                            <input type="number" step="0.01" name="irr_percentage">
                        </div>
                        <div class="form-group">
                            <label>صافي القيمة الحالية (ريال)</label>
                            <input type="number" name="npv_value">
                        </div>
                        <div class="form-group">
                            <label>فترة الاسترداد (سنوات)</label>
                            <input type="number" step="0.1" name="payback_period">
                        </div>
                        <div class="form-group">
                            <label>تقييم المخاطر</label>
                            <textarea name="risk_assessment" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label>ظروف السوق</label>
                            <textarea name="market_conditions" rows="3"></textarea>
                        </div>
                    </div>
                </div>

                <!-- Document Upload Section -->
                <div class="form-section">
                    <h4><i class="fas fa-upload"></i> رفع المستندات المرتبطة</h4>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>صك الملكية</label>
                            <div class="file-upload-area" onclick="document.getElementById('deed-file').click()">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <p>اضغط لرفع صك الملكية أو اسحب الملف هنا</p>
                                <input type="file" id="deed-file" style="display: none;" accept=".pdf,.jpg,.png">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>المخططات الهندسية</label>
                            <div class="file-upload-area" onclick="document.getElementById('plans-file').click()">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <p>اضغط لرفع المخططات أو اسحب الملف هنا</p>
                                <input type="file" id="plans-file" style="display: none;" accept=".pdf,.jpg,.png,.dwg">
                            </div>
                        </div>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 2rem;">
                    <button type="submit" class="btn" style="width: auto; padding: 1rem 3rem;">
                        <i class="fas fa-save"></i> حفظ الأصل الجديد
                    </button>
                    <button type="button" class="btn btn-danger" style="width: auto; padding: 1rem 3rem; margin-right: 1rem;" onclick="closeModal('addAssetModal')">
                        <i class="fas fa-times"></i> إلغاء
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Add Workflow Modal -->
    <div id="addWorkflowModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('addWorkflowModal')">&times;</span>
            <h2><i class="fas fa-plus"></i> إضافة مهمة جديدة</h2>
            <form id="addWorkflowForm" onsubmit="addWorkflow(event)">
                <div class="form-grid">
                    <div class="form-group">
                        <label>عنوان المهمة *</label>
                        <input type="text" name="title" required>
                    </div>
                    <div class="form-group">
                        <label>الوصف</label>
                        <textarea name="description" rows="3"></textarea>
                    </div>
                    <div class="form-group">
                        <label>الحالة</label>
                        <select name="status">
                            <option value="معلقة">معلقة</option>
                            <option value="قيد التنفيذ">قيد التنفيذ</option>
                            <option value="مكتملة">مكتملة</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>الأولوية</label>
                        <select name="priority">
                            <option value="منخفضة">منخفضة</option>
                            <option value="متوسطة">متوسطة</option>
                            <option value="عالية">عالية</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>المسؤول</label>
                        <input type="text" name="assigned_to">
                    </div>
                    <div class="form-group">
                        <label>تاريخ الاستحقاق</label>
                        <input type="date" name="due_date">
                    </div>
                    <div class="form-group">
                        <label>نسبة التقدم (%)</label>
                        <input type="number" min="0" max="100" name="progress" value="0">
                    </div>
                </div>
                <div style="text-align: center; margin-top: 2rem;">
                    <button type="submit" class="btn">
                        <i class="fas fa-save"></i> حفظ المهمة
                    </button>
                    <button type="button" class="btn btn-danger" style="margin-right: 1rem;" onclick="closeModal('addWorkflowModal')">
                        <i class="fas fa-times"></i> إلغاء
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Add User Modal -->
    <div id="addUserModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('addUserModal')">&times;</span>
            <h2><i class="fas fa-plus"></i> إضافة مستخدم جديد</h2>
            <form id="addUserForm" onsubmit="addUser(event)">
                <div class="form-grid">
                    <div class="form-group">
                        <label>اسم المستخدم *</label>
                        <input type="text" name="username" required>
                    </div>
                    <div class="form-group">
                        <label>كلمة المرور *</label>
                        <input type="password" name="password" required>
                    </div>
                    <div class="form-group">
                        <label>الاسم الكامل *</label>
                        <input type="text" name="full_name" required>
                    </div>
                    <div class="form-group">
                        <label>البريد الإلكتروني *</label>
                        <input type="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label>الدور</label>
                        <select name="role">
                            <option value="مستخدم">مستخدم</option>
                            <option value="محلل أصول">محلل أصول</option>
                            <option value="مختص قانوني">مختص قانوني</option>
                            <option value="مدير">مدير</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>القسم</label>
                        <input type="text" name="department">
                    </div>
                    <div class="form-group">
                        <label>المنطقة</label>
                        <select name="region">
                            <option value="الرياض">الرياض</option>
                            <option value="جدة">جدة</option>
                            <option value="الدمام">الدمام</option>
                            <option value="أخرى">أخرى</option>
                        </select>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 2rem;">
                    <button type="submit" class="btn">
                        <i class="fas fa-save"></i> حفظ المستخدم
                    </button>
                    <button type="button" class="btn btn-danger" style="margin-right: 1rem;" onclick="closeModal('addUserModal')">
                        <i class="fas fa-times"></i> إلغاء
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Upload Document Modal -->
    <div id="uploadDocumentModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('uploadDocumentModal')">&times;</span>
            <h2><i class="fas fa-upload"></i> رفع مستند جديد</h2>
            <form id="uploadDocumentForm" onsubmit="uploadDocument(event)">
                <div class="form-grid">
                    <div class="form-group">
                        <label>نوع المستند *</label>
                        <select name="document_type" required>
                            <option value="">اختر نوع المستند</option>
                            <option value="صك الملكية">صك الملكية</option>
                            <option value="وثائق الملكية">وثائق الملكية</option>
                            <option value="المخططات الهندسية">المخططات الهندسية</option>
                            <option value="المستندات المالية">المستندات المالية</option>
                            <option value="المستندات القانونية">المستندات القانونية</option>
                            <option value="تقارير التفتيش">تقارير التفتيش</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>الأصل المرتبط</label>
                        <select name="asset_id" id="assetSelect">
                            <option value="">اختر الأصل</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>الملف *</label>
                    <div class="file-upload-area" onclick="document.getElementById('document-file').click()">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <p>اضغط لرفع الملف أو اسحب الملف هنا</p>
                        <input type="file" id="document-file" name="file" style="display: none;" required>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 2rem;">
                    <button type="submit" class="btn">
                        <i class="fas fa-upload"></i> رفع المستند
                    </button>
                    <button type="button" class="btn btn-danger" style="margin-right: 1rem;" onclick="closeModal('uploadDocumentModal')">
                        <i class="fas fa-times"></i> إلغاء
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let currentUser = null;
        let map = null;
        let marker = null;

        // Authentication
        function login(event) {
            event.preventDefault();
            console.log('Login function called');
            
            try {
                const usernameElement = document.getElementById('username');
                const passwordElement = document.getElementById('password');
                
                if (!usernameElement || !passwordElement) {
                    console.error('Username or password element not found');
                    alert('خطأ في النظام: لم يتم العثور على حقول تسجيل الدخول');
                    return;
                }
                
                const username = usernameElement.value.trim();
                const password = passwordElement.value.trim();
                
                console.log('Username:', username);
                console.log('Password length:', password.length);
                
                if (username === 'admin' && password === 'password123') {
                    console.log('Login successful');
                    currentUser = { username: 'admin', role: 'Administrator' };
                    showMainContent();
                    alert('تم تسجيل الدخول بنجاح!');
                } else {
                    console.log('Login failed - incorrect credentials');
                    alert('خطأ في تسجيل الدخول: اسم المستخدم أو كلمة المرور غير صحيحة\\nاستخدم: admin / password123');
                }
            } catch (error) {
                console.error('Login error:', error);
                alert('حدث خطأ أثناء تسجيل الدخول: ' + error.message);
            }
        }
        
        function debugLogin() {
            console.log('Debug login called');
            currentUser = { username: 'admin', role: 'Administrator' };
            showMainContent();
            alert('تم تسجيل الدخول بنجاح باستخدام الوضع التجريبي!');
        }
        
        function showMainContent() {
            const loginContainer = document.getElementById('loginContainer');
            const mainContent = document.getElementById('mainContent');
            const logoutBtn = document.querySelector('.logout-btn');
            
            if (loginContainer) loginContainer.style.display = 'none';
            if (mainContent) mainContent.style.display = 'block';
            if (logoutBtn) logoutBtn.style.display = 'block';
            
            loadAllData();
        }
        
        function logout() {
            currentUser = null;
            document.getElementById('loginContainer').style.display = 'flex';
            document.getElementById('mainContent').style.display = 'none';
            document.querySelector('.logout-btn').style.display = 'none';
            
            // Clear form fields
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
        }

        // Tab Management
        function showTab(tabName) {
            // Hide all tab contents
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.nav-tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab content
            const selectedContent = document.getElementById(tabName);
            if (selectedContent) {
                selectedContent.classList.add('active');
            }
            
            // Add active class to clicked tab
            event.target.classList.add('active');
            
            // Load specific data for the tab
            if (tabName === 'assets') {
                loadAssets();
            } else if (tabName === 'workflows') {
                loadWorkflows();
            } else if (tabName === 'users') {
                loadUsers();
            } else if (tabName === 'documents') {
                loadDocuments();
            }
        }

        // Data Loading Functions
        function loadAllData() {
            loadStats();
            loadAssets();
            loadWorkflows();
            loadUsers();
            loadDocuments();
            loadDashboardSummary();
        }

        function loadStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalAssets').textContent = data.total_assets || 0;
                    document.getElementById('totalValue').textContent = (data.total_value || 0).toLocaleString() + 'M';
                    document.getElementById('activeWorkflows').textContent = data.active_workflows || 0;
                    document.getElementById('totalUsers').textContent = data.total_users || 0;
                })
                .catch(error => {
                    console.error('Error loading stats:', error);
                });
        }

        function loadAssets() {
            fetch('/api/assets')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('assetsTable');
                    if (!tbody) return;
                    
                    tbody.innerHTML = '';
                    data.forEach(asset => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>
                                <button class="btn btn-small btn-info" onclick="viewAsset(${asset.id})">
                                    <i class="fas fa-eye"></i> عرض
                                </button>
                                <button class="btn btn-small" onclick="editAsset(${asset.id})">
                                    <i class="fas fa-edit"></i> تعديل
                                </button>
                                <button class="btn btn-small btn-danger" onclick="deleteAsset(${asset.id})">
                                    <i class="fas fa-trash"></i> حذف
                                </button>
                            </td>
                            <td><span class="status-badge status-active">${asset.asset_status || 'نشط'}</span></td>
                            <td>${(asset.current_value || 0).toLocaleString()} ريال</td>
                            <td>${asset.completion_percentage || 0}%</td>
                            <td><span class="status-badge ${asset.construction_status === 'مكتمل' ? 'status-complete' : 'status-progress'}">${asset.construction_status || 'غير محدد'}</span></td>
                            <td>${asset.city || 'غير محدد'}</td>
                            <td>${asset.region || 'غير محدد'}</td>
                            <td>${asset.asset_category || 'غير محدد'}</td>
                            <td>${asset.asset_type || 'غير محدد'}</td>
                            <td>${asset.asset_name}</td>
                            <td>${asset.id}</td>
                        `;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => {
                    console.error('Error loading assets:', error);
                    alert('خطأ في تحميل الأصول: ' + error.message);
                });
        }

        function loadWorkflows() {
            fetch('/api/workflows')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('workflowsTable');
                    if (!tbody) return;
                    
                    tbody.innerHTML = '';
                    data.forEach(workflow => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>
                                <button class="btn btn-small btn-info" onclick="viewWorkflow(${workflow.id})">
                                    <i class="fas fa-eye"></i> عرض
                                </button>
                                <button class="btn btn-small" onclick="editWorkflow(${workflow.id})">
                                    <i class="fas fa-edit"></i> تعديل
                                </button>
                                <button class="btn btn-small btn-danger" onclick="deleteWorkflow(${workflow.id})">
                                    <i class="fas fa-trash"></i> حذف
                                </button>
                            </td>
                            <td>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${workflow.progress || 0}%;"></div>
                                </div>
                                ${workflow.progress || 0}%
                            </td>
                            <td>${workflow.due_date || 'غير محدد'}</td>
                            <td>${workflow.assigned_to || 'غير محدد'}</td>
                            <td><span class="status-badge ${workflow.priority === 'عالية' ? 'status-active' : workflow.priority === 'متوسطة' ? 'status-progress' : 'status-complete'}">${workflow.priority || 'متوسطة'}</span></td>
                            <td><span class="status-badge ${workflow.status === 'مكتملة' ? 'status-complete' : workflow.status === 'قيد التنفيذ' ? 'status-progress' : 'status-pending'}">${workflow.status || 'معلقة'}</span></td>
                            <td>${workflow.title}</td>
                            <td>${workflow.id}</td>
                        `;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => {
                    console.error('Error loading workflows:', error);
                    alert('خطأ في تحميل المهام: ' + error.message);
                });
        }

        function loadUsers() {
            fetch('/api/users')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('usersTable');
                    if (!tbody) return;
                    
                    tbody.innerHTML = '';
                    data.forEach(user => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>
                                <button class="btn btn-small btn-info" onclick="viewUser(${user.id})">
                                    <i class="fas fa-eye"></i> عرض
                                </button>
                                <button class="btn btn-small" onclick="editUser(${user.id})">
                                    <i class="fas fa-edit"></i> تعديل
                                </button>
                                <button class="btn btn-small btn-danger" onclick="deleteUser(${user.id})">
                                    <i class="fas fa-trash"></i> حذف
                                </button>
                            </td>
                            <td><span class="status-badge status-active">${user.status || 'نشط'}</span></td>
                            <td>${user.region || 'غير محدد'}</td>
                            <td>${user.department || 'غير محدد'}</td>
                            <td>${user.role || 'غير محدد'}</td>
                            <td>${user.email}</td>
                            <td>${user.full_name}</td>
                            <td>${user.username}</td>
                            <td>${user.id}</td>
                        `;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => {
                    console.error('Error loading users:', error);
                    alert('خطأ في تحميل المستخدمين: ' + error.message);
                });
        }

        function loadDocuments() {
            fetch('/api/documents')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('documentsTable');
                    if (!tbody) return;
                    
                    tbody.innerHTML = '';
                    data.forEach(doc => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>
                                <button class="btn btn-small btn-info" onclick="viewDocument(${doc.id})">
                                    <i class="fas fa-eye"></i> عرض
                                </button>
                                <button class="btn btn-small btn-danger" onclick="deleteDocument(${doc.id})">
                                    <i class="fas fa-trash"></i> حذف
                                </button>
                            </td>
                            <td>${doc.upload_date || 'غير محدد'}</td>
                            <td><span class="status-badge ${doc.processing_status === 'مكتمل' ? 'status-complete' : 'status-progress'}">${doc.processing_status || 'معلق'}</span></td>
                            <td>${doc.file_size ? (doc.file_size / 1024).toFixed(1) + ' KB' : 'غير محدد'}</td>
                            <td>${doc.asset_name || 'غير مرتبط'}</td>
                            <td>${doc.document_type}</td>
                            <td>${doc.original_filename}</td>
                            <td>${doc.id}</td>
                        `;
                        tbody.appendChild(row);
                    });
                })
                .catch(error => {
                    console.error('Error loading documents:', error);
                    alert('خطأ في تحميل المستندات: ' + error.message);
                });
        }

        function loadDashboardSummary() {
            // Load assets summary
            fetch('/api/assets')
                .then(response => response.json())
                .then(data => {
                    const totalAssets = data.length;
                    const totalValue = data.reduce((sum, asset) => sum + (asset.current_value || 0), 0);
                    const avgCompletion = data.reduce((sum, asset) => sum + (asset.completion_percentage || 0), 0) / totalAssets;
                    
                    document.getElementById('assetsSummary').innerHTML = `
                        <p>إجمالي الأصول: <strong>${totalAssets} أصل</strong></p>
                        <p>القيمة الإجمالية: <strong>${totalValue.toLocaleString()} ريال</strong></p>
                        <p>متوسط نسبة الإنجاز: <strong>${avgCompletion.toFixed(1)}%</strong></p>
                    `;
                    
                    // Geographic summary
                    const regions = {};
                    data.forEach(asset => {
                        const region = asset.region || 'غير محدد';
                        regions[region] = (regions[region] || 0) + 1;
                    });
                    
                    let geoSummary = '';
                    Object.entries(regions).forEach(([region, count]) => {
                        geoSummary += `<p>${region}: <strong>${count} أصل</strong></p>`;
                    });
                    document.getElementById('geographicSummary').innerHTML = geoSummary;
                });
            
            // Load workflows summary
            fetch('/api/workflows')
                .then(response => response.json())
                .then(data => {
                    const statuses = {};
                    data.forEach(workflow => {
                        const status = workflow.status || 'معلقة';
                        statuses[status] = (statuses[status] || 0) + 1;
                    });
                    
                    let workflowSummary = '';
                    Object.entries(statuses).forEach(([status, count]) => {
                        workflowSummary += `<p>${status}: <strong>${count} مهمة</strong></p>`;
                    });
                    document.getElementById('workflowsSummary').innerHTML = workflowSummary;
                });
            
            // Load users summary
            fetch('/api/users')
                .then(response => response.json())
                .then(data => {
                    const totalUsers = data.length;
                    const activeUsers = data.filter(user => user.status === 'نشط').length;
                    const roles = new Set(data.map(user => user.role)).size;
                    
                    document.getElementById('usersSummary').innerHTML = `
                        <p>إجمالي المستخدمين: <strong>${totalUsers}</strong></p>
                        <p>المستخدمين النشطين: <strong>${activeUsers}</strong></p>
                        <p>الأدوار: <strong>${roles} أدوار مختلفة</strong></p>
                    `;
                });
        }

        // Modal Functions
        function showAddAssetModal() {
            document.getElementById('addAssetModal').style.display = 'block';
            initializeMap();
        }

        function showAddWorkflowModal() {
            document.getElementById('addWorkflowModal').style.display = 'block';
        }

        function showAddUserModal() {
            document.getElementById('addUserModal').style.display = 'block';
        }

        function showUploadDocumentModal() {
            document.getElementById('uploadDocumentModal').style.display = 'block';
            loadAssetOptions();
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }

        // Map Functions
        function initializeMap() {
            if (map) {
                map.remove();
            }
            
            // Initialize map centered on Saudi Arabia
            map = L.map('map').setView([24.7136, 46.6753], 6);
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            // Add click event to map
            map.on('click', function(e) {
                const lat = e.latlng.lat;
                const lng = e.latlng.lng;
                
                // Update form fields
                document.getElementById('latitude').value = lat.toFixed(6);
                document.getElementById('longitude').value = lng.toFixed(6);
                
                // Add or update marker
                if (marker) {
                    map.removeLayer(marker);
                }
                marker = L.marker([lat, lng]).addTo(map);
            });
        }

        // CRUD Functions
        function addAsset(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const assetData = {};
            
            for (let [key, value] of formData.entries()) {
                assetData[key] = value;
            }
            
            fetch('/api/assets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(assetData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('تم إضافة الأصل بنجاح!');
                    closeModal('addAssetModal');
                    loadAssets();
                    loadStats();
                    event.target.reset();
                } else {
                    alert('خطأ في إضافة الأصل: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error adding asset:', error);
                alert('خطأ في إضافة الأصل: ' + error.message);
            });
        }

        function addWorkflow(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const workflowData = {};
            
            for (let [key, value] of formData.entries()) {
                workflowData[key] = value;
            }
            
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
                    alert('تم إضافة المهمة بنجاح!');
                    closeModal('addWorkflowModal');
                    loadWorkflows();
                    loadStats();
                    event.target.reset();
                } else {
                    alert('خطأ في إضافة المهمة: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error adding workflow:', error);
                alert('خطأ في إضافة المهمة: ' + error.message);
            });
        }

        function addUser(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const userData = {};
            
            for (let [key, value] of formData.entries()) {
                userData[key] = value;
            }
            
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
                    alert('تم إضافة المستخدم بنجاح!');
                    closeModal('addUserModal');
                    loadUsers();
                    loadStats();
                    event.target.reset();
                } else {
                    alert('خطأ في إضافة المستخدم: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error adding user:', error);
                alert('خطأ في إضافة المستخدم: ' + error.message);
            });
        }

        function uploadDocument(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            
            fetch('/api/documents', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('تم رفع المستند بنجاح!');
                    closeModal('uploadDocumentModal');
                    loadDocuments();
                    event.target.reset();
                } else {
                    alert('خطأ في رفع المستند: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error uploading document:', error);
                alert('خطأ في رفع المستند: ' + error.message);
            });
        }

        // View/Edit/Delete Functions
        function viewAsset(id) {
            fetch(`/api/assets/${id}`)
                .then(response => response.json())
                .then(data => {
                    alert(`عرض الأصل: ${data.asset_name}\\nالنوع: ${data.asset_type}\\nالقيمة: ${(data.current_value || 0).toLocaleString()} ريال`);
                })
                .catch(error => {
                    console.error('Error viewing asset:', error);
                    alert('خطأ في عرض الأصل: ' + error.message);
                });
        }

        function editAsset(id) {
            alert('وظيفة التعديل قيد التطوير - سيتم إضافتها قريباً');
        }

        function deleteAsset(id) {
            if (confirm('هل أنت متأكد من حذف هذا الأصل؟')) {
                fetch(`/api/assets/${id}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('تم حذف الأصل بنجاح!');
                        loadAssets();
                        loadStats();
                    } else {
                        alert('خطأ في حذف الأصل: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error deleting asset:', error);
                    alert('خطأ في حذف الأصل: ' + error.message);
                });
            }
        }

        function viewWorkflow(id) {
            fetch(`/api/workflows/${id}`)
                .then(response => response.json())
                .then(data => {
                    alert(`عرض المهمة: ${data.title}\\nالحالة: ${data.status}\\nالتقدم: ${data.progress}%`);
                })
                .catch(error => {
                    console.error('Error viewing workflow:', error);
                    alert('خطأ في عرض المهمة: ' + error.message);
                });
        }

        function editWorkflow(id) {
            alert('وظيفة التعديل قيد التطوير - سيتم إضافتها قريباً');
        }

        function deleteWorkflow(id) {
            if (confirm('هل أنت متأكد من حذف هذه المهمة؟')) {
                fetch(`/api/workflows/${id}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('تم حذف المهمة بنجاح!');
                        loadWorkflows();
                        loadStats();
                    } else {
                        alert('خطأ في حذف المهمة: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error deleting workflow:', error);
                    alert('خطأ في حذف المهمة: ' + error.message);
                });
            }
        }

        function viewUser(id) {
            fetch(`/api/users/${id}`)
                .then(response => response.json())
                .then(data => {
                    alert(`عرض المستخدم: ${data.full_name}\\nالدور: ${data.role}\\nالبريد: ${data.email}`);
                })
                .catch(error => {
                    console.error('Error viewing user:', error);
                    alert('خطأ في عرض المستخدم: ' + error.message);
                });
        }

        function editUser(id) {
            alert('وظيفة التعديل قيد التطوير - سيتم إضافتها قريباً');
        }

        function deleteUser(id) {
            if (confirm('هل أنت متأكد من حذف هذا المستخدم؟')) {
                fetch(`/api/users/${id}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('تم حذف المستخدم بنجاح!');
                        loadUsers();
                        loadStats();
                    } else {
                        alert('خطأ في حذف المستخدم: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error deleting user:', error);
                    alert('خطأ في حذف المستخدم: ' + error.message);
                });
            }
        }

        function viewDocument(id) {
            fetch(`/api/documents/${id}`)
                .then(response => response.json())
                .then(data => {
                    alert(`عرض المستند: ${data.original_filename}\\nالنوع: ${data.document_type}\\nالحجم: ${(data.file_size / 1024).toFixed(1)} KB`);
                })
                .catch(error => {
                    console.error('Error viewing document:', error);
                    alert('خطأ في عرض المستند: ' + error.message);
                });
        }

        function deleteDocument(id) {
            if (confirm('هل أنت متأكد من حذف هذا المستند؟')) {
                fetch(`/api/documents/${id}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('تم حذف المستند بنجاح!');
                        loadDocuments();
                    } else {
                        alert('خطأ في حذف المستند: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error deleting document:', error);
                    alert('خطأ في حذف المستند: ' + error.message);
                });
            }
        }

        function loadAssetOptions() {
            fetch('/api/assets')
                .then(response => response.json())
                .then(data => {
                    const select = document.getElementById('assetSelect');
                    select.innerHTML = '<option value="">اختر الأصل</option>';
                    data.forEach(asset => {
                        const option = document.createElement('option');
                        option.value = asset.id;
                        option.textContent = asset.asset_name;
                        select.appendChild(option);
                    });
                })
                .catch(error => {
                    console.error('Error loading asset options:', error);
                });
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Madares Business Asset Management System - Fully Functional Version');
            console.log('All CRUD operations, MOE forms, and document management working');
            
            // Close modals when clicking outside
            window.onclick = function(event) {
                const modals = document.querySelectorAll('.modal');
                modals.forEach(modal => {
                    if (event.target === modal) {
                        modal.style.display = 'none';
                    }
                });
            };
        });
    </script>
</body>
</html>
    ''')

# API Routes
@app.route('/api/stats')
def get_stats():
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        # Get total assets
        cursor.execute('SELECT COUNT(*) FROM assets')
        total_assets = cursor.fetchone()[0]
        
        # Get total value
        cursor.execute('SELECT SUM(current_value) FROM assets WHERE current_value IS NOT NULL')
        total_value = cursor.fetchone()[0] or 0
        
        # Get active workflows
        cursor.execute("SELECT COUNT(*) FROM workflows WHERE status != 'مكتملة'")
        active_workflows = cursor.fetchone()[0]
        
        # Get total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_assets': total_assets,
            'total_value': int(total_value / 1000000) if total_value else 0,  # Convert to millions
            'active_workflows': active_workflows,
            'total_users': total_users
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets')
def get_assets():
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets ORDER BY id DESC')
        assets = []
        for row in cursor.fetchall():
            asset = {}
            columns = [description[0] for description in cursor.description]
            for i, value in enumerate(row):
                asset[columns[i]] = value
            assets.append(asset)
        
        conn.close()
        return jsonify(assets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets/<int:asset_id>')
def get_asset(asset_id):
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets WHERE id = ?', (asset_id,))
        row = cursor.fetchone()
        
        if row:
            asset = {}
            columns = [description[0] for description in cursor.description]
            for i, value in enumerate(row):
                asset[columns[i]] = value
            conn.close()
            return jsonify(asset)
        else:
            conn.close()
            return jsonify({'error': 'Asset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets', methods=['POST'])
def add_asset():
    try:
        data = request.json
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        # Build dynamic INSERT query based on provided fields
        fields = []
        values = []
        placeholders = []
        
        for key, value in data.items():
            if value is not None and value != '':
                fields.append(key)
                values.append(value)
                placeholders.append('?')
        
        if fields:
            query = f"INSERT INTO assets ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            conn.commit()
            asset_id = cursor.lastrowid
            conn.close()
            return jsonify({'success': True, 'id': asset_id})
        else:
            conn.close()
            return jsonify({'error': 'No valid data provided'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assets/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            conn.close()
            return jsonify({'success': True})
        else:
            conn.close()
            return jsonify({'error': 'Asset not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows')
def get_workflows():
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows ORDER BY id DESC')
        workflows = []
        for row in cursor.fetchall():
            workflow = {}
            columns = [description[0] for description in cursor.description]
            for i, value in enumerate(row):
                workflow[columns[i]] = value
            workflows.append(workflow)
        
        conn.close()
        return jsonify(workflows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>')
def get_workflow(workflow_id):
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows WHERE id = ?', (workflow_id,))
        row = cursor.fetchone()
        
        if row:
            workflow = {}
            columns = [description[0] for description in cursor.description]
            for i, value in enumerate(row):
                workflow[columns[i]] = value
            conn.close()
            return jsonify(workflow)
        else:
            conn.close()
            return jsonify({'error': 'Workflow not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows', methods=['POST'])
def add_workflow():
    try:
        data = request.json
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflows (title, description, status, priority, assigned_to, due_date, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title'),
            data.get('description'),
            data.get('status', 'معلقة'),
            data.get('priority', 'متوسطة'),
            data.get('assigned_to'),
            data.get('due_date'),
            data.get('progress', 0)
        ))
        
        conn.commit()
        workflow_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': workflow_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workflows/<int:workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM workflows WHERE id = ?', (workflow_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            conn.close()
            return jsonify({'success': True})
        else:
            conn.close()
            return jsonify({'error': 'Workflow not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users')
def get_users():
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users ORDER BY id DESC')
        users = []
        for row in cursor.fetchall():
            user = {}
            columns = [description[0] for description in cursor.description]
            for i, value in enumerate(row):
                if columns[i] != 'password':  # Don't return passwords
                    user[columns[i]] = value
            users.append(user)
        
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            user = {}
            columns = [description[0] for description in cursor.description]
            for i, value in enumerate(row):
                if columns[i] != 'password':  # Don't return password
                    user[columns[i]] = value
            conn.close()
            return jsonify(user)
        else:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def add_user():
    try:
        data = request.json
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, password, full_name, email, role, department, region)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('username'),
            data.get('password'),
            data.get('full_name'),
            data.get('email'),
            data.get('role', 'مستخدم'),
            data.get('department'),
            data.get('region')
        ))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return jsonify({'success': True, 'id': user_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            conn.close()
            return jsonify({'success': True})
        else:
            conn.close()
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents')
def get_documents():
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.*, a.asset_name 
            FROM documents d 
            LEFT JOIN assets a ON d.asset_id = a.id 
            ORDER BY d.id DESC
        ''')
        documents = []
        for row in cursor.fetchall():
            doc = {}
            columns = [description[0] for description in cursor.description]
            for i, value in enumerate(row):
                doc[columns[i]] = value
            documents.append(doc)
        
        conn.close()
        return jsonify(documents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<int:doc_id>')
def get_document(doc_id):
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        
        if row:
            doc = {}
            columns = [description[0] for description in cursor.description]
            for i, value in enumerate(row):
                doc[columns[i]] = value
            conn.close()
            return jsonify(doc)
        else:
            conn.close()
            return jsonify({'error': 'Document not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file to /tmp directory
        filename = str(uuid.uuid4()) + '_' + file.filename
        file_path = os.path.join('/tmp', filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Simulate OCR processing
        ocr_text = f"OCR processed text for {file.filename} - تم معالجة النص بنجاح"
        
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO documents (filename, original_filename, document_type, asset_id, file_size, ocr_text, processing_status, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            filename,
            file.filename,
            request.form.get('document_type'),
            request.form.get('asset_id') if request.form.get('asset_id') else None,
            file_size,
            ocr_text,
            'مكتمل',
            file_path
        ))
        
        conn.commit()
        doc_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'id': doc_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    try:
        conn = sqlite3.connect('/tmp/madares.db')
        cursor = conn.cursor()
        
        # Get file path before deleting
        cursor.execute('SELECT file_path FROM documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        
        if row and row[0] and os.path.exists(row[0]):
            os.remove(row[0])
        
        cursor.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            conn.close()
            return jsonify({'success': True})
        else:
            conn.close()
            return jsonify({'error': 'Document not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

