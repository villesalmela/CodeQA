from qcl import app
from qcl.utils import dbrunner, code_format, fileops, validate
from qcl.integrations import gpt, linter, testrunner
from qcl.models.user import User

from functools import wraps
import traceback
import json

from flask import render_template, request, session, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

import logging
logging.basicConfig(level=logging.INFO)



def needs_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_role" not in session:
            return redirect(url_for("unauthorized"))
        elif session["user_role"] not in ["user", "admin"]:
            return redirect(url_for("forbidden"))
        return func(*args, **kwargs)
    return wrapper

def needs_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_role" not in session:
            return redirect(url_for("unauthorized"))
        elif session["user_role"] != "admin":
            return redirect(url_for("forbidden"))
        return func(*args, **kwargs)
    return wrapper


@app.route("/unauthorized")
def unauthorized():
    return render_template("unauthorized.html"), 401

@app.route("/badrequest")
def badrequest():
    return render_template("badrequest.html"), 400
@app.route("/forbidden")
def forbidden():
    return render_template("forbidden.html"), 403

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
    lint = SubmitField("Run Linting")
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

@app.route("/", methods=['GET', 'POST'])
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
@needs_user
def add():
    form = CodeForm()
    if request.method == "GET":
        if source_code := session.get("source_code"):
            form.code.data = source_code
        return render_template("add.html", form=form)
        
    elif request.method == "POST":
        if form.validate(): #data ok
            source_code = form.code.data
            session["source_code"] = source_code

            if form.lint.data: # clicked run linting
                filename = fileops.create_tempfile(source_code)
                try:
                    lint_result = linter.run_pylint(filename)
                finally:
                    fileops.delete_file(filename)
                return render_template("add.html", form=form, lint_result=lint_result)
            
            elif form.doc.data: # clicked next
                return redirect(url_for("doc"))
            
            else: # unexpected submit
                raise RuntimeError()
        
        else: # data not ok
            return render_template("add.html", form=form)
    else: # unexpected method
        raise RuntimeError()

@app.route("/doc", methods=["GET", "POST"])
@needs_user
def doc():
    form = DocForm()
    if request.method == "GET":
        if source_code := session.get("source_code"):
            form.code.data = source_code
        if documented := session.get("source_code_documented"):
            form.documented.data = documented
        return render_template("doc.html", form=form)

    elif request.method == "POST":
        if form.generate.data: # clicked generate tests
            # TODO: validate source code
            documented = gpt.process_code(form.code.data, mode="doc")
            form.documented.data = documented
            return render_template("doc.html", form=form)

        elif form.next.data: # clicked next
            if form.validate(): # data ok
                session["source_code"] = form.code.data
                session["source_code_documented"] = form.documented.data
                return redirect(url_for("test"))
            else: # data not ok
                return render_template("doc.html", form=form)
        else: # unexpected submit
            raise RuntimeError()
    else: # unexpected method
        raise RuntimeError()

@app.route("/test", methods=["GET", "POST"])
@needs_user
def test():
    form = TestForm()
    if request.method == "GET":
        if documented := session.get("source_code_documented"):
            form.documented.data = documented
        if unittests := session.get("source_code_unittests"):
            form.unittests.data = unittests
        return render_template("test.html", form=form)

    if request.method == "POST":
        if form.generate.data: # clicked generate tests
            unittests = gpt.process_code(form.documented.data, mode="test")
            form.unittests.data = unittests
            return render_template("test.html", form=form)
        elif form.run.data: # clicked run tests
            success, results = testrunner.execute(func=form.documented.data, test=form.unittests.data)
            if not success: #TODO: handle failure
                raise RuntimeError(results)
            results = json.dumps(results, indent=4)
            return render_template("test.html", form=form, results=results)
        elif form.next.data: # clicked next
            if form.validate(): # data ok
                session["source_code_documented"] = form.documented.data
                session["source_code_unittests"] = form.unittests.data
                return redirect(url_for("classify"))
            else: # data not ok
                return render_template("test.html", form=form)
        else: # unexpected submit
            raise RuntimeError()
    else: # unexpected method
        raise RuntimeError()


@app.route("/classify", methods=["GET", "POST"])
@needs_user
def classify():
    expected_args = ["source_code_documented", "source_code_unittests"]
    for arg in expected_args:
        if not arg in session:
            return redirect(url_for("badrequest"))
    
    form = ClassifyForm()

    if request.method == "GET":
        return render_template("classify.html", form=form)

    if request.method == "POST":
        if form.generate.data: # clicked generate keywords
            keywords = set(gpt.process_code(session["source_code_documented"], mode="classify"))
            keywords_str = str(keywords).strip("}{")
            form.keywords.data = keywords_str
            return render_template("classify.html", form=form)
        if form.save.data: # clicked save
            if form.validate(): # data ok
                keywords = {x.strip() for x in form.keywords.data.split(",")}
                keywords_str = str(keywords).strip("}{")
                session["function_keywords"] = keywords_str
                session["function_name"] = form.name.data
                session["function_usecase"] = form.usecase.data
                return redirect(url_for("save_new_function"))
            else: # data not ok
                return render_template("classify.html", form=form)
    
    
@app.route("/save_new_function")
@needs_user
def save_new_function():
    expected_args = ["source_code", "source_code_documented", "source_code_unittests", "function_keywords", "function_name",
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
        if login_status: # all ok
            session["user_id"] = user.id
            session["user_role"] = user.role
            return redirect(url_for("index"))
        elif login_status is None: # credentials ok, verification not done
            session["temp_user_id"] = user.id
            session["temp_user_role"] = user.role
            session["temp_username"] = user.name
            return render_template("email_verification.html", form=EmailVerificationForm(), error=False)
        else: # credentials not ok
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
            return "Something went wrong, registration failed.", 500

    return render_template("register.html", form=form)
