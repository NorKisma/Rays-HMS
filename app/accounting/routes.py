
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Account, JournalEntry, JournalItem
from . import bp
from .forms import AccountForm, JournalEntryForm
from sqlalchemy import func
from datetime import datetime

@bp.route('/')
@login_required
def dashboard():
    """Accounting Dashboard"""
    # Quick Stats
    accounts_count = Account.query.count()
    entries_count = JournalEntry.query.count()
    
    recent_entries = JournalEntry.query.order_by(JournalEntry.date.desc()).limit(5).all()
    
    return render_template('accounting/dashboard.html', 
                           accounts_count=accounts_count,
                           entries_count=entries_count,
                           recent_entries=recent_entries)

# ---------------------------------------------------------
# Chart of Accounts
# ---------------------------------------------------------
@bp.route('/accounts')
@login_required
def chart_of_accounts():
    accounts = Account.query.order_by(Account.code).all()
    # Group by type for display
    grouped = {}
    for acc in accounts:
        if acc.type not in grouped:
            grouped[acc.type] = []
        grouped[acc.type].append(acc)
        
    return render_template('accounting/chart_of_accounts.html', grouped_accounts=grouped)

@bp.route('/accounts/add', methods=['GET', 'POST'])
@login_required
def add_account():
    form = AccountForm()
    if form.validate_on_submit():
        if Account.query.filter_by(code=form.code.data).first():
            flash('Account code already exists.', 'danger')
        else:
            acc = Account(
                code=form.code.data,
                name=form.name.data,
                type=form.type.data,
                description=form.description.data
            )
            db.session.add(acc)
            db.session.commit()
            flash('Account added successfully.', 'success')
            return redirect(url_for('accounting.chart_of_accounts'))
    return render_template('accounting/add_account.html', form=form)

# ---------------------------------------------------------
# Journal Entries
# ---------------------------------------------------------
@bp.route('/journal')
@login_required
def journal_entries():
    entries = JournalEntry.query.order_by(JournalEntry.date.desc(), JournalEntry.id.desc()).all()
    return render_template('accounting/journal_entries.html', entries=entries)

