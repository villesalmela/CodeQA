from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from qcl.utils import validate


class SignupForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired("Username cannot be empty"),
        Length(min=14, max=100),
        validate.check_email

    ])
    password = PasswordField('Password', validators=[
        DataRequired("Password cannot be empty"),
        Length(min=8, max=100)
    ])


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired("Username cannot be empty")

    ])
    password = PasswordField('Password', validators=[
        DataRequired("Password cannot be empty")
    ])


class EmailVerificationForm(FlaskForm):
    code = StringField("Verification code", validators=[
        DataRequired("The code is required"),
        Length(min=6, max=12)
    ])


class CodeForm(FlaskForm):
    code = StringField(validators=[
        Length(min=10, max=1500)
    ])
    run = SubmitField("Run Checks")
    doc = SubmitField("Next")


class DocForm(FlaskForm):
    code = StringField(validators=[
        Length(min=10, max=1500)
    ])
    documented = StringField(validators=[
        Length(min=10, max=2000)
    ])
    generate = SubmitField("Generate Docs", render_kw={"formnovalidate": True})
    next = SubmitField("Next")


class TestForm(FlaskForm):
    documented = StringField(validators=[
        Length(min=10, max=2000)
    ])
    unittests = StringField(validators=[
        Length(min=10, max=3000)
    ])
    generate = SubmitField("Generate Tests", render_kw={"formnovalidate": True})
    run = SubmitField("Run Tests", render_kw={"formnovalidate": True})
    next = SubmitField("Next")


class ClassifyForm(FlaskForm):
    keywords = TextAreaField("Keywords (comma separated)", validators=[
        Length(min=3, max=200)
    ])
    name = StringField("Function name", validators=[
        DataRequired(),
        Length(min=3, max=50)
    ])
    usecase = TextAreaField("Use case", validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])
    generate = SubmitField("Generate keywords", render_kw={"formnovalidate": True})
    save = SubmitField("Save function")