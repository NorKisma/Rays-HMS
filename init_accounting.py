
from app import create_app, db
from app.models.accounting import Account

def init_accounting():
    app = create_app()
    with app.app_context():
        # Create Tables
        db.create_all()
        print("✓ Accounting tables created/verified.")
        
        # Default Chart of Accounts
        # Code structure:
        # 1000-1999: Assets
        # 2000-2999: Liabilities
        # 3000-3999: Equity
        # 4000-4999: Revenue
        # 5000-5999: Expenses
        
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
            {'code': '3000', 'name': 'Owner\'s Equity', 'type': 'Equity'},
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
        
        print("Initializing Chart of Accounts...")
        count = 0
        for data in default_accounts:
            existing = Account.query.filter_by(code=data['code']).first()
            if not existing:
                account = Account(
                    code=data['code'],
                    name=data['name'],
                    type=data['type'],
                    description=f"Standard {data['name']} account"
                )
                db.session.add(account)
                count += 1
                
        db.session.commit()
        print(f"✓ Added {count} new accounts to the Chart of Accounts.")

if __name__ == "__main__":
    init_accounting()
