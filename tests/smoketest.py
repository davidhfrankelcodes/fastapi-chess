import requests

BASE_URL = "http://127.0.0.1:8000"

def print_status(step):
    print(f"✅ {step}")

def check_status(game_id, expect_check=False, expect_checkmate=False):
    r = requests.get(f"{BASE_URL}/status/{game_id}")
    status = r.json()
    if expect_check:
        assert status["is_check"], "Expected check"
        print("☑️  CHECK detected")
    if expect_checkmate:
        assert status["is_checkmate"], "Expected checkmate"
        print("☑️  CHECKMATE detected")
    return status

def smoketest():
    # 1. Start
    r = requests.post(f"{BASE_URL}/start_game"); data = r.json()
    gid, wtk, btk = data["game_id"], data["white_token"], data["black_token"]
    print_status("Game created")

    # 2. Join
    requests.post(f"{BASE_URL}/join_game/{gid}?token={wtk}"); print_status("White joined")
    requests.post(f"{BASE_URL}/join_game/{gid}?token={btk}"); print_status("Black joined")

    # 3. Scholar's Mate
    moves = [
        ("e2e4", wtk),  # 1
        ("e7e5", btk),  # 2
        ("d1h5", wtk),  # 3
        ("b8c6", btk),  # 4
        ("f1c4", wtk),  # 5
        ("g8f6", btk),  # 6
        ("h5f7", wtk),  # 7 → check + mate
    ]
    for i, (uci, token) in enumerate(moves, 1):
        requests.post(f"{BASE_URL}/move/{gid}?token={token}", json={"move": uci})
        print_status(f"Move {i} ({uci}) executed")
    # Final move both checks:
    check_status(gid, expect_check=True, expect_checkmate=True)

    # 4. Cleanup
    requests.delete(f"{BASE_URL}/game/{gid}"); print_status("Game deleted")

    print("🎉 Scholar’s Mate smoketest passed")

if __name__ == "__main__":
    smoketest()
