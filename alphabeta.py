import math
from copy import deepcopy
import threading
import time

class ChessAI:
    def __init__(self, depth=4):
        self.cache = {}
        self.transposition_table = {}  # Enhanced caching with transposition table
        self.depth = depth
        self.nodes_searched = 0  # Track number of nodes searched for analytics
        self.use_iterative_deepening = True  # Use iterative deepening for better move quality
        self.time_limit = 5.0  # 5 seconds time limit for thinking by default
        
        # Center control bonus for general piece positioning
        self.CENTER_CONTROL_BONUS = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 5, 10, 10, 10, 10, 5, 0],
            [0, 10, 20, 25, 25, 20, 10, 0],
            [0, 10, 25, 30, 30, 25, 10, 0],
            [0, 10, 25, 30, 30, 25, 10, 0],
            [0, 10, 20, 25, 25, 20, 10, 0],
            [0, 5, 10, 10, 10, 10, 5, 0],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]

        # PAWN position values (improved)
        self.PAWN_POSITION = [
            [0, 0, 0, 0, 0, 0, 0, 0],         # Last rank (rarely occurs for pawns)
            [50, 50, 50, 50, 50, 50, 50, 50], # About to promote
            [10, 10, 20, 30, 30, 20, 10, 10], # Advanced pawns
            [5, 5, 10, 25, 25, 10, 5, 5],     # Past midpoint
            [0, 0, 5, 20, 20, 5, 0, 0],       # Center control
            [5, -5, -10, 0, 0, -10, -5, 5],   # Initial pawn movement area
            [5, 10, 10, -20, -20, 10, 10, 5], # Starting row
            [0, 0, 0, 0, 0, 0, 0, 0]          # Never occurs for pawns
        ]

        # PAWN advancement bonus (missing in original code)
        self.PAWN_ADVANCEMENT = [
            [0, 0, 0, 0, 0, 0, 0, 0],         # Never occurs for pawns
            [80, 80, 80, 80, 80, 80, 80, 80], # About to promote
            [50, 50, 50, 50, 50, 50, 50, 50], # Very advanced
            [30, 30, 30, 40, 40, 30, 30, 30], # Advanced
            [15, 15, 20, 25, 25, 20, 15, 15], # Past midpoint
            [5, 5, 10, 15, 15, 10, 5, 5],     # Forward movement
            [0, 0, 0, 0, 0, 0, 0, 0],         # Starting row
            [0, 0, 0, 0, 0, 0, 0, 0]          # Never occurs
        ]

        # KNIGHT position values
        self.KNIGHT_POSITION = [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20, 0, 5, 5, 0, -20, -40],
            [-30, 0, 10, 15, 15, 10, 0, -30],
            [-30, 5, 15, 20, 20, 15, 5, -30],
            [-30, 5, 15, 20, 20, 15, 5, -30],
            [-30, 0, 10, 15, 15, 10, 0, -30],
            [-40, -20, 0, 5, 5, 0, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50]
        ]

        # BISHOP position values
        self.BISHOP_POSITION = [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10, 5, 0, 0, 0, 0, 5, -10],
            [-10, 10, 10, 10, 10, 10, 10, -10],
            [-10, 0, 10, 15, 15, 10, 0, -10],
            [-10, 5, 5, 15, 15, 5, 5, -10],
            [-10, 0, 5, 10, 10, 5, 0, -10],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20]
        ]

        # ROOK position values
        self.ROOK_POSITION = [
            [0, 0, 0, 5, 5, 0, 0, 0],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [5, 10, 10, 10, 10, 10, 10, 5],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]

        # QUEEN position values
        self.QUEEN_POSITION = [
            [-20, -10, -10, -5, -5, -10, -10, -20],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-10, 0, 5, 5, 5, 5, 0, -10],
            [-5, 0, 5, 10, 10, 5, 0, -5],
            [0, 0, 5, 10, 10, 5, 0, -5],
            [-10, 5, 5, 5, 5, 5, 0, -10],
            [-10, 0, 5, 0, 0, 0, 0, -10],
            [-20, -10, -10, -5, -5, -10, -10, -20]
        ]

        # KING middle game position values
        self.KING_MIDDLEGAME_POSITION = [
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [20, 20, 0, 0, 0, 0, 20, 20],
            [20, 30, 10, 0, 0, 10, 30, 20]
        ]

        # KING endgame position values
        self.KING_ENDGAME_POSITION = [
            [-50, -30, -30, -30, -30, -30, -30, -50],
            [-30, -20, -10, -10, -10, -10, -20, -30],
            [-30, -10, 20, 30, 30, 20, -10, -30],
            [-30, -10, 30, 40, 40, 30, -10, -30],
            [-30, -10, 30, 40, 40, 30, -10, -30],
            [-30, -10, 20, 30, 30, 20, -10, -30],
            [-30, -30, 0, 0, 0, 0, -30, -30],
            [-50, -30, -30, -30, -30, -30, -30, -50]
        ]

        # Define specific tables for passed pawns and isolated pawns
        self.PASSED_PAWN_BONUS = [0, 10, 20, 40, 60, 80, 100, 0]  # Indexed by rank
        self.ISOLATED_PAWN_PENALTY = -15
        self.DOUBLED_PAWN_PENALTY = -10
        
        # Mobility bonuses
        self.MOBILITY_BONUS = {
            'P': 0,   # Pawns get no mobility bonus
            'N': 2,   # Knights get 2 points per available move
            'B': 2,   # Bishops get 2 points per available move
            'R': 3,   # Rooks get 3 points per available move
            'Q': 1,   # Queens get 1 point per available move (less to avoid early development)
            'K': 0    # Kings get no mobility bonus (safety is more important)
        }
        
        # Cache for king positions
        self.king_positions_cache = {}
        
        # Move ordering heuristics weights
        self.MVV_LVA_TABLE = {  # Most Valuable Victim, Least Valuable Attacker
            'P': {'P': 105, 'N': 104, 'B': 103, 'R': 102, 'Q': 101, 'K': 100},
            'N': {'P': 205, 'N': 204, 'B': 203, 'R': 202, 'Q': 201, 'K': 200},
            'B': {'P': 305, 'N': 304, 'B': 303, 'R': 302, 'Q': 301, 'K': 300},
            'R': {'P': 405, 'N': 404, 'B': 403, 'R': 402, 'Q': 401, 'K': 400},
            'Q': {'P': 505, 'N': 504, 'B': 503, 'R': 502, 'Q': 501, 'K': 500},
            'K': {'P': 605, 'N': 604, 'B': 603, 'R': 602, 'Q': 601, 'K': 600}
        }

        # Historical move scores for move ordering
        self.history_table = {}
        self.killer_moves = [[None, None] for _ in range(100)]  # Store 2 killer moves per ply

    def set_search_parameters(self, depth=None, time_limit=None, use_iterative_deepening=None):
        """Set search parameters for the AI"""
        if depth is not None:
            self.depth = depth
        if time_limit is not None:
            self.time_limit = time_limit
        if use_iterative_deepening is not None:
            self.use_iterative_deepening = use_iterative_deepening

    def get_best_move(self, board, color):
        """Get the best move using either fixed depth or iterative deepening with time limit"""
        self.nodes_searched = 0
        
        if not self.use_iterative_deepening:
            return self._get_best_move_fixed_depth(board, color)
        else:
            return self._get_best_move_iterative_deepening(board, color)
    
    def _get_best_move_iterative_deepening(self, board, color):
        """Use iterative deepening to find best move within time limit"""
        best_move = None
        best_eval = -math.inf if color == 'w' else math.inf
        start_time = time.time()
        depth = 1
        
        # Clear history tables for new search
        self.history_table = {}
        self.killer_moves = [[None, None] for _ in range(100)]
        
        while depth <= self.depth:
            current_best_move = None
            current_best_eval = -math.inf if color == 'w' else math.inf
            
            moves = self.get_all_moves(board, color)
            if not moves:
                return None  # No moves available
                
            # Sort moves based on previous iteration results
            moves = self.order_moves(board, moves, color, 0)
            
            for move in moves:
                new_board, _ = self.make_move(deepcopy(board), move)
                eval = self.alphabeta(new_board, depth - 1, -math.inf, math.inf, 
                                      maximizing=(color != 'w'), ply=0)
                
                if ((color == 'w' and eval > current_best_eval) or 
                    (color == 'b' and eval < current_best_eval)):
                    current_best_eval = eval
                    current_best_move = move
                    
                # Check if we've exceeded time limit
                if time.time() - start_time > self.time_limit:
                    if depth == 1:  # Ensure we have at least one valid move
                        return current_best_move
                    return best_move
            
            # Update best move from completed depth
            best_move = current_best_move
            best_eval = current_best_eval
            
            # Prepare for next iteration
            depth += 1
            
        return best_move
    
    def _get_best_move_fixed_depth(self, board, color):
        """Get best move using fixed depth search"""
        best_eval = -math.inf if color == 'w' else math.inf
        best_move = None

        # Clear history tables for new search
        self.history_table = {}
        self.killer_moves = [[None, None] for _ in range(100)]

        moves = self.get_all_moves(board, color)
        if not moves:
            return None  # No moves available

        # Sort moves based on heuristics for better alpha-beta performance
        moves = self.order_moves(board, moves, color, 0)

        for move in moves:
            new_board, _ = self.make_move(deepcopy(board), move)
            eval = self.alphabeta(new_board, self.depth - 1, -math.inf, math.inf, 
                                 maximizing=(color != 'w'), ply=0)

            if (color == 'w' and eval > best_eval) or (color == 'b' and eval < best_eval):
                best_eval = eval
                best_move = move

        return best_move

    def order_moves(self, board, moves, color, ply):
        """Order moves for more efficient alpha-beta pruning"""
        move_scores = []
        
        for move in moves:
            r1, c1, r2, c2 = move
            piece = board[r1][c1]
            target = board[r2][c2]
            score = 0
            
            # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
            if target:
                score += self.MVV_LVA_TABLE[piece.name][target.name]
            
            # Prefer moves that were good previously (history heuristic)
            history_key = (piece.name, r1, c1, r2, c2)
            if history_key in self.history_table:
                score += self.history_table[history_key] // 100  # Scale down to not overwhelm MVV-LVA
            
            # Killer move heuristic
            if self.killer_moves[ply][0] == move:
                score += 900000  # First killer move bonus
            elif self.killer_moves[ply][1] == move:
                score += 800000  # Second killer move bonus

            # Promote pawn captures
            if piece.name == 'P' and target:
                score += 10000
            
            # Promote checks
            new_board, _ = self.make_move(deepcopy(board), move)
            opponent_color = 'b' if color == 'w' else 'w'
            opponent_king_pos = self.find_king(new_board, opponent_color)
            if opponent_king_pos and self.is_in_check(new_board, opponent_king_pos, opponent_color):
                score += 20000
                
            # Promote pawn advancement
            if piece.name == 'P':
                # Bonus for advancing pawns toward promotion
                if color == 'w':
                    score += (7 - r1) * 10  # White pawns go up the board
                else:
                    score += r1 * 10        # Black pawns go down the board
            
            move_scores.append((move, score))
        
        # Sort moves by score in descending order
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]

    def evaluate_board_after_move(self, board, move):
        """Simulate the move and evaluate the board position after it"""
        new_board, _ = self.make_move(deepcopy(board), move)
        return self.evaluate_board(new_board)

    def alphabeta(self, board, depth, alpha, beta, maximizing, ply=0):
        """Alpha-beta pruning with enhanced move ordering and transposition table"""
        self.nodes_searched += 1
        
        # Check transposition table
        board_key = self.board_to_key(board)
        tt_entry = self.transposition_table.get(board_key)
        if tt_entry and tt_entry.get('depth', 0) >= depth:
            return tt_entry['value']
        
        # Check if game over or leaf node
        if depth == 0 or self.is_game_over(board):
            eval = self.evaluate_board(board)
            # Store in transposition table
            self.transposition_table[board_key] = {'value': eval, 'depth': depth}
            return eval

        color = 'b' if maximizing else 'w'
        moves = self.get_all_moves(board, color)
        
        # No moves, it's either checkmate or stalemate
        if not moves:
            # If king is in check, it's checkmate
            king_pos = self.find_king(board, color)
            if king_pos and self.is_in_check(board, king_pos, color):
                return -math.inf if color == 'w' else math.inf
            else:
                return 0  # Stalemate (draw)
                
        # Order moves for better pruning
        moves = self.order_moves(board, moves, color, ply)

        if maximizing:
            max_eval = -math.inf
            for move in moves:
                new_board, _ = self.make_move(deepcopy(board), move)
                eval = self.alphabeta(new_board, depth - 1, alpha, beta, False, ply + 1)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                
                # Update history and killer moves if good move found
                if eval >= beta:
                    # Update killer moves
                    if self.killer_moves[ply][0] != move:
                        self.killer_moves[ply][1] = self.killer_moves[ply][0]
                        self.killer_moves[ply][0] = move
                    
                    # Update history table
                    r1, c1, r2, c2 = move
                    piece = board[r1][c1]
                    history_key = (piece.name, r1, c1, r2, c2)
                    if history_key not in self.history_table:
                        self.history_table[history_key] = 0
                    self.history_table[history_key] += depth * depth
                    
                    break  # Beta cutoff
            
            # Store in transposition table
            self.transposition_table[board_key] = {'value': max_eval, 'depth': depth}
            return max_eval
        else:
            min_eval = math.inf
            for move in moves:
                new_board, _ = self.make_move(deepcopy(board), move)
                eval = self.alphabeta(new_board, depth - 1, alpha, beta, True, ply + 1)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                
                # Update history and killer moves if good move found
                if eval <= alpha:
                    # Update killer moves
                    if self.killer_moves[ply][0] != move:
                        self.killer_moves[ply][1] = self.killer_moves[ply][0]
                        self.killer_moves[ply][0] = move
                    
                    # Update history table
                    r1, c1, r2, c2 = move
                    piece = board[r1][c1]
                    history_key = (piece.name, r1, c1, r2, c2)
                    if history_key not in self.history_table:
                        self.history_table[history_key] = 0
                    self.history_table[history_key] += depth * depth
                    
                    break  # Alpha cutoff
            
            # Store in transposition table
            self.transposition_table[board_key] = {'value': min_eval, 'depth': depth}
            return min_eval

    def make_move(self, board, move, return_undo=False):
        """Make a move on the board"""
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
        """Convert board to hashable key for caching"""
        return tuple(tuple((p.name, p.color) if p else None for p in row) for row in board)

    def evaluate_board(self, board):
        """Evaluate board position with advanced features"""
        # Check if we're in an endgame situation
        is_endgame = self.is_endgame(board)
        
        # Calculate material balance and positional scores
        white_material = 0
        black_material = 0
        white_positional_score = 0
        black_positional_score = 0
        
        # Find kings for both sides
        white_king_pos = self.find_king(board, 'w')
        black_king_pos = self.find_king(board, 'b')
        
        # Count pawns in each file for structure analysis
        white_pawn_files = [0] * 8
        black_pawn_files = [0] * 8
        
        # Calculate mobility
        white_mobility = 0
        black_mobility = 0
        
        # Basic material and position scoring
        for r, row in enumerate(board):
            for c, piece in enumerate(row):
                if not piece:
                    continue
                    
                # Get base piece value
                piece_value = self.piece_value(piece)
                abs_value = abs(piece_value)
                
                # Add to material count
                if piece.color == 'w':
                    white_material += abs_value
                else:
                    black_material += abs_value
                
                # Calculate position value based on piece type and game phase
                position_value = 0
                
                if piece.name == 'P':
                    # Track pawns by file for structure analysis
                    if piece.color == 'w':
                        white_pawn_files[c] += 1
                        position_value = self.PAWN_POSITION[r][c]
                    else:
                        black_pawn_files[c] += 1
                        position_value = self.PAWN_POSITION[7-r][c]
                        
                elif piece.name == 'N':
                    position_value = self.KNIGHT_POSITION[r][c]
                    
                elif piece.name == 'B':
                    position_value = self.BISHOP_POSITION[r][c]
                    
                elif piece.name == 'R':
                    position_value = self.ROOK_POSITION[r][c]
                    
                elif piece.name == 'Q':
                    position_value = self.QUEEN_POSITION[r][c]
                    
                elif piece.name == 'K':
                    if is_endgame:
                        position_value = self.KING_ENDGAME_POSITION[r][c]
                    else:
                        position_value = self.KING_MIDDLEGAME_POSITION[r][c]
                
                # Add position value to respective color
                if piece.color == 'w':
                    white_positional_score += position_value
                else:
                    black_positional_score += position_value
                    
                # Calculate mobility for this piece
                if piece.name != 'P':  # Skip pawns for mobility calculation
                    piece_moves = piece.get_possible_moves(board, r, c)
                    mobility_score = len(piece_moves) * self.MOBILITY_BONUS[piece.name]
                    if piece.color == 'w':
                        white_mobility += mobility_score
                    else:
                        black_mobility += mobility_score
        
        # Calculate pawn structure scores
        white_pawn_structure = self.evaluate_pawn_structure(board, white_pawn_files, 'w')
        black_pawn_structure = self.evaluate_pawn_structure(board, black_pawn_files, 'b')
        
        # Calculate king safety
        white_king_safety = self.evaluate_king_safety(board, white_king_pos, 'w', is_endgame)
        black_king_safety = self.evaluate_king_safety(board, black_king_pos, 'b', is_endgame)
        
        # Combine all evaluation components
        white_score = (white_material + white_positional_score + 
                      white_pawn_structure + white_king_safety + white_mobility)
        black_score = (black_material + black_positional_score + 
                      black_pawn_structure + black_king_safety + black_mobility)
        
        # Return final evaluation from white's perspective
        return white_score - black_score

    def is_endgame(self, board):
        """Determine if the game is in endgame phase"""
        white_material = 0
        black_material = 0
        piece_count = 0
        
        # Count major pieces and material
        for row in board:
            for piece in row:
                if piece:
                    piece_count += 1
                    if piece.name in ['Q', 'R', 'B', 'N']:
                        value = self.piece_value(piece)
                        if piece.color == 'w':
                            white_material += abs(value)
                        else:
                            black_material += abs(value)
        
        # Endgame criteria: 
        # 1. Total piece count is less than 10, or
        # 2. Both sides have less than 1300 material (excluding kings and pawns)
        return piece_count <= 10 or (white_material < 1300 and black_material < 1300)

    def evaluate_pawn_structure(self, board, pawn_files, color):
        """Evaluate pawn structure: doubled, isolated, and passed pawns"""
        score = 0
        
        # Find all pawns of the given color
        pawns = []
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece and piece.name == 'P' and piece.color == color:
                    pawns.append((r, c))
        
        # Check each pawn for structure characteristics
        for r, c in pawns:
            # Doubled pawns (multiple pawns in same file)
            if pawn_files[c] > 1:
                score += self.DOUBLED_PAWN_PENALTY
            
            # Isolated pawns (no friendly pawns in adjacent files)
            is_isolated = True
            for adj_file in [c-1, c+1]:
                if 0 <= adj_file < 8 and pawn_files[adj_file] > 0:
                    is_isolated = False
                    break
            
            if is_isolated:
                score += self.ISOLATED_PAWN_PENALTY
            
            # Passed pawns (no enemy pawns ahead in same or adjacent files)
            is_passed = True
            enemy_color = 'b' if color == 'w' else 'w'
            # Determine which ranks to check based on pawn color
            if color == 'w':
                ranks_to_check = range(r-1, -1, -1)  # Check forward for white
            else:
                ranks_to_check = range(r+1, 8)      # Check forward for black
                
            for check_r in ranks_to_check:
                for check_c in [c-1, c, c+1]:
                    if 0 <= check_c < 8:
                        piece = board[check_r][check_c]
                        if piece and piece.name == 'P' and piece.color == enemy_color:
                            is_passed = False
                            break
                if not is_passed:
                    break
                    
            if is_passed:
                # Convert rank for indexing (higher bonus for more advanced pawns)
                if color == 'w':
                    rank_index = 7 - r  # Higher for more advanced white pawns
                else:
                    rank_index = r  # Higher for more advanced black pawns
                
                score += self.PASSED_PAWN_BONUS[rank_index]
        
        return score

    def evaluate_king_safety(self, board, king_pos, color, is_endgame):
        """Evaluate king safety based on pawn shield, open files, and attacker proximity"""
        if not king_pos:
            return 0  # No king found
            
        score = 0
        r, c = king_pos
        
        # In endgame, king activity is good; in middlegame, king safety is paramount
        if is_endgame:
            # In endgame, we want the king to be active and in the center
            return 0  # Position tables already handle this
        
        # Check pawn shield in front of king (assumes castled king)
        pawn_shield_score = 0
        pawn_shield_count = 0
        
        # Define pawn shield area based on king position and color
        if color == 'w':
            shield_r = [r-1, r-2]  # One and two ranks in front of the king
            shield_files = [max(0, c-1), c, min(7, c+1)]  # King's file and adjacent files
        else:
            shield_r = [r+1, r+2]  # One and two ranks in front of the king
            shield_files = [max(0, c-1), c, min(7, c+1)]  # King's file and adjacent files
        
        # Check for pawns in shield positions
        for sr in shield_r:
            if 0 <= sr < 8:
                for sc in shield_files:
                    piece = board[sr][sc]
                    if piece and piece.name == 'P' and piece.color == color:
                        pawn_shield_count += 1
                        # Pawns directly in front of king are more valuable
                        if sc == c:
                            pawn_shield_score += 10
                        else:
                            pawn_shield_score += 5
        
        # Penalize if king has no pawn shield
        if pawn_shield_count == 0:
            score -= 30
        else:
            score += pawn_shield_score
        
        # Check for open files near king (very dangerous)
        king_file_open = True
        adjacent_files_open = 0
        
        # Check king's file
        for check_r in range(8):
            piece = board[check_r][c]
            if piece and piece.name == 'P' and piece.color == color:
                king_file_open = False
                break
                
        # Check adjacent files
        for adj_c in [max(0, c-1), min(7, c+1)]:
            if adj_c == c:
                continue
                
            file_open = True
            for check_r in range(8):
                piece = board[check_r][adj_c]
                if piece and piece.name == 'P' and piece.color == color:
                    file_open = False
                    break
            
            if file_open:
                adjacent_files_open += 1
        
        # Penalize open files
        if king_file_open:
            score -= 40
        score -= adjacent_files_open * 20
        
        # Check enemy piece proximity to king (only major pieces)
        enemy_color = 'b' if color == 'w' else 'w'
        enemy_attackers = 0
        
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                check_r, check_c = r + dr, c + dc
                if 0 <= check_r < 8 and 0 <= check_c < 8:
                    piece = board[check_r][check_c]
                    if piece and piece.color == enemy_color and piece.name in ['Q', 'R', 'B', 'N']:
                        enemy_attackers += 1
                        # Queen and rook are more dangerous
                        if piece.name in ['Q', 'R']:
                            score -= 15
                        else:
                            score -= 10
        
        # Severe penalty for multiple attackers (potential mating attack)
        if enemy_attackers >= 2:
            score -= enemy_attackers * 10
            
        return score

    def get_all_moves(self, board, color):
        """Get all legal moves for the given color"""
        moves = []
        for r, row in enumerate(board):
            for c, p in enumerate(row):
                if p and p.color == color:
                    piece_moves = p.get_possible_moves(board, r, c)
                    # Filter moves that would leave the king in check
                    for move in piece_moves:
                        temp_board, undo_data = self.make_move(deepcopy(board), (r, c, move[0], move[1]), return_undo=True)
                        king_pos = self.find_king(temp_board, color)
                        if not king_pos or not self.is_in_check(temp_board, king_pos, color):
                            moves.append((r, c, move[0], move[1]))
        return moves

    def is_game_over(self, board):
        """Check if the game is over (checkmate, stalemate, or insufficient material)"""
        # Check if any kings are missing
        if not self.find_king(board, 'w') or not self.find_king(board, 'b'):
            return True

        # Check for checkmate or stalemate
        if not self.has_legal_moves(board, 'b'):
            black_king_pos = self.find_king(board, 'b')
            if black_king_pos and self.is_in_check(board, black_king_pos, 'b'):
                return True  # Black is checkmated
            else:
                return True  # Stalemate

        if not self.has_legal_moves(board, 'w'):
            white_king_pos = self.find_king(board, 'w')
            if white_king_pos and self.is_in_check(board, white_king_pos, 'w'):
                return True  # White is checkmated
            else:
                return True  # Stalemate
                
        # Check for insufficient material
        if self.has_insufficient_material(board):
            return True

        return False

    def has_insufficient_material(self, board):
        """Check if there is insufficient material to continue"""
        piece_counts = {'w': {}, 'b': {}}
        
        # Count pieces for each color
        for row in board:
            for piece in row:
                if piece:
                    if piece.name not in piece_counts[piece.color]:
                        piece_counts[piece.color][piece.name] = 0
                    piece_counts[piece.color][piece.name] += 1
        
        # K vs K
        if (len(piece_counts['w']) == 1 and 'K' in piece_counts['w'] and 
            len(piece_counts['b']) == 1 and 'K' in piece_counts['b']):
            return True
            
        # K vs K+N/B
        if ((len(piece_counts['w']) == 1 and 'K' in piece_counts['w'] and 
             len(piece_counts['b']) == 2 and 'K' in piece_counts['b'] and 
             (('N' in piece_counts['b'] and piece_counts['b']['N'] == 1) or 
              ('B' in piece_counts['b'] and piece_counts['b']['B'] == 1))) or
            (len(piece_counts['b']) == 1 and 'K' in piece_counts['b'] and 
             len(piece_counts['w']) == 2 and 'K' in piece_counts['w'] and 
             (('N' in piece_counts['w'] and piece_counts['w']['N'] == 1) or 
              ('B' in piece_counts['w'] and piece_counts['w']['B'] == 1)))):
            return True
            
        # K+B vs K+B (same color bishops)
        if (len(piece_counts['w']) == 2 and 'K' in piece_counts['w'] and 'B' in piece_counts['w'] and piece_counts['w']['B'] == 1 and
            len(piece_counts['b']) == 2 and 'K' in piece_counts['b'] and 'B' in piece_counts['b'] and piece_counts['b']['B'] == 1):
            
            # Find the colors of both bishops
            white_bishop_square_color = None
            black_bishop_square_color = None
            
            for r in range(8):
                for c in range(8):
                    piece = board[r][c]
                    if piece and piece.name == 'B':
                        square_color = (r + c) % 2  # 0 for light, 1 for dark squares
                        if piece.color == 'w':
                            white_bishop_square_color = square_color
                        else:
                            black_bishop_square_color = square_color
            
            # If bishops are on the same colored squares, it's a draw
            if white_bishop_square_color == black_bishop_square_color:
                return True
                
        return False

    def is_in_check(self, board, king_position, color):
        """Check if the king is in check"""
        king_row, king_col = king_position
        opponent_color = 'b' if color == 'w' else 'w'

        # Check all opponent's pieces to see if they threaten the king
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece and piece.color == opponent_color:
                    moves = piece.get_possible_moves(board, row, col)
                    if (king_row, king_col) in moves:
                        return True
        return False

    def has_legal_moves(self, board, color):
        """Check if the given color has any legal moves"""
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
        """Find the king's position for the given color"""
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

    def piece_value(self, piece):
        """Get the base value of a piece"""
        values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
        return values.get(piece.name.upper(), 0) * (1 if piece.color == 'w' else -1)

    def calculate_best_move_async(self, board, color, callback):
        """Calculate best move in a separate thread"""
        def async_task():
            best_move = self.get_best_move(board, color)
            if callback:
                callback(best_move)

        # Running the AI calculation in a separate thread
        thread = threading.Thread(target=async_task)
        thread.start()
        
    def get_search_stats(self):
        """Return statistics about the last search"""
        return {
            "nodes_searched": self.nodes_searched,
            "transposition_table_size": len(self.transposition_table),
            "cache_size": len(self.cache)
        }