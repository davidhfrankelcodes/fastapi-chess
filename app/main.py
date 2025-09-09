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

# static & templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/game/{game_id}", include_in_schema=False)
async def game_page(request: Request, game_id: str):
    # auto-init on first visit if UUID is valid
    ensure_game_exists(game_id)
    return templates.TemplateResponse(
        "game.html",
        {"request": request, "game_id": game_id}
    )

def validate_uuid(game_id: str) -> None:
    try:
        uuid.UUID(game_id)
    except Exception:
        raise HTTPException(400, "Invalid game_id (must be a valid UUID)")

def ensure_game_exists(game_id: str) -> None:
    """
    Validate UUID and create a new starting position if this game_id
    hasn't been seen before.
    """
    validate_uuid(game_id)
    with get_db() as db:
        row = db.execute("SELECT 1 FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            board = chess.Board()
            db.execute(
                "INSERT INTO games (id, fen) VALUES (?, ?)",
                (game_id, board.fen()),
            )

def fetch_board(game_id: str) -> chess.Board:
    ensure_game_exists(game_id)
    with get_db() as db:
        row = db.execute("SELECT fen FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            # Shouldn't happen because ensure_game_exists created it.
            raise HTTPException(404, "Game not found")
        return chess.Board(row["fen"])

def save_board(game_id: str, board: chess.Board) -> None:
    with get_db() as db:
        db.execute("UPDATE games SET fen = ? WHERE id = ?", (board.fen(), game_id))

# fetch the current FEN (auto-starts game if new UUID)
@app.get("/fen/{game_id}")
def get_fen(game_id: str):
    board = fetch_board(game_id)
    return {"fen": board.fen()}

# make a move using a color param instead of tokens (auto-starts game if new UUID)
@app.post("/move/{game_id}")
def make_move(
    game_id: str,
    color: str = Query(..., description="Move as 'white' or 'black'"),
    move: str = Body(..., embed=True),
):
    color_lc = color.lower()
    if color_lc not in ("white", "black"):
        raise HTTPException(400, "Invalid color (must be 'white' or 'black')")

    board = fetch_board(game_id)

    # whose turn?
    player_color = chess.WHITE if color_lc == "white" else chess.BLACK

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
    save_board(game_id, board)

    return {
        "status": "ok",
        "new_fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "is_game_over": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None,
    }

# status endpoint (auto-starts game if new UUID)
@app.get("/status/{game_id}")
def get_status(game_id: str):
    board = fetch_board(game_id)
    return {
        "turn": "white" if board.turn == chess.WHITE else "black",
        "is_check": board.is_check(),
        "is_game_over": board.is_game_over(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "result": board.result() if board.is_game_over() else None,
    }

# ascii board (auto-starts game if new UUID)
@app.get("/board/{game_id}")
def get_board_ascii(game_id: str):
    board = fetch_board(game_id)
    rows = str(board).splitlines()
    return {"board": rows}

# delete game (requires valid UUID; no auto-create here)
@app.delete("/game/{game_id}")
def delete_game(game_id: str):
    validate_uuid(game_id)
    with get_db() as db:
        row = db.execute("SELECT 1 FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")
        db.execute("DELETE FROM games WHERE id = ?", (game_id,))
        return {"message": f"Game {game_id} deleted"}

