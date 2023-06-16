import importlib

from django.conf import settings
from django.test import Client
from django.core.management import call_command

# SQLAlchemy
from sqlalchemy_utils import drop_database, create_database, database_exists
from sqlalchemy.orm.session import Session

# Lamb Framework
import lamb.db.session
from lamb.db.session import metadata, lamb_db_session_maker

import pytest

# Project
from api.models import SuperAdmin, AbstractUser

from .factories import *


@pytest.fixture(autouse=True)
def db() -> Session:
    settings.DATABASES["default"]["NAME"] = "test_core"
    importlib.reload(lamb.db.session)
    session = lamb_db_session_maker()

    db_url = session.get_bind().url
    if database_exists(db_url):
        drop_database(db_url)
    create_database(session.get_bind().url)

    session.execute("CREATE EXTENSION pgcrypto")
    session.commit()

    metadata.bind = session.get_bind()
    metadata.create_all()
    # fill_handbooks
    call_command("fill_handbooks")

    session = lamb_db_session_maker()
    AlchemyModelFactory._meta.sqlalchemy_session = session
    yield session
    session.rollback()
    drop_database(db_url)


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def admin_user(db: Session) -> SuperAdmin:
    admin_user = db.query(AbstractUser).filter(AbstractUser.email == 'super_admin@example.com').first()
    return admin_user


@pytest.fixture
def another_user(db: Session) -> AbstractUser:
    user: AbstractUser = OperatorFactory.create()
    user.set_password('AnotherVeryStrongPassword')
    db.add(user)
    db.commit()
    return user
