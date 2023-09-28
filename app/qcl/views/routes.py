from qcl import app
from qcl.utils import dbrunner, code_format, fileops, validate
from qcl.integrations import gpt, linter, testrunner
from qcl.models.user import User

from functools import wraps
import traceback
import json

from flask import render_template, request, session, redirect, url_for
from flask_api import status
from flask_wtf import FlaskForm
from flask_codemirror.fields import CodeMirrorField
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

import logging
logging.basicConfig(level=logging.INFO)


logging.info(dbrunner.execute("SELECT VERSION()"))


from flask_codemirror import CodeMirror
codemirror = CodeMirror(app)


def needs_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_role" not in session or session["user_role"] not in ["user", "admin"]:
            return redirect(url_for("unauthorized"))
        return func(*args, **kwargs)
    return wrapper

def needs_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_role" not in session or session["user_role"] != "admin":
            return redirect(url_for("unauthorized"))
        return func(*args, **kwargs)
    return wrapper


@app.route("/unauthorized")
def unauthorized():
    return render_template("unauthorized.html"), status.HTTP_401_UNAUTHORIZED

@app.route("/badrequest")
def badrequest():
    return render_template("badrequest.html"), status.HTTP_400_BAD_REQUEST

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
    code = CodeMirrorField("Source Code", language="python", config={"linenumbers": True}, validators=[
        Length(min=10, max=1500)
    ])
    lint = SubmitField("Run Linting")
    doc = SubmitField("Next")

class DocForm(FlaskForm):
    code = CodeMirrorField("Original Source Code", language="python", config={"linenumbers": True}, validators=[
        Length(min=10, max=1500)
    ])
    documented = CodeMirrorField("Documented Source Code", language="python", config={"linenumbers": True}, validators=[
        Length(max=2000)
    ])
    generate = SubmitField("Generate Docs")
    next = SubmitField("Next")

class TestForm(FlaskForm):
    documented = CodeMirrorField("Documented Source Code", language="python", config={"linenumbers": True}, validators=[
        Length(min=10, max=2000)
    ])
    unittests = CodeMirrorField("Unit Tests", language="python", config={"linenumbers": True}, validators=[
        Length(max=3000)
    ])
    generate = SubmitField("Generate Tests")
    run = SubmitField("Run Tests")
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
    generate = SubmitField("Generate keywords")
    save = SubmitField("Save function")

@app.route("/", methods=['GET', 'POST'])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
@needs_user
def add():
    form = CodeForm()
    if form.validate_on_submit():
        source_code = form.code.data
        session["source_code"] = source_code
        if form.lint.data:
            filename = fileops.create_tempfile(source_code)
            try:
                lint_result = linter.run_pylint(filename)
            finally:
                fileops.delete_file(filename)
            return render_template("add.html", form=form, lint_result=lint_result, post=True)
        elif form.doc.data:
            return redirect(url_for("doc"))
        

    return render_template("add.html", form=form)

@app.route("/doc", methods=["GET", "POST"])
@needs_user
def doc():
    if "source_code" in session and request.method == "GET":
        form = DocForm(code=session["source_code"])
        del session["source_code"]
    elif request.method == "POST":
        form = DocForm()
    else:
        return redirect(url_for("badrequest"))
    if form.validate_on_submit():
        if form.generate.data:
            documented = gpt.process_code(form.code.data, mode="doc")
            form.documented.data = documented
            return render_template("doc.html", form=form)
        elif form.next.data:
            session["source_code_documented"] = form.documented.data
            return redirect(url_for("test"))
        
    return render_template("doc.html", form=form)

@app.route("/test", methods=["GET", "POST"])
@needs_user
def test():
    if "source_code_documented" in session and request.method == "GET":
        form = TestForm(documented=session["source_code_documented"])
        del session["source_code_documented"]
    elif request.method == "POST":
        form = TestForm()
    else:
        return redirect(url_for("badrequest"))
    if form.validate_on_submit():
        if form.generate.data:
            unittests = gpt.process_code(form.documented.data, mode="test")
            form.unittests.data = unittests
            return render_template("test.html", form=form)
        elif form.run.data:
            success, results = testrunner.execute(func=form.documented.data, test=form.unittests.data)
            if not success:
                raise RuntimeError(results)
            results = json.dumps(results, indent=4)
            return render_template("test.html", form=form, results=results)
        elif form.next.data:
            session["source_code_documented"] = form.documented.data
            session["source_code_unittests"] = form.unittests.data
            return redirect(url_for("classify"))
        
    return render_template("test.html", form=form)

