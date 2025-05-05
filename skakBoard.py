import pygame
import os
import sys
from alphabeta import ChessAI
from skakPieces import Pawn, Rook, Knight, Bishop, Queen, King

# Skærmindstillinger
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Farver
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

PIECE_IMAGES = {}

def initialize_board():
    return [
        [Rook('b'), Knight('b'), Bishop('b'), Queen('b'), King('b'), Bishop('b'), Knight('b'), Rook('b')],
        [Pawn('b') for _ in range(8)],
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [Pawn('w') for _ in range(8)],
        [Rook('w'), Knight('w'), Bishop('w'), Queen('w'), King('w'), Bishop('w'), Knight('w'), Rook('w')],
    ]

def load_images():
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        path = os.path.join("assets", f"{piece}.png")
        image = pygame.image.load(path)
        PIECE_IMAGES[piece] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))

def draw_board(screen):
    for row in range(ROWS):
        for col in range(COLS):
            color = LIGHT if (row + col) % 2 == 0 else DARK
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(screen, board):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece:
                image = PIECE_IMAGES[piece.image[:-4]]
                screen.blit(image, (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_possible_moves(screen, possible_moves):
    for row, col in possible_moves:
        pygame.draw.circle(screen, GREEN, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 15)

def highlight_check(screen, king_pos):
    if king_pos:
        row, col = king_pos
        pygame.draw.rect(screen, RED, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)

def get_square_under_mouse():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    return mouse_y // SQUARE_SIZE, mouse_x // SQUARE_SIZE

def show_start_menu(screen):
    font = pygame.font.SysFont("Arial", 48)
    title = font.render("Velkommen til Skak!", True, (0, 0, 0))
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

    start_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 60)
    start_font = pygame.font.SysFont("Arial", 36)
    start_text = start_font.render("Start Spil", True, (255, 255, 255))

    while True:
        screen.fill((200, 200, 200))
        screen.blit(title, title_rect)
        pygame.draw.rect(screen, (0, 128, 0), start_btn)
        screen.blit(start_text, (start_btn.x + 25, start_btn.y + 10))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.collidepoint(event.pos):
                    return

def show_game_over_menu(screen, winner_text):
    font = pygame.font.SysFont("Arial", 48)
    text = font.render(winner_text, True, (200, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

    replay_btn = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2, 100, 50)
    quit_btn = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2, 100, 50)

    small_font = pygame.font.SysFont("Arial", 24)
    replay_text = small_font.render("Spil igen", True, (255, 255, 255))
    quit_text = small_font.render("Afslut", True, (255, 255, 255))

    while True:
        screen.fill((255, 255, 255))
        screen.blit(text, text_rect)

        pygame.draw.rect(screen, (0, 128, 0), replay_btn)
        pygame.draw.rect(screen, (128, 0, 0), quit_btn)
        screen.blit(replay_text, (replay_btn.x + 10, replay_btn.y + 12))
        screen.blit(quit_text, (quit_btn.x + 20, quit_btn.y + 12))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if replay_btn.collidepoint(event.pos):
                    return True
                elif quit_btn.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Skak GUI med pygame")
    clock = pygame.time.Clock()

    load_images()
    show_start_menu(screen)

    while True:
        board = initialize_board()
        ai = ChessAI(depth=3)

        selected_piece = None
        possible_moves = []
        human_turn = True
        game_over = False
        winner_text = ""

        while True:
            draw_board(screen)
            draw_pieces(screen, board)
            draw_possible_moves(screen, possible_moves)

            if not game_over:
                white_king_pos = ai.find_king(board, 'w')
                black_king_pos = ai.find_king(board, 'b')

                if white_king_pos and ai.is_in_check(board, white_king_pos, 'w'):
                    highlight_check(screen, white_king_pos)
                if black_king_pos and ai.is_in_check(board, black_king_pos, 'b'):
                    highlight_check(screen, black_king_pos)

            pygame.display.flip()
            clock.tick(60)

            if game_over:
                replay = show_game_over_menu(screen, winner_text)
                if replay:
                    break
                else:
                    return

            if not human_turn:
                best_move = ai.get_best_move(board, 'b')
                if best_move:
                    r1, c1, r2, c2 = best_move
                    board[r2][c2] = board[r1][c1]
                    board[r1][c1] = None

                if ai.is_game_over(board):
                    game_over = True
                    winner_text = "Hvid vinder!" if ai.find_king(board, 'b') is None else "Sort vinder!"
                human_turn = True
                continue

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

                if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                    row, col = get_square_under_mouse()
                    piece = board[row][col]

                    if selected_piece:
                        if (row, col) in possible_moves:
                            board[row][col] = selected_piece[2]
                            board[selected_piece[0]][selected_piece[1]] = None
                            selected_piece = None
                            possible_moves = []

                            if ai.is_game_over(board):
                                game_over = True
                                winner_text = "Sort vinder!" if ai.find_king(board, 'w') is None else "Hvid vinder!"
                            else:
                                human_turn = False
                        else:
                            selected_piece = None
                            possible_moves = []
                    elif piece and piece.color == 'w':
                        selected_piece = (row, col, piece)
                        possible_moves = piece.get_possible_moves(board, row, col)

if __name__ == "__main__":
    main()
