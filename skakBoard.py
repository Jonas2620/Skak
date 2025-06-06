import pygame
import os
import sys
import time
import threading
from alphabeta import ChessAI
from skakPieces import Piece, Pawn, Rook, Knight, Bishop, Queen, King
from copy import deepcopy
import sys
sys.setrecursionlimit(10000)

# Skærmindstillinger
WIDTH, HEIGHT = 650, 650
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Farver
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
HIGHLIGHT = (255, 255, 0, 100)  # Gul med gennemsigtighed
BLUE = (65, 105, 225)  # Sidste træk markering

# Game states
STATE_MENU = 0
STATE_SETTINGS = 1
STATE_GAME = 2
STATE_GAME_OVER = 3

class ChessGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Skak GUI med pygame")
        self.clock = pygame.time.Clock()
        
        self.piece_images = {}
        self.load_images()
        self.move_log = []    # Historik over træk
        self.is_paused = False  # For at kontrollere om spillet er sat på pause
        self.player_color = None  

        
        # Standardsværhedsgrader
        self.difficulty_settings = {
            "let": 1,
            "mellem": 2,
            "svær": 3
        }

        
        # Spilvariabler
        self.board = None
        self.ai = None
        self.ai_depth = None
        self.selected_piece = None
        self.possible_moves = []
        self.human_turn = True
        self.game_over = False
        self.winner_text = ""
        self.last_move = None
        self.ai_thinking = False
        self.move_log = []

        
        self.state = STATE_MENU
        
        # Font initialisering
        self.large_font = pygame.font.SysFont("Arial", 48)
        self.medium_font = pygame.font.SysFont("Arial", 36)
        self.small_font = pygame.font.SysFont("Arial", 24)
        self.tiny_font = pygame.font.SysFont("Arial", 14)
            # Undo-knap
        self.undo_button = pygame.Rect(WIDTH - 110, HEIGHT - 50, 100, 40)
        self.undo_text = self.small_font.render("Undo", True, (255,255,255))
    
   
    def undo_move(self):
    # Kør op til to gange (AI + menneske)
     for i in range(2):
        if not self.move_log:
            break
        r1, c1, r2, c2, moved, captured = self.move_log.pop()
        # Rul tilbage på brættet
        self.board[r1][c1] = moved
        self.board[r2][c2] = captured
        # Skift tur: efter begge undo skal det være menneskets tur
        # (første iteration går til AI’s tur, anden til menneskets)
        self.human_turn = (i == 1)
    # Ryd highlights
     self.selected_piece = None
     self.possible_moves = []
     self.last_move = None
    
    def load_images(self):
        # Indlæser brikkebilleder
        pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
        for piece in pieces:
            path = os.path.join("assets", f"{piece}.png")
            try:
                image = pygame.image.load(path)
                self.piece_images[piece] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
            except pygame.error:
                print(f"Kunne ikke indlæse billedfil: {path}")
                sys.exit(1)
    
    def initialize_board(self):
        # Initialiserer skakbrættet med brikker
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
    
    def draw_board(self):
        # Tegner skakbrættet
        for row in range(ROWS):
            for col in range(COLS):
                color = LIGHT if (row + col) % 2 == 0 else DARK
                pygame.draw.rect(self.screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        # Hvis spillet er på pause, vis en pause-overlay
        if self.is_paused:
            pause_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pause_overlay.fill((0, 0, 0, 150))  # Halvtransparent overlay
            self.screen.blit(pause_overlay, (0, 0))

            pause_text = self.medium_font.render("Spillet er på pause", True, (255, 255, 255))
            self.screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))


    
    def draw_coordinates(self):
        # Tegner skakkoordinater
        for col in range(COLS):
            label = self.tiny_font.render(chr(97 + col), True, (0, 0, 0))
            self.screen.blit(label, (col * SQUARE_SIZE + SQUARE_SIZE - 15, HEIGHT - 15))
        
        for row in range(ROWS):
            label = self.tiny_font.render(str(8 - row), True, (0, 0, 0))
            self.screen.blit(label, (5, row * SQUARE_SIZE + 5))
    
    def draw_pieces(self):
        # Tegner skakbrikker
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    image_key = f"{piece.color}{piece.name}"
                    if image_key in self.piece_images:
                        self.screen.blit(self.piece_images[image_key], (col * SQUARE_SIZE, row * SQUARE_SIZE))

        # Hvis en brik er valgt under pause, fremhæv den
        if self.selected_piece:
            row, col, _ = self.selected_piece
            pygame.draw.rect(self.screen, BLUE, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)
    
    def draw_possible_moves(self):
        # Tegner mulige træk
        for row, col in self.possible_moves:
            # Tjek om feltet er tomt eller har en modstander
            if self.board[row][col] is None:
                # Tegn en cirkel for tomme felter
                pygame.draw.circle(self.screen, GREEN, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 10)
            else:
                # Tegn en rød kant omkring felter med modstanderbrikker
                pygame.draw.rect(self.screen, RED, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
    
    def highlight_selected(self):
        # Fremhæver den valgte brik
        if self.selected_piece:
            row, col, _ = self.selected_piece
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT)
            self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    
    def highlight_last_move(self):
        # Fremhæver det sidste træk
        if self.last_move:
            r1, c1, r2, c2 = self.last_move
            pygame.draw.rect(self.screen, BLUE, (c1 * SQUARE_SIZE, r1 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
            pygame.draw.rect(self.screen, BLUE, (c2 * SQUARE_SIZE, r2 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
    
    def highlight_check(self, king_pos):
        # Fremhæver en konge, der er i skak
        if king_pos:
            row, col = king_pos
            pygame.draw.rect(self.screen, RED, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
    
    def get_square_under_mouse(self):
        # Returnerer koordinaterne for feltet under musen
        mouse_x, mouse_y = pygame.mouse.get_pos()
        row = mouse_y // SQUARE_SIZE
        col = mouse_x // SQUARE_SIZE
        if 0 <= row < 8 and 0 <= col < 8:
            return row, col
        return None
    
    def show_thinking_indicator(self):
        # Viser en indikator når AI'en tænker
        if self.ai_thinking:
            thinking_text = self.small_font.render("Let him cook", True, (0, 0, 0))
            # Increase the box width from 140 to 200 and height stays at 40
            text_bg = pygame.Rect(WIDTH // 2 - 100, 10, 200, 40)  # Changed width and x-position
            pygame.draw.rect(self.screen, (200, 200, 200), text_bg)
            pygame.draw.rect(self.screen, (0, 0, 0), text_bg, 2)
            # Center the text in the larger box
            text_x = WIDTH // 2 - thinking_text.get_width() // 2
            self.screen.blit(thinking_text, (text_x, 15))
            pygame.display.update(text_bg)
    
    def draw_slider(self, x, y, width, value, min_val, max_val, label):
        # Beregn position for slideren
        pos = x + ((value - min_val) / (max_val - min_val)) * width
        
        # Tegn sliderhåndtaget
        pygame.draw.circle(self.screen, (0, 128, 0), (int(pos), y + 5), 10)
        
        # Vis værdi og etiket
        value_text = self.medium_font.render(f"{label}: {value}", True, (0, 0, 0))
        self.screen.blit(value_text, (x, y - 30))
    
    def handle_slider(self, x, y, width, value, min_val, max_val, mouse_pos, mouse_pressed):
        # Håndterer interaktion med en slider
        if mouse_pressed and y - 10 <= mouse_pos[1] <= y + 20:
            if x <= mouse_pos[0] <= x + width:
                # Beregn ny værdi baseret på museposition
                new_value = min_val + ((mouse_pos[0] - x) / width) * (max_val - min_val)
                # Afrund til heltal og begræns indenfor min/max
                return max(min_val, min(max_val, round(new_value)))
        return value
    
    def show_difficulty_settings(self):
        # Viser indstillinger for sværhedsgrad
        title = self.large_font.render("Sværhedsgrad Indstillinger", True, (0, 0, 0))
        title_rect = title.get_rect(center=(WIDTH // 2, 80))
        
        easy_depth = self.difficulty_settings["let"]
        medium_depth = self.difficulty_settings["mellem"]
        hard_depth = self.difficulty_settings["svær"]
        
        slider_width = 400
        slider_x = WIDTH // 2 - slider_width // 2
        
        easy_y = 200
        medium_y = 300
        hard_y = 400
        
        start_btn = pygame.Rect(WIDTH // 2 - 100, 550, 200, 60)
        btn_text = self.medium_font.render("Start Spil", True, (255, 255, 255))
        
        running = True
        while running:
            self.screen.fill((200, 200, 200))
            self.screen.blit(title, title_rect)
            
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()[0]
            
            # Tegn slidere
            self.draw_slider(slider_x, easy_y, slider_width, easy_depth, 1, 5, "Let")
            self.draw_slider(slider_x, medium_y, slider_width, medium_depth, 1, 5, "Mellem")
            self.draw_slider(slider_x, hard_y, slider_width, hard_depth, 1, 5, "Svær")
            
            # Opdater sliderværdier hvis musen er trykket ned
            easy_depth = self.handle_slider(slider_x, easy_y, slider_width, easy_depth, 1, 5, mouse_pos, mouse_pressed)
            medium_depth = self.handle_slider(slider_x, medium_y, slider_width, medium_depth, 1, 5, mouse_pos, mouse_pressed)
            hard_depth = self.handle_slider(slider_x, hard_y, slider_width, hard_depth, 1, 5, mouse_pos, mouse_pressed)
            
            # Sørg for at sværhedsgraderne er i stigende rækkefølge
            if easy_depth > medium_depth:
                medium_depth = easy_depth
            if medium_depth > hard_depth:
                hard_depth = medium_depth
            
            # Tegn start-knap
            pygame.draw.rect(self.screen, (0, 128, 0), start_btn)
            self.screen.blit(btn_text, (start_btn.x + 30, start_btn.y + 10))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if start_btn.collidepoint(event.pos):
                        running = False 
        
        # Gem de valgte dybder
        self.difficulty_settings = {
            "let": easy_depth,
            "mellem": medium_depth,
            "svær": hard_depth
        }
        self.state = STATE_MENU
    
    def show_difficulty_menu(self):
        # Viser sværhedsgrad menu efter farvevalg
        title = self.large_font.render("Vælg Sværhedsgrad", True, (0, 0, 0))
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

        difficulty_options = [
            ("Let", self.difficulty_settings["let"]),
            ("Mellem", self.difficulty_settings["mellem"]),
            ("Svær", self.difficulty_settings["svær"]),
            ("Tilpas indstillinger", 0)
        ]
        
        buttons = []
        
        for i, (level, depth) in enumerate(difficulty_options):
            btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + i * 70, 300, 60)
            if i < 3:
                text = self.medium_font.render(f"{level} (Dybde {depth})", True, (255, 255, 255))
            else:
                text = self.medium_font.render(level, True, (255, 255, 255))
            buttons.append((btn, text, depth))

        running = True
        while running:
            self.screen.fill((200, 200, 200))
            self.screen.blit(title, title_rect)
            
            for btn, text, _ in buttons:
                pygame.draw.rect(self.screen, (0, 128, 0), btn)
                self.screen.blit(text, (btn.x + 25, btn.y + 10))
                
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, (btn, _, depth) in enumerate(buttons):
                        if btn.collidepoint(event.pos):
                            if depth == 0:
                                self.state = STATE_SETTINGS
                                return
                            self.ai_depth = depth
                            self.start_new_game()
                            return
    
    def show_start_menu(self):
        # Viser startmenuen med farvevalg    
        title = self.large_font.render("Velkommen til Skak!", True, (0, 0, 0))
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))

        # Color selection buttons
        white_btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 60)
        black_btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 60)
        
        white_text = self.medium_font.render("Spil som Hvid", True, (255, 255, 255))
        black_text = self.medium_font.render("Spil som Sort", True, (255, 255, 255))

        while self.state == STATE_MENU:
            self.screen.fill((200, 200, 200))
            self.screen.blit(title, title_rect)
            
            # Draw color selection buttons
            pygame.draw.rect(self.screen, (0, 128, 0), white_btn)
            pygame.draw.rect(self.screen, (0, 128, 0), black_btn)
            
            self.screen.blit(white_text, (white_btn.x + 65, white_btn.y + 15))
            self.screen.blit(black_text, (black_btn.x + 65, black_btn.y + 15))
            
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if white_btn.collidepoint(event.pos):
                        self.player_color = 'w'
                        self.show_difficulty_menu()
                        return
                    elif black_btn.collidepoint(event.pos):
                        self.player_color = 'b'
                        self.show_difficulty_menu()
                        return
    
    def show_game_over_menu(self):
        # Viser spil slut menuen
        text = self.large_font.render(self.winner_text, True, (200, 0, 0))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

        replay_btn = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2, 100, 50)
        quit_btn = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2, 100, 50)

        replay_text = self.small_font.render("Spil igen", True, (255, 255, 255))
        quit_text = self.small_font.render("Afslut", True, (255, 255, 255))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Halvt gennemsigtig sort overlay

        self.screen.blit(overlay, (0, 0))  # Tilføj overlay
        
        # Tegn menu
        pygame.draw.rect(self.screen, (255, 255, 255), pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 150, 300, 250))
        self.screen.blit(text, text_rect)

        pygame.draw.rect(self.screen, (0, 128, 0), replay_btn)
        pygame.draw.rect(self.screen, (128, 0, 0), quit_btn)
        self.screen.blit(replay_text, (replay_btn.x + 10, replay_btn.y + 12))
        self.screen.blit(quit_text, (quit_btn.x + 20, quit_btn.y + 12))

        pygame.display.flip()

        waiting_for_input = True
        while waiting_for_input:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if replay_btn.collidepoint(event.pos):
                        self.state = STATE_MENU
                        waiting_for_input = False
                    elif quit_btn.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
    
    def start_new_game(self):
        # Starter et nyt spil
        self.board = self.initialize_board()
        self.ai = ChessAI(depth=self.ai_depth)
        self.selected_piece = None
        self.possible_moves = []
        self.human_turn = self.player_color == 'w'  # Set initial turn based on color
        self.game_over = False
        self.winner_text = ""
        self.last_move = None
        self.ai_thinking = False
        self.state = STATE_GAME
        #Tæller moves for begge farver (spiller)
        self.white_move_count = 0
        self.black_move_count = 0
    
    
    def get_valid_moves(self, row, col, piece):
        # Finder lovlige træk for en brik, der ikke efterlader kongen i skak
        all_moves = piece.get_possible_moves(self.board, row, col)
        valid_moves = []
        
        for move in all_moves:
            # Test hvert træk for at se, om det efterlader kongen i skak
            temp_board = deepcopy(self.board)
            temp_board[move[0]][move[1]] = piece
            temp_board[row][col] = None
            
            # Force refresh king position for the temp board
            king_pos = None
            if piece.name == 'K':
                king_pos = (move[0], move[1])  # Use new king position directly
            else:
                king_pos = self.ai.find_king(temp_board, piece.color)  # This will now do a fresh search
                
            if king_pos and not self.ai.is_in_check(temp_board, piece.color, king_pos):
                valid_moves.append(move)
        
        return valid_moves
    
    def handle_game_event(self, event):
        # Håndterer spilbegivenheder under selve skakspillet med understøttelse af rokade
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Hvis spillet er på pause, tillad at flytte brikker rundt
            if self.is_paused:
                square = self.get_square_under_mouse()
                if square:
                    row, col = square
                    piece = self.board[row][col]

                    if self.selected_piece:
                        r1, c1, p = self.selected_piece
                        if (row, col) != (r1, c1):  # Gør kun ændringer, hvis det er et andet felt
                            self.board[row][col] = p
                            self.board[r1][c1] = None
                            self.selected_piece = None  # Fjern den valgte brik
                            self.possible_moves = []  # Fjern mulige træk
                    else:
                        if piece:  # Hvis der er en brik på det felt
                            self.selected_piece = (row, col, piece)  # Vælg brikken
                            self.possible_moves = self.get_valid_moves(row, col, piece)
                return

            # Normale spiltræk, når spillet ikke er på pause
            if self.human_turn and not self.game_over:
                square = self.get_square_under_mouse()
                if square:
                    row, col = square
                    piece = self.board[row][col]

                    if self.selected_piece:
                        r1, c1, p = self.selected_piece
                        
                        # Tjek for rokade
                        if isinstance(p, King) and isinstance(piece, Rook) and p.color == piece.color:
                            # Rokade fra venstre side (queenside)
                            if col < c1 and not p.has_moved and not piece.has_moved:
                                dest_col = c1 - 2
                                if self._verify_castling_path(self.board, row, c1, dest_col, p.color):
                                    self.board = p.perform_castling(self.board, r1, c1, dest_col)
                                    self.last_move = (r1, c1, r1, dest_col)
                                    self.selected_piece = None
                                    self.possible_moves = []
                                    self.human_turn = False
                                    return
                            
                            # Rokade fra højre side (kingside)
                            elif col > c1 and not p.has_moved and not piece.has_moved:
                                dest_col = c1 + 2
                                if self._verify_castling_path(self.board, row, c1, dest_col, p.color):
                                    self.board = p.perform_castling(self.board, r1, c1, dest_col)
                                    self.last_move = (r1, c1, r1, dest_col)
                                    self.selected_piece = None
                                    self.possible_moves = []
                                    self.human_turn = False
                                    return

                        # Normal træk
                        if (row, col) in self.possible_moves:
                        # Log trækket før udførsel
                            r1, c1, p = self.selected_piece
                            captured = self.board[row][col]           # det stykke (eller None), som slås
                            self.move_log.append((r1, c1, row, col, p, captured))
                            # Udfør trækket
                            self.board[row][col] = p
                            self.board[r1][c1] = None
                            self.last_move = (r1, c1, row, col)
                            
                            # Bondeforvandling til dronning hvis en bonde når modstanderens baglinje
                            if p.name == 'P' and (row == 0 or row == 7):  # Både hvid og sort baglinje
                                self.board[row][col] = Queen(p.color)
                            
                            # Markér at kongen/tårnet har bevæget sig (for rokade)
                            if p.name == 'K' or p.name == 'R':
                                p.has_moved = True
                            
                            self.selected_piece = None
                            self.possible_moves = []

                            if self.ai.is_game_over(self.board):
                                self.game_over = True
                                self.winner_text = "Sort vinder!" if self.ai.find_king(self.board, 'w') is None else "Hvid vinder!"
                                self.state = STATE_GAME_OVER
                            else:
                                #Tæller træk for begge farver
                                self.white_move_count += 1
                                if self.white_move_count >= 50:
                                    self.game_over= True
                                    self.winner_text = "Sort vinder (Hvid lavede 50 træk)"
                                    self.state= STATE_GAME_OVER
                                    return
                                self.human_turn = False
                        elif piece and piece.color == 'w':
                            # Vælg en ny brik
                            self.selected_piece = (row, col, piece)
                            self.possible_moves = self.get_valid_moves(row, col, piece)
                        else:
                            self.selected_piece = None
                            self.possible_moves = []
                    elif piece and piece.color == 'w':
                        self.selected_piece = (row, col, piece)
                        self.possible_moves = self.get_valid_moves(row, col, piece)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:  # Tryk på "P" for at pause og genoptage spillet
                self.is_paused = not self.is_paused  # Skift pause-tilstand
                self.selected_piece = None
                self.possible_moves = []  # Ryd mulige træk, når spillet pauses

    
    def _verify_castling_path(self, board, row, start_col, end_col, color):
        #
        # Verificerer at ingen felter mellem start og slut kolonner er truet under rokade
        #
        # :param board: Hele skakbrættet
        # :param row: Kongens række
        # :param start_col: Startkolonne for kongen
        # :param end_col: Slutkolonne for kongen
        # :param color: Farven på kongen der rokerer
        # :return: True hvis vejen er sikker, False ellers
        #
        # Bestem retningen for rokaden (positiv eller negativ)
        step = 1 if end_col > start_col else -1
        
        # Tjek felterne kongen passerer
        for current_col in range(start_col, end_col + step, step):
            # Tjek om dette felt er truet af nogen modstanderbrikker
            if self._is_square_under_attack(board, row, current_col, color):
                return False
        
        return True
    
    def _is_square_under_attack(self, board, target_row, target_col, defending_color):
        #
        # Tjekker om et felt er truet af modstanderbrikker
        #
        # :param board: Hele skakbrættet
        # :param target_row: Række for det felt der tjekkes
        # :param target_col: Kolonne for det felt der tjekkes
        # :param defending_color: Farven på den forsvarende side
        # :return: True hvis feltet er truet, False ellers
        #
        # Gennemgå hele brættet
        for row in range(8):
            for col in range(8):
                # Find modstanderbrikker
                piece = board[row][col]
                if isinstance(piece, Piece) and piece.color != defending_color:
                    # Få mulige angrebsfelter for denne brik
                    attack_moves = piece.get_possible_moves(board, row, col, include_attacks=True)
                    
                    # Se om nogle af disse angrebsfelter rammer target-feltet
                    if (target_row, target_col) in attack_moves:
                        return True
        
        return False
    
    def ai_move_callback(self, best_move):
        # Callback funktion til håndtering af AI træk
        if best_move:
         r1, c1, r2, c2 = best_move
         moved = self.board[r1][c1]
         captured = self.board[r2][c2]
         self.move_log.append((r1, c1, r2, c2, moved, captured))

         self.board[r2][c2] = moved
         self.board[r1][c1] = None
         self.last_move = best_move

            
            # Bondeforvandling til dronning hvis en bonde når modstanderens baglinje
         if self.board[r2][c2].name == 'P' and r2 == 7:  # Sort bonde når hvid baglinje
                self.board[r2][c2] = Queen('b')

        self.ai_thinking = False
        self.human_turn = True
        #Tæller antal træk for begge farver
        if self.ai.is_game_over(self.board):
            self.game_over = True
            self.winner_text = "Hvid vinder!" if self.ai.find_king(self.board, 'b') is None else "Sort vinder!"
            self.state = STATE_GAME_OVER
            self.black_move_count += 1
            if self.black_move_count >= 50:
                self.game_over = True
                self.winner_text = "Hvid vinder (Sort lavede 50 træk)"
                self.state = STATE_GAME_OVER
                return
        
        self.human_turn = True
    
    def update_game(self):
        # Opdaterer spilfasen
        if not self.human_turn and not self.ai_thinking:
            self.ai_thinking = True
            pygame.display.flip()  # Opdater skærmen med "AI tænker..." besked
            
            # Start AI beregning i baggrunden
            self.ai.calculate_best_move_async(self.board, 'b', self.ai_move_callback)
    
    def render_game(self):
        # Tegner spilfasen
        self.draw_board()
        self.draw_coordinates()
        self.highlight_last_move()
        self.draw_pieces()
        self.highlight_selected()
        self.draw_possible_moves()
        self.show_thinking_indicator()

        # Vis skak-status
        white_king_pos = self.ai.find_king(self.board, 'w')
        black_king_pos = self.ai.find_king(self.board, 'b')

        if white_king_pos and self.ai.is_in_check(self.board, 'w', white_king_pos):
            self.highlight_check(white_king_pos)
            # Vis "Skak!" tekst
            check_text = self.small_font.render("Skak til hvid!", True, (255, 0, 0))
            self.screen.blit(check_text, (WIDTH - 150, 10))
            
        if black_king_pos and self.ai.is_in_check(self.board, 'b', black_king_pos):
            self.highlight_check(black_king_pos)
            # Vis "Skak!" tekst
            check_text = self.small_font.render("Skak til sort!", True, (255, 0, 0))
            self.screen.blit(check_text, (WIDTH - 150, 40))
        
        # Vis hvis det er menneskets tur
        if self.human_turn and not self.game_over:
            turn_text = self.small_font.render("Din tur (hvid)", True, (0, 0, 0))
            self.screen.blit(turn_text, (10, 10))
    
               # Tegn Undo-knap
            pygame.draw.rect(self.screen, (50,50,50), self.undo_button, border_radius=5)
            self.screen.blit(
            self.undo_text,
            (
                self.undo_button.x + (self.undo_button.width - self.undo_text.get_width())//2,
                self.undo_button.y + (self.undo_button.height - self.undo_text.get_height())//2
            )
         )
    
    def run(self):
        # Kører hovedspiløjfen
        while True:
            if self.state == STATE_MENU:
                self.show_start_menu()
            elif self.state == STATE_MENU:
                self.show_start_menu()
            elif self.state == STATE_SETTINGS:
                self.show_difficulty_settings()
            elif self.state == STATE_GAME:
                # Håndter begivenheder
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    # Tjek for klik på Undo-knap
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.undo_button.collidepoint(event.pos):
                            self.undo_move()
                            continue  # spring almindelig spil-håndtering over for undo

                    # Almindelig spil-håndtering (klik på bræt)
                    self.handle_game_event(event)

                # Opdater spillet (AI-træk osv.)
                self.update_game()

                # Render spillet (bræt, brikker, knapper mv.)
                self.render_game()
                pygame.display.flip()
                self.clock.tick(60)

            elif self.state == STATE_GAME_OVER:
                self.show_game_over_menu()
                

if __name__ == "__main__":
    game = ChessGame()
    game.run()