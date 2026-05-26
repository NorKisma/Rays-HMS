from app.extensions import db
from .user import TimestampMixin, SoftDeleteMixin, MultiTenantMixin

class Billing(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = "billings"
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False) # e.g. INV-0001
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0.0)
    discount = db.Column(db.Numeric(10, 2), default=0.0)
    net_amount = db.Column(db.Numeric(10, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), default=0.0)
    balance_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.String(20), default="unpaid") # unpaid, partially_paid, paid
    payment_method = db.Column(db.String(50)) # cash, card, insurance, bank_transfer
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    
    patient = db.relationship("Patient", backref=db.backref("billings", lazy=True))
    appointment = db.relationship("Appointment", backref=db.backref("billing", uselist=False))
    user = db.relationship("User", backref=db.backref("billings", lazy=True))
    
    def __repr__(self):
        return f"<Billing {self.invoice_number} - {self.payment_status}>"

class BillingItem(db.Model, SoftDeleteMixin, TimestampMixin, MultiTenantMixin):
    __tablename__ = "billing_items"
    id = db.Column(db.Integer, primary_key=True)
    billing_id = db.Column(db.Integer, db.ForeignKey("billings.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    billing = db.relationship("Billing", backref=db.backref("items", lazy=True))
