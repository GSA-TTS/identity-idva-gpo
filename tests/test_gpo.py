""" GPO API unit tests """
from fastapi.testclient import TestClient
from gpo.main import app

client = TestClient(app)
