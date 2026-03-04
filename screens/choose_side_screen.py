import pygame
import chess
from .base_screen import BaseScreen
from ui_elements import draw_themed_button
import drawing
from config import *

class ChooseSideScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        self.button_rects = {}
        super().__init__(screen_manager, game, **kwargs)
        self.raw_background_image = self.assets.get('raw_background_image')
        self.ui_icons = self.assets.get('ui_icons', {})

    def _reset_panel_animations(self, screen):
        """Hàm helper để reset animation của panel."""
        drawing._panel_anim_time = 0.0
        drawing._current_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        drawing._target_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        drawing._menu_entry_anim_progress = 0.0
        drawing._light_sweep_timer = 0.0
        drawing._light_sweep_active = False

    def _start_game(self, player_color):
        """Bắt đầu game với phe đã chọn và chuyển sang màn hình chơi."""
        self.game.game_state.player_color = player_color
        self.game.reset_board()
        # Chuyển sang màn hình chuyển cảnh
        self.screen_manager.switch_to("TRANSITION_TO_PLAY")
        # Gọi hàm on_enter của màn hình transition để reset timer
        self.screen_manager.current_screen.on_enter()

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT: # type: ignore
                self.game.game_state.running = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.button_rects.get("white") and self.button_rects["white"].collidepoint(e.pos):
                    self._start_game(chess.WHITE)
                elif self.button_rects.get("black") and self.button_rects["black"].collidepoint(e.pos):
                    self._start_game(chess.BLACK)
                elif self.button_rects.get("back") and self.button_rects["back"].collidepoint(e.pos):
                    self._reset_panel_animations(pygame.display.get_surface())
                    self.screen_manager.switch_to("RUN_SETUP") # Sửa lỗi logic: Quay về Run Setup thay vì Menu chính

    def recalculate_layout(self, screen):
        """Tính toán lại vị trí các nút bấm."""
        self.button_rects.clear()
        # SỬA LỖI: Tự tính toán panel_rect dựa trên kích thước ảo, không gọi hàm vẽ.
        panel_rect = get_menu_panel_rect(SCREEN_WIDTH, SCREEN_HEIGHT)
        button_width, button_height = 300, 60

        self.button_rects["white"] = pygame.Rect(panel_rect.centerx - button_width // 2, panel_rect.y + panel_rect.height * 0.2, button_width, button_height)
        self.button_rects["black"] = pygame.Rect(panel_rect.centerx - button_width // 2, self.button_rects["white"].bottom + panel_rect.height * 0.05, button_width, button_height)
        self.button_rects["back"] = pygame.Rect(panel_rect.centerx - 150, self.button_rects["black"].bottom + panel_rect.height * 0.08, 300, 50)

    def _draw(self, screen):
        drawing.draw_responsive_background(screen, self.raw_background_image)
        drawing.draw_balatro_filter(screen)
        panel_rect = drawing.draw_fantasy_menu_panel(screen, self.game.game_state.dt)
        drawing.draw_fantasy_menu_logo(screen, self.game.game_state.dt)

        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)
        white_rect = self.button_rects.get("white")
        black_rect = self.button_rects.get("black")
        back_rect = self.button_rects.get("back")

        if white_rect: draw_themed_button(screen, white_rect, "Chơi quân Trắng", GOLD_ACCENT, ROYAL_PURPLE_DARK, white_rect.collidepoint(mouse_pos_virtual), glow_color=GOLD_ACCENT, icon=self.ui_icons.get("icon_knight_white")) # type: ignore
        if black_rect: draw_themed_button(screen, black_rect, "Chơi quân Đen", DISABLED_TEXT, ROYAL_PURPLE_DARK, black_rect.collidepoint(mouse_pos_virtual), glow_color=ARCANE_GLOW, icon=self.ui_icons.get("icon_knight_black")) # type: ignore
        if back_rect: draw_themed_button(screen, back_rect, "Quay lại", DISABLED_TEXT, ROYAL_PURPLE_DARK, back_rect.collidepoint(mouse_pos_virtual), icon=self.ui_icons.get("icon_back")) # type: ignore