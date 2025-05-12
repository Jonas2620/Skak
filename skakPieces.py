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
        - Rochade (hvis betingelserne er opfyldt)
        """
        moves = []
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        # Normale king moves
        for d_row, d_col in king_moves:
            new_row, new_col = row + d_row, col + d_col
            
            if not self.is_valid_position(new_row, new_col):
                continue
                
            if board[new_row][new_col] is None or include_attacks or (
                isinstance(board[new_row][new_col], Piece) and board[new_row][new_col].color != self.color
            ):
                moves.append((new_row, new_col))

        # Rochade (castling) - kun hvis vi ikke er i include_attacks mode
        if not include_attacks and not self.has_moved:
            # Tjek kingside castling (short castling)
            if self._can_castle_kingside(board, row, col):
                moves.append((row, col + 2))
                
            # Tjek queenside castling (long castling)
            if self._can_castle_queenside(board, row, col):
                moves.append((row, col - 2))

        return moves
    
    def _can_castle_kingside(self, board: list, row: int, col: int) -> bool:
        """Tjekker om kingside (kort) rochade er mulig."""
        # Kongen må ikke have flyttet sig, og tårnet må ikke have flyttet sig
        if self.has_moved or col + 3 >= 8:
            return False
            
        rook_pos = board[row][col + 3]
        if not isinstance(rook_pos, Rook) or rook_pos.color != self.color or rook_pos.has_moved:
            return False
            
        # Felterne mellem kongen og tårnet skal være tomme
        if board[row][col + 1] is not None or board[row][col + 2] is not None:
            return False
            
        # Kongen må ikke være i skak, og felterne kongen passerer må ikke være under angreb
        # Dette vil normalt blive tjekket af skaklogikken efter dette træk returneres
        
        return True
    
    def _can_castle_queenside(self, board: list, row: int, col: int) -> bool:
        """Tjekker om queenside (lang) rochade er mulig."""
        # Kongen må ikke have flyttet sig, og tårnet må ikke have flyttet sig
        if self.has_moved or col - 4 < 0:
            return False
            
        rook_pos = board[row][col - 4]
        if not isinstance(rook_pos, Rook) or rook_pos.color != self.color or rook_pos.has_moved:
            return False
            
        # Felterne mellem kongen og tårnet skal være tomme
        if board[row][col - 1] is not None or board[row][col - 2] is not None or board[row][col - 3] is not None:
            return False
            
        # Kongen må ikke være i skak, og felterne kongen passerer må ikke være under angreb
        # Dette vil normalt blive tjekket af skaklogikken efter dette træk returneres
        
        return True