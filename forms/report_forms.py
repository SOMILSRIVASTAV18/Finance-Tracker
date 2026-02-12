from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, SelectMultipleField, DateField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Profile')

class PasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')

class ReportForm(FlaskForm):
    report_type = SelectField('Report Type', choices=[
        ('summary', 'Summary'),
        ('category', 'By Category'),
        ('transactions', 'Transactions')
    ], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    categories = SelectMultipleField('Categories', coerce=int, validators=[Optional()])
    include_charts = BooleanField('Include Charts')
    export_format = SelectField('Export Format', choices=[
        ('none', 'Preview Only'),
        ('csv', 'CSV'),
        ('pdf', 'PDF')
    ], validators=[DataRequired()])
    submit = SubmitField('Generate Report')
