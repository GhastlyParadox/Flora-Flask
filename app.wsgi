activate_this = '/var/www/python-projects/herbflask_env/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

import sys
path = '/var/www/python-projects/herbflask'
if path not in sys.path:
    sys.path.insert(0, path)
from application import create_app
application = create_app()
