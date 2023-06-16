from datetime import datetime, timedelta
from http import HTTPStatus

from django.apps import apps
from django.urls import reverse
from django.test.client import Client

import pytest
from freezegun import freeze_time

# Project
from api.utils import get_handbooks_values
from api.models import AbstractUser, Operator, SettingsValue, SuperAdmin, handbook_map



def test_ping(client: Client):
    response = client.get(reverse("api:ping"), content_type="application/json")
    assert response.status_code == 200
    assert response.json() == {"response": "pong"}



@pytest.mark.parametrize(
        argnames=['email', 'password', 'expected_status'],
        argvalues=[
            ('some@email.com', 'StrongPassword', HTTPStatus.UNAUTHORIZED),
            ('super_admin@example.com', 'StrongPass777', HTTPStatus.OK)
        ]
)
def test_auth_creds(client: Client,
                    email: str,
                    password: str,
                    expected_status: HTTPStatus):
    response = client.post(
        reverse("api:auth"),
        content_type="application/json",
        data={
            "engine": "email",
            "credentials": {
                "email": email,
                "password": password,
            },
        },
    )
    assert response.status_code == expected_status
    if response.status_code == HTTPStatus.OK:
        response_data: dict = response.json()
        assert response_data.get('access_token')
        user: dict = response_data.get('user')
        assert user.get('email') == "super_admin@example.com"


def test_auth_token_expires(client: Client):
    initial_time = datetime.utcnow()
    response = client.post(
        reverse("api:auth"),
        content_type="application/json",
        data={
            "engine": "email",
            "credentials": {
                "email": 'super_admin@example.com',
                "password": 'StrongPass777',
            },
        },
    )
    token = response.json().get('access_token')
    headers = {'HTTP_X_LAMB_AUTH_TOKEN': token}
    response = client.get(
        reverse('api:user', args=('me',)),
        **headers
    )
    assert response.status_code == HTTPStatus.OK
    with freeze_time(initial_time + timedelta(minutes=SettingsValue.access_token_timeout.val + 1)):
        response = client.get(
            reverse('api:user', args=('me',)),
            **headers
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_admin_can_see_another_user(client: Client,
                                    another_user: AbstractUser):
    response = client.post(
        reverse("api:auth"),
        content_type="application/json",
        data={
            "engine": "email",
            "credentials": {
                "email": 'super_admin@example.com',
                "password": 'StrongPass777',
            },
        },
    )
    token = response.json().get('access_token')
    headers = {'HTTP_X_LAMB_AUTH_TOKEN': token}
    response = client.get(
        reverse('api:user', args=(another_user.user_id,)),
        **headers
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data.get('user_id') == str(another_user.user_id)


def test_user_cant_see_another_user(client: Client,
                                    another_user: AbstractUser,
                                    admin_user: SuperAdmin,
                                    db):
    response = client.post(
        reverse("api:auth"),
        content_type="application/json",
        data={
            "engine": "email",
            "credentials": {
                "email": another_user.email,
                "password": 'AnotherVeryStrongPassword',
            },
        },
    )
    users = db.query(AbstractUser).all()
    token = response.json().get('access_token')
    headers = {'HTTP_X_LAMB_AUTH_TOKEN': token}
    response = client.get(
        reverse('api:user', args=(admin_user.user_id,)),
        **headers
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_app_version_view(client: Client):
    response = client.get(
        reverse('api:app_versions'),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        app.name: app.module.__version__ for app in apps.get_app_configs() if hasattr(app.module, "__version__")
    }


def test_handbooks_list_view(client: Client):
    response = client.get(
        reverse('api:handbooks_list'),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        handbook_name: get_handbooks_values(response.wsgi_request, handbook_class)
        for handbook_name, handbook_class in handbook_map.items()
    }


@pytest.mark.parametrize(
        argnames=['data', 'expected_status',],
        argvalues=[
            ('configs', HTTPStatus.OK),
            ('user_types', HTTPStatus.OK),
            ('not_in_handbook', HTTPStatus.NOT_FOUND)
        ]
)
def test_handbooks_item_list(client: Client,
                             data: str,
                             expected_status: HTTPStatus):
    response = client.get(
        reverse('api:handbooks_item_list', args=(data,))
    )
    assert response.status_code == expected_status
