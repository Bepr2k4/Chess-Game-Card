import pygame
from .base_screen import BaseScreen
import drawing
from config import *
from ui_elements import draw_themed_button, wrap_text
from profile_manager import load_profile
from card_database import CARD_DATABASE

class ProfileScreen(BaseScreen):
    """Màn hình hiển thị thống kê và thành tích của người chơi."""
    def __init__(self, screen_manager, game, **kwargs):
        super().__init__(screen_manager, game, **kwargs)
        self.profile_data = {}
        self.sorted_card_usage = []
        self.button_rects = {}
        self.raw_background_image = self.assets.get('raw_background_image')
        self.ui_icons = self.assets.get('ui_icons', {})
        # Tạo một cache để lấy thông tin thẻ bài nhanh hơn
        self.card_info_cache = {card['id']: card for card in CARD_DATABASE}

    def on_enter(self, **kwargs):
        """Tải dữ liệu hồ sơ mỗi khi vào màn hình."""
        self.profile_data = load_profile()
        # Xử lý trước dữ liệu sử dụng thẻ để hiển thị
        self.sorted_card_usage = sorted(
            self.profile_data.get("card_usage", {}).items(),
            key=lambda item: item[1],
            reverse=True
        )

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT:
                self.game.game_state.running = False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_pos = drawing.get_transformed_mouse_pos(self.game.game_state)
                if self.button_rects.get("back") and self.button_rects["back"].collidepoint(mouse_pos):
                    self.screen_manager.switch_to("MENU")

    def recalculate_layout(self, screen):
        """Tính toán lại vị trí các nút bấm và panel."""
        self.button_rects["back"] = pygame.Rect(SCREEN_WIDTH * 0.05, SCREEN_HEIGHT * 0.9, 200, 50)

    def _draw(self, screen):
        drawing.draw_responsive_background(screen, self.raw_background_image)
        drawing.draw_balatro_filter(screen)

        # --- Bố cục chính ---
        title_surf = MENU_FONT.render("HỒ SƠ NGƯỜI CHƠI", True, WHITE_TEXT)
        screen.blit(title_surf, title_surf.get_rect(centerx=SCREEN_WIDTH / 2, y=SCREEN_HEIGHT * 0.05))

        # --- Panel Thống kê chung ---
        stats_panel_rect = pygame.Rect(0, 0, SCREEN_WIDTH * 0.3, SCREEN_HEIGHT * 0.35)
        stats_panel_rect.midtop = (SCREEN_WIDTH * 0.2, SCREEN_HEIGHT * 0.15)
        drawing.draw_panel_bezel(screen, stats_panel_rect)
        self._draw_general_stats(screen, stats_panel_rect)

        # --- Panel Thẻ bài yêu thích ---
        card_panel_rect = pygame.Rect(0, 0, SCREEN_WIDTH * 0.3, SCREEN_HEIGHT * 0.35)
        card_panel_rect.midtop = (SCREEN_WIDTH * 0.2, stats_panel_rect.bottom + 30)
        drawing.draw_panel_bezel(screen, card_panel_rect)
        self._draw_card_stats(screen, card_panel_rect)

        # --- Panel Lịch sử Lượt chơi ---
        history_panel_rect = pygame.Rect(0, 0, SCREEN_WIDTH * 0.55, SCREEN_HEIGHT * 0.7)
        history_panel_rect.midtop = (SCREEN_WIDTH * 0.68, SCREEN_HEIGHT * 0.15)
        drawing.draw_panel_bezel(screen, history_panel_rect)
        self._draw_run_history(screen, history_panel_rect)

        # --- Nút Quay lại ---
        back_button = self.button_rects.get("back")
        if back_button:
            mouse_pos = drawing.get_transformed_mouse_pos(self.game.game_state)
            draw_themed_button(screen, back_button, "Quay Lại", DISABLED_TEXT, ROYAL_PURPLE_DARK, back_button.collidepoint(mouse_pos), icon=self.ui_icons.get("icon_back"))

    def _draw_general_stats(self, screen, panel_rect):
        """Vẽ nội dung cho panel thống kê chung."""
        title_surf = CARD_FONT.render("THỐNG KÊ TỔNG QUÁT", True, GOLD_ACCENT)
        screen.blit(title_surf, title_surf.get_rect(centerx=panel_rect.centerx, y=panel_rect.y + 30))

        stats_to_show = [
            ("Tổng số lượt chơi:", self.profile_data.get("total_runs_started", 0)),
            ("Tầng cao nhất đạt được:", self.profile_data.get("highest_stage_reached", 1)),
            # Thêm các thống kê khác ở đây
        ]

        y_offset = panel_rect.y + 100
        for label, value in stats_to_show:
            label_surf = INFO_FONT.render(label, True, WHITE_TEXT)
            value_surf = INFO_FONT.render(str(value), True, GOLD_HIGHLIGHT)

            screen.blit(label_surf, (panel_rect.x + 40, y_offset))
            screen.blit(value_surf, (panel_rect.right - 40 - value_surf.get_width(), y_offset))
            y_offset += 50

    def _draw_card_stats(self, screen, panel_rect):
        """Vẽ nội dung cho panel thẻ bài yêu thích."""
        title_surf = CARD_FONT.render("THẺ BÀI SỬ DỤNG NHIỀU NHẤT", True, GOLD_ACCENT)
        screen.blit(title_surf, title_surf.get_rect(centerx=panel_rect.centerx, y=panel_rect.y + 30))

        y_offset = panel_rect.y + 70
        max_usage = self.sorted_card_usage[0][1] if self.sorted_card_usage else 1

        for i, (card_id, count) in enumerate(self.sorted_card_usage[:7]): # Hiển thị top 7
            if y_offset > panel_rect.bottom - 50:
                break

            card_info = self.card_info_cache.get(card_id)
            if not card_info:
                continue

            # Tên thẻ
            card_name = card_info.get("name", "Thẻ không xác định")
            name_surf = INFO_FONT.render(card_name, True, RARITY_COLORS.get(card_info.get("rarity"), WHITE_TEXT))
            screen.blit(name_surf, (panel_rect.x + 30, y_offset))

            # Số lần sử dụng
            count_surf = INFO_FONT.render(str(count), True, WHITE_TEXT)
            screen.blit(count_surf, (panel_rect.right - 30 - count_surf.get_width(), y_offset))

            # Biểu đồ thanh
            bar_width = (panel_rect.width - 80) * (count / max_usage)
            bar_rect = pygame.Rect(panel_rect.x + 30, y_offset + 35, bar_width, 10)
            bar_color = RARITY_COLORS.get(card_info.get("rarity"), WHITE_TEXT).lerp(ROYAL_PURPLE_LIGHT, 0.3)
            pygame.draw.rect(screen, bar_color, bar_rect, border_radius=5)

            y_offset += 50 # Giảm khoảng cách

    def _draw_run_history(self, screen, panel_rect):
        """Vẽ nội dung cho panel lịch sử lượt chơi."""
        title_surf = CARD_FONT.render("LỊCH SỬ CÁC LƯỢT CHƠI GẦN ĐÂY", True, GOLD_ACCENT)
        screen.blit(title_surf, title_surf.get_rect(centerx=panel_rect.centerx, y=panel_rect.y + 30))

        y_offset = panel_rect.y + 80
        run_history = self.profile_data.get("run_history", [])

        if not run_history:
            no_history_surf = INFO_FONT.render("Chưa có lịch sử để hiển thị.", True, DISABLED_TEXT)
            screen.blit(no_history_surf, no_history_surf.get_rect(center=panel_rect.center))
            return

        for run in run_history:
            if y_offset > panel_rect.bottom - 40:
                break

            result = run.get("result", "UNKNOWN")
            if result == "LOSE":
                result_text = f"Thua ở Tầng {run.get('stage')} - Vòng {run.get('round')}"
                result_color = ERROR_RED
            else: # WIN_STAGE
                result_text = f"Vượt qua Tầng {run.get('stage')}"
                result_color = SUCCESS_GREEN

            result_surf = INFO_FONT.render(result_text, True, result_color)
            screen.blit(result_surf, (panel_rect.x + 30, y_offset))
            y_offset += 40