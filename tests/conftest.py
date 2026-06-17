import pytest

from app.main import app as fastapi_app
from app.database import Base, engine
import app.models


@pytest.fixture(scope="session", autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def app():
    return fastapi_app
