from fastapi import FastAPI, HTTPException
import chess
import uuid
from db import get_db, init_db

app = FastAPI()
init_db()

@app.post("/start_game/{username}")
def start_game(username: str):
    game_id = str(uuid.uuid4())
    white_token = str(uuid.uuid4())
    black_token = str(uuid.uuid4())
    board = chess.Board()

    with get_db() as db:
        db.execute("""
        INSERT INTO games (id, fen, white_username, white_token, black_token)
        VALUES (?, ?, ?, ?, ?)
        """, (game_id, board.fen(), username, white_token, black_token))

    return {
        "game_id": game_id,
        "white_token": white_token,
        "black_token": black_token
    }

@app.post("/join_game/{game_id}")
def join_game(game_id: str, username: str, token: str):
    with get_db() as db:
        row = db.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")

        if row["black_username"] is not None:
            raise HTTPException(400, "Game already has a black player")

        if token != row["black_token"]:
            raise HTTPException(403, "Invalid join token")

        db.execute("UPDATE games SET black_username = ? WHERE id = ?", (username, game_id))
        return {"message": f"{username} joined as black"}

@app.get("/fen/{game_id}")
def get_fen(game_id: str):
    with get_db() as db:
        row = db.execute("SELECT fen FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")
        return {"fen": row["fen"]}
