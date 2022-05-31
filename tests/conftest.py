"""fixtures"""
import sys
import typing

import pytest
from fastapi import testclient

import db

# pylint: disable=wrong-import-position
sys.modules["gpo.database"] = db
from gpo import main, models


@pytest.fixture
def generate_data():
    """test fixture"""

    def get_letter() -> models.Letter:
        """get a letter object"""
        return models.Letter(
            id=5,
            name="Name",
            address="Address",
            address2="Address 2",
            city="City",
            state="State",
            zip="Zip",
            code="Code",
            date="Date",
            expiry="Date",
            app="App",
            url="Url",
        )

    return get_letter


@pytest.fixture(scope="session")
def session() -> typing.Generator:
    """session"""
    yield db.SessionLocal()


@pytest.fixture(scope="module")
def client() -> typing.Generator:
    """api test client"""
    with testclient.TestClient(main.app) as test_client:
        yield test_client
