
import os
from datetime import datetime
from flask import send_from_directory
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# from werkzeug.security import generate, check
from werkzeug.utils import secure_filename
import pymysql
pymysql.install_as_MySQLdb()

# Import configuration
from config import Config

# Import database models
from models import db
from models.user import User
from models.expense import Expense
from models.category import Category

# Import forms
from forms.auth_forms import LoginForm, RegistrationForm, ResetPasswordForm
from forms.expense_forms import ExpenseForm, FilterForm
from forms.profile_forms import ProfileForm, PasswordForm
from forms.report_forms import ReportForm

# Import utilities
from utils.auth import setup_login_manager
from utils.charts import (
    generate_expense_pie_chart, 
    generate_monthly_trend_chart, 
    generate_chart_data_for_js,
    generate_monthly_data_for_js
)
from utils.export import export_to_csv, export_to_pdf

# Create Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Setup login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables if they don't exist
with app.app_context():
    db.create_all()
    
    # Create default categories if none exist
    if Category.query.count() == 0:
        default_categories = [
            {'name': 'Food', 'color': '#FF5733'},
            {'name': 'Transportation', 'color': '#33FF57'},
            {'name': 'Housing', 'color': '#3357FF'},
            {'name': 'Entertainment', 'color': '#F033FF'},
            {'name': 'Utilities', 'color': '#FF9033'},
            {'name': 'Healthcare', 'color': '#33FFF0'},
            {'name': 'Education', 'color': '#FF33A8'},
            {'name': 'Shopping', 'color': '#A833FF'},
            {'name': 'Personal', 'color': '#33A8FF'},
            {'name': 'Other', 'color': '#AAAAAA'}
        ]
        
        for cat in default_categories:
            category = Category(name=cat['name'], color=cat['color'])
            db.session.add(category)
        
        db.session.commit()

# Ensure export directories exist
os.makedirs(app.config['CSV_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

# Template filters
@app.template_filter('format_currency')
def format_currency(value):
    """Format a number as currency"""
    return f"{value:,.2f}"

# Routes
@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Create default categories for the user
        default_categories = Category.query.filter_by(user_id=None).all()
        for default_cat in default_categories:
            user_cat = Category(
                name=default_cat.name,
                color=default_cat.color,
                user_id=user.id
            )
            db.session.add(user_cat)
        
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get quick add form
    from forms.expense_forms import QuickExpenseForm
    quick_form = QuickExpenseForm()
    quick_form.category.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]
    
    # Get financial summary
    total_income = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.is_income == True
    ).scalar() or 0
    
    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.is_income == False
    ).scalar() or 0
    
    # Get recent transactions
    recent_transactions = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(Expense.date.desc()).limit(5).all()
    
    # Generate chart data
    expense_chart_data = generate_chart_data_for_js(current_user.id)
    trend_chart_data = generate_monthly_data_for_js(current_user.id)
    
    return render_template(
        'dashboard.html',
        quick_form=quick_form,
        total_income=total_income,
        total_expenses=total_expenses,
        recent_transactions=recent_transactions,
        expense_chart_data=expense_chart_data,
        trend_chart_data=trend_chart_data
    )


@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    # ===== Expense Form =====
    form = ExpenseForm()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category.choices = [(c.id, c.name) for c in categories]

    # ===== Filter Form =====
    filter_form = FilterForm()
    filter_form.category.choices = [(0, 'All Categories')] + [
        (c.id, c.name) for c in categories
    ]

    # ===== Handle Add Expense =====
    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            description=form.description.data,
            date=form.date.data,
            is_income=form.is_income.data,
            is_recurring=form.is_recurring.data,
            recurring_frequency=form.recurring_frequency.data
            if form.is_recurring.data else None,
            category_id=form.category.data,
            user_id=current_user.id
        )

        db.session.add(expense)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('expenses'))

    # ===== Query Builder =====
    page = request.args.get('page', 1, type=int)
    query = Expense.query.filter_by(user_id=current_user.id)

    # Filters (GET)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category', type=int)

    if start_date:
        query = query.filter(Expense.date >= start_date)

    if end_date:
        query = query.filter(Expense.date <= end_date)

    if category_id and category_id != 0:
        query = query.filter_by(category_id=category_id)

    transactions = query.order_by(
        Expense.date.desc()
    ).paginate(page=page, per_page=10)

    return render_template(
        'expenses.html',
        form=form,
        filter_form=filter_form,
        transactions=transactions
    )

