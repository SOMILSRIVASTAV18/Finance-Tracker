

from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, BooleanField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional


class ExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    date = DateField('Date', validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    is_income = BooleanField('Income')
    is_recurring = BooleanField('Recurring')

    recurring_frequency = SelectField(
        'Frequency',
        choices=[
            ('none', 'None'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly')
        ],
        validators=[Optional()]
    )

    submit = SubmitField('Save')


class FilterForm(FlaskForm):
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])

    category = SelectField(
        'Category',
        coerce=int,
        choices=[(0, 'All Categories')],
        default=0
    )

    submit = SubmitField('Filter')
class QuickExpenseForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    is_income = BooleanField('Income')
    submit = SubmitField('Add')