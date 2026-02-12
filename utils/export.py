import os
import csv
import pandas as pd
from datetime import datetime
from flask import current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from models.expense import Expense
from models.category import Category
from models.user import User
from utils.charts import generate_expense_pie_chart, generate_monthly_trend_chart, generate_budget_comparison_chart

def export_to_csv(user_id, start_date=None, end_date=None):
    filename = f"user_{user_id}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(current_app.config['CSV_FOLDER'], filename)

    with open(path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Category', 'Amount', 'Type'])

        expenses = Expense.query.filter_by(user_id=user_id).all()
        for e in expenses:
            writer.writerow([
                e.date,
                e.category.name if e.category else 'N/A',
                e.amount,
                'Income' if e.is_income else 'Expense'
            ])

    return path

def export_to_pdf(user_id, start_date=None, end_date=None, include_charts=True):
    user = User.query.get(user_id)
    if not user:
        return None

    query = Expense.query.filter_by(user_id=user_id)

    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    expenses = query.order_by(Expense.date.desc()).all()
    if not expenses:
        return None

    os.makedirs(current_app.config['PDF_FOLDER'], exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"user_{user_id}_expenses_{timestamp}.pdf"
    filepath = os.path.join(current_app.config['PDF_FOLDER'], filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Financial Report for {user.username}", styles['Heading1']))
    elements.append(Spacer(1, 0.25 * inch))

    if start_date and end_date:
        date_text = f"{start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}"
    elif start_date:
        date_text = f"From {start_date:%Y-%m-%d}"
    elif end_date:
        date_text = f"Until {end_date:%Y-%m-%d}"
    else:
        date_text = "All transactions"

    elements.append(Paragraph(date_text, styles['Normal']))
    elements.append(Spacer(1, 0.25 * inch))

    total_income = sum(e.amount for e in expenses if e.is_income)
    total_expense = sum(e.amount for e in expenses if not e.is_income)
    balance = total_income - total_expense

    summary = Table([
        ["Total Income", f"₹{total_income:.2f}"],
        ["Total Expense", f"₹{total_expense:.2f}"],
        ["Balance", f"₹{balance:.2f}"]
    ])
    summary.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('TEXTCOLOR', (1,2), (1,2), colors.green if balance >=0 else colors.red)
    ]))
    elements.append(summary)
    elements.append(Spacer(1, 0.5 * inch))

    if include_charts:
        temp_dir = os.path.join(current_app.static_folder, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        pie_path = os.path.join(temp_dir, f'pie_{user_id}.png')
        trend_path = os.path.join(temp_dir, f'trend_{user_id}.png')

        if generate_expense_pie_chart(user_id, pie_path):
            elements.append(Image(pie_path, width=5 * inch, height=4 * inch))

        if generate_monthly_trend_chart(user_id, trend_path):
            elements.append(Image(trend_path, width=5 * inch, height=3 * inch))

    data = [["Date", "Description", "Category", "Amount", "Type"]]
    for e in expenses:
        data.append([
            e.date.strftime('%Y-%m-%d'),
            e.description or "",
            e.category.name if e.category else "Uncategorized",
            f"₹ {e.amount:.2f}",
            "Income" if e.is_income else "Expense"
        ])

    table = Table(data, colWidths=[1*inch, 2.5*inch, 1.5*inch, 1*inch, 1*inch])
    style = [
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (3,1), (3,-1), 'RIGHT'),
    ]
    
    for i, e in enumerate(expenses, start=1):
        if e.is_income:
            style.append(('TEXTCOLOR', (3, i), (3, i), colors.green))
        else:
            style.append(('TEXTCOLOR', (3, i), (3, i), colors.black))
    
    
    table.setStyle(TableStyle(style))
    

    elements.append(table)
    doc.build(elements)

    return filepath
