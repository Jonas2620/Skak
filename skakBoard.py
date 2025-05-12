import pygame
import os
import sys
import time
import threading
from alphabeta import ChessAI
from skakPieces import Pawn, Rook, Knight, Bishop, Queen, King
from copy import deepcopy

# Skærmindstillinger
WIDTH, HEIGHT = 800, 800
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
        """Indlæser brikkebilleder"""
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
        """Initialiserer skakbrættet med brikker"""
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
        """Tegner skakbrættet"""
        for row in range(ROWS):
            for col in range(COLS):
                color = LIGHT if (row + col) % 2 == 0 else DARK
                pygame.draw.rect(self.screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    def draw_coordinates(self):
        """Tegner skakkoordinater"""
        for col in range(COLS):
            label = self.tiny_font.render(chr(97 + col), True, (0, 0, 0))
            self.screen.blit(label, (col * SQUARE_SIZE + SQUARE_SIZE - 15, HEIGHT - 15))
        
        for row in range(ROWS):
            label = self.tiny_font.render(str(8 - row), True, (0, 0, 0))
            self.screen.blit(label, (5, row * SQUARE_SIZE + 5))
    
    def draw_pieces(self):
        """Tegner skakbrikker"""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    image_key = f"{piece.color}{piece.name}"
                    if image_key in self.piece_images:
                        self.screen.blit(self.piece_images[image_key], (col * SQUARE_SIZE, row * SQUARE_SIZE))
    
    def draw_possible_moves(self):
        """Tegner mulige træk"""
        for row, col in self.possible_moves:
            # Tjek om feltet er tomt eller har en modstander
            if self.board[row][col] is None:
                # Tegn en cirkel for tomme felter
                pygame.draw.circle(self.screen, GREEN, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 10)
            else:
                # Tegn en rød kant omkring felter med modstanderbrikker
                pygame.draw.rect(self.screen, RED, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
    
    def highlight_selected(self):
        """Fremhæver den valgte brik"""
        if self.selected_piece:
            row, col, _ = self.selected_piece
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT)
            self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    
    def highlight_last_move(self):
        """Fremhæver det sidste træk"""
        if self.last_move:
            r1, c1, r2, c2 = self.last_move
            pygame.draw.rect(self.screen, BLUE, (c1 * SQUARE_SIZE, r1 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
            pygame.draw.rect(self.screen, BLUE, (c2 * SQUARE_SIZE, r2 * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
    
    def highlight_check(self, king_pos):
        """Fremhæver en konge, der er i skak"""
        if king_pos:
            row, col = king_pos
            pygame.draw.rect(self.screen, RED, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)
    
    def get_square_under_mouse(self):
        """Returnerer koordinaterne for feltet under musen"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        row = mouse_y // SQUARE_SIZE
        col = mouse_x // SQUARE_SIZE
        if 0 <= row < 8 and 0 <= col < 8:
            return row, col
        return None
    
    def show_thinking_indicator(self):
        """Viser en indikator når AI'en tænker"""
        if self.ai_thinking:
            thinking_text = self.small_font.render("AI tænker...", True, (0, 0, 0))
            text_bg = pygame.Rect(WIDTH // 2 - 60, 10, 120, 30)
            pygame.draw.rect(self.screen, (200, 200, 200), text_bg)
            pygame.draw.rect(self.screen, (0, 0, 0), text_bg, 2)
            self.screen.blit(thinking_text, (WIDTH // 2 - 50, 15))
            pygame.display.update(text_bg)
    
    def draw_slider(self, x, y, width, value, min_val, max_val, label):
        """Tegner en slider til indstillinger"""
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, width, 10))
        
        # Beregn position for slideren
        pos = x + ((value - min_val) / (max_val - min_val)) * width
        
        # Tegn sliderhåndtaget
        pygame.draw.circle(self.screen, (0, 128, 0), (int(pos), y + 5), 10)
        
        # Vis værdi og etiket
        value_text = self.medium_font.render(f"{label}: {value}", True, (0, 0, 0))
        self.screen.blit(value_text, (x, y - 30))
    
    def handle_slider(self, x, y, width, value, min_val, max_val, mouse_pos, mouse_pressed):
        """Håndterer interaktion med en slider"""
        if mouse_pressed and y - 10 <= mouse_pos[1] <= y + 20:
            if x <= mouse_pos[0] <= x + width:
                # Beregn ny værdi baseret på museposition
                new_value = min_val + ((mouse_pos[0] - x) / width) * (max_val - min_val)
                # Afrund til heltal og begræns indenfor min/max
                return max(min_val, min(max_val, round(new_value)))
        return value
    
    def show_difficulty_settings(self):
        """Viser indstillinger for sværhedsgrad"""
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
             elif event.type == pygame.KEYDOWN and event.key == pygame.K_z:
        # Tryk Z for at undo det sidste træk
              self.undo_move()
             else:
              self.handle_game_event(event)
        
        # Gem de valgte dybder
        self.difficulty_settings = {
            "let": easy_depth,
            "mellem": medium_depth,
            "svær": hard_depth
        }
        self.state = STATE_MENU
    
    def show_start_menu(self):
        """Viser startmenuen"""    
        title = self.large_font.render("Velkommen til Skak!", True, (0, 0, 0))
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))

        difficulty_options = [
            ("Let", self.difficulty_settings["let"]),
            ("Mellem", self.difficulty_settings["mellem"]),
            ("Svær", self.difficulty_settings["svær"]),
            ("Tilpas indstillinger", 0)  # Specialværdi for at åbne indstillinger igen
        ]
        
        buttons = []
        
        for i, (level, depth) in enumerate(difficulty_options):
            btn = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + i * 70, 300, 60)
            if i < 3:  # For sværhedsgraderne
                text = self.medium_font.render(f"{level} (Dybde {depth})", True, (255, 255, 255))
            else:  # For "Tilpas indstillinger" knappen
                text = self.medium_font.render(level, True, (255, 255, 255))
            buttons.append((btn, text, depth))

        while self.state == STATE_MENU:
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
                            if depth == 0:  # Hvis "Tilpas indstillinger" er valgt
                                self.state = STATE_SETTINGS
                                return
                            self.ai_depth = depth
                            self.start_new_game()
                            return
    
    def show_game_over_menu(self):
        """Viser spil slut menuen"""
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
        """Starter et nyt spil"""
        self.board = self.initialize_board()
        self.ai = ChessAI(depth=self.ai_depth)
        self.selected_piece = None
        self.possible_moves = []
        self.human_turn = True
        self.game_over = False
        self.winner_text = ""
        self.last_move = None
        self.ai_thinking = False
        self.state = STATE_GAME
    
    def get_valid_moves(self, row, col, piece):
        """Finder lovlige træk for en brik, der ikke efterlader kongen i skak"""
        all_moves = piece.get_possible_moves(self.board, row, col)
        valid_moves = []
        for move in all_moves:
            # Test hvert træk for at se, om det efterlader kongen i skak
            temp_board = deepcopy(self.board)
            temp_board[move[0]][move[1]] = piece
            temp_board[row][col] = None
            king_pos = self.ai.find_king(temp_board, 'w')
            if king_pos and not self.ai.is_in_check(temp_board, 'w'):
                valid_moves.append(move)
        return valid_moves
    
    def handle_game_event(self, event):
        """Håndterer spilbegivenheder under selve skakspillet"""
        if event.type == pygame.MOUSEBUTTONDOWN and self.human_turn and not self.game_over:
            square = self.get_square_under_mouse()
            if square:
                row, col = square
                piece = self.board[row][col]

                if self.selected_piece:
                    if (row, col) in self.possible_moves:
                       # Log trækket før udførsel
                        r1, c1, p = self.selected_piece
                        captured = self.board[row][col]           # det stykke (eller None), som slås
                        self.move_log.append((r1, c1, row, col, p, captured))
                        # Udfør trækket
                        r1, c1, p = self.selected_piece
                        self.board[row][col] = p
                        self.board[r1][c1] = None
                        self.last_move = (r1, c1, row, col)
                        
                        # Bondeforvandling til dronning hvis en bonde når modstanderens baglinje
                        if p.name == 'P' and row == 0:  # Hvid bonde når sort baglinje
                            self.board[row][col] = Queen('w')
                        
                        self.selected_piece = None
                        self.possible_moves = []

                        if self.ai.is_game_over(self.board):
                            self.game_over = True
                            self.winner_text = "Sort vinder!" if self.ai.find_king(self.board, 'w') is None else "Hvid vinder!"
                            self.state = STATE_GAME_OVER
                        else:
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
    
    def ai_move_callback(self, best_move):
        """Callback funktion til håndtering af AI træk"""
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
        
        if self.ai.is_game_over(self.board):
            self.game_over = True
            self.winner_text = "Hvid vinder!" if self.ai.find_king(self.board, 'b') is None else "Sort vinder!"
            self.state = STATE_GAME_OVER
        
        self.human_turn = True
    
    def update_game(self):
        """Opdaterer spilfasen"""
        if not self.human_turn and not self.ai_thinking:
            self.ai_thinking = True
            pygame.display.flip()  # Opdater skærmen med "AI tænker..." besked
            
            # Start AI beregning i baggrunden
            self.ai.calculate_best_move_async(self.board, 'b', self.ai_move_callback)
    
    def render_game(self):
        """Tegner spilfasen"""
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
        """Kører hovedspiløjfen"""
        while True:
            if self.state == STATE_MENU:
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