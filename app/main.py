from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import chess, uuid
from app.db import get_db, init_db

app = FastAPI()
init_db()

# Mount a static directory (for CSS/JS if needed)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")

@app.get("/game/{game_id}", include_in_schema=False)
async def game_page(request: Request, game_id: str):
    # Could fetch initial FEN or status here
    return templates.TemplateResponse(
        "game.html",
        {"request": request, "game_id": game_id}
    )


@app.post("/start_game")
def start_game():
    game_id = str(uuid.uuid4())
    white_token = str(uuid.uuid4())
    black_token = str(uuid.uuid4())
    board = chess.Board()

    with get_db() as db:
        db.execute("""
        INSERT INTO games (id, fen, white_joined, black_joined, white_token, black_token)
        VALUES (?, ?, NULL, NULL, ?, ?)
        """, (game_id, board.fen(), white_token, black_token))

    return {
        "game_id": game_id,
        "white_token": white_token,
        "black_token": black_token
    }


@app.post("/join_game/{game_id}")
def join_game(game_id: str, token: str = Query(...)):
    with get_db() as db:
        row = db.execute("SELECT * FROM games WHERE id = ?",
                         (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")

        if token == row["white_token"]:
            if row["white_joined"] is not None:
                raise HTTPException(400, "White already joined")
            db.execute(
                "UPDATE games SET white_joined = ? WHERE id = ?", ("joined", game_id))
            return {"role": "white", "message": "White player joined"}

        elif token == row["black_token"]:
            if row["black_joined"] is not None:
                raise HTTPException(400, "Black already joined")
            db.execute(
                "UPDATE games SET black_joined = ? WHERE id = ?", ("joined", game_id))
            return {"role": "black", "message": "Black player joined"}

        else:
            raise HTTPException(403, "Invalid token")


@app.get("/fen/{game_id}")
def get_fen(game_id: str):
    with get_db() as db:
        row = db.execute("SELECT fen FROM games WHERE id = ?",
                         (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")
        return {"fen": row["fen"]}


@app.post("/move/{game_id}")
def make_move(
    game_id: str,
    token: str = Query(...),
    move: str = Body(..., embed=True)  # expects { "move": "e2e4" }
):
    with get_db() as db:
        row = db.execute("SELECT * FROM games WHERE id = ?",
                         (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")

        board = chess.Board(row["fen"])

        # Determine the player's color
        if token == row["white_token"]:
            player_color = chess.WHITE
        elif token == row["black_token"]:
            player_color = chess.BLACK
        else:
            raise HTTPException(403, "Invalid token")

        # Check turn
        if board.turn != player_color:
            raise HTTPException(403, "Not your turn")

        # Try to parse and apply the move
        try:
            move_obj = chess.Move.from_uci(move)
        except ValueError:
            raise HTTPException(400, "Invalid UCI move format")

        if move_obj not in board.legal_moves:
            raise HTTPException(400, "Illegal move")

        board.push(move_obj)

        # Save updated FEN
        db.execute("UPDATE games SET fen = ? WHERE id = ?",
                   (board.fen(), game_id))

        return {
            "status": "ok",
            "new_fen": board.fen(),
            "turn": "white" if board.turn == chess.WHITE else "black",
            "is_game_over": board.is_game_over(),
            "result": board.result() if board.is_game_over() else None
        }


@app.get("/status/{game_id}")
def get_status(game_id: str):
    with get_db() as db:
        row = db.execute("SELECT fen FROM games WHERE id = ?",
                         (game_id,)).fetchone()
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


@app.get("/board/{game_id}")
def get_board_ascii(game_id: str):
    with get_db() as db:
        row = db.execute("SELECT fen FROM games WHERE id = ?",
                         (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")

        board = chess.Board(row["fen"])
        rows = str(board).splitlines()  # Split the ASCII board into 8 lines
        return {"board": rows}


@app.delete("/game/{game_id}")
def delete_game(game_id: str):
    with get_db() as db:
        row = db.execute("SELECT 1 FROM games WHERE id = ?",
                         (game_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Game not found")

        db.execute("DELETE FROM games WHERE id = ?", (game_id,))
        return {"message": f"Game {game_id} deleted"}
