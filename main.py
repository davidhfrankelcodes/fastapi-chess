from fastapi import FastAPI
import chess

app = FastAPI()

# Global board for now (not suitable for multi-user, but fine to start)
board = chess.Board()

@app.get("/")
def read_root():
    return {"message": "Welcome to your Chess API!"}

@app.get("/fen")
def get_fen():
    return {"fen": board.fen()}

@app.get("/board")
def get_board_ascii():
    return {"board": str(board)}
