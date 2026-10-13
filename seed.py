import os
import sys
from datetime import datetime, timedelta
import random

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.department import Department
from app.models.category import WasteCategory
from app.models.waste_record import WasteRecord
from app.models.feedback import PredictionFeedback

def seed_database():
    """Populate database with institutional BMW 2016 rules, departments, users, and realistic logs."""
    print("Initializing database tables...")
    db.create_all()

    # 1. Seed Users
    users_data = [
        {
            "username": "admin",
            "email": "admin@hospital.org",
            "password": "Admin@123",
            "full_name": "Dr. Rajesh Sharma (Medical Superintendent)",
            "role": User.ROLE_ADMIN
        },
        {
            "username": "staff",
            "email": "staff@hospital.org",
            "password": "Staff@123",
            "full_name": "Nurse Sunita Rao (ICU Ward In-Charge)",
            "role": User.ROLE_STAFF
        },
        {
            "username": "officer",
            "email": "officer@hospital.org",
            "password": "Officer@123",
            "full_name": "Dr. Ananya Sen (Infection Control Officer)",
            "role": User.ROLE_ADMIN
        }
    ]

    user_map = {}
    for u in users_data:
        existing = User.query.filter_by(username=u["username"]).first()
        if not existing:
            user = User(
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                role=u["role"]
            )
            user.set_password(u["password"])
            db.session.add(user)
            db.session.flush()
            user_map[u["username"]] = user
            print(f"Created user: {u['username']} [{u['role']}]")
        else:
            user_map[u["username"]] = existing

    # 2. Seed Departments
    departments_data = [
        {"code": "ICU", "name": "Intensive Care Unit", "floor": "Level 3 - Critical Wing", "contact": "Dr. V. Gupta"},
        {"code": "OT", "name": "Operation Theatre Complex", "floor": "Level 2 - Surgical Block", "contact": "Dr. R. Kapoor"},
        {"code": "ER", "name": "Emergency & Trauma Care", "floor": "Ground Floor - Bay A", "contact": "Dr. S. Nair"},
        {"code": "GEN", "name": "General Medical Ward", "floor": "Level 4 - Inpatient", "contact": "Nurse M. Das"},
        {"code": "PATH", "name": "Pathology & Microbiology Lab", "floor": "Level 1 - Diagnostics", "contact": "Dr. K. Verma"},
        {"code": "RAD", "name": "Radiology & Imaging", "floor": "Basement 1", "contact": "Dr. P. Joshi"},
        {"code": "OPD", "name": "Outpatient Polyclinic", "floor": "Ground Floor - Annex", "contact": "Dr. H. Mehra"}
    ]

    dept_map = {}
    for d in departments_data:
        existing = Department.query.filter_by(code=d["code"]).first()
        if not existing:
            dept = Department(
                code=d["code"],
                name=d["name"],
                floor_location=d["floor"],
                contact_person=d["contact"]
            )
            db.session.add(dept)
            db.session.flush()
            dept_map[d["code"]] = dept
            print(f"Created department: {d['code']} ({d['name']})")
        else:
            dept_map[d["code"]] = existing

    # 3. Seed Configurable Waste Categories (Indian BMW Rules 2016)
    categories_data = [
        {
            "code": "YELLOW",
            "name": "Infectious & Anatomical Waste",
            "bin_color_name": "Yellow",
            "bin_color_hex": "#ffc107",
            "badge_class": "bg-warning text-dark",
            "container_type": "Non-chlorinated yellow plastic bags (Barcode tagged)",
            "treatment_method": "Incineration or Plasma Pyrolysis / Deep Burial as per CPCB standards",
            "permitted_items": "Human tissues, organs, soiled cotton, plaster casts, blood bags, expired pharmaceutical drugs, cytotoxic items",
            "prohibited_items": "Needles, scalpels, recyclable plastic bottles, municipal food wrappers",
            "storage_instructions": "Maximum allowable on-site storage: 48 hours. Temperature controlled if > 24 hours."
        },
        {
            "code": "RED",
            "name": "Contaminated Recyclable Plastics",
            "bin_color_name": "Red",
            "bin_color_hex": "#dc3545",
            "badge_class": "bg-danger text-white",
            "container_type": "Non-chlorinated red plastic bags / containers",
            "treatment_method": "Autoclaving or Microwaving followed by shredding and registered plastic recycling",
            "permitted_items": "Disposable IV tubing, catheter bags, intravenous bottles, syringes without needles, surgical gloves, urine bags",
            "prohibited_items": "Sharps with needles, glass ampoules, soiled dressings, anatomical remains",
            "storage_instructions": "Drain fluids before bagging. Double-tie bags and weigh before dispatch."
        },
        {
            "code": "WHITE",
            "name": "Waste Sharps including Metals",
            "bin_color_name": "White / Translucent",
            "bin_color_hex": "#e2e8f0",
            "badge_class": "bg-light text-dark border border-secondary",
            "container_type": "Puncture-proof, tamper-proof, leak-proof translucent rigid box",
            "treatment_method": "Autoclaving or Dry Heat Sterilization followed by shredding / encapsulation",
            "permitted_items": "Contaminated sharps, hypodermic needles, scalpels, blades, fixed needles, trocars",
            "prohibited_items": "Plastic tubing, soft dressings, glass bottles, general trash",
            "storage_instructions": "Seal container when 3/4th full. Never bend or recap needles manually."
        },
        {
            "code": "BLUE",
            "name": "Glassware & Metallic Implants",
            "bin_color_name": "Blue",
            "bin_color_hex": "#0d6efd",
            "badge_class": "bg-primary text-white",
            "container_type": "Puncture-proof and leak-proof cardboard box / plastic box with blue marking",
            "treatment_method": "Disinfection with sodium hypochlorite (1-2%) or autoclaving followed by recycling",
            "permitted_items": "Broken medicine vials, glass ampoules, antibiotic bottles, orthopedic metallic body implants",
            "prohibited_items": "Sharps with needles, soft dressings, cytotoxic vials, general plastic",
            "storage_instructions": "Cushion glass containers to avoid in-transit shattering."
        },
        {
            "code": "GENERAL",
            "name": "General Non-Infectious Waste",
            "bin_color_name": "Black / Green",
            "bin_color_hex": "#212529",
            "badge_class": "bg-dark text-white",
            "container_type": "Standard municipal dustbin with black/green liner",
            "treatment_method": "Municipal solid waste collection / Composting for organic fractions",
            "permitted_items": "Office paper, sterile wrappers, clean cardboard, fruit peels, empty drink bottles",
            "prohibited_items": "Any item in contact with blood or body fluids, chemicals, sharps",
            "storage_instructions": "Segregate dry and wet municipal waste at source."
        },
        {
            "code": "UNKNOWN",
            "name": "Unknown / Needs Manual Review",
            "bin_color_name": "Grey / Orange",
            "bin_color_hex": "#6c757d",
            "badge_class": "bg-secondary text-white",
            "container_type": "Isolated quarantine holding bin with warning label",
            "treatment_method": "Mandatory manual safety inspection by Infection Control Officer prior to routing",
            "permitted_items": "Unidentified chemical residues, damaged unlabelled vials, mixed emergency waste",
            "prohibited_items": "Do not mix with general municipal waste",
            "storage_instructions": "Hold under supervisor lock until formal inspection is logged."
        }
    ]

    cat_map = {}
    for c in categories_data:
        existing = WasteCategory.query.filter_by(code=c["code"]).first()
        if not existing:
            cat = WasteCategory(
                code=c["code"],
                name=c["name"],
                bin_color_name=c["bin_color_name"],
                bin_color_hex=c["bin_color_hex"],
                badge_class=c["badge_class"],
                container_type=c["container_type"],
                treatment_method=c["treatment_method"],
                permitted_items=c["permitted_items"],
                prohibited_items=c["prohibited_items"],
                storage_instructions=c["storage_instructions"]
            )
            db.session.add(cat)
            db.session.flush()
            cat_map[c["code"]] = cat
            print(f"Created category: {c['code']} ({c['name']})")
        else:
            cat_map[c["code"]] = existing

    db.session.commit()

    # 4. Seed Realistic Historical Waste Records (if table is sparse)
    if WasteRecord.query.count() < 10:
        print("Populating realistic hospital waste records across past 7 days...")
        now = datetime.utcnow()
        sample_items = [
            ("YELLOW", "ICU", "Used dressing cotton and surgical gauze", 3.4, True, "Routine morning dressing change"),
            ("RED", "ICU", "Discarded dialysis tubing and saline bottles", 6.8, True, "Disinfected before bagging"),
            ("WHITE", "OT", "Surgical scalpel blades and suture needles", 0.9, True, "Deposited in puncture-proof box"),
            ("BLUE", "GEN", "Glass vials of antibiotic Ceftriaxone", 2.1, True, "Rinsed in sodium hypochlorite"),
            ("YELLOW", "OT", "Extracted anatomical tissue & biopsy remnants", 4.2, True, "Pathology specimen released"),
            ("RED", "ER", "Latex examination gloves and empty IV bags", 5.5, True, "Trauma bay resuscitation kit"),
            ("GENERAL", "OPD", "Cardboard packaging boxes & paper towels", 7.2, True, "Dry municipal waste"),
            ("YELLOW", "PATH", "Used microbiological culture plates", 2.7, True, "Autoclaved prior to yellow binning"),
            ("WHITE", "ER", "Intravenous cannula needles and lancets", 1.2, True, "Sharp needle burner used"),
            ("RED", "GEN", "Catheter bags and disposable suction tubes", 4.8, False, "Awaiting supervisor verification"),
            ("BLUE", "OT", "Broken anesthetic glass ampoules", 1.8, True, "Secured in cardboard bin"),
            ("UNKNOWN", "ER", "Unlabeled chemical reagent spill residue", 1.5, False, "Flagged for Infection Officer inspection")
        ]

        for i, (cat_code, dept_code, desc, qty, verified, remarks) in enumerate(sample_items):
            day_offset = (i % 7)
            record_time = now - timedelta(days=day_offset, hours=random.randint(1, 10), minutes=random.randint(5, 50))
            
            # Status distribution
            if day_offset > 3:
                status = WasteRecord.STATUS_DISPATCHED
                manifest = f"MNF-2026-DL-{1000 + i}"
                carrier = "BioClean Environmental Services Pvt. Ltd. (Truck DL-1L-4421)"
            elif day_offset > 1:
                status = WasteRecord.STATUS_STORED
                manifest = None
                carrier = None
            else:
                status = WasteRecord.STATUS_GENERATED
                manifest = None
                carrier = None

            rec = WasteRecord(
                tracking_code=f"BMW-{record_time.strftime('%Y%m%d')}-{100 + i}",
                department_id=dept_map[dept_code].id,
                category_id=cat_map[cat_code].id,
                logged_by_id=user_map["staff"].id,
                verified_by_id=user_map["officer"].id if verified else None,
                quantity_kg=qty,
                item_description=desc,
                ai_suggested_category=cat_code if cat_code != "UNKNOWN" else "RED",
                ai_confidence=0.88 if cat_code != "UNKNOWN" else 0.42,
                staff_verified=verified,
                disposal_status=status,
                dispatch_manifest_no=manifest,
                dispatch_carrier=carrier,
                remarks=remarks,
                created_at=record_time,
                updated_at=record_time
            )
            db.session.add(rec)
            db.session.flush()

            # Add feedback record for the overridden item
            if cat_code == "UNKNOWN":
                fb = PredictionFeedback(
                    waste_record_id=rec.id,
                    user_id=user_map["officer"].id,
                    image_filename=None,
                    predicted_category="RED",
                    predicted_confidence=0.42,
                    actual_category="UNKNOWN",
                    correction_reason="Low AI confidence. Chemical residue detected requiring safety protocol inspection.",
                    created_at=record_time
                )
                db.session.add(fb)

        db.session.commit()
        print("Seeded realistic historical records and feedback log successfully.")

    print("\nDatabase initialization complete!")
    print("Demo Accounts:")
    print("  1. Admin:   admin@hospital.org / Admin@123   (or username: admin)")
    print("  2. Staff:   staff@hospital.org / Staff@123   (or username: staff)")
    print("  3. Officer: officer@hospital.org / Officer@123 (or username: officer)")

if __name__ == "__main__":
    app = create_app("development")
    with app.app_context():
        seed_database()
