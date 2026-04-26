import pytest

@pytest.fixture
def base_url():
    return "http://localhost:8000"

@pytest.fixture(scope="session")
def login_url(base_url):
    return base_url + "/auth/login"

@pytest.fixture(scope="session")
def register_url(base_url):
    return base_url + "/auth/register"

@pytest.fixture(scope="session")
def reset_url(base_url):
    return base_url + "/auth/reset"

@pytest.fixture(scope="session")
def profile_url(base_url):
    return base_url + "/profile/index"
