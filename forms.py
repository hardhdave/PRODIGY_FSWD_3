from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange

class CheckoutForm(FlaskForm):
    customer_name = StringField('Full Name', validators=[DataRequired()])
    customer_email = StringField('Email', validators=[DataRequired(), Email()])
    customer_phone = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Shipping Address', validators=[DataRequired()])
    submit = SubmitField('Place Order')
