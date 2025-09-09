import pytest
import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture
def new_game(base_url):
    """
    Generates a fresh UUID game_id. The server will auto-initialize the game
    on first use of this ID (e.g., when calling /move, /fen, /status, etc.).
    """
    gid = str(uuid.uuid4())
    yield gid
    # cleanup
    requests.delete(f"{base_url}/game/{gid}")

