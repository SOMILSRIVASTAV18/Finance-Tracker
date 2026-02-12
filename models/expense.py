from datetime import datetime
from models import db

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(256))
    date = db.Column(db.Date, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_income = db.Column(db.Boolean, default=False)  # True for income, False for expense
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20))  # 'daily', 'weekly', 'monthly', 'yearly'
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    def __repr__(self):
        return f'<{"Income" if self.is_income else "Expense"} {self.amount}>'
