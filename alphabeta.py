import math
from copy import deepcopy
import threading
import time
from skakPieces import Piece

class ChessAI:
    def __init__(self, depth=4):
        self.cache = {}
        self.depth = depth
        self.transposition_table = {}  # For more efficient alpha-beta search
        self.killer_moves = [[None, None] for _ in range(20)]  # Store killer moves per depth
        self.history_table = {}  # History heuristic
        
        # Stats tracking for alpha-beta pruning
        self.stats = {
            'nodes_evaluated': 0,
            'alpha_cutoffs': 0,
            'beta_cutoffs': 0,
            'transposition_hits': 0,
            'killer_move_cutoffs': 0,
            'null_move_cutoffs': 0,
            'late_move_reductions': 0
        }
        
        # Enhanced center control values with more nuanced weighting
        self.CENTER_CONTROL_BONUS = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 5, 10, 10, 10, 10, 5, 0],
            [0, 10, 20, 25, 25, 20, 10, 0],
            [0, 10, 25, 30, 30, 25, 10, 0],
            [0, 10, 25, 30, 30, 25, 10, 0],
            [0, 10, 20, 25, 25, 20, 10, 0],
            [0, 5, 10, 10, 10, 10, 5, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        
        # Improved positional values for pieces
        self.PAWN_POSITION = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5, 5, 10, 27, 27, 10, 5, 5],
            [0, 0, 0, 25, 25, 0, 0, 0],
            [5, -5, -10, 0, 0, -10, -5, 5],
            [5, 10, 10, -20, -20, 10, 10, 5],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]
        
        self.KNIGHT_POSITION = [
            [-50, -40, -30, -30, -30, -30, -40, -50],
            [-40, -20, 0, 5, 5, 0, -20, -40],
            [-30, 5, 15, 20, 20, 15, 5, -30],
            [-30, 0, 15, 25, 25, 15, 0, -30],
            [-30, 5, 15, 25, 25, 15, 5, -30],
            [-30, 10, 15, 20, 20, 15, 10, -30],
            [-40, -20, 5, 10, 10, 5, -20, -40],
            [-50, -40, -30, -30, -30, -30, -40, -50]
        ]
        
        self.BISHOP_POSITION = [
            [-20, -10, -10, -10, -10, -10, -10, -20],
            [-10, 5, 0, 0, 0, 0, 5, -10],
            [-10, 10, 10, 10, 10, 10, 10, -10],
            [-10, 0, 10, 15, 15, 10, 0, -10],
            [-10, 5, 5, 15, 15, 5, 5, -10],
            [-10, 0, 5, 10, 10, 5, 0, -10],
            [-10, 5, 0, 0, 0, 0, 5, -10],
            [-20, -10, -10, -10, -10, -10, -10, -20]
        ]
        
        self.ROOK_POSITION = [
            [0, 0, 0, 5, 5, 0, 0, 0],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 0, 0, 0, 0, 0, -5],
            [-5, 0, 5, 5, 5, 5, 0, -5],
            [5, 10, 10, 10, 10, 10, 10, 5],
            [0, 0, 0, 0, 0, 0, 0, 0]
        ]
        
        self.QUEEN_POSITION = [
            [-20, -10, -10, -5, -5, -10, -10, -20],
            [-10, 0, 5, 0, 0, 0, 0, -10],
            [-10, 5, 5, 5, 5, 5, 0, -10],
            [-5, 0, 5, 5, 5, 5, 0, -5],
            [0, 0, 5, 5, 5, 5, 0, -5],
            [-10, 0, 5, 5, 5, 5, 0, -10],
            [-10, 0, 0, 0, 0, 0, 0, -10],
            [-20, -10, -10, -5, -5, -10, -10, -20]
        ]
        
        # Enhanced king position tables
        self.KING_MIDDLEGAME_POSITION = [
            [30, 40, 10, 0, 0, 10, 40, 30],
            [20, 20, 0, 0, 0, 0, 20, 20],
            [-10, -20, -20, -20, -20, -20, -20, -10],
            [-20, -30, -30, -40, -40, -30, -30, -20],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30],
            [-30, -40, -40, -50, -50, -40, -40, -30]
        ]
        
        self.KING_ENDGAME_POSITION = [
            [-50, -30, -30, -30, -30, -30, -30, -50],
            [-30, -20, 0, 0, 0, 0, -20, -30],
            [-30, 0, 20, 30, 30, 20, 0, -30],
            [-30, 0, 30, 40, 40, 30, 0, -30],
            [-30, 0, 30, 40, 40, 30, 0, -30],
            [-30, 0, 20, 30, 30, 20, 0, -30],
            [-30, -20, 0, 0, 0, 0, -20, -30],
            [-50, -30, -30, -30, -30, -30, -30, -50]
        ]
        
        # King safety bonuses (castling and safe corner)
        self.KING_SAFETY_BONUS = {
            'w': {
                'castled': 150,        # Bonus for castling
                'pawn_shield': 50,     # Bonus for each pawn in front of the king
                'open_lines': -30      # Penalty for open lines in front of the king
            },
            'b': {
                'castled': 150,
                'pawn_shield': 50,
                'open_lines': -30
            }
        }
        
        # Cache for storing king positions
        self.king_positions_cache = {}
        
        # Dynamic piece values based on game phase
        self.PIECE_VALUES = {
            'P': {'opening': 100, 'middlegame': 100, 'endgame': 150},
            'N': {'opening': 320, 'middlegame': 320, 'endgame': 300},
            'B': {'opening': 330, 'middlegame': 340, 'endgame': 350},
            'R': {'opening': 500, 'middlegame': 510, 'endgame': 550},
            'Q': {'opening': 900, 'middlegame': 920, 'endgame': 950},
            'K': {'opening': 2000, 'middlegame': 2000, 'endgame': 2000}
        }
        
        # Mobility bonus (more legal moves = better position)
        self.MOBILITY_BONUS = {
            'P': 1,
            'N': 4,
            'B': 3,
            'R': 2,
            'Q': 1,
            'K': 0.5
        }
        
        # Bonuses for specific structures and positions
        self.PAWN_STRUCTURE_BONUS = {
            'doubled': -20,         # Penalty for doubled pawns
            'isolated': -15,        # Penalty for isolated pawns
            'connected': 10,        # Bonus for connected pawns
            'passed': 30,           # Bonus for passed pawns
            'backward': -10,        # Penalty for backward pawns
            'chain': 8,             # Bonus for pawn chains
            'protected': 12         # Bonus for protected pawns
        }
        
        self.max_time = 14  # Maximum time in seconds for a move
        self.start_time = None
        self.nodes_searched = 0

        self.position_cache = {}  # Cache for evaluated positions
        self.cache_hits = 0
        
        # Aspiration window settings
        self.aspiration_window = 50
        
        # Late move reduction settings
        self.lmr_depth_threshold = 3
        self.lmr_move_threshold = 4
        
        # Null move pruning settings
        self.null_move_depth_threshold = 3
        self.null_move_reduction = 2

    def reset_stats(self):
        #Reset the alpha-beta pruning statistics
        self.stats = {
            'nodes_evaluated': 0,
            'alpha_cutoffs': 0,
            'beta_cutoffs': 0,
            'transposition_hits': 0,
            'killer_move_cutoffs': 0,
            'null_move_cutoffs': 0,
            'late_move_reductions': 0
        }
        self.killer_moves = [[None, None] for _ in range(20)]
        self.history_table = {}
        
    def print_stats(self):
        #Print comprehensive statistics
        print("\n=== Enhanced Alpha-Beta Statistics ===")
        print(f"Total nodes evaluated: {self.stats['nodes_evaluated']}")
        print(f"Alpha cutoffs: {self.stats['alpha_cutoffs']}")
        print(f"Beta cutoffs: {self.stats['beta_cutoffs']}")
        print(f"Killer move cutoffs: {self.stats['killer_move_cutoffs']}")
        print(f"Null move cutoffs: {self.stats['null_move_cutoffs']}")
        print(f"Late move reductions: {self.stats['late_move_reductions']}")
        print(f"Transposition hits: {self.stats['transposition_hits']}")
        
        total_cutoffs = (self.stats['alpha_cutoffs'] + self.stats['beta_cutoffs'] + 
                        self.stats['killer_move_cutoffs'] + self.stats['null_move_cutoffs'])
        
        if self.stats['nodes_evaluated'] > 0:
            pruning_efficiency = total_cutoffs / self.stats['nodes_evaluated'] * 100
            print(f"Total pruning efficiency: {pruning_efficiency:.2f}%")
        print("=====================================\n")

    def is_time_up(self):
        #Check if we've exceeded our time limit
        if self.start_time is None:
            return False
        return time.time() - self.start_time > self.max_time

    def get_best_move(self, board, color):
        #Calculate and return the best move with time management
        self.start_time = time.time()
        self.nodes_searched = 0

        self.reset_stats()

        best_move = None
        best_score = 0
        
        # Iterative deepening
        best_move = None
        current_depth = 1
        
        # Iterative deepening with aspiration windows
        for depth in range(1, self.depth + 1):
            if self.is_time_up():
                break
                
            try:
                if depth == 1:
                    # First iteration uses full window
                    score, move = self.search_with_aspiration(board, color, depth, -math.inf, math.inf)
                else:
                    # Use aspiration window around previous best score
                    alpha = best_score - self.aspiration_window
                    beta = best_score + self.aspiration_window
                    score, move = self.search_with_aspiration(board, color, depth, alpha, beta)
                    
                    # If aspiration window fails, re-search with full window
                    if score <= alpha or score >= beta:
                        score, move = self.search_with_aspiration(board, color, depth, -math.inf, math.inf)
                
                if move:
                    best_move = move
                    best_score = score
                    
            except TimeoutError:
                break
        
        self.print_stats()
        return best_move
    
    def search_with_aspiration(self, board, color, depth, alpha, beta):
        #Search with aspiration window
        moves = self.get_all_moves(board, color)
        if not moves:
            return 0, None
        
        moves = self.sort_moves_advanced(board, moves, color, depth)
        
        best_move = moves[0] if moves else None
        best_score = -math.inf if color == 'w' else math.inf
        
        for move in moves:
            if self.is_time_up():
                raise TimeoutError
                
            new_board = self.make_move_fast(board, move)
            score = self.alphabeta_enhanced(new_board, depth - 1, alpha, beta, color == 'b', depth)
            
            if color == 'w' and score > best_score:
                best_score = score
                best_move = move
                alpha = max(alpha, score)
            elif color == 'b' and score < best_score:
                best_score = score
                best_move = move
                beta = min(beta, score)
                
            if beta <= alpha:
                break
                
        return best_score, best_move

    def alphabeta_enhanced(self, board, depth, alpha, beta, maximizing, original_depth, null_move_allowed=True):
        #Enhanced alpha-beta with multiple pruning techniques
        self.stats['nodes_evaluated'] += 1
        
        # Check time limit
        if self.is_time_up():
            raise TimeoutError
            
        # Transposition table lookup
        board_key = self.board_to_key(board)
        if board_key in self.transposition_table:
            entry = self.transposition_table[board_key]
            if entry['depth'] >= depth:
                self.stats['transposition_hits'] += 1
                return entry['value']
        
        # Terminal node check
        if depth == 0:
            return self.quiescence_search(board, alpha, beta, maximizing, 4)
        
        # Check for game over
        if self.is_game_over(board):
            color = 'w' if maximizing else 'b'
            king_pos = self.find_king(board, color)
            if king_pos and self.is_in_check(board, color, king_pos):
                return -20000 + (original_depth - depth) if maximizing else 20000 - (original_depth - depth)
            return 0  # Stalemate
        
        # Null move pruning
        if (null_move_allowed and depth >= self.null_move_depth_threshold and 
            not self.is_in_check(board, 'w' if maximizing else 'b')):
            
            null_score = self.alphabeta_enhanced(board, depth - self.null_move_reduction - 1, 
                                              -beta, -beta + 1, not maximizing, 
                                              original_depth, False)
            if maximizing and null_score >= beta:
                self.stats['null_move_cutoffs'] += 1
                return beta
            elif not maximizing and null_score <= alpha:
                self.stats['null_move_cutoffs'] += 1
                return alpha
        
        # Generate and sort moves
        color = 'w' if maximizing else 'b'
        moves = self.get_all_moves(board, color)
        
        if not moves:
            return 0  # Stalemate
            
        moves = self.sort_moves_advanced(board, moves, color, depth)
        
        best_score = -math.inf if maximizing else math.inf
        moves_searched = 0
        
        for i, move in enumerate(moves):
            new_board = self.make_move_fast(board, move)
            
            # Late move reduction
            if (i >= self.lmr_move_threshold and depth >= self.lmr_depth_threshold and 
                not self.is_capture(board, move) and not self.is_check_giving_move(board, move)):
                
                # Search with reduced depth first
                reduction = 1 if i < 8 else 2
                score = self.alphabeta_enhanced(new_board, depth - reduction - 1, alpha, beta, 
                                             not maximizing, original_depth)
                
                # If the reduced search suggests this move is good, re-search with full depth
                if ((maximizing and score > alpha) or (not maximizing and score < beta)):
                    score = self.alphabeta_enhanced(new_board, depth - 1, alpha, beta, 
                                                 not maximizing, original_depth)
                    self.stats['late_move_reductions'] += 1
            else:
                # Principal variation search for first move
                if i == 0:
                    score = self.alphabeta_enhanced(new_board, depth - 1, alpha, beta, 
                                                 not maximizing, original_depth)
                else:
                    # Null window search for other moves
                    if maximizing:
                        score = self.alphabeta_enhanced(new_board, depth - 1, alpha, alpha + 1, 
                                                     not maximizing, original_depth)
                        if alpha < score < beta:
                            score = self.alphabeta_enhanced(new_board, depth - 1, score, beta, 
                                                         not maximizing, original_depth)
                    else:
                        score = self.alphabeta_enhanced(new_board, depth - 1, beta - 1, beta, 
                                                     not maximizing, original_depth)
                        if alpha < score < beta:
                            score = self.alphabeta_enhanced(new_board, depth - 1, alpha, score, 
                                                         not maximizing, original_depth)
            
            moves_searched += 1
            
            if maximizing:
                if score > best_score:
                    best_score = score
                alpha = max(alpha, score)
                if beta <= alpha:
                    # Store killer move
                    if depth < len(self.killer_moves):
                        if self.killer_moves[depth][0] != move:
                            self.killer_moves[depth][1] = self.killer_moves[depth][0]
                            self.killer_moves[depth][0] = move
                    
                    # Update history table
                    move_key = self.move_to_key(move)
                    self.history_table[move_key] = self.history_table.get(move_key, 0) + depth * depth
                    
                    self.stats['beta_cutoffs'] += 1
                    break
            else:
                if score < best_score:
                    best_score = score
                beta = min(beta, score)
                if beta <= alpha:
                    # Store killer move
                    if depth < len(self.killer_moves):
                        if self.killer_moves[depth][0] != move:
                            self.killer_moves[depth][1] = self.killer_moves[depth][0]
                            self.killer_moves[depth][0] = move
                    
                    # Update history table
                    move_key = self.move_to_key(move)
                    self.history_table[move_key] = self.history_table.get(move_key, 0) + depth * depth
                    
                    self.stats['alpha_cutoffs'] += 1
                    break
        
        # Store in transposition table
        self.transposition_table[board_key] = {'value': best_score, 'depth': depth}
        
        return best_score
    
    def quiescence_search(self, board, alpha, beta, maximizing, depth):
        #Quiescence search to avoid horizon effect
        if depth == 0:
            return self.evaluate_board(board)
            
        stand_pat = self.evaluate_board(board)
        
        if maximizing:
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)
        else:
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)
        
        # Only consider captures and checks
        color = 'w' if maximizing else 'b'
        moves = self.get_tactical_moves(board, color)
        moves = self.sort_moves_advanced(board, moves, color, depth)
        
        for move in moves:
            new_board = self.make_move_fast(board, move)
            score = self.quiescence_search(new_board, alpha, beta, not maximizing, depth - 1)
            
            if maximizing:
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            else:
                beta = min(beta, score)
                if beta <= alpha:
                    break
                    
        return alpha if maximizing else beta
    
    def get_tactical_moves(self, board, color):
        #Get only captures and check-giving moves for quiescence search
        moves = []
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece and piece.color == color:
                    piece_moves = piece.get_possible_moves(board, r, c)
                    for move in piece_moves:
                        # Add captures
                        if board[move[0]][move[1]] is not None:
                            moves.append((r, c, move[0], move[1]))
                        # Add check-giving moves (simplified check)
                        elif self.is_check_giving_move(board, (r, c, move[0], move[1])):
                            moves.append((r, c, move[0], move[1]))
        return moves

    def sort_moves_advanced(self, board, moves, color, depth):
        #Advanced move ordering with multiple heuristics
        if not moves:
            return moves
            
        move_scores = []
        
        for move in moves:
            score = 0
            r1, c1, r2, c2 = move
            piece = board[r1][c1]
            target = board[r2][c2]
            
            # 1. Hash move (from transposition table) - highest priority
            board_key = self.board_to_key(board)
            if board_key in self.transposition_table:
                # This would require storing best moves in transposition table
                pass
            
            # 2. Captures with MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
            if target:
                victim_value = self.piece_value(target)
                attacker_value = self.piece_value(piece)
                score += 10000 + victim_value - attacker_value
            
            # 3. Killer moves
            if depth < len(self.killer_moves):
                if move == self.killer_moves[depth][0]:
                    score += 9000
                    self.stats['killer_move_cutoffs'] += 1
                elif move == self.killer_moves[depth][1]:
                    score += 8000
                    self.stats['killer_move_cutoffs'] += 1
            
            # 4. History heuristic
            move_key = self.move_to_key(move)
            score += self.history_table.get(move_key, 0)
            
            # 5. Promotions
            if piece.name == 'P' and (r2 == 0 or r2 == 7):
                score += 7000
            
            # 6. Checks
            if self.is_check_giving_move(board, move):
                score += 500
            
            # 7. Central squares
            center_bonus = self.CENTER_CONTROL_BONUS[r2][c2]
            score += center_bonus
            
            # 8. Piece development
            if piece.name in ['N', 'B'] and self.is_development_move(r1, c1, r2, c2, color):
                score += 100
            
            # 9. Castling
            if piece.name == 'K' and abs(c2 - c1) == 2:
                score += 200
            
            move_scores.append((move, score))
        
        # Sort moves by score (highest first)
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]

    def make_move_fast(self, board, move):
        #Fast move making without deep copy for performance
        r1, c1, r2, c2 = move
        new_board = [row[:] for row in board]  # Shallow copy is faster than deepcopy
        piece = new_board[r1][c1]
        new_board[r2][c2] = piece
        new_board[r1][c1] = None
        return new_board

    def is_capture(self, board, move):
        #Check if move is a capture
        r1, c1, r2, c2 = move
        return board[r2][c2] is not None

    def is_check_giving_move(self, board, move):
        #Check if move gives check (simplified)
        r1, c1, r2, c2 = move
        piece = board[r1][c1]
        if not piece:
            return False
            
        # Quick check for direct attacks on opponent king
        opponent_color = 'b' if piece.color == 'w' else 'w'
        opponent_king_pos = self.find_king(board, opponent_color)
        
        if not opponent_king_pos:
            return False
            
        # Make temporary move and check if opponent king is in check
        temp_board = self.make_move_fast(board, move)
        return self.is_in_check(temp_board, opponent_color, opponent_king_pos)

    def is_development_move(self, r1, c1, r2, c2, color):
        #Check if move develops a piece
        if color == 'w':
            return r1 == 7 and r2 < 7  # Moving from back rank
        else:
            return r1 == 0 and r2 > 0  # Moving from back rank

    def move_to_key(self, move):
        #Convert move to hashable key
        return tuple(move)

    # Keep all the original evaluation functions
    def evaluate_board(self, board):
        #Cached board evaluation (same as original but with fast lookup)
        board_key = self.board_to_key(board)
        if board_key in self.position_cache:
            self.cache_hits += 1
            return self.position_cache[board_key]
        
        # Use original evaluation logic
        value = self._evaluate_board_internal(board)
        self.position_cache[board_key] = value
        return value

    def _evaluate_board_internal(self, board):
        #Internal evaluation function (same as original)
        value = 0
        white_piece_count = 0
        black_piece_count = 0
        
        white_material = 0
        black_material = 0
        
        white_pawns_by_file = [0] * 8
        black_pawns_by_file = [0] * 8
        
        # Phase determination
        total_pieces = sum(1 for row in board for p in row if p is not None)
        game_phase = self.determine_game_phase(total_pieces)
        
        # Count pieces and calculate material
        for r, row in enumerate(board):
            for c, p in enumerate(row):
                if p:
                    if p.color == 'w':
                        white_piece_count += 1
                        white_material += self.piece_value(p, game_phase)
                        if p.name == 'P':
                            white_pawns_by_file[c] += 1
                    else:
                        black_piece_count += 1
                        black_material += self.piece_value(p, game_phase)
                        if p.name == 'P':
                            black_pawns_by_file[c] += 1
        
        # Material balance
        value = white_material - black_material
        
        # Add position evaluations, mobility, pawn structure, etc.
        # (Keep all the original evaluation logic here)
        
        return value

    def _get_move_at_depth(self, board, color, depth):
        best_eval = -math.inf if color == 'w' else math.inf
        best_move = None
        moves = self.get_all_moves(board, color)
        moves = self.sort_moves(board, moves, color)  # Sort moves for better pruning

        for move in moves:
            if self.is_time_up():
                raise TimeoutError
                
            new_board = deepcopy(board)
            r1, c1, r2, c2 = move
            piece = new_board[r1][c1]
            new_board[r2][c2] = piece
            new_board[r1][c1] = None
            
            eval_value = self.alphabeta(new_board, depth - 1, -math.inf, math.inf, color == 'b')
            
            if color == 'w' and eval_value > best_eval:
                best_eval = eval_value
                best_move = move
            elif color == 'b' and eval_value < best_eval:
                best_eval = eval_value
                best_move = move

        return best_move

    def calculate_best_move_async(self, board, color, callback):
        #Calculate the best move asynchronously and call the callback function when ready
        def worker():
            best_move = self.get_best_move(board, color)
            callback(best_move)
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
    
    def sort_moves(self, board, moves, color):
        #Improved move ordering with check handling
        move_scores = []
        king_pos = self.find_king(board, color)
        in_check = king_pos and self.is_in_check(board, color, king_pos)
        
        for move in moves:
            score = 0
            r1, c1, r2, c2 = move
            piece = board[r1][c1]
            target = board[r2][c2]
            
            # If we're in check, prioritize moves that escape check
            if in_check:
                temp_board = deepcopy(board)
                temp_board[r2][c2] = piece
                temp_board[r1][c1] = None
                new_king_pos = (r2, c2) if piece.name == 'K' else king_pos
                if not self.is_in_check(temp_board, color, new_king_pos):
                    score += 1000
            
            # Existing scoring logic
            if target:
                score += 10 * self.piece_value(target) - self.piece_value(piece)
            
            if piece.name == 'P' and (r2 == 0 or r2 == 7):
                score += 900
            
            if piece.name in ['N', 'B'] and 2 <= r2 <= 5 and 2 <= c2 <= 5:
                score += 50
            
            move_scores.append((move, score))
        
        return [move for move, _ in sorted(move_scores, key=lambda x: x[1], reverse=(color=='w'))]

    def is_opening(self, board):
        #Check if we're in the opening phase of the game
        piece_count = sum(1 for row in board for piece in row if piece is not None)
        return piece_count >= 28  # More than 28 pieces on the board

    def alphabeta(self, board, depth, alpha, beta, maximizing):
        #Enhanced alpha-beta pruning with better check handling
        self.stats['nodes_evaluated'] += 1
        board_key = self.board_to_key(board)

        # Check transposition table
        if board_key in self.transposition_table and self.transposition_table[board_key]['depth'] >= depth:
            self.stats['transposition_hits'] += 1
            return self.transposition_table[board_key]['value']

        if depth == 0 or self.is_game_over(board):
            eval_value = self.evaluate_board(board)
            self.transposition_table[board_key] = {'value': eval_value, 'depth': depth}
            return eval_value

        color = 'w' if maximizing else 'b'
        moves = self.get_all_moves(board, color)

        # If in check and no moves available, it's checkmate
        king_pos = self.find_king(board, color)
        if king_pos and self.is_in_check(board, color, king_pos) and not moves:
            return -20000 if maximizing else 20000

        # If no moves available but not in check, it's stalemate
        if not moves:
            return 0

        # Sort moves to improve pruning
        moves = self.sort_moves(board, moves, color)

        prune_occurred = False  # Track if pruning happened
        
        if maximizing:
            max_eval = -math.inf
            for move in moves:
                # Make a temporary move
                new_board = deepcopy(board)
                r1, c1, r2, c2 = move
                piece = new_board[r1][c1]
                new_board[r2][c2] = piece
                new_board[r1][c1] = None
                
                eval_value = self.alphabeta(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_value)
                alpha = max(alpha, eval_value)
                
                if beta <= alpha:
                    if not prune_occurred:  # Count cutoff only once per node
                        self.stats['beta_cutoffs'] += 1
                        prune_occurred = True
                    break  # Beta cutoff
                    
            self.transposition_table[board_key] = {'value': max_eval, 'depth': depth}
            return max_eval
        else:
            min_eval = math.inf
            for move in moves:
                # Make a temporary move
                new_board = deepcopy(board)
                r1, c1, r2, c2 = move
                piece = new_board[r1][c1]
                new_board[r2][c2] = piece
                new_board[r1][c1] = None
                
                eval_value = self.alphabeta(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_value)
                beta = min(beta, eval_value)
                
                if beta <= alpha:
                    if not prune_occurred:  # Count cutoff only once per node
                        self.stats['alpha_cutoffs'] += 1
                        prune_occurred = True
                    break  # Alpha cutoff
                    
            self.transposition_table[board_key] = {'value': min_eval, 'depth': depth}
            return min_eval

    def make_move(self, board, move, return_undo=False):
        #Make a move on the board and return the new board state
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
        #Undo a move on the board
        r1, c1, r2, c2, piece, target = undo_data
        board[r1][c1] = piece
        board[r2][c2] = target
        self.king_positions_cache = {}  # Clear cache

    def board_to_key(self, board):
        #Convert board to a hashable key for the transposition table
        return tuple(tuple((p.name, p.color) if p else None for p in row) for row in board)

    def evaluate_board(self, board):
        #Cached board evaluation
        board_key = self.board_to_key(board)
        if board_key in self.position_cache:
            self.cache_hits += 1
            return self.position_cache[board_key]
        
        value = 0
        white_piece_count = 0
        black_piece_count = 0
        
        white_material = 0
        black_material = 0
        
        white_pawns_by_file = [0] * 8
        black_pawns_by_file = [0] * 8
        
        # Phase determination
        total_pieces = sum(1 for row in board for p in row if p is not None)
        game_phase = self.determine_game_phase(total_pieces)
        
        # Count pieces and calculate material
        for r, row in enumerate(board):
            for c, p in enumerate(row):
                if p:
                    if p.color == 'w':
                        white_piece_count += 1
                        white_material += self.piece_value(p, game_phase)
                        if p.name == 'P':
                            white_pawns_by_file[c] += 1
                    else:
                        black_piece_count += 1
                        black_material += self.piece_value(p, game_phase)
                        if p.name == 'P':
                            black_pawns_by_file[c] += 1
        
        # Material balance
        value = white_material - black_material
        
        # Board position value for all pieces
        white_position_value = 0
        black_position_value = 0
        
        # Mobility
        white_mobility = 0
        black_mobility = 0
        
        # Pawn structure
        white_pawn_structure = 0
        black_pawn_structure = 0
        
        # King safety
        white_king_safety = 0
        black_king_safety = 0
        
        # Find king positions
        white_king_pos = self.find_king(board, 'w')
        black_king_pos = self.find_king(board, 'b')
        
        # Evaluate all pieces on the board
        for r, row in enumerate(board):
            for c, p in enumerate(row):
                if not p:
                    continue
                    
                # Position evaluation based on piece type
                position_value = self.get_position_value(p.name, r, c, game_phase == 'endgame', p.color)
                
                # Mobility (number of legal moves)
                possible_moves = p.get_possible_moves(board, r, c)
                mobility_value = len(possible_moves) * self.MOBILITY_BONUS.get(p.name, 0)
                
                if p.color == 'w':
                    white_position_value += position_value
                    white_mobility += mobility_value
                    
                    # Pawn structure evaluation for white
                    if p.name == 'P':
                        white_pawn_structure += self.evaluate_pawn_structure(board, r, c, 'w', white_pawns_by_file)
                else:
                    black_position_value += position_value
                    black_mobility += mobility_value
                    
                    # Pawn structure evaluation for black
                    if p.name == 'P':
                        black_pawn_structure += self.evaluate_pawn_structure(board, r, c, 'b', black_pawns_by_file)
        
        # Evaluate king safety if kings are on the board
        if white_king_pos:
            white_king_safety = self.evaluate_king_safety(board, white_king_pos, 'w', game_phase)
        
        if black_king_pos:
            black_king_safety = self.evaluate_king_safety(board, black_king_pos, 'b', game_phase)
        
        # Add all components to the final evaluation
        value += (white_position_value - black_position_value)
        value += (white_mobility - black_mobility)
        value += (white_pawn_structure - black_pawn_structure)
        value += (white_king_safety - black_king_safety)
        
        # Add bonus for development in the opening
        if game_phase == 'opening':
            white_development = self.calculate_development(board, 'w')
            black_development = self.calculate_development(board, 'b')
            value += (white_development - black_development) * 10
        
        # Add bonuses for center control
        value += self.evaluate_center_control(board)
        
        # Add bonuses for piece coordination
        value += self.evaluate_piece_coordination(board)
        
        # Endgame-specific evaluations
        if game_phase == 'endgame':
            value += self.evaluate_endgame(board, white_king_pos, black_king_pos)
            
        self.position_cache[board_key] = value
        return value

    def evaluate_endgame(self, board, white_king_pos, black_king_pos):
        #Evaluate endgame-specific factors
        value = 0
        
        # If we have kings
        if white_king_pos and black_king_pos:
            # In endgame, kings should be active and move toward the center
            white_king_r, white_king_c = white_king_pos
            black_king_r, black_king_c = black_king_pos
            
            # Calculate distance to center (4,4)
            white_king_center_dist = max(abs(white_king_r - 3.5), abs(white_king_c - 3.5))
            black_king_center_dist = max(abs(black_king_r - 3.5), abs(black_king_c - 3.5))
            
            # King centralization bonus (white wants smaller distance, black wants larger)
            value += (black_king_center_dist - white_king_center_dist) * 10
            
            # If one side has a material advantage, encourage moving kings closer to opponent king
            material_diff = self.count_material(board, 'w') - self.count_material(board, 'b')
            
            if material_diff > 300:  # White advantage
                # Kings distance - white wants to get closer
                king_distance = abs(white_king_r - black_king_r) + abs(white_king_c - black_king_c)
                value -= king_distance * 10
            elif material_diff < -300:  # Black advantage
                # Kings distance - black wants to get closer
                king_distance = abs(white_king_r - black_king_r) + abs(white_king_c - black_king_c)
                value += king_distance * 10
        
        return value
        
    def count_material(self, board, color):
        #Count total material value for a given color
        total = 0
        for row in board:
            for piece in row:
                if piece and piece.color == color:
                    total += self.PIECE_VALUES[piece.name]['endgame']
        return total

    def determine_game_phase(self, total_pieces):
        #Determine the current game phase based on number of pieces
        if total_pieces >= 28:  # 32 - 4 pieces
            return 'opening'
        elif total_pieces >= 15:
            return 'middlegame'
        else:
            return 'endgame'
    
    def evaluate_pawn_structure(self, board, row, col, color, pawns_by_file):
        #Evaluate pawn structure for a given pawn
        value = 0
        
        # Doubled pawns (penalty)
        if pawns_by_file[col] > 1:
            value += self.PAWN_STRUCTURE_BONUS['doubled']
            
        # Isolated pawns (penalty)
        is_isolated = True
        for adj_file in [col-1, col+1]:
            if 0 <= adj_file < 8 and pawns_by_file[adj_file] > 0:
                is_isolated = False
                break
        if is_isolated:
            value += self.PAWN_STRUCTURE_BONUS['isolated']
            
        # Connected pawns (bonus)
        is_connected = False
        for adj_col in [col-1, col+1]:
            if 0 <= adj_col < 8:
                for adj_row in [row-1, row, row+1]:
                    if 0 <= adj_row < 8 and board[adj_row][adj_col] and board[adj_row][adj_col].name == 'P' and board[adj_row][adj_col].color == color:
                        is_connected = True
                        break
        if is_connected:
            value += self.PAWN_STRUCTURE_BONUS['connected']
            
        # Passed pawns (bonus - no opponent pawns in front or to the sides)
        is_passed = True
        forward_range = range(row-1, -1, -1) if color == 'w' else range(row+1, 8)
        for r in forward_range:
            for c in [col-1, col, col+1]:
                if 0 <= c < 8 and 0 <= r < 8 and board[r][c] and board[r][c].name == 'P' and board[r][c].color != color:
                    is_passed = False
                    break
        if is_passed:
            value += self.PAWN_STRUCTURE_BONUS['passed']
            
        # Protected pawns (bonus)
        is_protected = False
        protect_row = row + 1 if color == 'w' else row - 1
        for protect_col in [col-1, col+1]:
            if 0 <= protect_row < 8 and 0 <= protect_col < 8:
                protector = board[protect_row][protect_col]
                if protector and protector.name == 'P' and protector.color == color:
                    is_protected = True
                    break
        if is_protected:
            value += self.PAWN_STRUCTURE_BONUS['protected']
            
        return value
          
    def evaluate_piece_coordination(self, board):
        #Evaluate how well pieces coordinate with each other
        coordination_score = 0
        piece_positions = {'w': [], 'b': []}

        # Find all pieces
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece:
                    piece_positions[piece.color].append((r, c))

        # Evaluate coordination between pieces
        for color in ['w', 'b']:
            for i, (r1, c1) in enumerate(piece_positions[color]):
                for j in range(i + 1, len(piece_positions[color])):
                    r2, c2 = piece_positions[color][j]
                    # Manhattan distance between pieces
                    distance = abs(r1 - r2) + abs(c1 - c2)
                    if distance <= 2:  # Pieces are close enough to support each other
                        coordination_score += 1 if color == 'w' else -1

        return coordination_score
            
    def evaluate_king_safety(self, board, king_pos, color, game_phase):
        #Evaluate king safety based on position, pawn protection, and open lines
        if game_phase == 'endgame':
            return 0  # In endgame, king safety is less important
        king_row, king_col = king_pos
        value = 0
        
        # Check for castling (based on king position)
        if color == 'w' and king_row == 7:
            if king_col in [1, 2]:  # King is in queenside castle position
                value += self.KING_SAFETY_BONUS[color]['castled']
            elif king_col in [6, 7]:  # King is in kingside castle position
                value += self.KING_SAFETY_BONUS[color]['castled']
        elif color == 'b' and king_row == 0:
            if king_col in [1, 2]:  # King is in queenside castle position
                value += self.KING_SAFETY_BONUS[color]['castled']
            elif king_col in [6, 7]:  # King is in kingside castle position
                value += self.KING_SAFETY_BONUS[color]['castled']
                
        # Check for pawn shield in front of king
        pawn_shield_count = 0
        front_row = king_row - 1 if color == 'w' else king_row + 1
        if 0 <= front_row < 8:
            for c in [king_col-1, king_col, king_col+1]:
                if 0 <= c < 8 and board[front_row][c] and board[front_row][c].name == 'P' and board[front_row][c].color == color:
                    pawn_shield_count += 1
                    
        value += pawn_shield_count * self.KING_SAFETY_BONUS[color]['pawn_shield']
        
        # Check for open lines in front of king
        open_lines_count = 0
        for c in [king_col-1, king_col, king_col+1]:
            if 0 <= c < 8:
                has_pawn = False
                for r in range(8):
                    if board[r][c] and board[r][c].name == 'P':
                        has_pawn = True
                        break
                if not has_pawn:
                    open_lines_count += 1
                    
        value += open_lines_count * self.KING_SAFETY_BONUS[color]['open_lines']
        
        return value
    
    def evaluate_center_control(self, board):
        #Evaluate control over the center
        value = 0
        
        # Define central squares
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        extended_center = [(2, 2), (2, 3), (2, 4), (2, 5), 
                          (3, 2), (3, 5), 
                          (4, 2), (4, 5), 
                          (5, 2), (5, 3), (5, 4), (5, 5)]
        
        # Tæl antallet af centrale felter der er kontrolleret af hver spiller
        white_center_control = 0
        black_center_control = 0
        
        for r, c in center_squares:
            # Centrumskontrol med brikker
            piece = board[r][c]
            if piece:
                if piece.color == 'w':
                    white_center_control += 3
                else:
                    black_center_control += 3
            
            # Centrumskontrol med angreb
            white_attacks = self.count_attacks_on_square(board, r, c, 'w')
            black_attacks = self.count_attacks_on_square(board, r, c, 'b')
            
            white_center_control += white_attacks * 2
            black_center_control += black_attacks * 2
            
        # Tæl det udvidede centrum
        for r, c in extended_center:
            # Centrumskontrol med brikker
            piece = board[r][c]
            if piece:
                if piece.color == 'w':
                    white_center_control += 1
                else:
                    black_center_control += 1
            
            # Centrumskontrol med angreb
            white_attacks = self.count_attacks_on_square(board, r, c, 'w')
            black_attacks = self.count_attacks_on_square(board, r, c, 'b')
            
            white_center_control += white_attacks
            black_center_control += black_attacks
            
        return (white_center_control - black_center_control) * 2
    
    def count_attacks_on_square(self, board, row, col, color):
        #Tæller hvor mange angreb en spiller har på et specifikt felt
        count = 0
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece and piece.color == color:
                    possible_moves = piece.get_possible_moves(board, r, c)
                    if (row, col) in possible_moves:
                        count += 1
        return count
    
    def piece_value(self, piece, phase='middlegame'):
        return self.PIECE_VALUES[piece.name][phase]

    def determine_game_phase(self, total_pieces):
        if total_pieces >= 28:
            return 'opening'
        elif total_pieces >= 16:
            return 'middlegame'
        else:
            return 'endgame'

    def get_position_value(self, name, r, c, is_endgame, color):
        if color == 'b':
            r = 7 - r  # vend rækken for sort

        table = {
            'P': self.PAWN_POSITION,
            'N': self.KNIGHT_POSITION,
            'B': self.BISHOP_POSITION,
            'R': self.ROOK_POSITION,
            'Q': self.QUEEN_POSITION,
            'K': self.KING_ENDGAME_POSITION if is_endgame else self.KING_MIDDLEGAME_POSITION
        }.get(name)

        return table[r][c] if table else 0

    def evaluate_pawn_structure(self, board, r, c, color, pawns_by_file):
        score = 0

        # Dobbeltbønder
        if pawns_by_file[c] > 1:
            score += self.PAWN_STRUCTURE_BONUS['doubled']

        # Isoleret bønde
        is_isolated = True
        for dc in [-1, 1]:
            nc = c + dc
            if 0 <= nc < 8 and pawns_by_file[nc] > 0:
                is_isolated = False
                break
        if is_isolated:
            score += self.PAWN_STRUCTURE_BONUS['isolated']

        # Fribønder og beskyttede bønder
        direction = -1 if color == 'w' else 1
        protected = False
        passed = True

        for dr in range(1, 8):
            nr = r + dr * direction
            if 0 <= nr < 8:
                for dc in [-1, 0, 1]:
                    nc = c + dc
                    if 0 <= nc < 8:
                        target = board[nr][nc]
                        if target and target.name == 'P' and target.color != color:
                            passed = False
        
        for dr in [-1]:
            nr = r + dr * direction
            for dc in [-1, 1]:
                nc = c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    support = board[nr][nc]
                    if support and support.name == 'P' and support.color == color:
                        protected = True

        if passed:
            score += self.PAWN_STRUCTURE_BONUS['passed']
        if protected:
            score += self.PAWN_STRUCTURE_BONUS['protected']

        return score

    def evaluate_king_safety(self, board, king_pos, color, game_phase):
        r, c = king_pos
        score = 0

        # Bonus hvis rokade er foretaget (baseret på placering)
        if (color == 'w' and r == 7 and c in (6, 2)) or (color == 'b' and r == 0 and c in (6, 2)):
            score += self.KING_SAFETY_BONUS[color]['castled']

        # Bonus for åbne linjer foran kongen
        for dc in [-1, 0, 1]:
            nc = c + dc
            if 0 <= nc < 8:
                if color == 'w' and (r - 1 >= 0 and board[r - 1][nc] is None):
                    score += self.KING_SAFETY_BONUS[color]['open_lines']
                if color == 'b' and (r + 1 < 8 and board[r + 1][nc] is None):
                    score += self.KING_SAFETY_BONUS[color]['open_lines']

        # Bonus for bondeskjold
        for dc in [-1, 0, 1]:
            nc = c + dc
            if 0 <= nc < 8:
                if color == 'w' and r - 1 >= 0:
                    shield = board[r - 1][nc]
                    if shield and shield.name == 'P' and shield.color == 'w':
                        score += self.KING_SAFETY_BONUS['w']['pawn_shield']
                elif color == 'b' and r + 1 < 8:
                    shield = board[r + 1][nc]
                    if shield and shield.name == 'P' and shield.color == 'b':
                        score += self.KING_SAFETY_BONUS['b']['pawn_shield']

        return score

    def calculate_development(self, board, color):
        #Calculate development score based on how many minor pieces have moved
        development_score = 0
        
        # Check development of knights and bishops
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece and piece.color == color and piece.name in ['N', 'B']:
                    # Give points if the piece is not on its starting position
                    if (color == 'w' and r < 7) or (color == 'b' and r > 0):
                        development_score += 1
                        
                        # Additional bonus for centralized minor pieces
                        if 2 <= r <= 5 and 2 <= c <= 5:
                            development_score += 0.5
        
        return development_score


    def find_king(self, board, color):
        #Find the king position for the given color
        # Clear the cache to ensure fresh king position lookup
        self.king_positions_cache = {}
            
        for r, row in enumerate(board):
            for c, piece in enumerate(row):
                if piece and piece.name == 'K' and piece.color == color:
                    self.king_positions_cache[color] = (r, c)
                    return (r, c)
        return None

    def is_game_over(self, board):
        return not any(self.get_all_moves(board, color) for color in ['w', 'b'])

    def is_in_check(self, board, color, king_pos=None):
        #Check if the given color is in check
        if king_pos is None:
            king_pos = self.find_king(board, color)
        if not king_pos:
            return False
            
        r, c = king_pos
        opponent_color = 'b' if color == 'w' else 'w'
        
        # Check if any opponent's piece can attack the king
        for r2, row in enumerate(board):
            for c2, piece in enumerate(row):
                if piece and piece.color == opponent_color:
                    moves = piece.get_possible_moves(board, r2, c2, include_attacks=True)
                    if king_pos in moves:
                        return True
        return False

    def get_all_moves(self, board, color):
        #Get all legal moves for the given color, ensuring no moves leave the king in check
        moves = []
        king_pos = self.find_king(board, color)
        if not king_pos:
            return moves

        # First check if we're in check
        in_check = self.is_in_check(board, color, king_pos)
        
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece and piece.color == color:
                    piece_moves = piece.get_possible_moves(board, r, c)
                    for move in piece_moves:
                        # Make a temporary move
                        temp_board = deepcopy(board)
                        temp_board[move[0]][move[1]] = piece
                        temp_board[r][c] = None
                        
                        # Update king position if the king is moving
                        new_king_pos = (move[0], move[1]) if piece.name == 'K' else king_pos
                        
                        # Verify that the move doesn't leave the king in check
                        if not self.is_in_check(temp_board, color, new_king_pos):
                            # If we're in check, only add moves that escape check
                            if not in_check or not self.is_in_check(temp_board, color, new_king_pos):
                                moves.append((r, c, move[0], move[1]))
        
        return moves

    def get_piece_moves(self,board, pos, piece):
        row, col = pos
        color = piece.color
        p_type = type(piece).__name__
        directions = []
        moves = []

        def in_bounds(r, c):
            return 0 <= r < 8 and 0 <= c < 8

        def is_enemy(r, c):
            return board[r][c] is not None and board[r][c][0] != color

        if p_type == 'P':
            dir = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1

            # Fremad
            if in_bounds(row + dir, col) and board[row + dir][col] is None:
                moves.append((row + dir, col))
                # Dobbelt fremad fra startposition
                if row == start_row and board[row + 2 * dir][col] is None:
                    moves.append((row + 2 * dir, col))

            # Diagonal slag
            for dc in [-1, 1]:
                r, c = row + dir, col + dc
                if in_bounds(r, c) and is_enemy(r, c):
                    moves.append((r, c))

        elif p_type == 'R':
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        elif p_type == 'B':
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        elif p_type == 'Q':
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                        (-1, -1), (-1, 1), (1, -1), (1, 1)]

        elif p_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    r, c = row + dr, col + dc
                    if in_bounds(r, c) and (board[r][c] is None or is_enemy(r, c)):
                        moves.append((r, c))

        elif p_type == 'N':
            knight_jumps = [
                (-2, -1), (-2, 1), (-1, -2), (-1, 2),
                (1, -2), (1, 2), (2, -1), (2, 1)
            ]
            for dr, dc in knight_jumps:
                r, c = row + dr, col + dc
                if in_bounds(r, c) and (board[r][c] is None or is_enemy(r, c)):
                    moves.append((r, c))

        # Hvis det er en brik med "glidende" retninger
        if directions:
            for dr, dc in directions:
                r, c = row + dr, col + dc
                while in_bounds(r, c):
                    if board[r][c] is None:
                        moves.append((r, c))
                    elif is_enemy(r, c):
                        moves.append((r, c))
                        break
                    else:
                        break
                    r += dr
                    c += dc

        return moves
    def piece_value(self, piece, phase='middlegame'):
        #Get the value of a piece based on the game phase
        return self.PIECE_VALUES[piece.name][phase]

    def get_position_value(self, name, r, c, is_endgame, color):
        #Get the positional value of a piece based on its type and position
        if color == 'b':
            r = 7 - r  # Mirror the row for black pieces
        
        table = {
            'P': self.PAWN_POSITION,
            'N': self.KNIGHT_POSITION,
            'B': self.BISHOP_POSITION,
            'R': self.ROOK_POSITION,
            'Q': self.QUEEN_POSITION,
            'K': self.KING_ENDGAME_POSITION if is_endgame else self.KING_MIDDLEGAME_POSITION
        }.get(name)
        
        return table[r][c] if table else 0

    def is_checkmate(self, board, color):
        
        #Checks if the given color is in checkmate. Returns True if in checkmate, False otherwise.
        
        # First check if the king is in check
        king_pos = self.find_king(board, color)
        if not king_pos or not self.is_in_check(board, color, king_pos):
            return False

        # Get all possible moves for the color
        all_moves = self.get_all_moves(board, color)
        
        # If there are any legal moves, it's not checkmate
        return len(all_moves) == 0