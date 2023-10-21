from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from qcl.utils import validate


class SignupForm(FlaskForm):
    username = StringField('Username', render_kw={"class": "form-control"}, validators=[
        DataRequired("Username cannot be empty"),
        Length(min=14, max=100),
        validate.check_email

    ])
    password = PasswordField('Password', render_kw={"class": "form-control"}, validators=[
        DataRequired("Password cannot be empty"),
        Length(min=8, max=100)
    ])
    register = SubmitField("Register", render_kw={"class": "btn btn-outline-light"})


class LoginForm(FlaskForm):
    username = StringField('Username', render_kw={"class": "form-control", "placeholder": "Email address"}, validators=[
        DataRequired("Username cannot be empty")

    ])
    password = PasswordField('Password', render_kw={"class": "form-control", "placeholder": "Password"}, validators=[
        DataRequired("Password cannot be empty")
    ])
    login = SubmitField("Login", render_kw={"class": "btn btn-outline-light"})


class EmailVerificationForm(FlaskForm):
    code = StringField("Verification code", validators=[
        DataRequired("The code is required"),
        Length(min=6, max=12)
    ])
    submit = SubmitField("Submit", render_kw={"class": "btn btn-outline-light"})


class CodeForm(FlaskForm):
    code = StringField(validators=[
        Length(min=10, max=1500)
    ])
    run = SubmitField("Run Checks", render_kw={"class": "btn btn-outline-primary"})
    doc = SubmitField("Next", render_kw={"class": "btn btn-outline-success"})


class DocForm(FlaskForm):
    code = StringField(validators=[
        Length(min=10, max=1500)
    ])
    documented = StringField(validators=[
        Length(min=10, max=2000)
    ])
    generate = SubmitField("Generate Docs", render_kw={"formnovalidate": True, "class": "btn btn-outline-primary"})
    next = SubmitField("Next", render_kw={"class": "btn btn-outline-success"})


class TestForm(FlaskForm):
    documented = StringField(validators=[
        Length(min=10, max=2000)
    ])
    unittests = StringField(validators=[
        Length(min=10, max=3000)
    ])
    generate = SubmitField("Generate Tests", render_kw={"formnovalidate": True, "class": "btn btn-outline-primary"})
    run = SubmitField("Run Tests", render_kw={"formnovalidate": True, "class": "btn btn-outline-primary"})
    next = SubmitField("Next", render_kw={"class": "btn btn-outline-success"})


class ClassifyForm(FlaskForm):
    keywords = TextAreaField("Keywords (comma separated)", render_kw={"class": "form-control", "placeholder": "Keywords (comma separated)"}, validators=[
        Length(min=3, max=200)
    ])
    name = StringField("Function name", render_kw={"class": "form-control", "placeholder": "Function name"}, validators=[
        DataRequired(),
        Length(min=3, max=50)
    ])
    usecase = TextAreaField("Use case", render_kw={"class": "form-control", "placeholder": "Use case"}, validators=[
        DataRequired(),
        Length(min=10, max=500)
    ])
    generate = SubmitField("Generate keywords", render_kw={"formnovalidate": True, "class": "btn btn-outline-primary"})
    save = SubmitField("Save function", render_kw={"class": "btn btn-outline-success"})