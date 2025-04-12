import pygame
import os

# Skærmindstillinger
WIDTH, HEIGHT = 640, 640
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Farver til brættet
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)

# Dictionary til brikbilleder
PIECE_IMAGES = {}

# Funktion til at oprette bræt
def initialize_board():
    return [
        ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
        ["bP"] * 8,
        [""] * 8,
        [""] * 8,
        [""] * 8,
        [""] * 8,
        ["wP"] * 8,
        ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
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
    for row in range(ROWS):
        for col in range(COLS):
            piece = board[row][col]
            if piece != "":
                screen.blit(PIECE_IMAGES[piece], (col * SQUARE_SIZE, row * SQUARE_SIZE))

# Main loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Skak GUI med pygame")
    clock = pygame.time.Clock()

    board = initialize_board()
    load_images()

    running = True
    while running:
        draw_board(screen)
        draw_pieces(screen, board)
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()

if __name__ == "__main__":
    main()

# Mangler at tilføjet funktionalitet til nyt spil, og vilkårlig startopstilling
# Mangler tid til hvert træk