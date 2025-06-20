import requests

def test_fools_mate(base_url, new_game):
    gid, wtk, btk = new_game

    # join both players
    requests.post(f"{base_url}/join_game/{gid}?token={wtk}")
    requests.post(f"{base_url}/join_game/{gid}?token={btk}")

    # Fool's Mate sequence
    moves = [
        ("f2f3", wtk),
        ("e7e5", btk),
        ("g2g4", wtk),
        ("d8h4", btk),  # checkmate
    ]

    for uci, token in moves:
        resp = requests.post(
            f"{base_url}/move/{gid}?token={token}",
            json={"move": uci}
        )
        assert resp.status_code == 200

    status = requests.get(f"{base_url}/status/{gid}").json()
    assert status["is_game_over"] is True
    assert status["is_checkmate"] is True
    assert status["result"] == "0-1"
