from application import create_app
import os
import logging


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGFILE = os.path.join(PROJECT_ROOT, 'herbflask.log')

# When this app is run via the Apache wsgi module, we need to use the logging functions to capture output that would
# typically be printed to the console.  In fact, the 'print' function will enrage Apache, so make sure to only use the
# log.
logging.basicConfig(filename=LOGFILE,
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    # os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"  # This is for development. Remove in production.
    try:
        app.run(debug=False)
    except Exception as e:
        logger.exception(str(e))
