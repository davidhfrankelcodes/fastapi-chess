# app/main.py
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import chess, uuid
from app.db import get_db, init_db

app = FastAPI()
init_db()

# serve docs at /
@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")

# serve the game page
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/game/{game_id}", include_in_schema=False)
async def game_page(request: Request, game_id: str):
    return templates.TemplateResponse(
        "game.html",
        {"request": request, "game_id": game_id}
    )

# start a new game, issue both tokens immediately
@app.post("/start_game")
def start_game():
    game_id = str(uuid.uuid4())
    white_token = str(uuid.uuid4())
    black_token = str(uuid.uuid4())
    board = chess.Board()

    with get_db() as db:
        db.execute("""
        INSERT INTO games (id, fen, white_token, black_token)
        VALUES (?, ?, ?, ?)
        """, (game_id, board.fen(), white_token, black_token))

    return {
        "game_id": game_id,
        "white_token": white_token,
        "black_token": black_token
    }

# fetch the current FEN
@app.get("/fen/{game_id}")
def get_fen(game_id: str):
    with get_db() as db:
        row = db.execute("SELECT fen FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")
        return {"fen": row["fen"]}

# make a move if you present a valid token (no explicit join needed)
@app.post("/move/{game_id}")
def make_move(
    game_id: str,
    token: str = Query(...),
    move: str = Body(..., embed=True)
):
    with get_db() as db:
        row = db.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")

        board = chess.Board(row["fen"])

        # authenticate token ⇒ determine color
        if token == row["white_token"]:
            player_color = chess.WHITE
        elif token == row["black_token"]:
            player_color = chess.BLACK
        else:
            raise HTTPException(403, "Invalid token")

        # enforce turn order
        if board.turn != player_color:
            raise HTTPException(403, "Not your turn")

        # parse & validate UCI
        try:
            move_obj = chess.Move.from_uci(move)
        except ValueError:
            raise HTTPException(400, "Invalid UCI move format")

        if move_obj not in board.legal_moves:
            raise HTTPException(400, "Illegal move")

        board.push(move_obj)

        db.execute("UPDATE games SET fen = ? WHERE id = ?", (board.fen(), game_id))

        return {
            "status": "ok",
            "new_fen": board.fen(),
            "turn": "white" if board.turn == chess.WHITE else "black",
            "is_game_over": board.is_game_over(),
            "result": board.result() if board.is_game_over() else None
        }

# status endpoint unchanged
@app.get("/status/{game_id}")
def get_status(game_id: str):
    with get_db() as db:
        row = db.execute("SELECT fen FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")
        board = chess.Board(row["fen"])
        return {
            "turn": "white" if board.turn == chess.WHITE else "black",
            "is_check": board.is_check(),
            "is_game_over": board.is_game_over(),
            "is_checkmate": board.is_checkmate(),
            "is_stalemate": board.is_stalemate(),
            "result": board.result() if board.is_game_over() else None
        }

# ascii board unchanged
@app.get("/board/{game_id}")
def get_board_ascii(game_id: str):
    with get_db() as db:
        row = db.execute("SELECT fen FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")
        board = chess.Board(row["fen"])
        rows = str(board).splitlines()
        return {"board": rows}

# delete unchanged
@app.delete("/game/{game_id}")
def delete_game(game_id: str):
    with get_db() as db:
        row = db.execute("SELECT 1 FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")
        db.execute("DELETE FROM games WHERE id = ?", (game_id,))
        return {"message": f"Game {game_id} deleted"}
