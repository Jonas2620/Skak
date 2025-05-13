

class Piece:
    def __init__(self, color, name):
        self.color = color  # 'w' eller 'b'
        self.name = name    # f.eks. 'P', 'R', 'N', 'B', 'Q', 'K'
        self.image = f"{color}{name}.png"

    def get_possible_moves(self, board, row, col, flipped=False):
        #base klasse for possible moves, returnere 
        return []

    def __str__(self):
        return f"{self.color}{self.name}"


class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, "P")

    def get_possible_moves(self, board, row, col, flipped=False):
        moves = []
        # Juster retning baseret på farve og om brættet er vendt
        direction = -1 if self.color == 'w' else 1
        if flipped:
            direction = -direction  # Vend retningen, hvis brættet er vendt

        # Juster startpositioner baseret på om brættet er vendt
        white_start_row = 6 if not flipped else 1
        black_start_row = 1 if not flipped else 6

        # Bevæge sig ét felt fremad (hvis ikke blokeret)
        if 0 <= row + direction < 8 and board[row + direction][col] is None:
            moves.append((row + direction, col))

        # Slå diagonalt
        if 0 <= row + direction < 8:
            if col - 1 >= 0 and isinstance(board[row + direction][col - 1], Piece) and board[row + direction][col - 1].color != self.color:
                moves.append((row + direction, col - 1))
            if col + 1 < 8 and isinstance(board[row + direction][col + 1], Piece) and board[row + direction][col + 1].color != self.color:
                moves.append((row + direction, col + 1))

        # Dobbelttræk på første række (hvis ikke blokeret)
        is_first_move_row = (self.color == 'w' and row == white_start_row) or (self.color == 'b' and row == black_start_row)
        if is_first_move_row and 0 <= row + direction * 2 < 8 and board[row + direction][col] is None and board[row + direction * 2][col] is None:
            moves.append((row + direction * 2, col))

        return moves
class Rook(Piece):
    def __init__(self, color):
        super().__init__(color, "R")

    def get_possible_moves(self, board, row, col, flipped=False):
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right

        for direction in directions:
            r, c = row, col
            while True:
                r += direction[0]
                c += direction[1]
                if 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] is None:
                        moves.append((r, c))
                    elif isinstance(board[r][c], Piece) and board[r][c].color != self.color:
                        moves.append((r, c))  # Slå en modstander
                        break
                    else:
                        break  # Stoppes, hvis egen brik er i vejen
                else:
                    break
        return moves


class Knight(Piece):
    def __init__(self, color):
        super().__init__(color, "N")

    def get_possible_moves(self, board, row, col, flipped=False):
        moves = []
        knight_moves = [(-2, -1), (-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1)]

        for move in knight_moves:
            r, c = row + move[0], col + move[1]
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] is None or isinstance(board[r][c], Piece) and board[r][c].color != self.color:
                    moves.append((r, c))

        return moves


class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color, "B")

    def get_possible_moves(self, board, row, col, flipped=False):
        moves = []
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Diagonale bevægelser

        for direction in directions:
            r, c = row, col
            while True:
                r += direction[0]
                c += direction[1]
                if 0 <= r < 8 and 0 <= c < 8:
                    if board[r][c] is None:
                        moves.append((r, c))
                    elif isinstance(board[r][c], Piece) and board[r][c].color != self.color:
                        moves.append((r, c))  # Slå en modstander
                        break
                    else:
                        break  # Stoppes, hvis egen brik er i vejen
                else:
                    break
        return moves


class Queen(Piece):
    def __init__(self, color):
        super().__init__(color, "Q")

    def get_possible_moves(self, board, row, col, flipped=False):
        # Kombinerer Rook og Bishop
        rook = Rook(self.color)
        bishop = Bishop(self.color)
        return rook.get_possible_moves(board, row, col, flipped=False) + bishop.get_possible_moves(board, row, col, flipped=False)


class King(Piece):
    def __init__(self, color):
        super().__init__(color, "K")

    def get_possible_moves(self, board, row, col, flipped=False):
        moves = []
        king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        for move in king_moves:
            r, c = row + move[0], col + move[1]
            if 0 <= r < 8 and 0 <= c < 8:
                if board[r][c] is None or isinstance(board[r][c], Piece) and board[r][c].color != self.color:
                    moves.append((r, c))

        return moves