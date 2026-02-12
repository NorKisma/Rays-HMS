from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin
from datetime import datetime

class Sale(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True) # Optional link to patient
    customer_name = db.Column(db.String(100), nullable=True) # For walk-ins
    total_amount = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    net_total = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    change_amount = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(50), default='Cash') # Cash, Card, Mobile, Mixed
    status = db.Column(db.String(20), default='completed') # completed, returned, cancelled
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Cashier

    customer = db.relationship('Patient', backref=db.backref('sales', lazy=True))
    user = db.relationship('User', backref=db.backref('sales_processed', lazy=True))

    def __repr__(self):
        return f"<Sale {self.invoice_number} Total {self.net_total}>"

class SaleItem(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    sale = db.relationship('Sale', backref=db.backref('items', lazy=True, cascade="all, delete-orphan"))
    product = db.relationship('Product')
    batch = db.relationship('Batch')

    def __repr__(self):
        return f"<SaleItem {self.product_id} Qty {self.quantity}>"
