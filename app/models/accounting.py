
from datetime import datetime
from app.extensions import db
from app.models.user import TimestampMixin, SoftDeleteMixin

class Account(db.Model, TimestampMixin, SoftDeleteMixin):
    """
    Chart of Accounts
    Types: Asset, Liability, Equity, Revenue, Expense
    """
    __tablename__ = "accounts"
    
    ACCOUNT_TYPES = [
        ('Asset', 'Asset'),
        ('Liability', 'Liability'),
        ('Equity', 'Equity'),
        ('Revenue', 'Revenue'),
        ('Expense', 'Expense')
    ]

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    journal_items = db.relationship('JournalItem', backref='account', lazy=True)

    def __repr__(self):
        return f"<Account {self.code} - {self.name}>"

class JournalEntry(db.Model, TimestampMixin, SoftDeleteMixin):
    """
    Header for a financial transaction (Double Entry)
    """
    __tablename__ = "journal_entries"
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    reference = db.Column(db.String(100)) # e.g. INV-001, PAY-002
    description = db.Column(db.String(255), nullable=False) # Narration
    status = db.Column(db.String(20), default='Posted', nullable=False) # Draft, Posted
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationship
    items = db.relationship('JournalItem', backref='journal_entry', cascade='all, delete-orphan', lazy=True)
    user = db.relationship('User', backref='journal_entries')

    @property
    def total_debit(self):
        return sum(item.debit for item in self.items)
    
    @property
    def total_credit(self):
        return sum(item.credit for item in self.items)

    def __repr__(self):
        return f"<JournalEntry {self.id} - {self.date}>"

class JournalItem(db.Model):
    """
    Line items for a journal entry (Debits and Credits)
    """
    __tablename__ = "journal_items"
    
    id = db.Column(db.Integer, primary_key=True)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    description = db.Column(db.String(255)) # Line item description (optional)
    
    debit = db.Column(db.Numeric(12, 2), default=0.00)
    credit = db.Column(db.Numeric(12, 2), default=0.00)
    
    def __repr__(self):
        return f"<JournalItem {self.account.name} Dr:{self.debit} Cr:{self.credit}>"

class Expense(db.Model, TimestampMixin, SoftDeleteMixin):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    category = db.Column(db.String(50)) # Rent, Salary, Supplies, Utilities
    date = db.Column(db.Date, default=datetime.utcnow)
    
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id')) # Link to Expense Account
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    staff = db.relationship('User')
    account = db.relationship('Account')

    def __repr__(self):
        return f"<Expense {self.category} - {self.amount}>"