@app.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    """Quick add expense from dashboard"""
    from forms.expense_forms import QuickExpenseForm
    form = QuickExpenseForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            description=form.description.data,
            date=datetime.utcnow().date(),
            is_income=form.is_income.data,
            category_id=form.category.data,
            user_id=current_user.id
        )
        
        db.session.add(expense)
        db.session.commit()
        
        flash('Transaction added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/expenses/get/<int:id>')
@login_required
def get_expense(id):
    """Get expense data for editing"""
    expense = Expense.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    return jsonify({
        'id': expense.id,
        'amount': expense.amount,
        'description': expense.description,
        'date': expense.date.strftime('%Y-%m-%d'),
        'category_id': expense.category_id,
        'is_income': expense.is_income,
        'is_recurring': expense.is_recurring,
        'recurring_frequency': expense.recurring_frequency
    })

@app.route('/expenses/edit/<int:id>', methods=['POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    expense.amount = request.form.get('amount')
    expense.description = request.form.get('description')
    expense.date = request.form.get('date')
    expense.category_id = request.form.get('category')
    expense.is_income = True if request.form.get('is_income') else False

    db.session.commit()
    flash('Transaction updated!', 'success')
    return redirect(url_for('expenses'))



@app.route('/expenses/delete/<int:id>')
@login_required
def delete_expense(id):
    """Delete an expense"""
    expense = Expense.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    db.session.delete(expense)
    db.session.commit()
    
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('expenses'))


@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    form = ReportForm()
    form.categories.choices = [
        (c.id, c.name)
        for c in Category.query.filter_by(user_id=current_user.id).all()
    ]

    report_data = None
    recent_exports = []

    if form.validate_on_submit():
        query = Expense.query.filter_by(user_id=current_user.id)

        if form.start_date.data:
            query = query.filter(Expense.date >= form.start_date.data)
        if form.end_date.data:
            query = query.filter(Expense.date <= form.end_date.data)
        if form.categories.data:
            query = query.filter(Expense.category_id.in_(form.categories.data))

        transactions = query.order_by(Expense.date.desc()).all()

        total_income = sum(t.amount for t in transactions if t.is_income)
        total_expenses = sum(t.amount for t in transactions if not t.is_income)

        charts = []
        if form.include_charts.data:
            pie_path = os.path.join(app.static_folder, 'temp', f'pie_{current_user.id}.png')
            trend_path = os.path.join(app.static_folder, 'temp', f'trend_{current_user.id}.png')

            pie = generate_expense_pie_chart(current_user.id, pie_path)
            trend = generate_monthly_trend_chart(current_user.id, trend_path)

            if pie:
                charts.append(pie)
            if trend:
                charts.append(trend)

        report_data = {
            'start_date': form.start_date.data,
            'end_date': form.end_date.data,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'transactions': transactions,
            'charts': charts
        }

        # ✅ EXPORT + AUTO DOWNLOAD
        if form.export_format.data == 'csv':
            export_path = export_to_csv(
                current_user.id,
                start_date=form.start_date.data,
                end_date=form.end_date.data
            )
            if export_path:
                return redirect(url_for(
                    'download_file',
                    file_type='csv',
                    filename=os.path.basename(export_path)
                ))

        elif form.export_format.data == 'pdf':
            export_path = export_to_pdf(
                current_user.id,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                include_charts=form.include_charts.data
            )
            if export_path:
                return redirect(url_for(
                    'download_file',
                    file_type='pdf',
                    filename=os.path.basename(export_path)
                ))

    # ===============================
    # RECENT EXPORTS
    # =============================== cleanup_old_expor
    csv_dir = app.config.get('CSV_FOLDER')
    pdf_dir = app.config.get('PDF_FOLDER')

    def collect_exports(directory, ext, file_type):
        if directory and os.path.exists(directory):
            for f in os.listdir(directory):
                if f.startswith(f'user_{current_user.id}_') and f.endswith(ext):
                    path = os.path.join(directory, f)
                    recent_exports.append({
                        'filename': f,
                        'type': file_type,
                        'date': datetime.fromtimestamp(os.path.getmtime(path))
                    })

    collect_exports(csv_dir, '.csv', 'CSV')
    collect_exports(pdf_dir, '.pdf', 'PDF')

    recent_exports.sort(key=lambda x: x['date'], reverse=True)
    recent_exports = recent_exports[:10]

    return render_template(
        'reports.html',
        form=form,
        report_data=report_data,
        recent_exports=recent_exports
    )

@app.route('/download/<file_type>/<filename>')
@login_required
def download_file(file_type, filename):
    """Download an exported file"""
    # Security check: ensure filename belongs to current user
    if not filename.startswith(f'user_{current_user.id}_'):
        flash('Access denied.', 'danger')
        return redirect(url_for('reports'))
    
    # Determine the correct directory
    if file_type.lower() == 'csv':
        directory = app.config['CSV_FOLDER']
    elif file_type.lower() == 'pdf':
        directory = app.config['PDF_FOLDER']
    else:
        flash('Invalid file type.', 'danger')
        return redirect(url_for('reports'))
    
    # Provide the file for download
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    profile_form = ProfileForm(obj=current_user)
    password_form = PasswordForm()
    
    if request.method == 'POST':
        if 'update_profile' in request.form and profile_form.validate_on_submit():
            # Check if email is already taken by another user
            if profile_form.email.data != current_user.email:
                existing_user = User.query.filter_by(email=profile_form.email.data).first()
                if existing_user:
                    flash('Email already in use by another account.', 'danger')
                    return redirect(url_for('profile'))
            
            # Check if username is already taken by another user
            if profile_form.username.data != current_user.username:
                existing_user = User.query.filter_by(username=profile_form.username.data).first()
                if existing_user:
                    flash('Username already in use by another account.', 'danger')
                    return redirect(url_for('profile'))
            
            # Update user profile
            current_user.username = profile_form.username.data
            current_user.email = profile_form.email.data
            db.session.commit()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        elif 'update_password' in request.form and password_form.validate_on_submit():
            # Verify current password
            if not current_user.check_password(password_form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('profile'))
            
            # Update password
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            
            flash('Password updated successfully!', 'success')
            return redirect(url_for('profile'))
    
    return render_template(
        'profile.html',
        profile_form=profile_form,
        password_form=password_form
    )

@app.route('/export_all_data')
@login_required
def export_all_data():
    """Export all user data to CSV"""
    export_path = export_to_csv(current_user.id)
    
    if export_path:
        # Get just the filename from the path
        filename = os.path.basename(export_path)
        flash('All data exported successfully!', 'success')
        return redirect(url_for('download_file', file_type='csv', filename=filename))
    else:
        flash('Error exporting data.', 'danger')
        return redirect(url_for('profile'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account and all associated data"""
    confirmation = request.form.get('confirmation')
    
    if confirmation != 'DELETE':
        flash('Account deletion canceled. Confirmation text did not match.', 'warning')
        return redirect(url_for('profile'))
    
    # Delete all user expenses
    Expense.query.filter_by(user_id=current_user.id).delete()
    
    # Delete all user categories
    Category.query.filter_by(user_id=current_user.id).delete()
    
    # Delete user
    user_id = current_user.id
    logout_user()
    User.query.filter_by(id=user_id).delete()
    
    db.session.commit()
    
    flash('Your account has been permanently deleted.', 'info')
    return redirect(url_for('index'))

@app.route('/quick_add', methods=['POST'])
@login_required
def quick_add():
    """Quick add expense from dashboard"""
    from forms.expense_forms import QuickExpenseForm
    
    form = QuickExpenseForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        expense = Expense(
            amount=form.amount.data,
            description=form.description.data,
            date=datetime.utcnow().date(),
            is_income=form.is_income.data,
            category_id=form.category.data,
            user_id=current_user.id
        )
        
        db.session.add(expense)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')
    
    return redirect(url_for('dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500
    return render_template('errors/500.html'), 500

@app.context_processor
def inject_now():
    """Inject current date into templates"""
    return {'now': datetime.utcnow()}

# # Clean up old exports periodically
# @app.before_request
# def cleanup_exports():
#     """Clean up old export files periodically"""
#     # Only run occasionally (1% chance per request)
#     import random
#     if random.random() < 0.01:
#         cleanup_exports(days_to_keep=30)
# Clean up old exports periodically
# @app.before_request
# def cleanup_exports():
#     """Clean up old export files periodically"""
#     # Only run occasionally (1% chance per request)
#     import random
#     if random.random() < 0.01:
#         cleanup_exports(days_to_keep=30)

if __name__ == '__main__':
    app.run(debug=True)



