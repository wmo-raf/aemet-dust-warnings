import logging
import sys

import graypy
from flask import Flask, jsonify
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from healthcheck import HealthCheck
from werkzeug.security import check_password_hash

from dustwarning.config import SETTINGS

logging.basicConfig(
    level=SETTINGS.get('logging', {}).get('level'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y%m%d-%H:%M%p',
)

# Flask App
app = Flask(__name__, template_folder=SETTINGS.get("TEMPLATE_DIR"))
auth = HTTPBasicAuth()
CORS(app)

# Ensure all unhandled exceptions are logged
logger = logging.getLogger(__name__)
logger.setLevel(SETTINGS.get('logging', {}).get('level'))
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

if SETTINGS.get("GRAYLOG_HOST") and SETTINGS.get("GRAYLOG_PORT"):
    handler = graypy.GELFUDPHandler(SETTINGS.get("GRAYLOG_HOST"), int(SETTINGS.get("GRAYLOG_PORT")))
    logger.addHandler(handler)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = SETTINGS.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# pagination
app.config['ITEMS_PER_PAGE'] = SETTINGS.get('ITEMS_PER_PAGE', 20)

# Database
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# wrap flask app and give a healthcheck url
health = HealthCheck(app, "/healthcheck")


def db_available():
    db.session.execute('SELECT 1')
    return True, "dbworks"


health.add_check(db_available)

# DB has to be ready!
from dustwarning.routes.api.v1 import endpoints, error


@auth.verify_password
def verify_password(username, password):
    if SETTINGS.get("API_USERNAME") and SETTINGS.get("API_PASSWORD_HASH") and SETTINGS.get("API_USERNAME") == username \
            and check_password_hash(SETTINGS.get("API_PASSWORD_HASH"), password):
        return True
    return False


@auth.error_handler
def auth_error(status):
    return jsonify(message="Unauthorized"), status


# Blueprint Flask Routing
app.register_blueprint(endpoints, url_prefix='/api/v1')


@app.errorhandler(403)
def forbidden(e):
    return error(status=403, detail='Forbidden')


@app.errorhandler(404)
def page_not_found(e):
    return error(status=404, detail='Not Found')


@app.errorhandler(405)
def method_not_allowed(e):
    return error(status=405, detail='Method Not Allowed')


@app.errorhandler(410)
def gone(e):
    return error(status=410, detail='Gone')


@app.errorhandler(500)
def internal_server_error(e):
    return error(status=500, detail='Internal Server Error')


from dustwarning import commands

app.cli.add_command(commands.setup_schema)
app.cli.add_command(commands.load_boundaries)
app.cli.add_command(commands.load_warnings)
