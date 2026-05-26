import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
from datetime import datetime, date, timedelta
from decimal import Decimal
from werkzeug.security import generate_password_hash

# Add current directory to path
sys.path.append(r"c:\Users\hp\OneDrive\Desktop\Rays-HMS")

from app import create_app, db
from app.models import (
    Hospital, User, Role, Patient, Doctor, Appointment,
    Billing, BillingItem, Category, Product, Batch, Inventory,
    Supplier, Account, Ward, Bed, LabTest, SystemSetting,
    VisitorLog, CallLog
)

def seed_all():
    app = create_app()
    with app.app_context():
        # Ensure database tables exist
        db.create_all()
        print("✓ Database tables verified.")

        # 1. Check if the demo hospital already exists
        existing_hospital = Hospital.query.filter_by(slug="rays-medical-center").first()
        if existing_hospital:
            print("💡 Rays Medical Center already exists! Cleaning up and re-seeding to guarantee fresh data...")
            # We can just use the existing one or delete it, but let's just keep it and proceed
            hospital = existing_hospital
        else:
            # Create Rays Medical Center
            hospital = Hospital(
                name="Rays Medical Center",
                slug="rays-medical-center",
                plan="enterprise",
                subscription_status="active",
                expiry_date=datetime.now() + timedelta(days=365),
                has_pos=True,
                has_pharmacy=True,
                has_clinical=True,
                has_accounting=True,
                has_inventory=True,
                has_lab=True,
                has_ipd=True,
                address="123 Rays Road, Kismayo, Somalia",
                phone="+252 61 555 0001",
                email="info@raysmedical.so",
                website="https://raysmedical.so"
            )
            db.session.add(hospital)
            db.session.flush()
            print(f"🏥 Hospital 'Rays Medical Center' created with ID: {hospital.id}")

        # 2. Setup Chart of Accounts for this hospital
        default_accounts = [
            # Assets
            {'code': '1000', 'name': 'Cash on Hand', 'type': 'Asset'},
            {'code': '1001', 'name': 'Petty Cash', 'type': 'Asset'},
            {'code': '1010', 'name': 'Bank - Main Account', 'type': 'Asset'},
            {'code': '1200', 'name': 'Accounts Receivable', 'type': 'Asset'},
            {'code': '1300', 'name': 'Inventory Asset', 'type': 'Asset'},
            {'code': '1500', 'name': 'Furniture & Fixtures', 'type': 'Asset'},
            {'code': '1510', 'name': 'Medical Equipment', 'type': 'Asset'},
            
            # Liabilities
            {'code': '2000', 'name': 'Accounts Payable', 'type': 'Liability'},
            {'code': '2010', 'name': 'Sales Tax Payable', 'type': 'Liability'},
            {'code': '2020', 'name': 'Salaries Payable', 'type': 'Liability'},
            
            # Equity
            {'code': '3000', 'name': "Owner's Equity", 'type': 'Equity'},
            {'code': '3010', 'name': 'Retained Earnings', 'type': 'Equity'},
            
            # Revenue
            {'code': '4000', 'name': 'Sales Revenue', 'type': 'Revenue'},
            {'code': '4010', 'name': 'Service Revenue (Consultation)', 'type': 'Revenue'},
            {'code': '4020', 'name': 'Lab Test Revenue', 'type': 'Revenue'},
            {'code': '4030', 'name': 'Other Income', 'type': 'Revenue'},
            
            # Expenses
            {'code': '5000', 'name': 'Cost of Goods Sold', 'type': 'Expense'},
            {'code': '5100', 'name': 'Rent Expense', 'type': 'Expense'},
            {'code': '5110', 'name': 'Salaries Expense', 'type': 'Expense'},
            {'code': '5120', 'name': 'Utilities Expense', 'type': 'Expense'},
            {'code': '5130', 'name': 'Office Supplies', 'type': 'Expense'},
            {'code': '5140', 'name': 'Maintenance & Repairs', 'type': 'Expense'},
            {'code': '5150', 'name': 'Depreciation Expense', 'type': 'Expense'},
        ]
        
        coa_count = 0
        for item in default_accounts:
            existing = Account.query.filter_by(code=item['code'], hospital_id=hospital.id).first()
            if not existing:
                account = Account(
                    code=item['code'],
                    name=item['name'],
                    type=item['type'],
                    description=f"Standard {item['name']} account for Rays Medical Center",
                    hospital_id=hospital.id
                )
                db.session.add(account)
                coa_count += 1
        print(f"✓ Added {coa_count} specific accounts to Chart of Accounts for Rays Medical Center.")

        # 3. Create Users for this Hospital
        # Make sure role names exist
        hms_roles = ['Admin', 'Doctor', 'Nurse', 'Receptionist', 'Pharmacist', 'Accountant']
        users_to_create = [
            {'email': 'admin@raysmedical.so', 'name': 'Rays Admin', 'role_name': 'Admin', 'pass': 'admin123'},
            {'email': 'doctor@raysmedical.so', 'name': 'Dr. Ahmed Omar', 'role_name': 'Doctor', 'pass': 'doctor123'},
            {'email': 'nurse@raysmedical.so', 'name': 'Nurse Halima', 'role_name': 'Nurse', 'pass': 'nurse123'},
            {'email': 'receptionist@raysmedical.so', 'name': 'Receptionist Maryan', 'role_name': 'Receptionist', 'pass': 'receptionist123'},
            {'email': 'pharmacist@raysmedical.so', 'name': 'Pharmacist Ali', 'role_name': 'Pharmacist', 'pass': 'pharmacist123'},
            {'email': 'accountant@raysmedical.so', 'name': 'Accountant Farah', 'role_name': 'Accountant', 'pass': 'accountant123'},
        ]

        for u_data in users_to_create:
            existing_user = User.query.filter_by(email=u_data['email']).first()
            if not existing_user:
                role = Role.query.filter_by(name=u_data['role_name']).first()
                if not role:
                    role = Role(name=u_data['role_name'], description=f"{u_data['role_name']} Role")
                    db.session.add(role)
                    db.session.flush()
                
                u = User(
                    name=u_data['name'],
                    email=u_data['email'],
                    password_hash=generate_password_hash(u_data['pass'], method='pbkdf2:sha256'),
                    is_active=True,
                    role_id=role.id,
                    hospital_id=hospital.id
                )
                db.session.add(u)
                print(f"👤 Added User: {u_data['email']} (Role: {u_data['role_name']})")
            else:
                print(f"👤 User {u_data['email']} already exists.")

        # 4. Create Doctor Records
        dr_role = User.query.filter_by(email='doctor@raysmedical.so').first()
        doc1 = Doctor.query.filter_by(email='doctor@raysmedical.so', hospital_id=hospital.id).first()
        if not doc1:
            doc1 = Doctor(
                license_number="LIC-48903",
                first_name="Ahmed",
                last_name="Omar",
                specialization="General Medicine",
                qualification="MD, MMed (Internal Medicine)",
                experience_years=10,
                phone="+252 61 511 2233",
                email="doctor@raysmedical.so",
                consultation_fee=15.00,
                availability_status="available",
                hospital_id=hospital.id
            )
            db.session.add(doc1)
            print("👨‍⚕️ Added Doctor: Dr. Ahmed Omar")
            
        doc2 = Doctor.query.filter_by(email="fatuma.ali@raysmedical.so", hospital_id=hospital.id).first()
        if not doc2:
            doc2 = Doctor(
                license_number="LIC-89302",
                first_name="Fatuma",
                last_name="Ali",
                specialization="Pediatrics",
                qualification="MD, Pediatrician Specialist",
                experience_years=8,
                phone="+252 61 544 3322",
                email="fatuma.ali@raysmedical.so",
                consultation_fee=20.00,
                availability_status="available",
                hospital_id=hospital.id
            )
            db.session.add(doc2)
            print("👨‍⚕️ Added Doctor: Dr. Fatuma Ali")

        # 5. Create Lab Tests
        lab_tests = [
            {'name': 'Complete Blood Count', 'code': 'CBC', 'category': 'Hematology', 'price': 10.00},
            {'name': 'Urinalysis', 'code': 'UA', 'category': 'Chemistry', 'price': 5.00},
            {'name': 'Malaria Blood Smear', 'code': 'MBS', 'category': 'Microbiology', 'price': 8.00},
            {'name': 'Fasting Blood Sugar', 'code': 'FBS', 'category': 'Chemistry', 'price': 6.00},
            {'name': 'Lipid Profile', 'code': 'LP', 'category': 'Chemistry', 'price': 15.00},
        ]
        for lt in lab_tests:
            existing = LabTest.query.filter_by(code=lt['code'], hospital_id=hospital.id).first()
            if not existing:
                lab = LabTest(
                    name=lt['name'],
                    code=lt['code'],
                    category=lt['category'],
                    price=Decimal(str(lt['price'])),
                    hospital_id=hospital.id
                )
                db.session.add(lab)
                print(f"🔬 Added Lab Test: {lt['name']}")

        # 6. Create Wards and Beds
        ward1 = Ward.query.filter_by(name="General Ward A").first()
        if not ward1:
            ward1 = Ward(
                name="General Ward A",
                ward_type="General",
                capacity=5,
                floor="Ground Floor",
                status="active"
            )
            db.session.add(ward1)
            db.session.flush()
            print("🏥 Added Ward: General Ward A")
            
            for i in range(1, 6):
                bed = Bed(
                    ward_id=ward1.id,
                    bed_number=f"GW-A{i}",
                    status="available"
                )
                db.session.add(bed)
                
        ward2 = Ward.query.filter_by(name="ICU Ward B").first()
        if not ward2:
            ward2 = Ward(
                name="ICU Ward B",
                ward_type="ICU",
                capacity=2,
                floor="First Floor",
                status="active"
            )
            db.session.add(ward2)
            db.session.flush()
            print("🏥 Added Ward: ICU Ward B")
            
            for i in range(1, 3):
                bed = Bed(
                    ward_id=ward2.id,
                    bed_number=f"ICU-B{i}",
                    status="available"
                )
                db.session.add(bed)

        # 7. Create Inventory Suppliers, Categories, Products, Batches, Inventory
        sup1 = Supplier.query.filter_by(name="Mogadishu Pharma Ltd", hospital_id=hospital.id).first()
        if not sup1:
            sup1 = Supplier(
                name="Mogadishu Pharma Ltd",
                contact_person="Bashir Yusuf",
                phone="+252 61 700 8090",
                email="bashir@mogadishupharma.so",
                address="Via Liberia, Mogadishu, Somalia",
                status="active",
                hospital_id=hospital.id
            )
            db.session.add(sup1)
            print("📦 Added Supplier: Mogadishu Pharma Ltd")

        cat1 = Category.query.filter_by(name="Antibiotics", hospital_id=hospital.id).first()
        if not cat1:
            cat1 = Category(name="Antibiotics", description="Antibacterial and antibiotic drugs", status="active", hospital_id=hospital.id)
            db.session.add(cat1)
            db.session.flush()
            print("📁 Added Category: Antibiotics")

        cat2 = Category.query.filter_by(name="Analgesics", hospital_id=hospital.id).first()
        if not cat2:
            cat2 = Category(name="Analgesics", description="Pain relievers and antipyretics", status="active", hospital_id=hospital.id)
            db.session.add(cat2)
            db.session.flush()
            print("📁 Added Category: Analgesics")

        cat3 = Category.query.filter_by(name="Cardiovascular", hospital_id=hospital.id).first()
        if not cat3:
            cat3 = Category(name="Cardiovascular", description="Heart and circulatory drugs", status="active", hospital_id=hospital.id)
            db.session.add(cat3)
            db.session.flush()
            print("📁 Added Category: Cardiovascular")

        # Products
        prod_data = [
            {'name': 'Amoxicillin 500mg Capsule', 'cat': cat1, 'barcode': '6001234567890', 'desc': 'Broad-spectrum antibiotic', 'unit': 'capsule'},
            {'name': 'Paracetamol 500mg Tablet', 'cat': cat2, 'barcode': '6009876543210', 'desc': 'Pain relief and fever reducer', 'unit': 'tablet'},
            {'name': 'Atorvastatin 20mg Tablet', 'cat': cat3, 'barcode': '6005554443332', 'desc': 'Cholesterol-lowering medication', 'unit': 'tablet'},
        ]

        products = {}
        for p_info in prod_data:
            prod = Product.query.filter_by(name=p_info['name'], hospital_id=hospital.id).first()
            if not prod:
                prod = Product(
                    name=p_info['name'],
                    category_id=p_info['cat'].id if p_info['cat'] else None,
                    barcode=p_info['barcode'],
                    description=p_info['desc'],
                    base_unit=p_info['unit'],
                    status="active",
                    hospital_id=hospital.id
                )
                db.session.add(prod)
                db.session.flush()
                print(f"💊 Added Product: {p_info['name']}")
            products[p_info['name']] = prod

        # Batches & Inventory
        today = date.today()
        batches_data = [
            {
                'product_name': 'Amoxicillin 500mg Capsule',
                'batch_num': 'AMX-2026-001',
                'expiry': today + timedelta(days=200),
                'cost': 0.08,
                'selling': 0.20,
                'qty': 300.0
            },
            {
                'product_name': 'Paracetamol 500mg Tablet',
                'batch_num': 'PAR-2027-042',
                'expiry': today + timedelta(days=400),
                'cost': 0.03,
                'selling': 0.10,
                'qty': 800.0
            },
            {
                'product_name': 'Atorvastatin 20mg Tablet',
                'batch_num': 'ATO-EXP-2026',
                # Expiring in 45 days (should trigger alert)
                'expiry': today + timedelta(days=45),
                'cost': 0.45,
                'selling': 1.00,
                'qty': 150.0
            }
        ]

        for b_info in batches_data:
            prod = products.get(b_info['product_name'])
            if prod:
                existing_batch = Batch.query.filter_by(batch_number=b_info['batch_num'], product_id=prod.id, hospital_id=hospital.id).first()
                if not existing_batch:
                    batch = Batch(
                        product_id=prod.id,
                        batch_number=b_info['batch_num'],
                        expiry_date=b_info['expiry'],
                        unit_cost=b_info['cost'],
                        selling_price=b_info['selling'],
                        status="active",
                        hospital_id=hospital.id
                    )
                    db.session.add(batch)
                    db.session.flush()
                    
                    inv = Inventory(
                        product_id=prod.id,
                        batch_id=batch.id,
                        quantity=b_info['qty'],
                        unit=prod.base_unit,
                        status="active",
                        hospital_id=hospital.id
                    )
                    db.session.add(inv)
                    print(f"📦 Added Batch {b_info['batch_num']} ({b_info['qty']} Qty) for {b_info['product_name']}")

        # 8. Create Patients
        patient_data = [
            {
                'first_name': 'Mohamed', 'last_name': 'Ibrahim', 'dob': date(1988, 3, 2),
                'gender': 'Male', 'blood': 'O+', 'phone': '+252 61 777 0001', 'email': 'mohamed.ibrahim@gmail.com',
                'address': 'Kismayo Central, Somalia', 'pat_id': 'PAT-0001', 'med_hist': 'Mild asthma', 'allergies': 'Penicillin'
            },
            {
                'first_name': 'Halima', 'last_name': 'Farah', 'dob': date(1994, 11, 15),
                'gender': 'Female', 'blood': 'A-', 'phone': '+252 61 888 0002', 'email': 'halima.farah@gmail.com',
                'address': 'Via Roma, Mogadishu, Somalia', 'pat_id': 'PAT-0002', 'med_hist': 'None', 'allergies': 'Sulfa drugs'
            }
        ]

        patients = []
        for p_info in patient_data:
            existing = Patient.query.filter_by(patient_id=p_info['pat_id'], hospital_id=hospital.id).first()
            if not existing:
                p = Patient(
                    patient_id=p_info['pat_id'],
                    first_name=p_info['first_name'],
                    last_name=p_info['last_name'],
                    date_of_birth=p_info['dob'],
                    gender=p_info['gender'],
                    blood_group=p_info['blood'],
                    phone=p_info['phone'],
                    email=p_info['email'],
                    address=p_info['address'],
                    medical_history=p_info['med_hist'],
                    allergies=p_info['allergies'],
                    hospital_id=hospital.id
                )
                db.session.add(p)
                print(f"🩹 Added Patient: {p.full_name}")
                patients.append(p)
            else:
                patients.append(existing)
                print(f"🩹 Patient {existing.full_name} already exists.")

        # 9. Create Settings
        SystemSetting.set("billing.card_fee", "5.00", group="billing", description="Default patient outpatient file card fee")
        SystemSetting.set("billing.currency", "$", group="billing", description="Default system billing currency symbol")
        print("✓ Initialized standard SystemSettings (billing.card_fee, billing.currency)")

        # 10. Create Demo Reception Logs
        admin_user = User.query.filter_by(email='admin@raysmedical.so').first()
        rec_user = User.query.filter_by(email='receptionist@raysmedical.so').first()
        recorded_by_id = rec_user.id if rec_user else (admin_user.id if admin_user else None)
        
        p1 = Patient.query.filter_by(patient_id='PAT-0001', hospital_id=hospital.id).first()
        
        vlog_existing = VisitorLog.query.filter_by(visitor_name="Eng. Hassan Guled", hospital_id=hospital.id).first()
        if not vlog_existing:
            vlog1 = VisitorLog(
                visitor_name="Eng. Hassan Guled",
                phone="+252 61 900 1122",
                purpose="IT Network Maintenance",
                id_type="National ID",
                id_number="N-98302-SO",
                check_in_time=datetime.utcnow() - timedelta(hours=3),
                check_out_time=datetime.utcnow() - timedelta(hours=1),
                temperature="36.6 C",
                recorded_by=recorded_by_id,
                hospital_id=hospital.id
            )
            db.session.add(vlog1)
            
            vlog2 = VisitorLog(
                visitor_name="Sahra Mohamed",
                phone="+252 61 733 4455",
                purpose="Visiting Patient",
                patient_id=p1.id if p1 else None,
                check_in_time=datetime.utcnow() - timedelta(minutes=45),
                temperature="36.8 C",
                recorded_by=recorded_by_id,
                hospital_id=hospital.id
            )
            db.session.add(vlog2)
            print("✓ Added demo visitor logs (IT Technician & Patient Relative)")

        call_existing = CallLog.query.filter_by(caller_name="Dr. Amina Weyrah", hospital_id=hospital.id).first()
        if not call_existing:
            call1 = CallLog(
                caller_name="Dr. Amina Weyrah",
                phone="+252 61 520 8900",
                call_type="Incoming",
                call_category="Inquiry",
                details="Inquired about availability of Pediatric ICU beds for a referral patient.",
                action_taken="Confirmed GW-A5 and ICU-B2 are active. Referred to Dr. Fatuma Ali.",
                recorded_by=recorded_by_id,
                hospital_id=hospital.id
            )
            db.session.add(call1)
            
            call2 = CallLog(
                caller_name="Yasin Sheikh",
                phone="+252 61 666 7777",
                call_type="Incoming",
                call_category="Appointment Booking",
                details="Wants to book a general checkup consultation with Dr. Ahmed Omar tomorrow.",
                action_taken="Scheduled preliminary appointment slot for 10:00 AM.",
                recorded_by=recorded_by_id,
                hospital_id=hospital.id
            )
            db.session.add(call2)
            print("✓ Added demo front desk call logs (Bed Inquiry & Booking Call)")

        db.session.commit()
        print("=" * 60)
        print("🎉 SEEDING DEMO DATA COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"🏨 Tenant URL Slug:  rays-medical-center")
        print(f"👤 Login Username:  admin@raysmedical.so")
        print(f"🔑 Login Password:  admin123")
        print("=" * 60)

if __name__ == "__main__":
    seed_all()
