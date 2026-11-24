import pytest

from app.input import sample
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    return create_app(tmp_path / 'inspection.sqlite').test_client()


@pytest.fixture
def dirty():
    return sample('dirty')


@pytest.fixture
def clean():
    return sample('clean')
