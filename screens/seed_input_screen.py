import pygame
from .base_screen import BaseScreen
from ui_elements import draw_themed_button
import drawing
from config import *
from save_manager import delete_save_file, save_game
import random

class SeedInputScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        self.button_rects = {}
        super().__init__(screen_manager, game, **kwargs)
        self.user_text = ""

    def _reset_panel_animations(self, screen): # Thêm tham số screen
        drawing._panel_anim_time = 0.0
        # SỬA LỖI: Căn giữa panel một cách động
        drawing._current_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2) 
        drawing._target_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2) 
        drawing._menu_entry_anim_progress = 0.0
        drawing._light_sweep_timer = 0.0
        drawing._light_sweep_active = False

    def _confirm_seed(self):
        """Logic để xác nhận và áp dụng seed."""
        if self.user_text:
            delete_save_file()
            self.game.game_state.current_seed = self.user_text.upper()
            random.seed(self.game.game_state.current_seed)
            save_game(self.game.game_state)
            self._reset_panel_animations(pygame.display.get_surface())
            self.screen_manager.switch_to("RUN_SETUP")
        else:
            self._reset_panel_animations(pygame.display.get_surface())
            self.screen_manager.switch_to("MENU")

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT: # type: ignore
                self.game.game_state.running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN or e.key == pygame.K_KP_ENTER:
                    self._confirm_seed()
                elif e.key == pygame.K_BACKSPACE:
                    self.user_text = self.user_text[:-1]
                else:
                    self.user_text += e.unicode
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.button_rects.get("confirm") and self.button_rects["confirm"].collidepoint(e.pos):
                    self._confirm_seed()
                if self.button_rects.get("back") and self.button_rects["back"].collidepoint(e.pos):
                    self._reset_panel_animations(pygame.display.get_surface())
                    self.screen_manager.switch_to("MENU")

    def _draw(self, screen):
        # Vẽ lại màn hình menu ở nền
        self.screen_manager._screens["MENU"].draw(screen)

        # Vẽ một lớp phủ mờ để làm nổi bật hộp thoại
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # Vẽ hộp thoại nhập seed (sử dụng hàm từ drawing.py)
        confirm_button, back_button = drawing.draw_seed_input_box(screen, self.user_text.upper())

        self.button_rects = {"confirm": confirm_button, "back": back_button}