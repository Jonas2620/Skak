import math
from copy import deepcopy
import threading

class ChessAI:
    def __init__(self, depth=4):
        self.cache = {}
        self.transposition_table = {}  # Enhanced caching with transposition table
        self.depth = depth
        # Forbedret vægtning af brikkernes værdi på brættet
        self.CENTER_CONTROL_BONUS = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 5, 10, 10, 10, 10, 5, 0],
            [0, 10, 20, 25, 25, 20, 10, 0],
            [0, 10, 25, 30, 30, 25, 10, 0],
            [0, 10, 25, 30, 30, 25, 10, 0],
            [0, 10, 20, 25, 25, 20, 10, 0],
            [0, 5, 10, 10, 10, 10, 5, 0],
            [0, 0, 5, 5, 5, 5, 0, 0],
        ]
        # Tilføjet værdier for bønders position (bedre at have bønder fremme)
        self.PAWN_ADVANCEMENT = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5, 5, 10, 25, 25, 10, 5, 5],
            [0, 0, 0, 20, 20, 0, 0, 0],
            [5, -5, -10, 0, 0, -10, -5, 5],
            [5, 10, 10, -20, -20, 10, 10, 5],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]
        # Cache for at gemme kongepositioner
        self.king_positions_cache = {}

    def get_best_move(self, board, color):
        best_eval = -math.inf if color == 'w' else math.inf
        best_move = None

        # Clear history tables for new search
        self.history_table = {}
        self.killer_moves = [[None, None] for _ in range(100)]

        moves = self.get_all_moves(board, color)
        if not moves:
            return None  # No moves available

        # Sort moves based on their estimated value to improve alpha-beta pruning
        moves.sort(key=lambda move: self.evaluate_board_after_move(board, move), reverse=(color == 'w'))

        for move in moves:
            new_board, _ = self.make_move(deepcopy(board), move)
            eval = self.alphabeta(new_board, self.depth - 1, -math.inf, math.inf, maximizing=(color != 'w'))

            if (color == 'w' and eval_value > best_eval) or (color == 'b' and eval_value < best_eval):
                best_eval = eval_value
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
        
        # Ingen træk, det er enten skakmat eller pat
        if not moves:
            # Hvis kongen er i skak, er det skakmat
            king_pos = self.find_king(board, color)
            if king_pos and self.is_in_check(board, king_pos, color):
                return -math.inf if color == 'w' else math.inf
            else:
                return 0  # Pat (uafgjort)

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
            undo_data = (r1, c1, r2, c2, piece, target)

        board[r2][c2] = piece
        board[r1][c1] = None
        
        # Clear king position cache when a move is made
        self.king_positions_cache = {}
        
        return board, undo_data

    def undo_move(self, board, undo_data):
        """Undo a move on the board"""
        r1, c1, r2, c2, piece, target = undo_data
        board[r1][c1] = piece
        board[r2][c2] = target
        self.king_positions_cache = {}  # Clear cache

    def board_to_key(self, board):
        return tuple(tuple((p.name, p.color) if p else None for p in row) for row in board)

    def evaluate_board(self, board):
        value = 0
        white_piece_count = 0
        black_piece_count = 0
        
        for r, row in enumerate(board):
            for c, p in enumerate(row):
                if p:
                    # Basisværdi for brikken
                    piece_value = self.piece_value(p)
                    value += piece_value
                    
                    # Føj positionsbonus til værdi
                    if p.color == 'w':
                        white_piece_count += 1
                        value += self.CENTER_CONTROL_BONUS[r][c]
                        # Tilføj bonus for bønder der er rykket frem
                        if p.name == 'P':
                            value += self.PAWN_ADVANCEMENT[r][c]
                    else:
                        black_piece_count += 1
                        value -= self.CENTER_CONTROL_BONUS[r][c]
                        # For sorte bønder, spejl bonusværdien
                        if p.name == 'P':
                            value -= self.PAWN_ADVANCEMENT[7-r][c]
        
        # Tillæg bonus for udvikling af brikker i midtspillet
        if 10 <= white_piece_count + black_piece_count <= 20:
            # Find udviklingsstatus - hvor mange brikker er flyttet fra startposition
            white_development = self.calculate_development(board, 'w')
            black_development = self.calculate_development(board, 'b')
            value += (white_development - black_development) * 5
            
        return value

    def calculate_development(self, board, color):
        # En simpel metode til at måle, hvor mange brikker der er udviklet
        development_score = 0
        back_rank = 7 if color == 'w' else 0
        
        # Tjek om springere og løbere er flyttet fra baglinjen
        for c in [1, 2, 5, 6]:  # kolonner for springere og løbere
            if board[back_rank][c] is None or board[back_rank][c].color != color:
                development_score += 1
                
        return development_score

    def piece_value(self, piece):
        values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 2000}
        return values.get(piece.name.upper(), 0) * (1 if piece.color == 'w' else -1)

    def get_all_moves(self, board, color):
        moves = []
        for r, row in enumerate(board):
            for c, p in enumerate(row):
                if p and p.color == color:
                    piece_moves = p.get_possible_moves(board, r, c)
                    # Filtrér træk der ville efterlade kongen i skak
                    for move in piece_moves:
                        temp_board, undo_data = self.make_move(deepcopy(board), (r, c, move[0], move[1]), return_undo=True)
                        king_pos = self.find_king(temp_board, color)
                        if not king_pos or not self.is_in_check(temp_board, king_pos, color):
                            moves.append((r, c, move[0], move[1]))
        return moves

    def is_game_over(self, board):
        # Tjek om en af kongerne er væk
        if not self.find_king(board, 'w') or not self.find_king(board, 'b'):
            return True

        # Tjek om sort er i skakmat
        if not self.has_legal_moves(board, 'b'):
            black_king_pos = self.find_king(board, 'b')
            if self.is_in_check(board, black_king_pos, 'b'):
                return True

        # Tjek om hvid er i skakmat
        if not self.has_legal_moves(board, 'w'):
            white_king_pos = self.find_king(board, 'w')
            if self.is_in_check(board, white_king_pos, 'w'):
                return True

        return False

    def is_in_check(self, board, king_position, color):
        king_row, king_col = king_position
        opponent_color = 'b' if color == 'w' else 'w'

        # Tjek alle modstanderens brikker for at se, om de truer kongen
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == opponent_color:
                    moves = piece.get_possible_moves(board, r2, c2, include_attacks=True)
                    if king_pos in moves:
                        return True
        return False

    def has_legal_moves(self, board, color):
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == color:
                    possible_moves = piece.get_possible_moves(board, row, col)
                    for move in possible_moves:
                        new_board, _ = self.make_move(deepcopy(board), (row, col, move[0], move[1]))
                        king_pos = self.find_king(new_board, color)
                        if king_pos and not self.is_in_check(new_board, king_pos, color):
                            return True
        return False

    def find_king(self, board, color):
        # Check cache first
        board_key = self.board_to_key(board)
        cache_key = (board_key, color)
        if cache_key in self.king_positions_cache:
            return self.king_positions_cache[cache_key]
        
        # Find king position
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.name == 'K' and piece.color == color:
                    # Cache the result
                    self.king_positions_cache[cache_key] = (row, col)
                    return (row, col)
        
        # No king found
        self.king_positions_cache[cache_key] = None
        return None

    def calculate_best_move_async(self, board, color, callback):
        def async_task():
            best_move = self.get_best_move(board, color)
            if callback:
                callback(best_move)

        # Running the AI calculation in a separate thread
        thread = threading.Thread(target=async_task)
        thread.start()