from fastapi import FastAPI, HTTPException
import chess
import uuid

app = FastAPI()

# games[username][game_id] = chess.Board()
games = {}

@app.get("/")
def read_root():
    return {"message": "Welcome to your Chess API with multiple games!"}

@app.post("/new_game/{username}")
def new_game(username: str):
    game_id = str(uuid.uuid4())
    board = chess.Board()
    
    if username not in games:
        games[username] = {}
    
    games[username][game_id] = board
    return {"username": username, "game_id": game_id, "fen": board.fen()}

@app.get("/fen/{username}/{game_id}")
def get_fen(username: str, game_id: str):
    board = get_board_or_404(username, game_id)
    return {"fen": board.fen()}

@app.get("/board/{username}/{game_id}")
def get_board_ascii(username: str, game_id: str):
    board = get_board_or_404(username, game_id)
    return {"board": str(board)}

def get_board_or_404(username: str, game_id: str) -> chess.Board:
    if username not in games or game_id not in games[username]:
        raise HTTPException(status_code=404, detail="Game not found.")
    return games[username][game_id]
