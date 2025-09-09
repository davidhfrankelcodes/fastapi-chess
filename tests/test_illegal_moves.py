import requests

def test_illegal_move_and_turn_and_color(base_url, new_game):
    gid = new_game

    # 1) Invalid color
    resp = requests.post(
        f"{base_url}/move/{gid}?color=purple",
        json={"move": "e2e4"}
    )
    assert resp.status_code == 400
    assert "Invalid color" in resp.json().get("detail", "")

    # 2) Move out of turn: White plays, then White again
    resp = requests.post(
        f"{base_url}/move/{gid}?color=white",
        json={"move": "e2e4"}
    )
    assert resp.status_code == 200

    resp = requests.post(
        f"{base_url}/move/{gid}?color=white",
        json={"move": "d2d4"}
    )
    assert resp.status_code == 403
    assert "Not your turn" in resp.json().get("detail", "")

    # 3) Bad UCI format (now Black to move)
    resp = requests.post(
        f"{base_url}/move/{gid}?color=black",
        json={"move": "not-a-move"}
    )
    assert resp.status_code == 400
    assert "Invalid UCI move format" in resp.json().get("detail", "")

