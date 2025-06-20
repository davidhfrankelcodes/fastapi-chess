import requests

BASE_URL = "http://127.0.0.1:8000"

def assert_condition(cond, msg):
    if not cond:
        raise AssertionError(msg)

def print_status(step):
    print(f"✅ {step}")

def check_status(game_id, expect_check=False, expect_checkmate=False):
    r = requests.get(f"{BASE_URL}/status/{game_id}")
    status = r.json()
    if expect_check:
        assert status["is_check"], f"Expected check, but wasn't"
        print("☑️  CHECK detected")
    if expect_checkmate:
        assert status["is_checkmate"], "Expected checkmate, but wasn't"
        print("☑️  CHECKMATE detected")
    return status

def smoketest():
    print("🚀 Starting smoketest with mid-game check + final checkmate")

    # Create game
    r = requests.post(f"{BASE_URL}/start_game")
    data = r.json()
    game_id = data["game_id"]
    white_token = data["white_token"]
    black_token = data["black_token"]
    print_status("Game created")

    # Join players
    r = requests.post(f"{BASE_URL}/join_game/{game_id}?token={white_token}")
    assert r.json()["role"] == "white"
    print_status("White joined")

    r = requests.post(f"{BASE_URL}/join_game/{game_id}?token={black_token}")
    assert r.json()["role"] == "black"
    print_status("Black joined")

    # Moves
    moves = [
        ("e2e4", white_token),   # 1
        ("e7e5", black_token),   # 2
        ("d1h5", white_token),   # 3
        ("b8c6", black_token),   # 4
        ("f1c4", white_token),   # 5
        ("g8f6", black_token),   # 6
        ("h5f7", white_token),   # 7 — CHECK!
        ("e8e7", black_token),   # 8 — escape check
        ("c4d5", white_token),   # 9
        ("f6d5", black_token),   # 10
        ("e4d5", white_token),   # 11
        ("e7d6", black_token),   # 12
        ("f7e6", white_token),   # 13 — CHECKMATE
    ]

    for i, (uci, token) in enumerate(moves, start=1):
        r = requests.post(f"{BASE_URL}/move/{game_id}?token={token}", json={"move": uci})
        assert r.status_code == 200, f"Move {i} failed: {uci}"
        print_status(f"Move {i} ({uci}) executed")

        # Status checks
        if i == 7:
            check_status(game_id, expect_check=True)
        elif i == 13:
            check_status(game_id, expect_check=True, expect_checkmate=True)

    # Final board
    r = requests.get(f"{BASE_URL}/board/{game_id}")
    assert r.status_code == 200
    assert len(r.json()["board"]) == 8
    print_status("Final board returned")

    # Delete game
    r = requests.delete(f"{BASE_URL}/game/{game_id}")
    assert r.status_code == 200
    print_status("Game deleted")

    # Confirm deletion
    r = requests.get(f"{BASE_URL}/fen/{game_id}")
    assert r.status_code == 404
    print_status("Deletion confirmed")

    print("🎉 Extended SMOKETEST PASSED")

if __name__ == "__main__":
    smoketest()
