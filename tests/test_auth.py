# SQLAlchemy
from sqlalchemy.orm.session import Session

# Lamb Framework
from lamb.exc import AuthCredentialsInvalid

import pytest

# Project
from api.models import SuperAdmin, RefreshToken
from api.auth.auth_engines.email import EmailAuthEngine


@pytest.fixture
def email_auth_engine(db: Session) -> EmailAuthEngine:
    return EmailAuthEngine(db_session=db)


@pytest.mark.parametrize(
        argnames=['email', 'password', 'user'],
        argvalues=[
            ('super_admin@example.com', 'StrongPass777', SuperAdmin),
            ('not_super_admin@example.com', 'StrongPass777', None),
        ],
)
def test_email_auth_engine_get_info(email_auth_engine: EmailAuthEngine,
                                    email: str,
                                    password: str,
                                    user: SuperAdmin | None):
    result_email, result_password, result_user = email_auth_engine._get_info(
        credentials={
            'email': email,
            'password': password,
        }
    )
    assert result_email == email
    assert result_password == password
    if not user:
        assert result_user is None
    else:
        assert result_user.first_name == 'admin'
        assert result_user.last_name == 'super'


@pytest.mark.parametrize(
        argnames=['email', 'password', 'user'],
        argvalues=[
            ('super_admin@example.com', 'StrongPass777', SuperAdmin),
            ('not_super_admin@example.com', 'StrongPass777', None),
        ],
)
def test_email_auth_engine_authenticate(email_auth_engine: EmailAuthEngine,
                                        email: str,
                                        password: str,
                                        user: SuperAdmin | None,
                                        db: Session):
    if user:
        assert not db.query(RefreshToken).all()
        access_token, refresh_token, result_user = email_auth_engine.authenticate(
            {
                'email': email,
                'password': password,
            }
        )
        assert access_token
        assert refresh_token
        assert result_user.email == email
        assert result_user.first_name == 'admin'
        assert result_user.last_name == 'super'
        token: RefreshToken = db.query(RefreshToken).first()
        assert token.user_id == result_user.user_id
        assert token.value == refresh_token
    else:
        with pytest.raises(AuthCredentialsInvalid):
            email_auth_engine.authenticate(
                {
                    'email': email,
                    'password': password,
                }
            )
