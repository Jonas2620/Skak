import pygame
import os
import sys
import time
from alphabeta import ChessAI
from skakPieces import Pawn, Rook, Knight, Bishop, Queen, King

# Skærmindstillinger
WIDTH, HEIGHT = 800, 650
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Farver
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
HIGHLIGHT = (255, 255, 0, 100)  # Gul med gennemsigtighed
BLUE = (65, 105, 225)  # Sidste træk markering

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
    
def initialize_board_mirrored():
    return [
        [Rook('w'), Knight('w'), Bishop('w'), Queen('w'), King('w'), Bishop('w'), Knight('w'), Rook('w')],
        [Pawn('w') for _ in range(8)],
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [Pawn('b') for _ in range(8)],
        [Rook('b'), Knight('b'), Bishop('b'), Queen('b'), King('b'), Bishop('b'), Knight('b'), Rook('b')],
    ]

def load_images():
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        path = os.path.join("assets", f"{piece}.png")
        try:
            image = pygame.image.load(path)
            PIECE_IMAGES[piece] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
        except pygame.error:
            print(f"Kunne ikke indlæse billedfil: {path}")
            sys.exit(1)

def draw_board(screen):
    for row in range(ROWS):
        for col in range(COLS):
            color = LIGHT if (row + col) % 2 == 0 else DARK
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_coordinates(screen):
    small_font = pygame.font.SysFont("Arial", 14)
    for col in range(COLS):
        label = small_font.render(chr(97 + col), True, (0, 0, 0))
        screen.blit(label, (col * SQUARE_SIZE + SQUARE_SIZE - 15, HEIGHT - 15))
    
    for row in range(ROWS):
        label = small_font.render(str(8 - row), True, (0, 0, 0))
        screen.blit(label, (5, row * SQUARE_SIZE + 5))

def draw_pieces(screen, board):
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece:
                image_key = f"{piece.color}{piece.name}"
                if image_key in PIECE_IMAGES:
                    screen.blit(PIECE_IMAGES[image_key], (col * SQUARE_SIZE, row * SQUARE_SIZE))

def draw_possible_moves(screen, possible_moves):
    for row, col in possible_moves:
        pygame.draw.circle(screen, GREEN, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 10)

def highlight_selected(screen, selected_piece):
    if selected_piece:
        row, col, _ = selected_piece
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(HIGHLIGHT)
        screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))

