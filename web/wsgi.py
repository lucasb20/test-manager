import logging
from logging.handlers import SMTPHandler
from flask import Flask, render_template
from flask_migrate import Migrate
from db import db
from routes.auth import bp as auth_bp
from routes.project import bp as project_bp
from routes.testcase import bp as testcase_bp
from routes.testsuite import bp as testsuite_bp
from routes.testrun import bp as testrun_bp
from routes.requirement import bp as requirement_bp
from routes.profile import bp as profile_bp
from routes.member import bp as member_bp
from utils import format_datetime, database_uri

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri("testdb", psswd_file='/run/secrets/db-password')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.register_blueprint(auth_bp)
app.register_blueprint(project_bp)
app.register_blueprint(testcase_bp)
app.register_blueprint(testrun_bp)
app.register_blueprint(testsuite_bp)
app.register_blueprint(requirement_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(member_bp)

db.init_app(app)
Migrate(app, db)

@app.route("/")
def index():
    return render_template('index.html')

app.jinja_env.filters['format_datetime'] = format_datetime

if not app.debug:
    mail_handler = SMTPHandler(
        mailhost=('maildev', 1025),
        fromaddr='server-error@example.com',
        toaddrs=['admin@example.com'],
        subject='Application Error'
    )
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    app.logger.addHandler(mail_handler)
