from qcl import app
from qcl.utils import code_format, fileops
from qcl.integrations import gpt, linter, testrunner, security, typecheck
from qcl.models.user import User
from qcl.models import user as user_module
from qcl.models import function, ratings
from qcl.views.forms import SignupForm, LoginForm, EmailVerificationForm, CodeForm, DocForm, TestForm, ClassifyForm
from qcl.models.session import server_session

from flask import render_template, request, redirect, url_for, g, abort, make_response, session as client_session
from functools import wraps
import json

### ACCESS CONTROL
def needs_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(g, "user"):
            abort(401)
        elif g.user.role not in ["user", "admin"]:
            abort(403)
        return func(*args, **kwargs)
    return wrapper

def needs_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(g, "user"):
            abort(401)
        elif g.user.role != "admin":
            abort(403)
        return func(*args, **kwargs)
    return wrapper

### CONTEXT HANDLING
@app.context_processor
def role_context():
    return {'user_role': getattr(g.get('user'), "role", None)}

@app.context_processor
def user_context():
    return {'username': getattr(g.get('user'), "name", None)}

### SESSION HANDLING
@app.before_request
def pre_request():

    app.logger.debug(f"{request.method} {request.path}")

    # public access to static allowed
    if request.path.startswith("/static/"):
        return None
    
    # client thinks it has session
    if session_id := client_session.get("session_id"):
        try:
            # open session
            g.psql_session_id = session_id
            g.psql_session_modified = False
            user_id, session_data = server_session.open(session_id) 
            g.psql_session = session_data
            
            # create user object and make it available globally for the duration of this request
            g.user = User(user_id=user_id)
        except TimeoutError:
            del client_session["session_id"]
            message = "Session expired"
            app.logger.debug(message)
            abort(401, message)
        except:
            # client has non-existing session_id or bad user
            del client_session["session_id"]
            message = "Invalid session"
            app.logger.exception(message)
            abort(401, message)

        user_status = g.user.check_status()
        if user_status == "ok": # all ok
            app.logger.debug("Session ok")
            # proceed with session
            return None
        
        elif user_status == "unverified": # credentials ok, but email not verified
            app.logger.debug("Session needs verifying")
            # allow logout and access to verification page
            if request.path in ["/verify_email", "/logout"]:
                return None
            else: # attempted normal access
                # redirect to verification
                return redirect(url_for("verify_email"))
        
        else: # account locked or disabled
            del client_session["session_id"]
            server_session.delete()
            message = "Your access is temporarily suspended, please come back later."
            app.logger.warning(message)
            abort(403, message)
    
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
            try:
                server_session.save()
            except Exception:
                message = "Failed to update session"
                app.logger.exception(message)
                response = make_response(render_template("error_internal_server_error.html.j2", message=message), 500)
    return response

### ERROR HANDLING
@app.errorhandler(401)
def unauthorized(error):
    return render_template("error_unauthorized.html.j2", message=error.description), 401

@app.errorhandler(400)
def bad_request(error):
    return render_template("error_bad_request.html.j2", message=error.description), 400

@app.errorhandler(403)
def forbidden(error):
    return render_template("error_forbidden.html.j2", message=error.description), 403

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("error_internal_server_error.html.j2", message=error.description), 500

### HOME PAGE
@app.route("/", methods=["GET"])
def index():
    if "session_id" not in client_session:
        return redirect(url_for("login"))
    return render_template("index.html.j2")

### LOGIN AND REGISTRATION
@app.route("/login", methods=["GET", "POST"])
def login():

    if "session_id" in client_session:
        app.logger.debug("already logged in")
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        username = request.form["username"]
        password = request.form["password"]
        try:
            user = User(username=username)
            login_status = user.login(password)
        except ValueError: # user not found
            login_status = "invalid credentials" 
        except Exception:
            message = "Login failed"
            app.logger.exception(message)
            abort(500, message)
        
        if login_status == "invalid credentials":
            return render_template("login.html.j2", form=form, error=True)
        elif login_status == "rejected":
            message = "Your access is temporarily suspended, please come back later."
            app.logger.warning(message)
            abort(403, message)
        elif login_status == "ok":
            try:
                session_id = server_session.new(user_id=user.id)
            except Exception:
                message = "Failed to create a new session"
                app.logger.exception(message)
                abort(500, message)
            app.logger.info("Login ok")
            client_session["session_id"] = session_id
            return redirect(url_for("index"))
        else:
            raise RuntimeError("Invalid login status")
    
    # GET request or invalid form
    return render_template("login.html.j2", form=form)