@app.route("/classify", methods=["GET", "POST"])
@needs_user
def classify():
    if not ("source_code_documented" in session and "source_code_unittests" in session):
        redirect(url_for("badrequest"))
    
    form = ClassifyForm()

    if request.method == "POST" and form.generate.data:
        keywords = set(gpt.process_code(session["source_code_documented"], mode="classify"))
        keywords_str = str(keywords).strip("}{")
        form.keywords.data = keywords_str
        return render_template("classify.html", form=form)
    elif form.validate_on_submit() and form.save.data:
        keywords = {x.strip() for x in form.keywords.data.split(",")}
        keywords_str = str(keywords).strip("}{")
        session["function_keywords"] = keywords_str
        session["function_name"] = form.name.data
        session["function_usecase"] = form.usecase.data
        return redirect(url_for("save_new_function"))
    return render_template("classify.html", form=form)
    

@app.route("/save_new_function")
@needs_user
def save_new_function():
    expected_args = ["source_code_documented", "source_code_unittests", "function_keywords", "function_name",
                     "function_usecase"]
    for arg in expected_args:
        if not arg in session:
            return redirect(url_for("badrequest"))
        
    code = session["source_code_documented"]
    tests = session["source_code_unittests"]
    keywords = session["function_keywords"]
    name = session["function_name"]
    usecase = session["function_usecase"]
    uid = session["user_id"]

    save_success, function_id = dbrunner.save_function(code, tests, keywords, usecase, name, uid)
    if not save_success:
        raise RuntimeError("Function save failed")

    # clear session
    for arg in expected_args:
        del session[arg]

    return redirect(url_for("view_function", function_id=function_id))

@app.route("/functions/<function_id>")
@needs_user
def view_function(function_id):
    fdata = dbrunner.get_function(int(function_id))
    fdata["code"] = code_format.format(fdata["code"])
    fdata["tests"] = code_format.format(fdata["tests"])
    fdata["keywords"] = [x.strip() for x in fdata["keywords"].split(",")]
    return render_template("function.html", fdata=fdata)

@app.route("/functions")
@needs_user
def list_functions():
    fdata = dbrunner.list_functions()
    return render_template("functions.html", fdata=fdata)

@app.route("/login",methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        username = request.form["username"]
        password = request.form["password"]
        try:
            user = User(username)
        except:
            logging.error(traceback.format_exc())
            return redirect(url_for("unauthorized")) 
        
        login_status = user.login(password)
        if login_status:
            session["user_id"] = user.id
            session["user_role"] = user.role
            return redirect(url_for("index"))
        if login_status is None:
            session["temp_user_id"] = user.id
            session["temp_user_role"] = user.role
            session["temp_username"] = user.name
            return render_template("email_verification.html", form=EmailVerificationForm(), error=False)
            
    
        return redirect(url_for("unauthorized"))
    return render_template("login.html", form=form)


@app.route("/verify_email", methods=["POST"])
def verify_email():
    if "temp_user_id" not in session:
        return redirect(url_for("unauthorized"))
    
    code = request.form["code"]
    user = User(session["temp_username"])
    valid = user.check_verification_code(code)
    if valid:
        session["user_id"] = session["temp_user_id"]
        session["user_role"] = session["temp_user_role"]
        del session["temp_user_id"]
        del session["temp_user_role"]
        del session["temp_username"]
        return redirect(url_for("index"))
    else:
        return render_template("email_verification.html", form=EmailVerificationForm(), error=True)


@app.route("/logout")
def logout():
    if "user_id" in session:
        del session["user_id"]
    if "user_role" in session:
        del session["user_role"]
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    # already logged in
    if "user_id" in session:
        logging.info("already logged in")
        return redirect(url_for("index"))
    
    form = SignupForm()

    logging.info("new user try")
    if form.validate_on_submit():
        username = request.form["username"]
        password = request.form["password"]

        try:
            User(username, password)
            logging.info("new user success")
            return render_template("register_complete.html")
        except:
            logging.info("new user fail")
            logging.error(traceback.format_exc())
            return "Something went wrong, registration failed.", status.HTTP_500_INTERNAL_SERVER_ERROR

    return render_template("register.html", form=form)
