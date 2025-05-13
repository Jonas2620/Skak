from typing import List, Tuple, Optional

class Piece:
    """Base klasse for alle skakbrikker."""
    
    def __init__(self, color: str, name: str):
        """
        Initialiserer en skakbrik.
        
        Args:
            color: Farven på brikken ('w' for hvid, 'b' for sort)
            name: Navnet på brikken ('P', 'R', 'N', 'B', 'Q', 'K')
        """
        self.color = color  # 'w' eller 'b'
        self.name = name    # f.eks. 'P', 'R', 'N', 'B', 'Q', 'K'
        self.image = f"{color}{name}.png"
        self.has_moved = False  # Tracker om brikken har bevæget sig (til rochade og bondens dobbelttræk)

    def get_possible_moves(self, board: list, row: int, col: int, include_attacks: bool = False) -> List[Tuple[int, int]]:
        """
        Beregner mulige træk for brikken.
        
        Args:
            board: Skakbrættet repræsenteret som en 2D liste
            row: Nuværende række position
            col: Nuværende kolonne position
            include_attacks: Om kun angrebsfelter skal inkluderes (bruges til skak-tjek)
            
        Returns:
            Liste af koordinater (række, kolonne) der kan flyttes til
        """
        return []

    def __str__(self) -> str:
        """String repræsentation af brikken."""
        return f"{self.color}{self.name}"
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Tjekker om en position er inden for brættet."""
        return 0 <= row < 8 and 0 <= col < 8


class Pawn(Piece):
    """Klasse der repræsenterer en bonde."""
    
    def __init__(self, color: str):
        """Initialiserer en bonde."""
        super().__init__(color, "P")
        self.en_passant_vulnerable = False  # Bruges til at spore om bonden kan slås med en-passant

    def get_possible_moves(self, board: list, row: int, col: int, include_attacks: bool = False) -> List[Tuple[int, int]]:
        """
        Beregner mulige træk for en bonde.
        
        Inkluderer:
        - Fremad bevægelse (et eller to felter fra startposition)
        - Diagonale angreb
        - En-passant angreb
        """
        moves = []
        direction = -1 if self.color == 'w' else 1  # Bevægelsesretning for "w" og "b"

        # Hvis vi kun er interesseret i angreb (til brug for is_in_check)
        if include_attacks:
            # Slå diagonalt
            if self.is_valid_position(row + direction, col - 1):
                moves.append((row + direction, col - 1))
            if self.is_valid_position(row + direction, col + 1):
                moves.append((row + direction, col + 1))
            return moves

        # Bevæge sig ét felt fremad (hvis ikke blokeret)
        if self.is_valid_position(row + direction, col) and board[row + direction][col] is None:
            moves.append((row + direction, col))

            # Dobbelttræk på første række (hvis ikke blokeret)
            start_row = 6 if self.color == 'w' else 1
            if row == start_row and self.is_valid_position(row + direction * 2, col) and board[row + direction * 2][col] is None:
                moves.append((row + direction * 2, col))

        # Slå diagonalt
        for c_offset in [-1, 1]:
            new_col = col + c_offset
            new_row = row + direction
            
            if self.is_valid_position(new_row, new_col):
                # Normal diagonal attack
                if isinstance(board[new_row][new_col], Piece) and board[new_row][new_col].color != self.color:
                    moves.append((new_row, new_col))
                    
                # En-passant
                elif board[new_row][new_col] is None and row == (3 if self.color == 'w' else 4):
                    # Tjek for en-passant mulighed
                    if self.is_valid_position(row, new_col) and isinstance(board[row][new_col], Pawn):
                        enemy_pawn = board[row][new_col]
                        if enemy_pawn.color != self.color and enemy_pawn.en_passant_vulnerable:
                            moves.append((new_row, new_col))

        return moves


class Rook(Piece):
    """Klasse der repræsenterer et tårn."""
    
    def __init__(self, color: str):
        """Initialiserer et tårn."""
        super().__init__(color, "R")

    def get_possible_moves(self, board: list, row: int, col: int, include_attacks: bool = False) -> List[Tuple[int, int]]:
        """
        Beregner mulige træk for et tårn.
        
        Bevæger sig vandret og lodret så langt som muligt indtil der mødes en brik eller brættets kant.
        """
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Op, Ned, Venstre, Højre

        for d_row, d_col in directions:
            r, c = row, col
            while True:
                r += d_row
                c += d_col
                if not self.is_valid_position(r, c):
                    break
                    
                if board[r][c] is None:
                    moves.append((r, c))
                elif isinstance(board[r][c], Piece):
                    # For når vi kun tjekker for angreb til is_in_check eller hvis det er en modstanderbrik
                    if include_attacks or board[r][c].color != self.color:
                        moves.append((r, c))  # Slå en modstander
                    break
                else:
                    break  # Dette burde aldrig ske med en velformet skakbræt
        return moves


class Knight(Piece):
    """Klasse der repræsenterer en springer."""
    
    def __init__(self, color: str):
        """Initialiserer en springer."""
        super().__init__(color, "N")

    def get_possible_moves(self, board: list, row: int, col: int, include_attacks: bool = False) -> List[Tuple[int, int]]:
        """
        Beregner mulige træk for en springer.
        
        Bevæger sig i L-form (2 felter i én retning og 1 felt i den anden).
        """
        moves = []
        knight_moves = [(-2, -1), (-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1)]

        for d_row, d_col in knight_moves:
            new_row, new_col = row + d_row, col + d_col
            
            if not self.is_valid_position(new_row, new_col):
                continue
                
            # Springer kan hoppe over andre brikker, så vi tjekker kun destinations-feltet
            if board[new_row][new_col] is None or include_attacks or (
                isinstance(board[new_row][new_col], Piece) and board[new_row][new_col].color != self.color
            ):
                moves.append((new_row, new_col))

        return moves


class Bishop(Piece):
    """Klasse der repræsenterer en løber."""
    
    def __init__(self, color: str):
        """Initialiserer en løber."""
        super().__init__(color, "B")

    def get_possible_moves(self, board: list, row: int, col: int, include_attacks: bool = False) -> List[Tuple[int, int]]:
        """
        Beregner mulige træk for en løber.
        
        Bevæger sig diagonalt så langt som muligt indtil der mødes en brik eller brættets kant.
        """
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Diagonale bevægelser

        for d_row, d_col in directions:
            r, c = row, col
            while True:
                r += d_row
                c += d_col
                if not self.is_valid_position(r, c):
                    break
                    
                if board[r][c] is None:
                    moves.append((r, c))
                elif isinstance(board[r][c], Piece):
                    # For når vi kun tjekker for angreb til is_in_check eller hvis det er en modstanderbrik
                    if include_attacks or board[r][c].color != self.color:
                        moves.append((r, c))  # Slå en modstander
                    break
                else:
                    break  # Dette burde aldrig ske med en velformet skakbræt
        return moves


class Queen(Piece):
    """Klasse der repræsenterer en dronning."""
    
    def __init__(self, color: str):
        """Initialiserer en dronning."""
        super().__init__(color, "Q")

    def get_possible_moves(self, board: list, row: int, col: int, include_attacks: bool = False) -> List[Tuple[int, int]]:
        """
        Beregner mulige træk for en dronning.
        
        Kombinerer tårnets og løberens bevægelser.
        """
        # Dronningen bevæger sig som både et tårn og en løber kombineret
        rook_moves = Rook(self.color).get_possible_moves(board, row, col, include_attacks)
        bishop_moves = Bishop(self.color).get_possible_moves(board, row, col, include_attacks)
        return rook_moves + bishop_moves


class King(Piece):
    """Klasse der repræsenterer en konge."""
    
    def __init__(self, color: str):
        """Initialiserer en konge."""
        super().__init__(color, "K")

    def get_possible_moves(self, board: list, row: int, col: int, include_attacks: bool = False) -> List[Tuple[int, int]]:
        """
        Beregner mulige træk for en konge.
        
        Inkluderer:
        - Normale træk (1 felt i alle retninger)
        - Rokade (hvis betingelserne er opfyldt)
        """
        # Hvis vi kun tjekker angreb, returner normale angrebsfelter
        if include_attacks:
            moves = []
            king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

            for d_row, d_col in king_moves:
                new_row, new_col = row + d_row, col + d_col
                
                if not self.is_valid_position(new_row, new_col):
                    continue
                    
                moves.append((new_row, new_col))

            return moves

        # Normale træk og rokade-muligheder
        moves = []
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        # Normale king moves
        for d_row, d_col in king_moves:
            new_row, new_col = row + d_row, col + d_col
            
            if not self.is_valid_position(new_row, new_col):
                continue
                
            if board[new_row][new_col] is None or (
                isinstance(board[new_row][new_col], Piece) and board[new_row][new_col].color != self.color
            ):
                moves.append((new_row, new_col))

        # Rokade-betingelser
        # Kingside rokade (kort rokade)
        if self._check_kingside_castling(board, row, col):
            moves.append((row, col + 2))

        # Queenside rokade (lang rokade)
        if self._check_queenside_castling(board, row, col):
            moves.append((row, col - 2))

        return moves
    
    def _check_kingside_castling(self, board: list, row: int, col: int) -> bool:
        """Tjekker om kingside (kort) rokade er mulig."""
        # Kongen må ikke have flyttet sig
        if self.has_moved:
            return False
        
        # Tjek om der er et tårn på kingside
        kingside_rook_col = 7
        if not (0 <= kingside_rook_col < 8):
            return False
        
        rook = board[row][kingside_rook_col]
        if not isinstance(rook, Rook) or rook.color != self.color or rook.has_moved:
            return False
        
        # Tjek om felterne mellem kongen og tårnet er tomme
        if board[row][col + 1] is not None or board[row][col + 2] is not None:
            return False
        
        # Verificer at ingen felter er truet under rokaden
        return self._verify_castling_path(board, row, col, col + 2)
    
    def _check_queenside_castling(self, board: list, row: int, col: int) -> bool:
        """Tjekker om queenside (lang) rokade er mulig."""
        # Kongen må ikke have flyttet sig
        if self.has_moved:
            return False
        
        # Tjek om der er et tårn på queenside
        queenside_rook_col = 0
        if not (0 <= queenside_rook_col < 8):
            return False
        
        rook = board[row][queenside_rook_col]
        if not isinstance(rook, Rook) or rook.color != self.color or rook.has_moved:
            return False
        
        # Tjek om felterne mellem kongen og tårnet er tomme
        if board[row][col - 1] is not None or board[row][col - 2] is not None or board[row][col - 3] is not None:
            return False
        
        # Verificer at ingen felter er truet under rokaden
        return self._verify_castling_path(board, row, col, col - 2)
    
    def _verify_castling_path(self, board: list, row: int, start_col: int, end_col: int) -> bool:
        """
        Verificerer at ingen felter mellem start og slut kolonner er truet
        
        :param board: Hele skakbrættet
        :param row: Kongens række
        :param start_col: Startkolonne for kongen
        :param end_col: Slutkolonne for kongen
        :return: True hvis vejen er sikker, False ellers
        """
        # Bestem retningen for rokaden (positiv eller negativ)
        step = 1 if end_col > start_col else -1
        
        # Tjek felterne kongen passerer
        for current_col in range(start_col, end_col + step, step):
            # Tjek om dette felt er truet af nogen modstanderbrikker
            if self._is_square_under_attack(board, row, current_col):
                return False
        
        return True
    
    def _is_square_under_attack(self, board: list, target_row: int, target_col: int) -> bool:
        """
        Tjekker om et felt er truet af modstanderbrikker
        
        :param board: Hele skakbrættet
        :param target_row: Række for det felt der tjekkes
        :param target_col: Kolonne for det felt der tjekkes
        :return: True hvis feltet er truet, False ellers
        """
        # Gennemgå hele brættet
        for row in range(8):
            for col in range(8):
                # Find modstanderbrikker
                piece = board[row][col]
                if isinstance(piece, Piece) and piece.color != self.color:
                    # Få mulige angrebsfelter for denne brik
                    attack_moves = piece.get_possible_moves(board, row, col, include_attacks=True)
                    
                    # Se om nogle af disse angrebsfelter rammer target-feltet
                    if (target_row, target_col) in attack_moves:
                        return True
        
        return False

    @staticmethod
    def perform_castling(board: list, king_row: int, king_col: int, dest_col: int) -> list:
        """
        Udfører rokaden ved at bytte plads mellem kongen og tårnet.
        
        Args:
            board: Skakbrættet
            king_row: Kongens nuværende række
            king_col: Kongens nuværende kolonne
            dest_col: Kongens destinationskolonne
        
        Returns:
            Opdateret skakbræt efter rokaden
        """
        # Bestem tårnets nuværende kolonne baseret på rokaderetningen
        rook_col = 7 if dest_col > king_col else 0
        
        # Bestem tårnets nye placering
        rook_new_col = dest_col - 1 if dest_col > king_col else dest_col + 1
        
        # Hent kongen og tårnet
        king = board[king_row][king_col]
        rook = board[king_row][rook_col]
        
        # Flyt kongen
        board[king_row][dest_col] = king
        board[king_row][king_col] = None
        king.has_moved = True
        
        # Flyt tårnet
        board[king_row][rook_new_col] = rook
        board[king_row][rook_col] = None
        rook.has_moved = True
        
        return board