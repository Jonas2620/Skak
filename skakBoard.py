import pygame
import os
from skakPieces import Pawn, Rook, Knight, Bishop, Queen, King

# Skærmindstillinger
WIDTH, HEIGHT = 640, 640
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Farver til brættet
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)

# Dictionary til brikbilleder
PIECE_IMAGES = {}

# Funktion til at oprette skakbrættet
def initialize_board():
    return [
        [Rook('b'), Knight('b'), Bishop('b'), Queen('b'), King('b'), Bishop('b'), Knight('b'), Rook('b')],
        [Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b'), Pawn('b')],
        [None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None],
        [None, None, None, None, None, None, None, None],
        [Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w'), Pawn('w')],
        [Rook('w'), Knight('w'), Bishop('w'), Queen('w'), King('w'), Bishop('w'), Knight('w'), Rook('w')],
    ]

# Henter og skalerer billeder
def load_images():
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        path = os.path.join("assets", f"{piece}.png")
        image = pygame.image.load(path)
        PIECE_IMAGES[piece] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))

# Tegn felterne
def draw_board(screen):
    for row in range(ROWS):
        for col in range(COLS):
            color = LIGHT if (row + col) % 2 == 0 else DARK
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

# Tegn brikkerne
def draw_pieces(screen, board):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece:
                image = PIECE_IMAGES[piece.image[:-4]]  # f.eks. "wP"
                screen.blit(image, (col * SQUARE_SIZE, row * SQUARE_SIZE))

# Markér de mulige træk
def draw_possible_moves(screen, possible_moves):
    for move in possible_moves:
        row, col = move
        pygame.draw.circle(screen, (0, 255, 0), (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 20)

# Håndter musens klik
def get_square_under_mouse():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    row = mouse_y // SQUARE_SIZE
    col = mouse_x // SQUARE_SIZE
    return row, col

# Main loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Skak GUI med pygame")
    clock = pygame.time.Clock()

    board = initialize_board()
    load_images()

    selected_piece = None  # Nu gemmer vi både position og brik som en tuple (row, col, piece)
    possible_moves = []
    
    running = True
    while running:
        draw_board(screen)
        draw_pieces(screen, board)
        draw_possible_moves(screen, possible_moves)
        
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                row, col = get_square_under_mouse()
                piece = board[row][col]

                # Hvis en brik er valgt
                if selected_piece:
                    # Hvis valget er et muligt træk
                    if (row, col) in possible_moves:
                        # Flyt brikken
                        board[row][col] = selected_piece[2]  # Brug brikken fra selected_piece
                        board[selected_piece[0]][selected_piece[1]] = None  # Fjern brikken fra dens gamle position
                    selected_piece = None
                    possible_moves = []
                elif piece:
                    # Hvis der er en brik, skal vi vælge den og vise de mulige træk
                    selected_piece = (row, col, piece)  # Gem både positionen og objektet
                    possible_moves = piece.get_possible_moves(board, row, col)

    pygame.quit()


if __name__ == "__main__":
    main()