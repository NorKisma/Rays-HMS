from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin
from datetime import datetime

class Category(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    status = db.Column(db.String(20), default='active')

    def __repr__(self):
        return f"<Category {self.name}>"

class Product(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    barcode = db.Column(db.String(100), unique=True, nullable=True)
    description = db.Column(db.Text, nullable=True)
    base_unit = db.Column(db.String(50), default="unit")
    status = db.Column(db.String(20), default='active')
    
    category = db.relationship('Category', backref=db.backref('products', lazy=True))

    def __repr__(self):
        return f"<Product {self.name}>"

class Batch(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'batches'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_number = db.Column(db.String(100), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    unit_cost = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')

    product = db.relationship('Product', backref=db.backref('batches', lazy=True))

    def __repr__(self):
        return f"<Batch {self.batch_number} - Product {self.product_id}>"

class Inventory(db.Model, SoftDeleteMixin, TimestampMixin):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    quantity = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='active')
    
    product = db.relationship('Product', backref=db.backref('inventory', lazy=True))
    batch = db.relationship('Batch', backref=db.backref('inventory_items', lazy=True))

    def __repr__(self):
        return f"<Inventory Product {self.product_id} Qty {self.quantity}>"

class StockLog(db.Model, SoftDeleteMixin, TimestampMixin):
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
    def __repr__(self):
        return f"<StockLog Product {self.product_id} Change {self.change_type}>"