@app.route("/verify_email", methods=["GET", "POST"])
@needs_user
def verify_email():

    if g.user.verified:
        app.logger.debug("already verified")
        return redirect(url_for("index"))
    
    form = EmailVerificationForm()

    if request.method == "GET":
        return render_template("email_verification.html.j2", form=form, error=False)
    
    elif request.method == "POST":
        app.logger.debug("verifying")
        if form.validate(): # form ok
            code = request.form["code"]
            try:
                valid = g.user.check_verification_code(code)
            except Exception:
                message = "Failed to check verification code"
                app.logger.exception(message)
                abort(500, message)
            if valid:
                app.logger.debug("verified")
                return redirect(url_for("index"))
            else:
                app.logger.debug("not verified")
                return render_template("email_verification.html.j2", form=form, error=True)
        else: # form not ok
            return render_template("email_verification.html.j2", form=form)

@app.route("/logout", methods=["GET"])
def logout():
    if "session_id" in client_session:
        del client_session["session_id"]
        app.logger.debug("Logging out")
        try:
            server_session.delete()
        except Exception:
            message = "Failed to delete session"
            app.logger.exception(message)
            abort(500, message)
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    # already logged in
    if "session_id" in client_session:
        app.logger.debug("already logged in")
        return redirect(url_for("index"))
    
    form = SignupForm()
    if form.validate_on_submit():
        username = request.form["username"]
        password = request.form["password"]

        try:
            User.new(username, password)
        except Exception:
            app.logger.debug("new user fail")
            message = "Failed to register a new user"
            app.logger.exception(message)
            abort(500, message)
        
        app.logger.debug("new user success")
        return render_template("register_complete.html.j2")

    return render_template("register.html.j2", form=form)

### APP FUNCTIONALITY
@app.route("/add", methods=["GET", "POST"])
@needs_user
def add():
    form = CodeForm()
    if request.method == "GET":
        if source_code := server_session.get("source_code"):
            form.code.data = source_code
        return render_template("add.html.j2", form=form)
        
    elif request.method == "POST":
        if form.validate(): #data ok
            source_code = form.code.data

            
            if form.run.data: # clicked run checks
                try:
                    code_format.check_function_only(source_code)
                    server_session["source_code"] = source_code
                except SyntaxError as e:
                    error = str(e)
                    return render_template("add.html.j2", form=form, error=error)
                
                filename = fileops.create_tempfile(source_code)
                try:
                    lint_result = linter.run_pylint(filename)
                    security_result = security.run_bandit(filename)
                    type_result = typecheck.run_pyright(filename)
                finally:
                    fileops.delete_file(filename)
                return render_template("add.html.j2", form=form, lint_result=lint_result, security_result=security_result, type_result=type_result)
            
            elif form.doc.data: # clicked next
                try:
                    code_format.check_function_only(source_code)
                    server_session["source_code"] = source_code
                except SyntaxError as e:
                    error = str(e)
                    return render_template("add.html.j2", form=form, error=error)
                return redirect(url_for("doc"))
            
            else: # unexpected submit
                abort(400)
        
        else: # data not ok
            return render_template("add.html.j2", form=form)

@app.route("/doc", methods=["GET", "POST"])
@needs_user
def doc():
    form = DocForm()
    if request.method == "GET":
        if source_code := server_session.get("source_code"):
            form.code.data = source_code
        if documented := server_session.get("source_code_documented"):
            form.documented.data = documented
        return render_template("doc.html.j2", form=form)

    elif request.method == "POST":
        if form.generate.data: # clicked generate tests
            # TODO: validate source code
            try:
                documented = gpt.enhance_code(form.code.data, mode="doc")
                error = False
            except ValueError:
                error = "Your source code was rejected."
                app.logger.warning(error)
                documented = ""
            except SyntaxError as e:
                error = str(e)
                documented = ""    
            except Exception:
                error = "Failed to generate code documentation."
                app.logger.error(error)
                documented = ""
            form.documented.data = documented
            return render_template("doc.html.j2", form=form, error=error)

        elif form.next.data: # clicked next
            if form.validate(): # data ok
                code = form.code.data
                documented = form.documented.data
                try:
                    code_format.check_function_only(code)
                    code_format.check_function_only(documented)
                except SyntaxError as e:
                    error = str(e)
                    return render_template("doc.html.j2", form=form, error=error)
                server_session["source_code"] = code
                server_session["source_code_documented"] = documented
                return redirect(url_for("test"))
            else: # data not ok
                return render_template("doc.html.j2", form=form)
        else: # unexpected submit
            abort(400)

