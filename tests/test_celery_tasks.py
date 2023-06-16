from http import HTTPStatus

# SQLAlchemy
from sqlalchemy.orm.session import Session

# Lamb Framework
from lamb.exc import ServerError

import pytest
from pytest import MonkeyPatch
from requests import Response

# Project
from api.tasks import store_exchanges_rates_task
from api.models import AbstractUser, ExchangeRatesRecord


@pytest.fixture
def fake_200_response() -> Response:
    response = Response()
    response.status_code = HTTPStatus.OK
    response._content = b'{\n    "disclaimer": "https://www.cbr-xml-daily.ru/#terms",\n    "date": "2023-06-16",\n    "timestamp": 1686862800,\n    "base": "RUB",\n    "rates": {\n        "AUD": 0.017461179,\n        "AZN": 0.02024746,\n        "GBP": 0.0093811,\n        "AMD": 4.603797,\n        "BYN": 0.0355558,\n        "BGN": 0.0215516,\n        "BRL": 0.057716,\n        "HUF": 4.108092,\n        "VND": 282.32158687,\n        "HKD": 0.093031,\n        "GEL": 0.03114896,\n        "DKK": 0.0821227,\n        "AED": 0.043745297,\n        "USD": 0.011910277,\n        "EUR": 0.01099305788,\n        "EGP": 0.367989,\n        "INR": 0.983545,\n        "IDR": 177.40373186,\n        "KZT": 5.3615278,\n        "CAD": 0.01583709,\n        "QAR": 0.043353478,\n        "KGS": 1.0432217,\n        "CNY": 0.0852108,\n        "MDL": 0.212272,\n        "NZD": 0.0193223,\n        "NOK": 0.1263489,\n        "PLN": 0.04907879,\n        "RON": 0.0544668,\n        "XDR": 0.00892951,\n        "SGD": 0.016009785,\n        "TJS": 0.12998289,\n        "THB": 0.414427,\n        "TRY": 0.281323,\n        "TMT": 0.0416859,\n        "UZS": 136.7059605,\n        "UAH": 0.439896888,\n        "CZK": 0.2620737,\n        "SEK": 0.12784846,\n        "CHF": 0.01075736,\n        "RSD": 1.291382,\n        "ZAR": 0.218319,\n        "KRW": 15.2511095,\n        "JPY": 1.670773986\n    }\n}'
    return response


@pytest.fixture
def fake_418_response() -> Response:
    response = Response()
    response.status_code = HTTPStatus.IM_A_TEAPOT
    response._content = b'{}'
    return response


def test_store_exchanges_rates_task_200(db: Session,
                                        monkeypatch: MonkeyPatch,
                                        fake_200_response: Response,
                                        admin_user: AbstractUser):
    def mocked_get(url, params=None, **kwargs) -> Response:
        return fake_200_response
    assert not db.query(ExchangeRatesRecord).all()
    monkeypatch.setattr('requests.get', mocked_get)
    store_exchanges_rates_task(admin_user.user_id)
    record: ExchangeRatesRecord = db.query(ExchangeRatesRecord).first()
    assert record.actor_id == admin_user.user_id
    assert record.rate == 0.011910277


def test_store_exchanges_rates_task_not_200(db: Session,
                                            monkeypatch: MonkeyPatch,
                                            fake_418_response: Response,
                                            admin_user: AbstractUser):
    def mocked_get(url, params=None, **kwargs) -> Response:
        return fake_418_response
    monkeypatch.setattr('requests.get', mocked_get)
    with pytest.raises(ServerError):
        store_exchanges_rates_task(admin_user.user_id)
    assert not db.query(ExchangeRatesRecord).all()
