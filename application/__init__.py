from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
import os
import logging
from flask_cors import CORS
import sqlite3


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGFILE = os.path.join('/var/log/miflora/herbflask.log')
CREDENTIALS_FILE = os.path.join(APP_ROOT, 'mif_prod2.p')
MIFLORA_BASE = declarative_base()

# When this app is run via the Apache wsgi module, we need to use the logging functions to capture output that would
# typically be printed to the console.  In fact, the 'print' function will enrage Apache, so make sure to only use the
# log.
try:
    logging.basicConfig(filename=LOGFILE,
                        level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
except Exception:
    LOGFILE = os.path.join(APP_ROOT, 'herbflask.log')
    logging.basicConfig(filename=LOGFILE,
                        level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


logger = logging.getLogger(__name__)

logger.info(APP_ROOT)

# Auth database
auth_db = SQLAlchemy()

# Flora database
from .db.miflora import MIFloraDB
flora_db = MIFloraDB()


def create_app():
    """Construct the core application."""

    # Both Flask and Vue use '{{ variable }}' by default for view templates; changing Flask
    class VueFlask(Flask):
        jinja_options = Flask.jinja_options.copy()
        jinja_options.update(dict(
            variable_start_string='%%',
            variable_end_string='%%',
        ))

    # Using Flask instance folder to store auth_config and db: https://exploreflask.com/en/latest/configuration.html
    app = VueFlask(__name__,
                   static_folder='../static',
                   template_folder='../templates',
                   instance_relative_config=True)

    app.config.from_pyfile('authConfig.py', silent=True)
    app.secret_key = app.config.get('SECRET_KEY')
    CORS(app)

    with app.app_context():
        from .routes.routes_bp import routes_bp
        from .auth.shibboleth import shibboleth, is_admin
        from .auth.models import init_auth_db, user_datastore
        from .db.init_db import init_flora_db
        from flask_security import Security
        from flask_security import current_user

        # Flora DB
        flora_db.init_app(app)
        try:
            init_flora_db()
        except Exception as e:
            # This should also log the stack trace to make debugging easier.
            logger.exception(str(e))

        from .resources.api_bp import api_bp
        from .admin.admin_bp import admin_bp

        # Auth DB
        auth_db.init_app(app)
        try:
            logger.debug("Trying init_auth_db()")
            init_auth_db()
            logger.debug("init_auth_db succeeded")
        except sqlite3.OperationalError as e:
            logger.exception(str(e))
            pass
        except Exception as e:
            logger.exception(str(e))

        # Register routes blueprint
        app.register_blueprint(routes_bp)

        # Register resource-api blueprint
        app.register_blueprint(api_bp, url_prefix="/api/v1.0")

        # Register shibboleth blueprint
        app.register_blueprint(shibboleth, url_prefix="/auth")

        # Register flora-admin blueprint
        app.register_blueprint(admin_bp, url_prefix="/admin")

        # Setup Flask-Security.
        # The last bit disables Flask Security's routes, which were hijacking ones aimed at shibboleth.
        security = Security(app,
                            datastore=user_datastore,
                            SECURITY_REGISTERABLE=False)

        import flaskfilemanager
        from flaskfilemanager.filemanager import filemanager_blueprint
        flaskfilemanager.init(app, url_prefix="/fm/species-images", access_control_function=is_admin(current_user))
        # app.register_blueprint(filemanager_blueprint, url_prefix="/fm/species-images")

    return app
