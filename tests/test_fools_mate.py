import requests

def test_fools_mate(base_url, new_game):
    gid = new_game

    # Fool's Mate sequence (colors instead of tokens)
    moves = [
        ("f2f3", "white"),
        ("e7e5", "black"),
        ("g2g4", "white"),
        ("d8h4", "black"),  # checkmate
    ]

    for uci, color in moves:
        resp = requests.post(
            f"{base_url}/move/{gid}?color={color}",
            json={"move": uci}
        )
        assert resp.status_code == 200, resp.text

    status = requests.get(f"{base_url}/status/{gid}").json()
    assert status["is_game_over"] is True
    assert status["is_checkmate"] is True
    assert status["result"] == "0-1"