def highlight_last_move(screen, last_move):
    if last_move:
        r1, c1, r2, c2 = last_move
        pygame.draw.rect(screen, BLUE, (c1 * SQUARE_SIZE, r1 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
        pygame.draw.rect(screen, BLUE, (c2 * SQUARE_SIZE, r2 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

def highlight_check(screen, king_pos):
    if king_pos:
        row, col = king_pos
        pygame.draw.rect(screen, RED, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

def get_square_under_mouse():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    row = mouse_y // SQUARE_SIZE
    col = mouse_x // SQUARE_SIZE
    if 0 <= row < 8 and 0 <= col < 8:
        return row, col
    return None

def show_thinking_indicator(screen, thinking=False):
    if thinking:
        font = pygame.font.SysFont("Arial", 24)
        thinking_text = font.render("AI tænker...", True, (0, 0, 0))
        text_bg = pygame.Rect(WIDTH // 2 - 60, 10, 120, 30)
        pygame.draw.rect(screen, (200, 200, 200), text_bg)
        pygame.draw.rect(screen, (0, 0, 0), text_bg, 2)
        screen.blit(thinking_text, (WIDTH // 2 - 50, 15))
        pygame.display.update(text_bg)

def draw_slider(screen, x, y, width, value, min_val, max_val, label):
    # Tegn slideren
    pygame.draw.rect(screen, (200, 200, 200), (x, y, width, 10))
    
    # Beregn position for slideren
    pos = x + ((value - min_val) / (max_val - min_val)) * width
    
    # Tegn sliderhåndtaget
    pygame.draw.circle(screen, (0, 128, 0), (int(pos), y + 5), 10)
    
    # Vis værdi og etiket
    font = pygame.font.SysFont("Arial", 20)
    value_text = font.render(f"{label}: {value}", True, (0, 0, 0))
    screen.blit(value_text, (x, y - 30))

def handle_slider(x, y, width, value, min_val, max_val, mouse_pos, mouse_pressed):
    if mouse_pressed and y - 10 <= mouse_pos[1] <= y + 20:
        if x <= mouse_pos[0] <= x + width:
            # Beregn ny værdi baseret på museposition
            new_value = min_val + ((mouse_pos[0] - x) / width) * (max_val - min_val)
            # Afrund til heltal og begræns indenfor min/max
            return max(min_val, min(max_val, round(new_value)))
    return value

def draw_flip_button(screen):
    button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 40, 110, 30)
    pygame.draw.rect(screen, (150, 150, 150), button_rect)
    pygame.draw.rect(screen, (0, 0, 0), button_rect, 2)
    
    font = pygame.font.SysFont("Arial", 16)
    button_text = font.render("Vend bræt", True, (0, 0, 0))
    screen.blit(button_text, (WIDTH - 105, HEIGHT - 35))
    
    return button_rect

def show_difficulty_settings(screen):
    font = pygame.font.SysFont("Arial", 48)
    title = font.render("Sværhedsgrad Indstillinger", True, (0, 0, 0))
    title_rect = title.get_rect(center=(WIDTH // 2, 80))
    
    easy_depth = 1
    medium_depth = 2
    hard_depth = 3
    
    slider_width = 400
    slider_x = WIDTH // 2 - slider_width // 2
    
    easy_y = 200
    medium_y = 300
    hard_y = 400
    
    start_btn = pygame.Rect(WIDTH // 2 - 100, 550, 200, 60)
    btn_text = pygame.font.SysFont("Arial", 36).render("Start Spil", True, (255, 255, 255))
    
    running = True
    while running:
        screen.fill((200, 200, 200))
        screen.blit(title, title_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        # Tegn slidere
        draw_slider(screen, slider_x, easy_y, slider_width, easy_depth, 1, 5, "Let")
        draw_slider(screen, slider_x, medium_y, slider_width, medium_depth, 1, 5, "Mellem")
        draw_slider(screen, slider_x, hard_y, slider_width, hard_depth, 1, 5, "Svær")
        
        # Opdater sliderværdier hvis musen er trykket ned
        easy_depth = handle_slider(slider_x, easy_y, slider_width, easy_depth, 1, 5, mouse_pos, mouse_pressed)
        medium_depth = handle_slider(slider_x, medium_y, slider_width, medium_depth, 1, 5, mouse_pos, mouse_pressed)
        hard_depth = handle_slider(slider_x, hard_y, slider_width, hard_depth, 1, 5, mouse_pos, mouse_pressed)
        
        # Sørg for at sværhedsgraderne er i stigende rækkefølge
        if easy_depth > medium_depth:
            medium_depth = easy_depth
        if medium_depth > hard_depth:
            hard_depth = medium_depth
        
        # Tegn start-knap
        pygame.draw.rect(screen, (0, 128, 0), start_btn)
        screen.blit(btn_text, (start_btn.x + 30, start_btn.y + 10))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.collidepoint(event.pos):
                    running = False
    
    # Returner de valgte dybder
    return {
        "let": easy_depth,
        "mellem": medium_depth,
        "svær": hard_depth
    }

def show_start_menu(screen, difficulty_settings):    
    font = pygame.font.SysFont("Arial", 48)
    title = font.render("Velkommen til Skak!", True, (0, 0, 0))
    title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

    difficulty_options = [
        ("Let", difficulty_settings["let"]),
        ("Mellem", difficulty_settings["mellem"]),
        ("Svær", difficulty_settings["svær"]),
        ("Tilpas indstillinger", 0)  # Specialværdi for at åbne indstillinger igen
    ]
    
    buttons = []
    button_font = pygame.font.SysFont("Arial", 36)
    
    for i, (level, depth) in enumerate(difficulty_options):
        btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + i * 70, 300, 60)
        if i < 3:  # For sværhedsgraderne
            text = button_font.render(f"{level} (Dybde {depth})", True, (255, 255, 255))
        else:  # For "Tilpas indstillinger" knappen
            text = button_font.render(level, True, (255, 255, 255))
        buttons.append((btn, text, depth))
        
          
    board_oriented_white_bottom = True #knap til at flip board
    
    orientation_btn_white_bottom = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + len(difficulty_options) * 70 + 20, 140, 40)
    orientation_btn_white_top = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2 + len(difficulty_options) * 70 + 20, 140, 40)
    
    orientation_font = pygame.font.SysFont("Arial", 18)
    orientation_text_white_bottom = orientation_font.render("Hvid i bund", True, (255, 255, 255))
    orientation_text_white_top = orientation_font.render("Hvid i top", True, (255, 255, 255))


    while True:
        screen.fill((200, 200, 200))
        screen.blit(title, title_rect)
        
        for btn, text, _ in buttons:
            pygame.draw.rect(screen, (0, 128, 0), btn)
            screen.blit(text, (btn.x + 25, btn.y + 10))
        
        # Tegn orienteringsknapperne med højlys for den valgte
        pygame.draw.rect(screen, (0, 100, 200) if board_oriented_white_bottom else (100, 100, 100), orientation_btn_white_bottom)
        pygame.draw.rect(screen, (0, 100, 200) if not board_oriented_white_bottom else (100, 100, 100), orientation_btn_white_top)
        
        screen.blit(orientation_text_white_bottom, (orientation_btn_white_bottom.x + 10, orientation_btn_white_bottom.y + 10))
        screen.blit(orientation_text_white_top, (orientation_btn_white_top.x + 10, orientation_btn_white_top.y + 10))
            
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Håndter klik på sværhedsknapper
                for btn, _, depth in buttons:
                    if btn.collidepoint(event.pos):
                        if depth == 0:  # Hvis "Tilpas indstillinger" er valgt
                            return None, board_oriented_white_bottom
                        return depth, board_oriented_white_bottom
                
                # Håndter klik på orienteringsknapper
                if orientation_btn_white_bottom.collidepoint(event.pos):
                    board_oriented_white_bottom = True
                elif orientation_btn_white_top.collidepoint(event.pos):
                    board_oriented_white_bottom = False


def show_game_over_menu(screen, winner_text):
    font = pygame.font.SysFont("Arial", 48)
    text = font.render(winner_text, True, (200, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

    replay_btn = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2, 100, 50)
    quit_btn = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2, 100, 50)

    small_font = pygame.font.SysFont("Arial", 24)
    replay_text = small_font.render("Spil igen", True, (255, 255, 255))
    quit_text = small_font.render("Afslut", True, (255, 255, 255))

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Halvt gennemsigtig sort overlay

    while True:
        # Bevar brættet i baggrunden
        screen.blit(overlay, (0, 0))  # Tilføj overlay
        
        # Tegn menu
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 150, 300, 250))
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
    
    # Standardsværhedsgrader (bliver opdateret når brugeren tilpasser dem)
    difficulty_settings = {
        "let": 1,
        "mellem": 2,
        "svær": 3
    }
    
    # Hovedspilsløjfe
    while True:
        # Vis første startmenu
        ai_depth, board_oriented_white_bottom = show_start_menu(screen, difficulty_settings)
        
        # Hvis brugeren valgte "Tilpas indstillinger"
        if ai_depth is None:
            difficulty_settings = show_difficulty_settings(screen)
            continue  # Gå tilbage til startmenuen med de opdaterede indstillinger
        
        # Initialiser spil
        board = initialize_board() if board_oriented_white_bottom else initialize_board_mirrored()
        board_flipped = not board_oriented_white_bottom  # Gem brættets orientering
        
        ai = ChessAI(depth=ai_depth)

        selected_piece = None
        possible_moves = []
        human_turn = True
        game_over = False
        winner_text = ""
        last_move = None
        ai_thinking = False

        # Selve spillet
        while True:
            draw_board(screen)
            draw_coordinates(screen)
            highlight_last_move(screen, last_move)
            draw_pieces(screen, board)
            highlight_selected(screen, selected_piece)
            draw_possible_moves(screen, possible_moves)
            show_thinking_indicator(screen, ai_thinking)
            
            flip_button = draw_flip_button(screen)

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

            if not human_turn and not ai_thinking:
                ai_thinking = True
                pygame.display.flip()  # Opdater skærmen med "AI tænker..." besked
                
                def ai_move_callback(best_move):
                    nonlocal human_turn, ai_thinking, last_move, game_over, winner_text
                    
                    if best_move:
                        r1, c1, r2, c2 = best_move
                        board[r2][c2] = board[r1][c1]
                        board[r1][c1] = None
                        last_move = best_move

                    ai_thinking = False
                    
                    if ai.is_game_over(board):
                        game_over = True
                        winner_text = "Hvid vinder!" if ai.find_king(board, 'b') is None else "Sort vinder!"
                    
                    human_turn = True
                
                # Start AI beregning i baggrunden
                ai.calculate_best_move_async(board, 'b', ai_move_callback)
                continue

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Håndter klik på "Vend bræt" knappen
                    if flip_button.collidepoint(event.pos):
                        # Vend brættet
                        board_flipped = not board_flipped
                        
                        # Opdater brættet baseret på den nye orientering
                        # Vi holder fast i det nuværende bræt, men ændrer renderingen
                        continue

                if event.type == pygame.MOUSEBUTTONDOWN and human_turn and not game_over:
                    square = get_square_under_mouse()
                    if square:
                        row, col = square
                        piece = board[row][col]

                        if selected_piece:
                            if (row, col) in possible_moves:
                                # Udfør trækket
                                r1, c1, p = selected_piece
                                board[row][col] = p
                                board[r1][c1] = None
                                last_move = (r1, c1, row, col)
                                
                                selected_piece = None
                                possible_moves = []

                                if ai.is_game_over(board):
                                    game_over = True
                                    winner_text = "Sort vinder!" if ai.find_king(board, 'w') is None else "Hvid vinder!"
                                else:
                                    human_turn = False
                            elif piece and piece.color == 'w':
                                # Vælg en ny brik
                                selected_piece = (row, col, piece)
                                possible_moves = []
                                
                                # Filtrér kun de lovlige træk der ikke efterlader kongen i skak
                                all_moves = piece.get_possible_moves(board, row, col)
                                for move in all_moves:
                                    temp_board = deepcopy(board)
                                    temp_board[move[0]][move[1]] = piece
                                    temp_board[row][col] = None
                                    king_pos = ai.find_king(temp_board, 'w')
                                    if king_pos and not ai.is_in_check(temp_board, king_pos, 'w'):
                                        possible_moves.append(move)
                            else:
                                selected_piece = None
                                possible_moves = []
                        elif piece and piece.color == 'w':
                            selected_piece = (row, col, piece)
                            # Hent lovlige træk (der ikke efterlader kongen i skak)
                            all_moves = piece.get_possible_moves(board, row, col)
                            possible_moves = []
                            for move in all_moves:
                                # Test hvert træk for at se, om det efterlader kongen i skak
                                temp_board, _ = ai.make_move(deepcopy(board), (row, col, move[0], move[1]))
                                king_pos = ai.find_king(temp_board, 'w')
                                if king_pos and not ai.is_in_check(temp_board, king_pos, 'w'):
                                    possible_moves.append(move)

if __name__ == "__main__":
    from copy import deepcopy
    main()