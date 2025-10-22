from flask import Flask, render_template
from flask_migrate import Migrate
from db import db
from routes.auth import bp as auth_bp
from routes.project import bp as project_bp
from routes.testcase import bp as testcase_bp
from routes.testplan import bp as testplan_bp
from routes.testexec import bp as execution_bp
from routes.requirement import bp as requirement_bp
from utils import format_datetime, database_uri


app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri("testdb", password_file='/run/secrets/db-password')

app.register_blueprint(auth_bp)
app.register_blueprint(project_bp)
app.register_blueprint(testcase_bp)
app.register_blueprint(execution_bp)
app.register_blueprint(testplan_bp)
app.register_blueprint(requirement_bp)

db.init_app(app)
Migrate(app, db)

@app.route("/")
def index():
    return render_template('index.html')

app.jinja_env.filters['format_datetime'] = format_datetime