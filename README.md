# AI-Based Smart Medical Waste Segregation and Management System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-Flask%203.0+-green.svg)](https://palletsprojects.com/p/flask/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy%203.1+-red.svg)](https://www.sqlalchemy.org/)
[![Bootstrap 5](https://img.shields.io/badge/UI-Bootstrap%205.3-purple.svg)](https://getbootstrap.com/)
[![Tests](https://img.shields.io/badge/tests-Pytest-brightgreen.svg)](https://docs.pytest.org/)
[![Compliance](https://img.shields.io/badge/standard-BMW%20Rules%202016%20(India)-amber.svg)](https://cpcb.nic.in/waste-management-rules/)

A comprehensive, full-stack, college-level software system designed to assist healthcare facilities in classifying biomedical waste, displaying regulatory containment guidance, tracking disposal lifecycles, and producing statutory audit reports.

---

> ### ⚠️ Mandatory Educational Prototype & Clinical Safety Notice
> **THIS SOFTWARE IS AN EDUCATIONAL ENGINEERING PROTOTYPE.**
> - It is **not** certified as an autonomous diagnostic or hazardous waste disposal device.
> - Computer vision predictions must **never** be treated as the final authority for physical waste disposal.
> - In strict compliance with the **Bio-Medical Waste Management Rules (2016)** formulated by the Ministry of Environment, Forest and Climate Change (MoEFCC), Government of India, all waste must be **physically verified** by authorized clinical personnel before containment and dispatch.

---

## 1. Regulatory Framework: Indian BMW Rules (2016)

The system maps all waste classifications to the statutory color-coded streams prescribed by the Central Pollution Control Board (CPCB):

| Stream / Bin | Prescribed Waste Category | Container Specification | Approved Treatment / Disposal Method |
| :--- | :--- | :--- | :--- |
| **🟡 Yellow** | Infectious & Anatomical Waste, Soiled Cotton, Expired Pharma, Blood Bags | Non-chlorinated Yellow plastic bag | Incineration or Plasma Pyrolysis / Deep Burial |
| **🔴 Red** | Contaminated Recyclable Plastics (IV Tubing, Catheters, Syringes w/o needle, Gloves) | Non-chlorinated Red plastic bag | Autoclaving/Microwaving followed by shredding and recycling |
| **⚪ White** | Waste Sharps including Metals (Needles, Scalpels, Blades, Fixed needles) | Puncture-proof, tamper-proof translucent container | Autoclaving or Dry heat sterilization followed by shredding / encapsulation |
| **🔵 Blue** | Glassware (Broken ampoules, vials) & Metallic Implants | Puncture-proof & leak-proof cardboard/plastic box | Disinfection with 1-2% Sodium Hypochlorite / Autoclaving followed by recycling |
| **⬛ General** | Non-infectious municipal hospital refuse (Office paper, packaging, food) | Standard black/green municipal bin | Municipal solid waste disposal / Composting |
| **🟠 Unknown** | Unidentified residue, damaged labels, emergency mixed waste | Isolated quarantine bin | **Mandatory physical inspection by Infection Control Officer** |

---

## 2. Key System Features

1. **AI-Assisted Vision Segregation**:
   - Built on a **MobileNetV2** transfer learning architecture (input $224 \times 224$).
   - Returns predicted stream, confidence percentage, certainty tier (`HIGH`, `MEDIUM`, `LOW`), and statutory containment instructions.
   - **Zero-Failure Fallback**: Operates via a transparent **Educational Heuristic Classifier** if TensorFlow or pre-trained weights are not present, ensuring no crashes during student demonstrations.
2. **Mandatory Human-in-the-Loop Checkpoint**:
   - The UI enforces a physical inspection checkpoint where staff must confirm or override the suggested category and record the net weight in kilograms.
3. **Continuous AI Retraining & Feedback Loop**:
   - When clinical staff overrides an AI suggestion, a record is automatically committed to the `PredictionFeedback` table with the original prediction, assigned category, and rationale.
4. **Interactive Executive Dashboard**:
   - Real-time **Chart.js** data visualizations: Category Distribution (Doughnut), 7-Day Hospital Generation Trend (Line), and Department Breakdown (Bar).
   - KPI metric counters: Total Waste (kg), Today's Generation (kg), Pending Verifications, Dispatched Waste (kg).
5. **Hospital Waste Ledger & Audit Trail**:
   - Full CRUD ledger with electronic tracking codes (`BMW-YYYYMMDD-XXXXXX`).
   - Lifecycle tracking: `GENERATED` $\rightarrow$ `STORED` $\rightarrow$ `DISPATCHED`.
   - Manifest numbers and transport carrier tracking.
   - One-click printable barcode tracking slip (`window.print()`).
6. **Regulatory Compliance Reporting**:
   - Filterable date-range and departmental reporting.
   - **CSV Export**: Audit-ready CSV with summary totals and legal disclaimers.
   - **PDF Export**: Institutional compliance certificate generated via **ReportLab** complete with supervisory signature blocks and PCB registration identifiers.
7. **Role-Based Access Control (RBAC)**:
   - **ADMIN**: Configuration of BMW categories, hospital department registry, user roster management, and model feedback inspection.
   - **STAFF**: Clinical intake, image scanning, verification, and ledger logging.

---

## 3. Technology Stack

- **Backend**: Python 3.11+, Flask 3.0, Flask-SQLAlchemy, Flask-Login, Werkzeug
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, JavaScript (ES6)
- **Visual Analytics**: Chart.js 4.4
- **AI & Vision**: MobileNetV2 architecture (TensorFlow/Keras supported) with transparent Educational Heuristic Engine
- **Report Generation**: ReportLab (PDF) and Python Standard Library (CSV)
- **Automated Testing**: Pytest 8.2, Pytest-Flask

---

## 4. Project Directory Structure

```
ai_medical_waste_system/
├── app/
│   ├── __init__.py                 # Flask application factory, error handlers, logging
│   ├── extensions.py               # SQLAlchemy and LoginManager instances
│   ├── models/                     # Database entities
│   │   ├── __init__.py
│   │   ├── user.py                 # User account model (Admin & Staff roles)
│   │   ├── department.py           # Hospital clinical units (ICU, OT, ER, etc.)
│   │   ├── category.py             # Configurable BMW categories & disposal protocols
│   │   ├── waste_record.py         # Primary waste ledger with tracking codes
│   │   └── feedback.py             # AI prediction correction audit log
│   ├── routes/                     # Modular Flask Blueprints
│   │   ├── __init__.py
│   │   ├── auth.py                 # Login, logout, profile, and demo quick-sign-in
│   │   ├── dashboard.py            # KPI dashboard and Chart.js JSON API
│   │   ├── waste.py                # Waste record CRUD, search, filter, and slip view
│   │   ├── ai.py                   # Image upload, validation, scan API, verification commit
│   │   ├── reports.py              # CSV and PDF compliance report generators
│   │   └── admin.py                # Category, department, user, and feedback management
│   ├── services/                   # Business logic and AI pipelines
│   │   ├── __init__.py
│   │   ├── ai_service.py           # MobileNetV2 classifier + demo heuristic fallback
│   │   ├── stats_service.py        # Analytics aggregation engine for Chart.js
│   │   └── report_service.py       # ReportLab PDF generator and CSV exporter
│   ├── static/
│   │   ├── css/custom.css          # Healthcare UI theme and BMW color badges
│   │   └── js/
│   │       ├── app.js              # Global utilities and alert auto-dismissal
│   │       ├── classifier.js       # Drag-and-drop scanner and verification controller
│   │       └── charts.js           # Chart.js initialization and live fetch
│   ├── templates/                  # Jinja2 templates (Bootstrap 5)
│   │   ├── base.html               # Master layout with top disclaimer and navbar
│   │   ├── errors/                 # 400, 403, 404, 500 healthcare error pages
│   │   ├── auth/                   # login.html, profile.html
│   │   ├── dashboard/              # index.html
│   │   ├── waste/                  # list.html, create.html, edit.html, view.html
│   │   ├── ai/                     # classify.html
│   │   ├── reports/                # index.html
│   │   └── admin/                  # categories.html, departments.html, users.html, feedback.html
│   └── utils/
│       ├── __init__.py
│       ├── decorators.py           # @admin_required, @staff_required
│       └── validators.py           # File extension, size, and image security validation
├── instance/                       # SQLite database storage (medical_waste.db)
├── uploads/                        # Uploaded waste scans
├── tests/                          # Automated Pytest suite
│   ├── conftest.py                 # Test fixtures and authenticated clients
│   ├── test_auth.py                # Password hashing, login, logout, RBAC
│   ├── test_waste.py               # CRUD operations, status lifecycle, search/filters
│   ├── test_ai.py                  # File upload security, scanner API, confidence logic
│   ├── test_feedback.py            # Prediction override and feedback collection
│   ├── test_reports.py             # CSV export and ReportLab PDF verification
│   └── test_admin.py               # Category, department, and user roster management
├── config.py                       # Development, Testing, and Production configurations
├── run.py                          # Application entry point with auto-seeding
├── seed.py                         # Standalone database seeder with BMW 2016 demo data
├── requirements.txt                # Pinned production dependencies
├── .env.example                    # Environment variables template
├── PROGRESS.md                     # Phase-by-phase implementation checklist
└── README.md                       # Complete documentation
```

---

## 5. Step-by-Step Installation & Execution Guide (Windows)

### Step 1: Open PowerShell
Open Windows PowerShell and navigate to the project directory:
```powershell
cd "C:\Users\Ayush Srivastav\.gemini\antigravity\scratch\ai_medical_waste_system"
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the `.env.example` file to create your local `.env`:
```powershell
copy .env.example .env
```

### Step 5: Initialize Database and Seed Demo Records
Run the seeder to generate tables, demo accounts, hospital departments, and 2016 BMW categories:
```powershell
python seed.py
```

### Step 6: Launch the Application
```powershell
python run.py
```
Open your web browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 6. Demo Accounts & Evaluator Shortcuts

The login page includes **1-Click Quick Demo Sign-In Buttons** for evaluators:

| Role | Username | Email | Password | Privileges |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin@hospital.org` | `Admin@123` | Full access: Categories, Departments, Users, Feedback, Records |
| **Staff** | `staff` | `staff@hospital.org` | `Staff@123` | Clinical intake: AI Scanner, Manual Logging, Slip View, Reports |
| **Officer** | `officer` | `officer@hospital.org` | `Officer@123` | Infection Control Officer: Verification, Audit, Quarantine Review |

---

## 7. Running Automated Tests

Run the complete test suite using **pytest**:
```powershell
python -m pytest tests/ -v
```

To run a specific test module (e.g., AI classification tests):
```powershell
python -m pytest tests/test_ai.py -v
```

---

## 8. College Project Evaluation Highlights

When demonstrating this project for academic viva or review:
1. **Explain the Safety Warning**: Point to the persistent regulatory banner and explain why autonomous AI disposal is illegal under biomedical waste management statutes.
2. **Demonstrate AI Image Analysis**: Open the **AI Smart Scanner**, upload an image (e.g., photo of a syringe or cotton swab), observe the certainty meter, and show how the statutory container type and treatment protocol are automatically displayed.
3. **Show the Human-in-the-Loop Override**: Change the category from the AI recommendation to a different stream, click "Confirm & Log", and then show the evaluator the **AI Feedback Ledger** under Administration to prove continuous retraining data collection.
4. **Showcase Barcode Waste Slips**: Click "Print Waste Slip" on any record to demonstrate the clean printable slip formatted for barcode labelling.
5. **Generate Audit Reports**: Download both the filtered **CSV** and the official **PDF certificate** to demonstrate statutory reporting for State Pollution Control Boards.
