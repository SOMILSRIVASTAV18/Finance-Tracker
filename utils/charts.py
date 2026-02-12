import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from models.expense import Expense
from models.category import Category
from models import db
import numpy as np
import io
import base64

def generate_expense_pie_chart(user_id, save_path=None):
    """Generate a pie chart of expenses by category"""
    # Get expenses grouped by category
    expenses = Expense.query.filter_by(user_id=user_id, is_income=False).all()
    
    if not expenses:
        return None
    
    # Group expenses by category
    category_totals = {}
    for expense in expenses:
        category_name = expense.category.name if expense.category else "Uncategorized"
        if category_name in category_totals:
            category_totals[category_name] += expense.amount
        else:
            category_totals[category_name] = expense.amount
    
    # Create pie chart
    plt.figure(figsize=(10, 8))
    plt.pie(
        list(category_totals.values()),
        labels=list(category_totals.keys()),
        autopct='%1.1f%%',
        startangle=90,
        shadow=True
    )
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title('Expense Distribution by Category')
    
    if save_path:
        # Save chart to file
        plt.savefig(save_path)
        plt.close()
        return save_path
    else:
        # Return as base64 encoded string for embedding in HTML
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        encoded = base64.b64encode(image_png).decode('utf-8')
        return f"data:image/png;base64,{encoded}"

def generate_monthly_trend_chart(user_id, save_path=None, months=6):
    """Generate a line chart showing expense trends over the last few months"""
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = (datetime.utcnow() - timedelta(days=30*months)).date()
    
    # Get expenses in date range
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()
    
    if not expenses:
        return None
    
    # Create DataFrame from expenses
    data = []
    for expense in expenses:
        data.append({
            'date': expense.date,
            'amount': expense.amount,
            'type': 'Income' if expense.is_income else 'Expense'
        })
    
    df = pd.DataFrame(data)
    
    # Group by month and type
    df['month'] = df['date'].apply(lambda x: x.strftime('%Y-%m'))
    monthly_data = df.groupby(['month', 'type'])['amount'].sum().unstack().fillna(0)
    
    # Ensure both Income and Expense columns exist
    if 'Income' not in monthly_data.columns:
        monthly_data['Income'] = 0
    if 'Expense' not in monthly_data.columns:
        monthly_data['Expense'] = 0
    
    # Sort by month
    monthly_data = monthly_data.sort_index()
    
    # Create line chart
    plt.figure(figsize=(12, 6))
    plt.plot(monthly_data.index, monthly_data['Income'], 'g-', marker='o', label='Income')
    plt.plot(monthly_data.index, monthly_data['Expense'], 'r-', marker='o', label='Expense')
    plt.title('Monthly Income vs Expenses')
    plt.xlabel('Month')
    plt.ylabel('Amount')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        # Save chart to file
        plt.savefig(save_path)
        plt.close()
        return save_path
    else:
        # Return as base64 encoded string for embedding in HTML
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        encoded = base64.b64encode(image_png).decode('utf-8')
        return f"data:image/png;base64,{encoded}"

def generate_budget_comparison_chart(user_id, save_path=None):
    """Generate a bar chart comparing budget vs actual spending by category"""
    # This is a placeholder - in a real app, you'd have a budget model
    # For now, we'll simulate budget data
    
    # Get actual expenses by category
    categories = Category.query.filter_by(user_id=user_id).all()
    
    if not categories:
        return None
    
    # Simulate budget data (in a real app, this would come from a budget model)
    budget_data = {}
    actual_data = {}
    
    for category in categories:
        # Simulate a budget amount (in a real app, this would be user-defined)
        budget_data[category.name] = 1000  # Example budget amount
        
        # Get actual spending for this category
        actual_spending = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.category_id == category.id,
            Expense.is_income == False
        ).scalar() or 0
        
        actual_data[category.name] = actual_spending
    
    # Create bar chart
    categories = list(budget_data.keys())
    budget_values = list(budget_data.values())
    actual_values = [actual_data[cat] for cat in categories]
    
    x = np.arange(len(categories))  # the label locations
    width = 0.35  # the width of the bars
    
    fig, ax = plt.subplots(figsize=(12, 7))
    rects1 = ax.bar(x - width/2, budget_values, width, label='Budget', color='skyblue')
    rects2 = ax.bar(x + width/2, actual_values, width, label='Actual', color='coral')
    
    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Amount')
    ax.set_title('Budget vs. Actual Spending by Category')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.legend()
    
    # Add value labels on bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.0f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    
    if save_path:
        # Save chart to file
        plt.savefig(save_path)
        plt.close()
        return save_path
    else:
        # Return as base64 encoded string for embedding in HTML
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        encoded = base64.b64encode(image_png).decode('utf-8')
        return f"data:image/png;base64,{encoded}"

def generate_chart_data_for_js(user_id):
    """Generate chart data in JSON format for Chart.js"""
    # Get expenses grouped by category
    expenses = Expense.query.filter_by(user_id=user_id, is_income=False).all()
    
    if not expenses:
        return json.dumps({})
    
    # Group expenses by category
    category_totals = {}
    for expense in expenses:
        category_name = expense.category.name if expense.category else "Uncategorized"
        if category_name in category_totals:
            category_totals[category_name] += expense.amount
        else:
            category_totals[category_name] = expense.amount
    
    # Get category colors
    categories = Category.query.filter_by(user_id=user_id).all()
    category_colors = {cat.name: cat.color for cat in categories}
    
    # Prepare data for Chart.js
    chart_data = {
        'labels': list(category_totals.keys()),
        'datasets': [{
            'data': list(category_totals.values()),
            'backgroundColor': [category_colors.get(cat, "#" + ''.join([f'{np.random.randint(0, 255):02x}' for _ in range(3)])) 
                               for cat in category_totals.keys()]
        }]
    }
    
    return json.dumps(chart_data)

def generate_monthly_data_for_js(user_id, months=6):
    """Generate monthly trend data in JSON format for Chart.js"""
    # Calculate date range
    end_date = datetime.utcnow().date()
    start_date = (datetime.utcnow() - timedelta(days=30*months)).date()
    
    # Get expenses in date range
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).all()
    
    if not expenses:
        return json.dumps({})
    
    # Create DataFrame from expenses
    data = []
    for expense in expenses:
        data.append({
            'date': expense.date,
            'amount': expense.amount,
            'type': 'Income' if expense.is_income else 'Expense'
        })
    
    df = pd.DataFrame(data)
    
    # Group by month and type
    df['month'] = df['date'].apply(lambda x: x.strftime('%Y-%m'))
    monthly_data = df.groupby(['month', 'type'])['amount'].sum().unstack().fillna(0)
    
    # Ensure both Income and Expense columns exist
    if 'Income' not in monthly_data.columns:
        monthly_data['Income'] = 0
    if 'Expense' not in monthly_data.columns:
        monthly_data['Expense'] = 0
    
    # Sort by month
    monthly_data = monthly_data.sort_index()
    
    # Prepare data for Chart.js
    chart_data = {
        'labels': monthly_data.index.tolist(),
        'datasets': [
            {
                'label': 'Income',
                'data': monthly_data['Income'].tolist(),
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'fill': True
            },
            {
                'label': 'Expense',
                'data': monthly_data['Expense'].tolist(),
                'borderColor': 'rgba(255, 99, 132, 1)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'fill': True
            }
        ]
    }
    
    return json.dumps(chart_data)
