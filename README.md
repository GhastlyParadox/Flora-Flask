# FloraFlask

Michigan Flora backend, includes Flora REST API to interact with the MI Flora and Specimen database.

### Setup ###

* [Full Install/Integration Guide](https://docs.google.com/document/d/1p4lBaYQCF9Z6s2T9dtoVux1KuPlIZxOR0TTdBZREXvQ/edit#): Describes how to set up and run the full stack locally, as well as deployment to the server.

### Installation:

1. Create a virtual environment for the code.
    * On Apache server - If you use Python 3's venv command, it will not install
    the needed activate_this.py script, so you'll need to provide this. See [here][3] for details.
    * Any other setup - Follow the [standard method][1].
2. Activate the virtual environment in your terminal.
    ```bash
    source /path/to/env/bin/activate
    ```
3. Install the required packages [via pip3][2]
    * Required packages are in requirements.txt. Install using:
    
    ``pip3 install -r requirements.text`` or ```python3 -m pip install -r requirements.txt```
    
4. Create an [instance folder](https://flask.palletsprojects.com/en/1.1.x/config/#instance-folders) within the 
root directory, and place [authConfig.py](https://drive.google.com/drive/u/0/folders/1Y98R1AqNs84PJ6DFfjpBtrtMciezgpKB) in there. The user database will be created/stored there as well.

5. Put the credential file (something like mif_bet_cred.p) in the application folder. This file can be created
with write_credentials in core.py and contains a pickled version of the username and password
for non-admin access to the database.

## Deployment Notes

 * For authentication, there are two REDIRECT_URI variables defined in authConfig -
    one for local/development, the other for production/server. Be sure the correct one 
    is set for the environment.
 *  For authentication in a local environment, there's an additional line in
    [__init__.py](https://gitlab.umich.edu/lsa-ts-rsp/herbflask/blob/master/__init__.py):
        `os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"`
    *Remove this line when deploying to the server.*
 * Note that once the code has been deployed to the server (currently miflora-beta.lsait.lsa.umich.edu), 
 you must touch the app.wsgi file in order to trigger Apache server to restart the app.
 This can be done with the command 
 `touch app.wsgi`.
 
[1]: https://docs.python.org/3/library/venv.html
[2]: https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#using-requirements-files
[3]: https://stackoverflow.com/questions/25020451/no-activate-this-py-file-in-venv-pyvenv