@app.route("/test", methods=["GET", "POST"])
@needs_user
def test():
    form = TestForm()
    if request.method == "GET":
        if documented := server_session.get("source_code_documented"):
            form.documented.data = documented
        if unittests := server_session.get("source_code_unittests"):
            form.unittests.data = unittests
        return render_template("test.html.j2", form=form)

    if request.method == "POST":
        if form.generate.data: # clicked generate tests
            try:
                unittests = gpt.enhance_code(form.documented.data, mode="test")
                error = False
            except ValueError:
                error = "Your source code was rejected."
                app.logger.warning(error)
                unittests = ""
            except SyntaxError as e:
                error = str(e)
                unittests = ""
            except Exception:
                error = "Failed to generate unit tests"
                app.logger.error(error)
                unittests = ""
            form.unittests.data = unittests
            return render_template("test.html.j2", form=form, error=error)
        elif form.run.data: # clicked run tests
            documented = form.documented.data
            unittests = form.unittests.data
            try:
                code_format.check_function_only(documented)
                code_format.check_unittest(unittests)
            except SyntaxError as e:
                error = str(e)
                return render_template("test.html.j2", form=form, error=error)
            try:
                results = testrunner.execute(func=documented, test=unittests)
                results = json.dumps(results, indent=4)
                error = False
            except Exception:
                error = "Failed to run unit tests"
                app.logger.exception(error)
                results = ""
            return render_template("test.html.j2", form=form, results=results, error=error)
        elif form.next.data: # clicked next
            if form.validate(): # data ok
                documented = form.documented.data
                unittests = form.unittests.data
                try:
                    code_format.check_function_only(documented)
                    code_format.check_unittest(unittests)
                except SyntaxError as e:
                    error = str(e)
                    return render_template("test.html.j2", form=form, error=error)
                server_session["source_code_documented"] = documented
                server_session["source_code_unittests"] = unittests
                return redirect(url_for("classify"))
            else: # data not ok
                return render_template("test.html.j2", form=form)
        else: # unexpected submit
            abort(400)

@app.route("/classify", methods=["GET", "POST"])
@needs_user
def classify():
    form = ClassifyForm()

    if request.method == "GET":
        expected_args = ["source_code_documented", "source_code_unittests"]
        for arg in expected_args:
            if not arg in server_session:
                message = "Invalid parameters"
                app.logger.error(message)
                abort(400, message)
        return render_template("classify.html.j2", form=form)

    if request.method == "POST":
        if form.generate.data: # clicked generate keywords
            try:
                keywords = gpt.classify_code(server_session["source_code_documented"])
                keywords_str = ", ".join(keywords)
                error = False
            except Exception:
                error = "Failed to generate keywords"
                app.logger.exception(error)
                keywords_str = ""
            form.keywords.data = keywords_str
            return render_template("classify.html.j2", form=form, error=error)
        elif form.save.data: # clicked save
            if form.validate(): # data ok
                keywords = {x.strip() for x in form.keywords.data.split(",")}
                keywords_str = ", ".join(keywords)
                name = form.name.data
                usecase = form.usecase.data
                code = server_session["source_code_documented"]
                tests = server_session["source_code_unittests"]
                user_id = g.user.id
                try:
                    gpt.check_code(code, mode="func")
                    gpt.check_code(tests, mode="unit")
                    function_id = function.save_function(code, tests, keywords_str, usecase, name, user_id)
                except ValueError:
                    error = "Your source code was rejected"
                    return render_template("classify.html.j2", form=form, error=error)
                except Exception:
                    error = "Failed to save function"
                    app.logger.exception(error)
                    return render_template("classify.html.j2", form=form, error=error)

                # clear saved function data from session
                for arg in ["source_code", "source_code_documented", "source_code_unittests"]:
                    del server_session[arg]

                return redirect(url_for("view_function", function_id=function_id)) 
            else: # data not ok
                return render_template("classify.html.j2", form=form)
        else: # invalid submit
            abort(400)

