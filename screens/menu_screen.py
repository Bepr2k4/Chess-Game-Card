import pygame
from .base_screen import BaseScreen
from ui_elements import draw_themed_button, get_menu_panel_rect
import drawing 
from config import *

class MenuScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        self.button_rects = {}
        self.pressed_button_key = None # Theo dõi nút đang được nhấn
        super().__init__(screen_manager, game, **kwargs)
        self.raw_background_image = self.assets.get('raw_background_image')
        self.has_save = self.assets.get('has_save_func')
        self.ui_icons = self.assets.get('ui_icons', {})

    def _reset_panel_animations(self, screen):
        """Hàm helper để reset animation của panel."""
        drawing._panel_anim_time = 0.0
        drawing._current_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        drawing._target_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        drawing._menu_entry_anim_progress = 0.0
        drawing._light_sweep_timer = 0.0
        drawing._light_sweep_active = False

    def handle_events(self, events):
        for e in events:
            self.pressed_button_key = None # Reset khi có sự kiện mới
            if e.type == pygame.QUIT: # type: ignore
                self.screen_manager.game.game_state.running = False # Tắt game

            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.button_rects.get("continue") and self.button_rects["continue"].collidepoint(e.pos):
                    self._reset_panel_animations(pygame.display.get_surface())
                    self.screen_manager.switch_to("RUN_SETUP")

                elif self.button_rects.get("new_game") and self.button_rects["new_game"].collidepoint(e.pos):
                    if self.has_save():
                        self.screen_manager.switch_to("CONFIRM_NEW_GAME")
                    else:
                        # SỬA LỖI: Gọi hàm helper để đảm bảo shop được tạo trước khi lưu
                        self.game.start_new_run()
                        self.screen_manager.switch_to("RUN_SETUP")

                elif self.button_rects.get("options") and self.button_rects["options"].collidepoint(e.pos):
                    self.screen_manager.switch_to("OPTIONS", from_screen="MENU")

                elif self.button_rects.get("profile") and self.button_rects["profile"].collidepoint(e.pos):
                    self.screen_manager.switch_to("PROFILE")

                elif self.button_rects.get("seed") and self.button_rects["seed"].collidepoint(e.pos):
                    self.screen_manager.switch_to("SEED_INPUT")

                elif self.button_rects.get("quit") and self.button_rects["quit"].collidepoint(e.pos):
                    self.screen_manager.game.game_state.running = False
            
            # Theo dõi trạng thái nhấn giữ chuột
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for key, rect in self.button_rects.items():
                    if rect and rect.collidepoint(e.pos):
                        self.pressed_button_key = key
                        break
            
            if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self.pressed_button_key = None

    def recalculate_layout(self, screen):
        """Tính toán lại vị trí các nút bấm."""
        self.button_rects.clear()

        panel_rect = get_menu_panel_rect(SCREEN_WIDTH, SCREEN_HEIGHT)

        buttons_to_draw = [("Continue", "icon_play", "continue", self.has_save()),
                           ("New Game", "icon_play", "new_game", True),
                           ("Profile", "icon_knight_white", "profile", True), # Thêm nút Profile
                           ("Quit", "icon_quit", "quit", True)]

        button_width, button_height = 300, 60
        button_spacing = 20
        num_panel_buttons = len(buttons_to_draw)
        total_button_height = (button_height * num_panel_buttons) + (button_spacing * (num_panel_buttons - 1))
        start_y = panel_rect.y + (panel_rect.height - total_button_height) // 2

        for i, (text, icon_name, key, enabled) in enumerate(buttons_to_draw):
            self.button_rects[key] = pygame.Rect(panel_rect.centerx - button_width // 2, start_y + i * (button_height + button_spacing), button_width, button_height)

        self.button_rects["options"] = pygame.Rect(SCREEN_WIDTH - (SCREEN_WIDTH * 0.02) - 50, SCREEN_HEIGHT - (SCREEN_HEIGHT * 0.03) - 50, 50, 50)
        self.button_rects["seed"] = pygame.Rect(SCREEN_WIDTH * 0.02, SCREEN_HEIGHT * 0.03, 160, 50)

    def _draw(self, screen):
        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)
        dt = self.screen_manager.game.game_state.dt # Lấy dt từ game object

        drawing.draw_responsive_background(screen, self.raw_background_image)
        drawing.draw_balatro_filter(screen)

        # --- Logic vẽ màn hình Menu được chuyển vào đây ---
        panel_rect = drawing.draw_fantasy_menu_panel(screen, dt)
        drawing.draw_fantasy_menu_logo(screen, dt)
        
        # Vẽ các nút đã được tính toán trong recalculate_layout
        button_configs = [("Continue", "icon_play", "continue", self.has_save()),
                          ("New Game", "icon_play", "new_game", True),
                          ("Profile", "icon_knight_white", "profile", True),
                          ("Quit", "icon_quit", "quit", True)]
        
        for text, icon_name, key, enabled in button_configs:
            rect = self.button_rects.get(key)
            if not rect: continue
            icon = self.ui_icons.get(icon_name)
            is_pressed = (self.pressed_button_key == key)
            if enabled:
                draw_themed_button(screen, rect, text, ARCANE_GLOW, ROYAL_PURPLE_DARK, rect.collidepoint(mouse_pos_virtual), is_pressed, glow_color=ARCANE_GLOW, icon=icon)
            else:
                draw_themed_button(screen, rect, text, DISABLED_TEXT, ROYAL_PURPLE_DARK, False, icon=icon) # Nút vô hiệu hóa (không hover)
        
        options_r = self.button_rects.get("options")
        seed_r = self.button_rects.get("seed")
        icon_options = self.ui_icons.get("icon_options")
        if options_r: draw_themed_button(screen, options_r, "", ARCANE_GLOW, ROYAL_PURPLE_DARK, options_r.collidepoint(mouse_pos_virtual), (self.pressed_button_key == "options"), glow_color=ARCANE_GLOW, icon=icon_options)
        if seed_r: draw_themed_button(screen, seed_r, "SEED", ERROR_RED, ROYAL_PURPLE_DARK, seed_r.collidepoint(mouse_pos_virtual), (self.pressed_button_key == "seed"), glow_color=GOLD_ACCENT)