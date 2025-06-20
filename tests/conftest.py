import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture
def new_game(base_url):
    """Starts a fresh game and yields (game_id, white_token, black_token)."""
    r = requests.post(f"{base_url}/start_game")
    data = r.json()
    yield data["game_id"], data["white_token"], data["black_token"]
    # cleanup
    requests.delete(f"{base_url}/game/{data['game_id']}")