@app.route("/delete_function/<int:function_id>", methods=["POST"])
@needs_user
def delete_function(function_id: int):
    try:
        function_data = function.get_function(function_id)
    except Exception:
        message = "Failed to delete function"
        app.logger.exception(message)
        abort(500, message)
    fuid = function_data["user_id"]
    user_id = g.user.id
    user_role = g.user.role
    if fuid == user_id or user_role == "admin":
        function.delete_function(function_id)
        return redirect(url_for("list_functions"))
    else:
        message = "Not authorized to delete functions created by others."
        app.logger.warning(message)
        abort(403, message)
    
@app.route("/function/<int:function_id>", methods=["GET"])
@needs_user
def view_function(function_id):
    try:
        fdata = function.get_function(function_id) 
    except Exception:
        message = "Failed to read function"
        app.logger.exception(message)
        abort(500, message)
    fdata["code"] = code_format.format(fdata["code"])
    fdata["tests"] = code_format.format(fdata["tests"])
    fdata["keywords"] = [x.strip() for x in fdata["keywords"].split(",")]
    fuid = fdata.pop("user_id")
    user_id = g.user.id
    user_role = g.user.role
    delete_permission = fuid == user_id or user_role == "admin"
    rating_permission = fuid != user_id
    average_rating = ratings.calc_avg_rating(function_id)
    default_rating = ratings.get_rating(function_id, user_id)
        
    return render_template("function.html.j2", fdata=fdata, function_id=function_id, default_rating=default_rating, average_rating=average_rating, rating_permission=rating_permission, delete_permission=delete_permission)

@app.route("/functions", methods=["GET"])
@needs_user
def list_functions():
    try:
        fdata = function.list_functions()
    except Exception:
        message = "Failed to list functions"
        app.logger.exception(message)
        abort(500, message)
    return render_template("functions.html.j2", fdata=fdata)

@app.route("/user_management", methods=["GET"])
@needs_admin
def user_management():
    data = user_module.list_users()
    return render_template("user_management.html.j2", data=data)

@app.route("/edit_user/<string:action>/<string:user_id>", methods=["POST"])
@needs_admin
def edit_user(action: str, user_id: str):
    try:
        user = User(user_id=user_id)
        match action:
            case "delete":
                func = user.delete
            case "disable":
                func = user.disable
            case "enable":
                func = user.enable
            case "lock":
                func = user.lock
            case "unlock":
                func = user.unlock
            case "logout":
                func = user.logout
            case "promote":
                func = user.promote
            case "demote":
                func = user.demote
            case _:
                abort(400, "Bad action")
        func()
    except ValueError:
        message = "User does not exist"
        public_message = f"Failed to {action} user" # public message is always same, to prevent user enumeration
        app.logger.error(message)
        abort(500, public_message)
    except Exception:
        message = f"Failed to {action} user"
        app.logger.exception(message)
        abort(500, message)
    
    # invalidating own access
    if user_id == g.user.id and action in ["delete", "disable", "lock", "logout"]:
        del client_session["session_id"]
        return redirect(url_for("index"))
    
    # deleting user
    elif action == "delete":
        return redirect(url_for("user_management"))

    # otherwise
    else:
        return redirect(url_for(f"user", user_id=user_id))
    
@app.route("/user/<string:user_id>", methods=["GET"])
@needs_admin
def user(user_id: str):
    user_functions = function.list_functions_by_user(user_id)
    try:
        user = User(user_id=user_id)
        count_active_sessions = user.count_active_sessions()
    except ValueError:
        message = "User does not exist"
        public_message = f"Failed to view user" # public message is always same, to prevent user enumeration
        app.logger.error(message)
        abort(500, public_message)
    except Exception:
        message = f"Failed to view user"
        app.logger.exception(message)
        abort(500, message)
    return render_template("user.html.j2", user=user, count_active_sessions=count_active_sessions, data=user_functions)


# API-endpoint, not accesible by UI
@app.route("/api/save_rating", methods=["POST"])
@needs_user
def save_rating():
    try:
        try:
            # parse input
            value = int(request.form.get("rating"))
            function_id = int(request.form.get("function_id"))
        
            # validate input
            if not value or value not in range(1, 6):
                raise ValueError
        except Exception:
            return "", 400

        try:
            # create rating object
            rating = ratings.Rating(function_id, g.user.id, value)
        except PermissionError:
            return "", 403
        
        # write the rating to db
        rating.save()

        # return new average rating
        return {"average": ratings.calc_avg_rating(function_id)}, 201

    except Exception:
        return "", 500