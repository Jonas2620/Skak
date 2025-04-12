import math

class ChessAI:
    def __init__(self, depth=3):
        self.depth = depth

    def minimax(self, board, depth, maximizing_player):
        if depth == 0 or self.is_game_over(board):
            return self.evaluate(board)

        if maximizing_player:
            max_eval = -math.inf
            for move in self.get_all_moves(board, "white"):
                new_board = self.make_move(board, move)
                eval = self.minimax(new_board, depth - 1, False)
                max_eval = max(max_eval, eval)
            return max_eval
        else:
            min_eval = math.inf
            for move in self.get_all_moves(board, "black"):
                new_board = self.make_move(board, move)
                eval = self.minimax(new_board, depth - 1, True)
                min_eval = min(min_eval, eval)
            return min_eval

    def get_best_move(self, board):
        best_move = None
        best_value = -math.inf
        for move in self.get_all_moves(board, "white"):
            new_board = self.make_move(board, move)
            move_value = self.minimax(new_board, self.depth - 1, False)
            if move_value > best_value:
                best_value = move_value
                best_move = move
        return best_move

    def evaluate(self, board):
        # Simpel evaluering baseret på brikværdier
        piece_values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 100}
        value = 0
        for row in board:
            for piece in row:
                if piece.isupper():  # Hvids brikker
                    value += piece_values.get(piece.upper(), 0)
                elif piece.islower():  # Sorts brikker
                    value -= piece_values.get(piece.upper(), 0)
        return value

    def is_game_over(self, board):
        # Simpel check (du kan udvide med skakmat eller pat)
        return False  

    def get_all_moves(self, board, color):
        # Returnerer alle gyldige træk for en given farve (skal implementeres)
        return []

    def make_move(self, board, move):
        # Returnerer en ny bræt-tilstand efter et træk (skal implementeres)
        return board
