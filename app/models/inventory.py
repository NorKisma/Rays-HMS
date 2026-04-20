from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin, MultiTenantMixin
from datetime import datetime

class Category(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    status = db.Column(db.String(20), default='active')

class Product(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    barcode = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    base_unit = db.Column(db.String(50), default="unit")
    status = db.Column(db.String(20), default='active')
    
    category = db.relationship('Category', backref=db.backref('products', lazy=True))

class Supplier(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')

class Batch(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_number = db.Column(db.String(100), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    unit_cost = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')

    product = db.relationship('Product', backref=db.backref('batches', lazy=True))

class Inventory(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    quantity = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='active')
    
    product = db.relationship('Product', backref=db.backref('inventory', lazy=True))
    batch = db.relationship('Batch', backref=db.backref('inventory_items', lazy=True))

class PurchaseOrder(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = 'purchase_orders'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_date = db.Column(db.DateTime)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='pending') # pending, received, cancelled
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    supplier = db.relationship('Supplier', backref=db.backref('purchase_orders', lazy=True))
    user = db.relationship('User', backref=db.backref('purchase_orders', lazy=True))

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)
    line_total = db.Column(db.Float, nullable=False)

    order = db.relationship('PurchaseOrder', backref=db.backref('items', lazy=True))
    product = db.relationship('Product')

class StockLog(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = 'stock_logs'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    change_type = db.Column(db.String(50), nullable=False) # Sale, Purchase, Adjustment
    old_qty = db.Column(db.Float, default=0.0)
    new_qty = db.Column(db.Float, default=0.0)
    difference = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    note = db.Column(db.String(255), nullable=True)

    product = db.relationship('Product', backref=db.backref('stock_logs', lazy=True))
