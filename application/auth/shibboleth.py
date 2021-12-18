from flask import flash, redirect, url_for, jsonify, current_app as app
from flask_security import current_user, login_user, login_required, logout_user, roles_required
from oauthlib.oauth2.rfc6749.errors import InvalidClientIdError, TokenExpiredError
from flask_dance.consumer import OAuth2ConsumerBlueprint, oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from .models import OAuth, User, Role
from application import auth_db
from application import logger


shibboleth = OAuth2ConsumerBlueprint(
    'shibboleth', __name__,
    client_id=app.config.get('CLIENT_ID'),
    client_secret=app.config.get('CLIENT_SECRET'),
    base_url=app.config.get('BASE_URL'),
    token_url=app.config.get('TOKEN_URL'),
    authorization_url=app.config.get('AUTHORIZATION_URL'),
    authorized_url=app.config.get('AUTHORIZED_URL'),
    scope=app.config.get('SCOPE'),
    storage=SQLAlchemyStorage(OAuth, auth_db.session, user=current_user)
)


def is_admin(username):
    admins = app.config.get('ADMINS')
    return True if username in admins else False


@shibboleth.before_app_first_request
def before_first_request():
    # Admin role check/create
    admin_role_query = Role.query.filter_by(name='admin')
    try:
        admin_role = admin_role_query.one()
    except NoResultFound:
        admin_role = Role(name='admin', description='Administrator')
        auth_db.session.add(admin_role)
        auth_db.session.commit()

    # End user role check/create
    end_user_role_query = Role.query.filter_by(name='end-user')
    try:
        end_user_role = end_user_role_query.one()
    except NoResultFound:
        end_user_role = Role(name='end-user', description='End user')
        auth_db.session.add(end_user_role)
        auth_db.session.commit()


# Create/login local user on successful OAuth login
@oauth_authorized.connect_via(shibboleth)
def shibboleth_logged_in(shibboleth, token):

    if not token:
        flash('Failed to log in.', category='error')
        return False

    resp = shibboleth.session.get('/idp/profile/oidc/userinfo')
    if not resp.ok:
        msg = 'Failed to fetch user info.'
        flash(msg, category='error')
        return False

    info = resp.json()
    user_id = info['preferred_username']

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(provider=shibboleth.name, provider_user_id=user_id)
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider=shibboleth.name, provider_user_id=user_id, token=token)

    if oauth.user:
        login_user(oauth.user)
        flash('Successfully signed in.')

    else:
        # Create a new local user account for this user
        user = User(email=info['email'],
                    uniqname=info['preferred_username'],
                    first_name=info['given_name'],
                    last_name=info['family_name'],
                    active=True)
        # Add end-user role.
        user.roles.append(Role.query.filter_by(name='end-user').one())

        # Admin role check
        if is_admin(user_id):
            user.roles.append(Role.query.filter_by(name='admin').one())

        auth_db.session.add(user)
        auth_db.session.commit()

        # Associate the new local user account with the OAuth token
        oauth.user = user
        # Save and commit our database models
        auth_db.session.add_all([user, oauth])
        auth_db.session.commit()
        # Log in the new local user account
        login_user(user)
        flash('Successfully signed in.')

    # Disable Flask-Dance's default behavior for saving the OAuth token
    return False


# Login
@shibboleth.route("/login")
def auth():
    return redirect(url_for("shibboleth.login"))


# Logout
@shibboleth.route("/logout", methods=['GET'])
def logout():

    if not shibboleth.authorized:
        logger.info("not logged in")
        return redirect(url_for('routes_bp.index'))

    try:
        resp = shibboleth.session.post(
            app.config.get('REVOKE_URL'),
            params={'token': app.blueprints['shibboleth'].session.token["access_token"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if resp.ok:
            del app.blueprints['shibboleth'].token
            auth_db.session.clear()
            logout_user()
        return redirect(url_for('routes_bp.index'))

    except TokenExpiredError as e:
        logger.info("Token expired")
        logout_user()
        return redirect(url_for('routes_bp.index'))


# Retrieve current user info
@shibboleth.route("/getuser")
def get_user():

    if not shibboleth.authorized:
        logger.info("not logged in")
        return redirect(url_for('routes_bp.index'))

    return jsonify(first_name=current_user.first_name,
                   email=current_user.email,
                   authenticated=True,
                   admin=is_admin(current_user.uniqname))


# notify on OAuth provider error
@oauth_error.connect_via(shibboleth)
def shibboleth_error(shibboleth, message, response):
    msg = 'OAuth error from {name}! message={message} response={response}'.format(
        name=shibboleth.name, message=message, response=response
    )
    flash(msg, category='error')