@bp.route('/journal/create', methods=['GET', 'POST'])
@login_required
def create_journal_entry():
    form = JournalEntryForm()
    accounts = Account.query.order_by(Account.code).all()
    
    if request.method == 'POST':
        # Custom validation for dynamic rows
        # We expect form item_account_[], item_debit_[], item_credit_[]
        
        try:
            date_str = request.form.get('date')
            ref = request.form.get('reference')
            desc = request.form.get('description')
            
            entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Create Header
            entry = JournalEntry(
                date=entry_date,
                reference=ref,
                description=desc,
                user_id=current_user.id
            )
            
            total_dr = 0
            total_cr = 0
            
            # Iterate through lists
            account_ids = request.form.getlist('item_account[]')
            debits = request.form.getlist('item_debit[]')
            credits = request.form.getlist('item_credit[]')
            # descs = request.form.getlist('item_desc[]') 
            
            if not account_ids:
                raise ValueError("No journal items provided.")

            for i in range(len(account_ids)):
                acc_id = int(account_ids[i])
                dr = float(debits[i]) if debits[i] else 0.0
                cr = float(credits[i]) if credits[i] else 0.0
                
                if dr == 0 and cr == 0:
                    continue
                    
                total_dr += dr
                total_cr += cr
                
                item = JournalItem(
                    account_id=acc_id,
                    debit=dr,
                    credit=cr
                )
                entry.items.append(item)
            
            # Validate Balance
            if abs(total_dr - total_cr) > 0.01:
                flash(f'Entry not balanced! Debit: {total_dr}, Credit: {total_cr}', 'danger')
                return render_template('accounting/create_journal_entry.html', form=form, accounts=accounts)
                
            db.session.add(entry)
            db.session.commit()
            flash('Journal Enty Posted Successfully.', 'success')
            return redirect(url_for('accounting.journal_entries'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating entry: {str(e)}', 'danger')
            return render_template('accounting/create_journal_entry.html', form=form, accounts=accounts)

    return render_template('accounting/create_journal_entry.html', form=form, accounts=accounts)

# ---------------------------------------------------------
# Reports
# ---------------------------------------------------------
@bp.route('/reports/balance-sheet')
@login_required
def balance_sheet():
    # Assets
    assets = db.session.query(Account, func.sum(JournalItem.debit - JournalItem.credit).label('balance'))\
        .join(JournalItem).filter(Account.type == 'Asset').group_by(Account.id).all()
    
    # Liabilities (Credit normal: Cr - Dr)
    liabilities = db.session.query(Account, func.sum(JournalItem.credit - JournalItem.debit).label('balance'))\
        .join(JournalItem).filter(Account.type == 'Liability').group_by(Account.id).all()
        
    # Equity (Credit normal: Cr - Dr)
    equity = db.session.query(Account, func.sum(JournalItem.credit - JournalItem.debit).label('balance'))\
        .join(JournalItem).filter(Account.type == 'Equity').group_by(Account.id).all()

    # Calculate Totals
    total_assets = sum(b for a, b in assets if b)
    total_liabilities = sum(b for a, b in liabilities if b)
    total_equity = sum(b for a, b in equity if b)
    
    # Calculate Current Net Income (Revenue - Expense) to add to Equity temporarily
    revenue_total = db.session.query(func.sum(JournalItem.credit - JournalItem.debit))\
        .join(Account).filter(Account.type == 'Revenue').scalar() or 0
        
    expense_total = db.session.query(func.sum(JournalItem.debit - JournalItem.credit))\
        .join(Account).filter(Account.type == 'Expense').scalar() or 0
        
    net_income = revenue_total - expense_total
    
    return render_template('accounting/balance_sheet.html', 
                           assets=assets, liabilities=liabilities, equity=equity,
                           total_assets=total_assets, total_liabilities=total_liabilities,
                           total_equity=total_equity, net_income=net_income)

@bp.route('/reports/profit-loss')
@login_required
def profit_loss():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Revenue (Cr - Dr)
    revenue_q = db.session.query(Account, func.sum(JournalItem.credit - JournalItem.debit).label('balance'))\
        .join(JournalItem).join(JournalEntry).filter(Account.type == 'Revenue')
        
    # Expenses (Dr - Cr)
    expense_q = db.session.query(Account, func.sum(JournalItem.debit - JournalItem.credit).label('balance'))\
        .join(JournalItem).join(JournalEntry).filter(Account.type == 'Expense')
        
    if start_date:
        revenue_q = revenue_q.filter(JournalEntry.date >= start_date)
        expense_q = expense_q.filter(JournalEntry.date >= start_date)
        
    if end_date:
        revenue_q = revenue_q.filter(JournalEntry.date <= end_date)
        expense_q = expense_q.filter(JournalEntry.date <= end_date)
        
    revenues = revenue_q.group_by(Account.id).all()
    expenses = expense_q.group_by(Account.id).all()
    
    total_revenue = sum(b for a, b in revenues if b)
    total_expense = sum(b for a, b in expenses if b)
    net_profit = total_revenue - total_expense
    
    return render_template('accounting/profit_loss.html',
                           revenues=revenues, expenses=expenses,
                           total_revenue=total_revenue, total_expense=total_expense,
                           net_profit=net_profit)

# ---------------------------------------------------------
# Expense Management
# ---------------------------------------------------------
from app.models.accounting import Expense

@bp.route('/expenses')
@login_required
def list_expenses():
    expenses = Expense.query.filter_by(is_deleted=False).order_by(Expense.date.desc()).all()
    categories = db.session.query(Expense.category).distinct().all()
    return render_template('accounting/expenses.html', 
                           expenses=expenses, 
                           categories=[c[0] for c in categories],
                           today_date=datetime.utcnow().date().isoformat())

@bp.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    desc = request.form.get('description')
    amount = float(request.form.get('amount'))
    category = request.form.get('category')
    date_str = request.form.get('date')
    
    expense = Expense(
        description=desc,
        amount=amount,
        category=category,
        date=datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date(),
        recorded_by=current_user.id
    )
    
    db.session.add(expense)
    db.session.commit()
    flash('Expense recorded successfully.', 'success')
    return redirect(url_for('accounting.list_expenses'))
