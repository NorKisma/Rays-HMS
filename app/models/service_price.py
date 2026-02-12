from app.extensions import db
from datetime import datetime

class ServicePrice(db.Model):
    """Model for storing configurable service prices"""
    __tablename__ = 'service_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), unique=True, nullable=False)
    service_name_so = db.Column(db.String(100))  # Somali translation
    price = db.Column(db.Numeric(10, 2), default=0.00)
    icon = db.Column(db.String(50), default='fa-cog')  # FontAwesome icon class
    color = db.Column(db.String(100), default='#3b82f6')  # Gradient start color
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ServicePrice {self.service_name}: ${self.price}>'
    
    @classmethod
    def get_price(cls, service_name):
        """Get price for a specific service"""
        service = cls.query.filter_by(service_name=service_name, is_active=True).first()
        return float(service.price) if service else 0.00
    
    @classmethod
    def get_all_active(cls):
        """Get all active service prices"""
        return cls.query.filter_by(is_active=True).all()
    
    @classmethod
    def get_prices_dict(cls):
        """Get dictionary of service names to prices"""
        services = cls.query.filter_by(is_active=True).all()
        return {s.service_name: float(s.price) for s in services}
