import math
from copy import deepcopy
import threading

class ChessAI:
    def __init__(self, depth=4):
        self.cache = {}
        self.depth = depth

        self.CENTER_CONTROL_BONUS = [
            [0, 0, 5, 5, 5, 5, 0, 0],
            [0, 5, 10, 10, 10, 10, 5, 0],
            [5, 10, 15, 20, 20, 15, 10, 5],
            [5, 10, 20, 25, 25, 20, 10, 5],
            [5, 10, 20, 25, 25, 20, 10, 5],
            [5, 10, 15, 20, 20, 15, 10, 5],
            [0, 5, 10, 10, 10, 10, 5, 0],
            [0, 0, 5, 5, 5, 5, 0, 0],
        ]

    def get_best_move(self, board, color):
        best_eval = -math.inf if color == 'w' else math.inf
        best_move = None

        moves = self.get_all_moves(board, color)

        # Sort moves based on their estimated value to improve alpha-beta pruning
        moves.sort(key=lambda move: self.evaluate_board_after_move(board, move), reverse=True)

        for move in moves:
            new_board, _ = self.make_move(deepcopy(board), move)
            eval = self.alphabeta(new_board, self.depth - 1, -math.inf, math.inf, maximizing=(color == 'w'))

            if (color == 'w' and eval > best_eval) or (color == 'b' and eval < best_eval):
                best_eval = eval
                best_move = move

        return best_move

    def evaluate_board_after_move(self, board, move):
        # Simulate the move and evaluate the board position after it
        new_board, _ = self.make_move(deepcopy(board), move)
        return self.evaluate_board(new_board)

    def alphabeta(self, board, depth, alpha, beta, maximizing):
        board_key = self.board_to_key(board)
        if board_key in self.cache:
            return self.cache[board_key]

        if depth == 0 or self.is_game_over(board):
            eval = self.evaluate_board(board)
            self.cache[board_key] = eval
            return eval

        color = 'w' if maximizing else 'b'
        moves = self.get_all_moves(board, color)

        if maximizing:
            max_eval = -math.inf
            for move in moves:
                new_board, _ = self.make_move(deepcopy(board), move)
                eval = self.alphabeta(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            self.cache[board_key] = max_eval
            return max_eval
        else:
            min_eval = math.inf
            for move in moves:
                new_board, _ = self.make_move(deepcopy(board), move)
                eval = self.alphabeta(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            self.cache[board_key] = min_eval
            return min_eval

    def make_move(self, board, move, return_undo=False):
        r1, c1, r2, c2 = move
        piece = board[r1][c1]
        target = board[r2][c2]

        undo_data = None
        if return_undo:
            undo_data = (r1, c1, piece, target)

        board[r2][c2] = piece
        board[r1][c1] = None
        return board, undo_data

    def undo_move(self, board, undo_data):
        r1, c1, piece, target = undo_data
        board[r1][c1] = piece
        board[undo_data[2]][undo_data[3]] = target

    def board_to_key(self, board):
        return tuple(tuple((p.name, p.color) if p else None for p in row) for row in board)

    def evaluate_board(self, board):
        value = 0
        for r, row in enumerate(board):
            for c, p in enumerate(row):
                if p:
                    value += self.piece_value(p)
                    # Adding center control bonus for position
                    value += self.CENTER_CONTROL_BONUS[r][c] if p.color == 'w' else -self.CENTER_CONTROL_BONUS[r][c]
        return value

    def piece_value(self, piece):
        values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 1000000}
        return values.get(piece.name.upper(), 0) * (1 if piece.color == 'w' else -1)

    def get_all_moves(self, board, color):
        moves = []
        for r, row in enumerate(board):
            for c, p in enumerate(row):
                if p and p.color == color:
                    for move in p.get_possible_moves(board, r, c):
                        moves.append((r, c, move[0], move[1]))
        return moves

    def is_game_over(self, board):
        white_king_position = None
        black_king_position = None

        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.name == "K":
                    if piece.color == "w":
                        white_king_position = (row, col)
                    elif piece.color == "b":
                        black_king_position = (row, col)

        if not white_king_position or not black_king_position:
            return True

        if self.is_in_check(board, white_king_position, 'w') and not self.has_legal_moves(board, 'w'):
            return True
        if self.is_in_check(board, black_king_position, 'b') and not self.has_legal_moves(board, 'b'):
            return True

        return False

    def is_in_check(self, board, king_position, color):
        king_row, king_col = king_position
        opponent_color = 'b' if color == 'w' else 'w'

        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == opponent_color:
                    if (king_row, king_col) in piece.get_possible_moves(board, row, col):
                        return True
        return False

    def has_legal_moves(self, board, color):
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == color:
                    possible_moves = piece.get_possible_moves(board, row, col)
                    for move in possible_moves:
                        new_board, undo_data = self.make_move(deepcopy(board), (row, col, move[0], move[1]), return_undo=True)
                        king_pos = self.find_king(new_board, color)
                        if king_pos and not self.is_in_check(new_board, king_pos, color):
                            return True
        return False

    def find_king(self, board, color):
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.name == 'K' and piece.color == color:
                    return (row, col)
        return None

    def calculate_best_move_async(self, board, color, callback):
        def async_task():
            best_move = self.get_best_move(board, color)
            if callback:
                callback(best_move)

        # Running the AI calculation in a separate thread
        thread = threading.Thread(target=async_task)
        thread.start()
