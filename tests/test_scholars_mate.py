import requests

def test_scholars_mate(base_url, new_game):
    gid = new_game

    # moves leading to Scholar's Mate (colors instead of tokens)
    moves = [
        ("e2e4", "white"),
        ("e7e5", "black"),
        ("d1h5", "white"),
        ("b8c6", "black"),
        ("f1c4", "white"),
        ("g8f6", "black"),
        ("h5f7", "white"),  # final check+mate
    ]

    for uci, color in moves:
        resp = requests.post(
            f"{base_url}/move/{gid}?color={color}",
            json={"move": uci}
        )
        assert resp.status_code == 200, resp.text

    status = requests.get(f"{base_url}/status/{gid}").json()
    assert status["is_check"] is True
    assert status["is_checkmate"] is True

