import math
from copy import deepcopy
import threading
import time  # added for iterative deepening and time control

class ChessAI:
    def __init__(self, depth=6):
        # Initialisering af AI med cache og maksimal søgedybde
        self.cache = {}  # Transposition table
        self.depth = depth

        # Bonus for at kontrollere centrum af brættet (strategisk vigtigt)
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

        self.CHECK_BONUS = 200        #bonus for at sætte modstander i skak
        self.CHECKMATE_BONUS = 1000  #høj bonus for skakmat

    def get_best_move(self, board, color):
        """
        Beregner det bedste træk ved hjælp af iterative deepening og alpha-beta.
        """
        best_move = None
        start_time = time.time()
        max_time = 15.0  # maks tid i sekunder

        # Iterative deepening for at bruge tid effektivt
        for d in range(1, self.depth + 1):
            
            move = self._search_best_move(board, color)
            if move:
                best_move = move
            # Stop hvis tidsgrænsen er nået
            if time.time() - start_time > max_time:
                break
        return best_move

    def _search_best_move(self, board, color):
        best_eval = -math.inf if color == 'w' else math.inf
        best_move = None

        # Hent og sorter træk (move ordering optimerer alpha-beta)
        moves = self.get_all_moves(board, color)
        moves.sort(key=lambda m: self.move_priority(board, m, color), reverse=(color=='w'))

        for move in moves:
            new_board, undo = self.make_move(board, move, return_undo=True)
            eval = self.alphabeta(new_board, self.depth - 1, -math.inf, math.inf, color == 'w')
            self.undo_move(new_board, undo)

            if (color == 'w' and eval > best_eval) or (color == 'b' and eval < best_eval):
                best_eval = eval
                best_move = move
        return best_move

    def alphabeta(self, board, depth, alpha, beta, maximizing):
        """
        Alpha-beta beskæring for Minimax.
        """
        key = self.board_to_key(board)
        if key in self.cache:
            return self.cache[key]

        if depth == 0 or self.is_game_over(board):
            value = self.evaluate_board(board)
            self.cache[key] = value
            return value

        color = 'w' if maximizing else 'b'
        # Move ordering i alphabeta
        moves = self.get_all_moves(board, color)
        moves.sort(key=lambda m: self.move_priority(board, m, color), reverse=maximizing)

        if maximizing:
            value = -math.inf
            for move in moves:
                new_board, undo = self.make_move(board, move, return_undo=True)
                score = self.alphabeta(new_board, depth-1, alpha, beta, False)
                self.undo_move(new_board, undo)
                value = max(value, score)
                alpha = max(alpha, score)
                if alpha >= beta:
                    break  # Beta cutoff
        else:
            value = math.inf
            for move in moves:
                new_board, undo = self.make_move(board, move, return_undo=True)
                score = self.alphabeta(new_board, depth-1, alpha, beta, True)
                self.undo_move(new_board, undo)
                value = min(value, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break  # Alpha cutoff

        self.cache[key] = value
        return value

    def make_move(self, board, move, return_undo=False):
        """
        Udfører et træk på brættet og returnerer undo-data.
        """
        r1, c1, r2, c2 = move
        piece = board[r1][c1]
        target = board[r2][c2]
        undo_data = None
        if return_undo:
            undo_data = (r1, c1, r2, c2, piece, target)
        board[r2][c2] = piece
        board[r1][c1] = None
        return board, undo_data

    def undo_move(self, board, undo_data):
        """
        Fortryder et tidligere træk.
        """
        r1, c1, r2, c2, piece, target = undo_data
        board[r1][c1] = piece
        board[r2][c2] = target

    def board_to_key(self, board):
        """
        Konverterer brættet til en nøgle til caching.
        """
        return tuple(tuple((p.name, p.color) if p else None for p in row) for row in board)

    def evaluate_board(self, board):
        #skakmat evaluering
        if self.is_game_over(board):
            wk = self.find_king(board, 'w')
            bk = self.find_king(board, 'b')
            if wk is None:
                return -float('inf')  #sort vinder
            elif bk is None:
                return float('inf')   #hvid vinder
            elif not self.has_legal_moves(board, 'w') and self.is_in_check(board, wk, 'w'):
                return -float('inf')  #hvid er skakmat
            elif not self.has_legal_moves(board, 'b') and self.is_in_check(board, bk, 'b'):
                return float('inf')   #sort er skakmat
            else:
                return 0  # pat (remis)
        """
        Evaluering med strategiske faktorer: centerkontrol, mobilitet, sikkerhed.
        """
        value = 0
        for r, row in enumerate(board):
            for c, p in enumerate(row):
                if p:
                    base = self.piece_value(p)
                    # Pionforfremmelsespotentiale
                    if p.name.upper() == 'P':
                        base += (7 - r) * 0.1 if p.color=='w' else r * 0.1
                    # Kongesikkerhed: straf for angreb nær kongen
                    king_penalty = 0
                    if p.name.upper() == 'K':
                        king_penalty = -self.count_attackers(board, r, c) * 5
                    pos_bonus = self.CENTER_CONTROL_BONUS[r][c] * (1 if p.color=='w' else -1)
                    mobi = len(p.get_possible_moves(board, r, c)) * 0.05
                    threat = self.threat_penalty(board, r, c, p)
                    prot = self.calculate_protection_bonus(board, r, c, p)
                    value += base + pos_bonus + mobi - threat + prot + king_penalty
        return value

    def evaluate_board_after_move(self, board, move):
        """
        Simulerer et træk og evaluerer resulterende bræt.
        """
        new_board, _ = self.make_move(deepcopy(board), move)
        score = self.evaluate_board(new_board)
    
        #Tjek om modstanderen er sat i skak
        next_color = 'b' if board[move[0]][move[1]].color == 'w' else 'w'
        king_pos = self.find_king(new_board, next_color)                   
        if king_pos and self.is_in_check(new_board, king_pos, next_color):
            score += 1.5 if next_color == 'b' else -1.5  #lille bonus for skak

        return score

    def count_attackers(self, board, r, c):
        """
        Tæller fjendebrikkers angreb mod feltet (r,c).
        """
        count = 0
        for i in range(8):
            for j in range(8):
                attacker = board[i][j]
                if attacker and attacker.color != board[r][c].color:
                    if (r, c) in attacker.get_possible_moves(board, i, j):
                        count += 1
        return count

    def calculate_protection_bonus(self, board, r, c, piece):
        """
        Bonus for beskyttelse fra egne brikker.
        """
        bonus = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if 0 <= r+i < 8 and 0 <= c+j < 8:
                    adj = board[r+i][c+j]
                    if adj and adj.color == piece.color:
                        bonus += 0.5
        return bonus

    def threat_penalty(self, board, r, c, piece):
        """
        Straf for at være i trussel; højere straf for værdifulde brikker.
        """
        penalty = 0
        opponent_color = 'b' if piece.color == 'w' else 'w'
        for i in range(8):
            for j in range(8):
                attacker = board[i][j]
                if attacker and attacker.color == opponent_color:
                    if (r, c) in attacker.get_possible_moves(board, i, j):
                        value = abs(self.piece_value(piece))
                        penalty += value * 2.0  # 🟢 beskyttelsesforstærkning
                        break
        return penalty

    def piece_value(self, piece):
        """
        Materiel værdi: dronning vægtet højere for beskyttelse.
        """
        values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 100, 'K': 2000}  # 🟢 dronningsværdi hævet
        return values.get(piece.name.upper(), 0) * (1 if piece.color == 'w' else -1)

    def get_all_moves(self, board, color):
        """
        Henter alle lovlige træk for farven og undgår skak.
        """
        moves = []
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p and p.color == color:
                    for mv in p.get_possible_moves(board, r, c):
                        tb, undo = self.make_move(board, (r, c, mv[0], mv[1]), return_undo=True)
                        kp = self.find_king(tb, color)
                        if kp and not self.is_in_check(tb, kp, color):
                            moves.append((r, c, mv[0], mv[1]))
                        self.undo_move(tb, undo)
        return moves
    
    def move_priority(self, board, move, color):
        """
        Returnerer en prioritetsscore til move ordering:
        - højere for skakmat
        - derefter skak
        - ellers baseret på brætvurdering
        """
        new_board, _ = self.make_move(deepcopy(board), move)
        opponent = 'b' if color == 'w' else 'w'
        opponent_king = self.find_king(new_board, opponent)
        
        if not opponent_king or (self.is_in_check(new_board, opponent_king, opponent) and not self.has_legal_moves(new_board, opponent)):
            return 10000  #skakmat
        elif opponent_king and self.is_in_check(new_board, opponent_king, opponent):
            return 500  #skak
        else:
            return self.evaluate_board(new_board)

    def is_game_over(self, board):
        """
        Tjek for skakmat, patt eller tabt konge.
        """
        wk = self.find_king(board, 'w')
        bk = self.find_king(board, 'b')
        if not wk or not bk:
            return True
        if self.is_in_check(board, wk, 'w') and not self.has_legal_moves(board, 'w'):
            return True
        if self.is_in_check(board, bk, 'b') and not self.has_legal_moves(board, 'b'):
            return True
        return False

    def is_in_check(self, board, king_pos, color):
        """
        Kontrollerer om kongen er i skak.
        """
        kr, kc = king_pos
        opp = 'b' if color=='w' else 'w'
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p and p.color==opp and (kr, kc) in p.get_possible_moves(board, r, c):
                    return True
        return False

    def has_legal_moves(self, board, color):
        """
        Kontrollerer om der er lovlige træk uden at komme i skak.
        """
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p and p.color==color:
                    for mv in p.get_possible_moves(board, r, c):
                        tb, undo = self.make_move(board, (r, c, mv[0], mv[1]), return_undo=True)
                        kp = self.find_king(tb, color)
                        legal = kp and not self.is_in_check(tb, kp, color)
                        self.undo_move(tb, undo)
                        if legal:
                            return True
        return False

    def find_king(self, board, color):
        """
        Finder kongens position på brættet.
        """
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p and p.name=='K' and p.color==color:
                    return (r, c)
        return None

    def calculate_best_move_async(self, board, color, callback):
        """
        Asynkront beregning af det bedste træk.
        """
        def task():
            move = self.get_best_move(board, color)
            if callback:
                callback(move)
        threading.Thread(target=task).start()
