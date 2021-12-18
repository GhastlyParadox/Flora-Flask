from flask import send_from_directory, Blueprint, send_from_directory, current_app as app
from application import logger
import os


routes_bp = Blueprint('routes_bp', __name__, template_folder='../../templates', static_folder='../../static')


# catches undefined routes and passes them to Vue
@routes_bp.route("/", defaults={"path": ""}, methods=['GET'])
@routes_bp.route("/<string:path>", methods=['GET'])
@routes_bp.route("/<path:path>", methods=['GET'])
def index(path):
    return send_from_directory(app.template_folder, "index.html")

'''
@routes_bp.route("/static/species-images/<path:path>/<path:filename>", methods=['GET'])
def send_image(path, filename):
    return send_from_directory(os.path.join(app.config.get('IMAGES_FOLDER'), path), filename)
'''