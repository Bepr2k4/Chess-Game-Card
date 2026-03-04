import pygame
from .base_screen import BaseScreen
from ui_elements import draw_themed_button
import drawing
from config import *
from save_manager import delete_save_file, save_game
import random

class ConfirmNewGameScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        self.button_rects = {}
        super().__init__(screen_manager, game, **kwargs)

    def _reset_panel_animations(self, screen):
        drawing._panel_anim_time = 0.0
        drawing._current_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        drawing._target_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        drawing._menu_entry_anim_progress = 0.0
        drawing._light_sweep_timer = 0.0
        drawing._light_sweep_active = False

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                self.game.game_state.running = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.button_rects.get("yes") and self.button_rects["yes"].collidepoint(e.pos):
                    # SỬA LỖI: Gọi một hàm duy nhất trong controller để xử lý toàn bộ logic new game
                    self.game.start_new_run()
                    self.screen_manager.switch_to("RUN_SETUP")
                elif self.button_rects.get("no") and self.button_rects["no"].collidepoint(e.pos):
                    self._reset_panel_animations(pygame.display.get_surface())
                    self.screen_manager.switch_to("MENU")

    def recalculate_layout(self, screen):
        """Tính toán lại vị trí các nút bấm."""
        self.button_rects.clear()
        box_width, box_height = 600, 300
        box_rect = pygame.Rect(0, 0, box_width, box_height)
        box_rect.center = screen.get_rect().center

        self.button_rects["yes"] = pygame.Rect(box_rect.centerx - 160, box_rect.bottom - 80, 150, 50)
        self.button_rects["no"] = pygame.Rect(box_rect.centerx + 10, box_rect.bottom - 80, 150, 50)

    def draw(self, screen):
        # Vẽ lại màn hình menu ở nền
        self.screen_manager._screens["MENU"].draw(screen)

        # Lớp phủ mờ
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # Hộp thoại xác nhận
        box_width, box_height = 600, 300
        box_rect = pygame.Rect(0, 0, box_width, box_height)
        box_rect.center = screen.get_rect().center
        pygame.draw.rect(screen, FANTASY_DARK_BG, box_rect, border_radius=15)
        pygame.draw.rect(screen, METALLIC_TRIM, box_rect, width=2, border_radius=15)

        title_surf = MENU_FONT.render("XÁC NHẬN", True, WHITE_TEXT) # type: ignore
        prompt_surf = INFO_FONT.render("Bắt đầu game mới sẽ xóa tiến trình hiện tại. Bạn có chắc không?", True, (200, 200, 220))
        screen.blit(title_surf, title_surf.get_rect(centerx=box_rect.centerx, y=box_rect.y + 40))
        screen.blit(prompt_surf, prompt_surf.get_rect(centerx=box_rect.centerx, y=box_rect.y + 110))

        yes_button_rect = self.button_rects.get("yes")
        no_button_rect = self.button_rects.get("no")

        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)
        if yes_button_rect: draw_themed_button(screen, yes_button_rect, "Có", ERROR_RED, ROYAL_PURPLE_DARK, yes_button_rect.collidepoint(mouse_pos_virtual)) # type: ignore
        if no_button_rect: draw_themed_button(screen, no_button_rect, "Không", DISABLED_TEXT, ROYAL_PURPLE_DARK, no_button_rect.collidepoint(mouse_pos_virtual)) # type: ignore