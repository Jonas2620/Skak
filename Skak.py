def initialize_chess_board():
    """Opretter 8x8 skakbræt"""
    return [
        ["r", "n", "b", "k", "q", "b", "n", "r"],
        ["p", "p", "p", "p", "p", "p", "p", "p"],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        [".", ".", ".", ".", ".", ".", ".", "."],
        ["P", "P", "P", "P", "P", "P", "P", "P"],
        ["R", "N", "B", "Q", "K", "B", "N", "R"]
    ]

def display_chess_board(board):

    for row in board:
        print(" ".join(row))
        
if __name__ == "__main__":
    chess_board = initialize_chess_board()
    display_chess_board(chess_board)