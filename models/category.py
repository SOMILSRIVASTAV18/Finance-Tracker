from datetime import datetime
from models import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    color = db.Column(db.String(7), default="#3498db")  # Hex color code
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    expenses = db.relationship('Expense', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'
