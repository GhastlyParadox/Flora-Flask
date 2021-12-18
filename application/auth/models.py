from application import auth_db
from flask_security import UserMixin, RoleMixin, SQLAlchemySessionUserDatastore, current_user
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, Column, Table
from sqlalchemy.orm import relationship, backref


roles_users = Table(
    'roles_users', auth_db.Model.metadata,
    Column('user_id', Integer(), ForeignKey('user.id')),
    Column('role_id', Integer(), ForeignKey('role.id')),
    info={'bind_key': 'auth_db'}
)


class Role(auth_db.Model, RoleMixin):
    __tablename__ = 'role'
    __bind_key__ = 'auth_db'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))


class User(auth_db.Model, UserMixin):
    __tablename__ = 'user'
    __bind_key__ = 'auth_db'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    uniqname = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean())
    is_authenticated = Column(Boolean())
    confirmed_at = Column(DateTime())
    roles = relationship('Role',
                         secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))


class OAuth(OAuthConsumerMixin, auth_db.Model):
    __bind_key__ = 'auth_db'
    provider_user_id = Column(String(256), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    user = relationship(User)


def init_auth_db():
    auth_db.create_all(bind='auth_db')


# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(auth_db.session, User, Role)
