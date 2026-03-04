import pygame
from .base_screen import BaseScreen
from ui_elements import draw_themed_button
import drawing
from config import *


class PauseMenuScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        super().__init__(screen_manager, game, **kwargs)
        self.button_rects = {}

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT: # type: ignore
                self.game.game_state.running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.screen_manager.switch_to("PLAYING") # Thoát menu tạm dừng
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.button_rects.get("resume") and self.button_rects["resume"].collidepoint(e.pos):
                    self.screen_manager.switch_to("PLAYING")
                elif self.button_rects.get("options") and self.button_rects["options"].collidepoint(e.pos):
                    self.screen_manager.switch_to("OPTIONS", from_screen="PAUSE_MENU") # Truyền tên màn hình hiện tại
                elif self.button_rects.get("main_menu") and self.button_rects["main_menu"].collidepoint(e.pos):
                    self.screen_manager.switch_to("MENU")

    def recalculate_layout(self, screen):
        """Tính toán lại vị trí các nút."""
        screen_width, screen_height = screen.get_size()
        self.button_rects.clear()

        resume_button = pygame.Rect(0, 0, 300, 60)
        resume_button.center = (screen_width // 2, screen_height * 0.48)
        options_button = pygame.Rect(0, 0, 300, 60)
        options_button.center = (screen_width // 2, resume_button.bottom + screen_height * 0.04)
        main_menu_button = pygame.Rect(0, 0, 300, 60)
        main_menu_button.center = (screen_width // 2, options_button.bottom + screen_height * 0.04)
        self.button_rects = {"resume": resume_button, "options": options_button, "main_menu": main_menu_button}

    def _draw(self, screen):
        # 1. Vẽ lại màn hình chơi game ở nền
        self.screen_manager._screens["PLAYING"].draw(screen)

        # 2. Vẽ một lớp phủ mờ
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        screen_width, screen_height = screen.get_size()
        # 3. Vẽ các nút của menu tạm dừng
        title_text = MENU_FONT.render("TẠM DỪNG", True, WHITE_TEXT)
        screen.blit(title_text, title_text.get_rect(centerx=screen_width // 2, y=screen_height * 0.3))

        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)
        resume_rect = self.button_rects.get("resume")
        options_rect = self.button_rects.get("options")
        main_menu_rect = self.button_rects.get("main_menu")
        
        if resume_rect: draw_themed_button(screen, resume_rect, "Tiếp tục", ARCANE_GLOW, ROYAL_PURPLE_DARK, resume_rect.collidepoint(mouse_pos_virtual))
        if options_rect: draw_themed_button(screen, options_rect, "Cài đặt", pygame.Color(80,80,80), ROYAL_PURPLE_DARK, options_rect.collidepoint(mouse_pos_virtual))
        if main_menu_rect: draw_themed_button(screen, main_menu_rect, "Về Menu chính", ERROR_RED, ROYAL_PURPLE_DARK, main_menu_rect.collidepoint(mouse_pos_virtual))