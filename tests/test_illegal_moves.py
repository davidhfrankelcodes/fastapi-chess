import requests

def test_illegal_move_and_token(base_url, new_game):
    gid, wtk, btk = new_game

    # 1) Invalid token
    resp = requests.post(
        f"{base_url}/move/{gid}?token=invalid-token",
        json={"move": "e2e4"}
    )
    assert resp.status_code == 403
    assert "Invalid token" in resp.json().get("detail", "")

    # 2) Move out of turn: White plays, then White again
    resp = requests.post(
        f"{base_url}/move/{gid}?token={wtk}",
        json={"move": "e2e4"}
    )
    assert resp.status_code == 200

    resp = requests.post(
        f"{base_url}/move/{gid}?token={wtk}",
        json={"move": "d2d4"}
    )
    assert resp.status_code == 403
    assert "Not your turn" in resp.json().get("detail", "")

    # 3) Bad UCI format
    resp = requests.post(
        f"{base_url}/move/{gid}?token={btk}",
        json={"move": "not-a-move"}
    )
    assert resp.status_code == 400
    assert "Invalid UCI move format" in resp.json().get("detail", "")
