from qcl import app
from qcl.utils import code_format, fileops
from qcl.integrations import gpt, linter, testrunner
from qcl.models.user import User
from qcl.models import function
from qcl.views.forms import SignupForm, LoginForm, EmailVerificationForm, CodeForm, DocForm, TestForm, ClassifyForm
from flask import session as client_session
from qcl.models.session import server_session


from functools import wraps
import traceback
import json
from flask import render_template, request, redirect, url_for, g

import logging
logging.basicConfig(level=logging.INFO)



def needs_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(g, "user"):
            return redirect(url_for("unauthorized"))
        elif g.user.role not in ["user", "admin"]:
            return redirect(url_for("forbidden"))
        return func(*args, **kwargs)
    return wrapper

def needs_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(g, "user"):
            return redirect(url_for("unauthorized"))
        elif g.user.role != "admin":
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

@app.route("/", methods=['GET', 'POST'])
def index():
    if "session_id" not in client_session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
@needs_user
def add():
    form = CodeForm()
    if request.method == "GET":
        if source_code := server_session.get("source_code"):
            form.code.data = source_code
        return render_template("add.html", form=form)
        
    elif request.method == "POST":
        if form.validate(): #data ok
            source_code = form.code.data
            server_session["source_code"] = source_code

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
        if source_code := server_session.get("source_code"):
            form.code.data = source_code
        if documented := server_session.get("source_code_documented"):
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
                server_session["source_code"] = form.code.data
                server_session["source_code_documented"] = form.documented.data
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
        if documented := server_session.get("source_code_documented"):
            form.documented.data = documented
        if unittests := server_session.get("source_code_unittests"):
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
                server_session["source_code_documented"] = form.documented.data
                server_session["source_code_unittests"] = form.unittests.data
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
        if not arg in server_session:
            return redirect(url_for("badrequest"))
    
    form = ClassifyForm()

    if request.method == "GET":
        return render_template("classify.html", form=form)

    if request.method == "POST":
        if form.generate.data: # clicked generate keywords
            keywords = set(gpt.process_code(server_session["source_code_documented"], mode="classify"))
            keywords_str = str(keywords).strip("}{")
            form.keywords.data = keywords_str
            return render_template("classify.html", form=form)
        if form.save.data: # clicked save
            if form.validate(): # data ok
                keywords = {x.strip() for x in form.keywords.data.split(",")}
                keywords_str = str(keywords).strip("}{")
                server_session["function_keywords"] = keywords_str
                server_session["function_name"] = form.name.data
                server_session["function_usecase"] = form.usecase.data
                return redirect(url_for("save_new_function"))
            else: # data not ok
                return render_template("classify.html", form=form)


@app.route("/delete_function/<int:function_id>", methods=["POST"])
@needs_user
def delete_function(function_id: int):
    function_data = function.get_function(function_id)
    fuid = function_data["user_id"]
    user_id = g.user.id
    user_role = g.user.role
    if fuid == user_id or user_role == "admin":
        function.delete_function(function_id)
        return redirect(url_for("list_functions"))
    else:
        return redirect(url_for("forbidden"))
    
@app.route("/save_new_function")
@needs_user
def save_new_function():
    expected_args = ["source_code", "source_code_documented", "source_code_unittests", "function_keywords", "function_name",
                     "function_usecase"]
    for arg in expected_args:
        if not arg in server_session:
            return redirect(url_for("badrequest"))
        
    code = server_session["source_code_documented"]
    tests = server_session["source_code_unittests"]
    keywords = server_session["function_keywords"]
    name = server_session["function_name"]
    usecase = server_session["function_usecase"]
    user_id = g.user.id

    save_success, function_id = function.save_function(code, tests, keywords, usecase, name, user_id)
    if not save_success:
        raise RuntimeError("Function save failed")

    # clear session
    for arg in expected_args:
        del server_session[arg]

    return redirect(url_for("view_function", function_id=function_id)) 

