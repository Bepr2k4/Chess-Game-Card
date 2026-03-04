import pygame
import random
from .base_screen import BaseScreen
from ui_elements import draw_themed_button
from config import *
import drawing # type: ignore

class GameOverScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        super().__init__(screen_manager, game, **kwargs)
        self.background_image = self.assets.get('background_image')
        self.animation_timer = 0
        self.animation_duration = 120 # 2 giây (Nhanh hơn 1.5 lần)
        self.particles = [] # Thêm danh sách hạt cho hiệu ứng

    def on_enter(self):
        """Reset animation timer khi vào màn hình."""
        self.animation_timer = 0

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT: # type: ignore
                self.game.game_state.running = False
            # Chỉ cho phép nhấn nút sau khi animation đã chạy được một lúc
            if hasattr(self, 'continue_button_rect') and self.animation_timer > 60 and e.type == pygame.MOUSEBUTTONDOWN:
                if self.continue_button_rect.collidepoint(e.pos):
                    self.screen_manager.switch_to("RUN_SETUP")

    def update(self, dt):
        if self.animation_timer < self.animation_duration:
            self.animation_timer += 1

    def recalculate_layout(self, screen):
        screen_width, screen_height = screen.get_size()
        self.continue_button_rect = pygame.Rect(0, 0, screen_width * 0.25, screen_height * 0.08)
        self.continue_button_rect.center = (screen_width // 2, screen_height * 0.85)

    def _draw(self, screen):
        screen_width, screen_height = SCREEN_WIDTH, SCREEN_HEIGHT
        # Vẽ lại màn hình chơi game ở nền
        self.screen_manager._screens["PLAYING"]._draw(screen) # Gọi _draw để tránh vòng lặp vô hạn

        progress = min(1.0, self.animation_timer / self.animation_duration)
        ease_out_progress = 1 - (1 - progress) ** 4 # Mạnh hơn một chút

        # Lớp phủ mờ dần
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * ease_out_progress)))
        screen.blit(overlay, (0, 0))

        result = self.game.get_game_result() # SỬA LỖI: Sử dụng hàm helper chuẩn
        if result == "WIN":
            result_text = "VICTORY"
            color = GOLD_ACCENT
            icon_char = "👑" # Vương miện
            particle_color = GOLD_HIGHLIGHT
            particle_vy = -2
        else: # LOSE hoặc DRAW
            result_text = "DEFEAT"
            color = ERROR_RED
            icon_char = "💀" # Đầu lâu
            particle_color = (100, 110, 120)
            particle_vy = 2

        # --- Hiệu ứng hạt (Particles) ---
        if progress > 0.2:
            if len(self.particles) < 100: # Giới hạn số lượng hạt
                self.particles.append({
                    'pos': [random.randint(0, screen_width), screen_height if particle_vy > 0 else 0],
                    'vel': [random.uniform(-0.5, 0.5), particle_vy * random.uniform(0.5, 1.5)],
                    'size': random.randint(2, 5),
                    'alpha': 255
                })
            
            for p in self.particles:
                p['pos'][0] += p['vel'][0]
                p['pos'][1] += p['vel'][1]
                p['alpha'] -= 3 # Mờ dần
                if p['alpha'] > 0:
                    # SỬA LỖI: Đảm bảo alpha không bao giờ âm.
                    safe_alpha = max(0, int(p['alpha']))
                    pygame.draw.circle(screen, (*particle_color, safe_alpha), p['pos'], p['size'])
            self.particles = [p for p in self.particles if p['alpha'] > 0]

        # --- Dải băng (Ribbon) ---
        if progress > 0.3:
            ribbon_p = min(1.0, (progress - 0.3) / 0.5)
            ribbon_ease_p = 1 - (1 - ribbon_p) ** 3
            ribbon_height = 120
            ribbon_width = screen_width * 0.6 * ribbon_ease_p
            ribbon_rect = pygame.Rect(0, 0, ribbon_width, ribbon_height)
            ribbon_rect.center = (screen_width // 2, screen_height // 2)
            
            # Vẽ dải băng
            pygame.draw.rect(screen, (40, 45, 55, 200 * ribbon_p), ribbon_rect, border_radius=10)
            pygame.draw.rect(screen, GOLD_ACCENT, ribbon_rect, width=2, border_radius=10)

        # --- Icon (Vương miện/Đầu lâu) ---
        if progress > 0.5:
            icon_p = min(1.0, (progress - 0.5) / 0.4)
            icon_ease_p = 1 - (1 - icon_p) ** 4 # Nảy lên
            icon_font_size = int(150 * icon_ease_p)
            icon_font = pygame.font.SysFont('segoeuisymbol', icon_font_size)
            icon_surf = icon_font.render(icon_char, True, color)
            icon_surf.set_alpha(int(255 * icon_p))
            icon_rect = icon_surf.get_rect(center=(screen_width // 2, screen_height // 2 - 80))
            screen.blit(icon_surf, icon_rect)

        # Text kết quả hiện ra
        if progress > 0.4:
            text_p = min(1.0, (progress - 0.4) / 0.5)
            text_ease_p = 1 - (1 - text_p) ** 3
            
            title_surf = MENU_FONT.render(result_text, True, color)
            title_surf.set_alpha(int(255 * text_ease_p))
            
            # Hiệu ứng scale-in cho text
            scaled_title = pygame.transform.smoothscale(title_surf, (int(title_surf.get_width() * (0.8 + 0.2 * text_ease_p)), int(title_surf.get_height() * (0.8 + 0.2 * text_ease_p))))
            title_rect = scaled_title.get_rect(center=(screen_width // 2, screen_height // 2))
            screen.blit(scaled_title, title_rect)

        # Nút tiếp tục hiện ra sau một lúc
        if self.animation_timer > 60:
            mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)
            button_progress = min(1.0, (self.animation_timer - 60) / (self.animation_duration - 60)) # type: ignore
            draw_themed_button(screen, self.continue_button_rect, "Tiếp tục", ARCANE_GLOW, ROYAL_PURPLE_DARK, self.continue_button_rect.collidepoint(mouse_pos_virtual), alpha_multiplier=button_progress)