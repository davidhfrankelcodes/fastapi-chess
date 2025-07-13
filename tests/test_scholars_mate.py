import requests

def test_scholars_mate(base_url, new_game):
    gid, wtk, btk = new_game

    # moves leading to Scholar's Mate
    moves = [
        ("e2e4", wtk),
        ("e7e5", btk),
        ("d1h5", wtk),
        ("b8c6", btk),
        ("f1c4", wtk),
        ("g8f6", btk),
        ("h5f7", wtk),  # final check+mate
    ]

    for uci, token in moves:
        resp = requests.post(f"{base_url}/move/{gid}?token={token}",
                             json={"move": uci})
        assert resp.status_code == 200

    status = requests.get(f"{base_url}/status/{gid}").json()
    assert status["is_check"] is True
    assert status["is_checkmate"] is True