@app.route("/functions/<int:function_id>")
@needs_user
def view_function(function_id):
    fdata = function.get_function(function_id)
    del fdata["user_id"]
    fdata["code"] = code_format.format(fdata["code"])
    fdata["tests"] = code_format.format(fdata["tests"])
    fdata["keywords"] = [x.strip() for x in fdata["keywords"].split(",")]
    return render_template("function.html", fdata=fdata)

@app.route("/functions")
@needs_user
def list_functions():
    fdata = function.list_functions()
    return render_template("functions.html", fdata=fdata)

@app.route("/session_expired")
def session_expired():
    return render_template("session_expired.html"), 401

@app.route("/login",methods=["GET", "POST"])
def login():

    if "session_id" in client_session:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        username = request.form["username"]
        password = request.form["password"]
        try:
            user = User(username=username)
        except:
            logging.error(traceback.format_exc())
            return redirect(url_for("unauthorized")) 
        
        login_status = user.login(password)
        if login_status is False: # credentials not ok
            return redirect(url_for("unauthorized"))
        elif login_status is True: # all ok
            verified = True
        elif login_status is None: # credentials ok, verification not done
            verified=False
        else:
            raise RuntimeError("Invalid login status")
        session_id = server_session.new(user_id=user.id, data={"verified": verified})
        client_session["session_id"] = session_id
        return redirect(url_for("index"))
    return render_template("login.html", form=form)

@app.before_request
def pre_request():

    # public access to static allowed
    if request.path.startswith("/static/"):
        return None
    
    # client thinks it has session
    if session_id := client_session.get("session_id"):
        try:
            # open session
            user_id = server_session.open(session_id) 
            
            # create user object and make it available globally for the duration of this request
            g.user = User(user_id=user_id)
        except TimeoutError:
            del client_session["session_id"]
            return redirect(url_for("session_expired"))
        except:
            # client has non-existing session_id or bad user
            del client_session["session_id"]
            return redirect(url_for("unauthorized"))

        if server_session.get("verified"): # all ok
            # proceed with session
            return None
        
        else: # credentials ok, but email not verified
            # allow access to verification page
            if request.path == "/verify_email":
                return None
            else: # attempted normal access
                # redirect to verification
                return redirect(url_for("verify_email"))
    
    # proceed without session
    return None

@app.after_request
def post_request(response):
    # skip session management for static
    if request.path.startswith("/static/"):
        return response
    
    # client thinks it has session
    if "session_id" in client_session:
        
        # server has session open for client
        if server_session.is_open():
            
            # save session
            server_session.save()
    return response
    


@app.route("/verify_email", methods=["GET", "POST"])
def verify_email():
    if request.method == "GET":
        return render_template("email_verification.html", form=EmailVerificationForm(), error=False)
    
    elif request.method == "POST":
        logging.info("verifying")
        if "session_id" not in client_session:
            return redirect(url_for("unauthorized"))
        
        code = request.form["code"]
        valid = g.user.check_verification_code(code)
        if valid:
            logging.info("verified")
            server_session["verified"] = True
            return redirect(url_for("index"))
        else:
            logging.info("not verified")
            return render_template("email_verification.html", form=EmailVerificationForm(), error=True)


@app.route("/logout")
def logout():
    if "session_id" in client_session:
        del client_session["session_id"]
        server_session.delete()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    # already logged in
    if "session_id" in client_session:
        logging.info("already logged in")
        return redirect(url_for("index"))
    
    form = SignupForm()

    logging.info("new user try")
    if form.validate_on_submit():
        username = request.form["username"]
        password = request.form["password"]

        try:
            User.new(username, password)
            logging.info("new user success")
            return render_template("register_complete.html")
        except:
            logging.info("new user fail")
            logging.error(traceback.format_exc())
            return "Something went wrong, registration failed.", 500

    return render_template("register.html", form=form)
