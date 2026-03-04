import pygame
from .base_screen import BaseScreen
from ui_elements import draw_themed_button, blur_surface
import drawing
from config import *


class RunSetupScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        super().__init__(screen_manager, game, **kwargs)
        self.button_rects = {}
        self.raw_background_image = self.assets.get('raw_background_image')
        self.ui_icons = self.assets.get('ui_icons', {})

    # SỬA LỖI: on_enter không còn cần thiết, logic sẽ được chuyển vào _draw

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT: # type: ignore
                self.game.game_state.running = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.button_rects.get("start") and self.button_rects["start"].collidepoint(e.pos):
                    self.screen_manager.switch_to("CHOOSE_SIDE")
                elif self.button_rects.get("shop") and self.button_rects["shop"].collidepoint(e.pos):
                    self.screen_manager.switch_to("SHOP")
                elif self.button_rects.get("back") and self.button_rects["back"].collidepoint(e.pos):
                    # SỬA LỖI: Logic đúng là chỉ cần chuyển màn hình.
                    # Các hàm reset animation không còn cần thiết trong kiến trúc mới.
                    self.screen_manager.switch_to("MENU")
                elif self.button_rects.get("skip") and self.button_rects["skip"].collidepoint(e.pos):
                    # Chỉ cho phép bỏ qua nếu không phải vòng boss
                    if not (self.game.game_state.round == self.game.game_state.max_rounds_per_stage):
                        # SỬA LỖI LOGIC: Đổi tên hàm để phản ánh đúng chức năng
                        self.game.claim_reward_and_skip()

    def recalculate_layout(self, screen):
        """Tính toán lại vị trí các nút bấm."""
        self.button_rects.clear()

        # --- Cột Trái (Sidebar) ---
        sidebar_width = 300
        self.sidebar_rect = pygame.Rect(0, 0, sidebar_width, SCREEN_HEIGHT)
        
        # Nút Cửa hàng và Về Menu ở cuối sidebar
        footer_button_width = sidebar_width - 60
        footer_button_height = 50
        self.button_rects["shop"] = pygame.Rect(self.sidebar_rect.centerx - footer_button_width / 2, self.sidebar_rect.bottom - 150, footer_button_width, footer_button_height)
        self.button_rects["back"] = pygame.Rect(self.sidebar_rect.centerx - footer_button_width / 2, self.sidebar_rect.bottom - 80, footer_button_width, footer_button_height)

        # --- Khu vực Chính (Content) - Hiển thị 3 thẻ ---
        card_width, card_height = 280, 420
        card_spacing = 40
        total_cards_width = (card_width * 3) + (card_spacing * 2)
        content_center_x = sidebar_width + (SCREEN_WIDTH - sidebar_width) / 2
        start_x = content_center_x - total_cards_width / 2

        self.card_rects = []
        for i in range(3):
            rect = pygame.Rect(start_x + i * (card_width + card_spacing), 0, card_width, card_height)
            rect.centery = SCREEN_HEIGHT / 2 - 30
            self.card_rects.append(rect)

        # Nút hành động bên dưới khu vực thẻ
        action_button_width = card_width
        action_button_height = 60
        self.button_rects["start"] = pygame.Rect(content_center_x - action_button_width / 2, self.card_rects[0].bottom + 20, action_button_width, action_button_height)
        self.button_rects["skip"] = pygame.Rect(content_center_x - action_button_width / 2, self.button_rects["start"].bottom + 15, action_button_width, action_button_height)

    def _draw(self, screen):
        # SỬA LỖI: Luôn chuẩn bị dữ liệu mới nhất cho trận đấu trước khi vẽ.
        # Điều này đảm bảo thông tin debuff của Boss luôn được cập nhật.
        self.game.prepare_new_match()

        drawing.draw_responsive_background(screen, self.raw_background_image)
        drawing.draw_balatro_filter(screen)

        # --- Vẽ Cột Trái (Sidebar) ---
        self._draw_sidebar(screen)

        # --- Vẽ Khu vực Chính (Content) ---
        self._draw_main_content(screen)

    def _draw_sidebar(self, screen):
        """Vẽ toàn bộ nội dung cho cột thông tin bên trái."""
        # Vẽ nền cho sidebar
        pygame.draw.rect(screen, (18, 18, 22), self.sidebar_rect)
        pygame.draw.line(screen, (40, 40, 45), self.sidebar_rect.topright, self.sidebar_rect.bottomright, 2)

        # Tiêu đề
        title_surf = MENU_FONT.render("LỰA CHỌN", True, WHITE_TEXT)
        screen.blit(title_surf, title_surf.get_rect(centerx=self.sidebar_rect.centerx, y=80))

        # Thông tin Tầng
        stage_surf = BUTTON_FONT.render(f"TẦNG {self.game.game_state.stage}", True, GOLD_ACCENT)
        screen.blit(stage_surf, stage_surf.get_rect(centerx=self.sidebar_rect.centerx, y=180))

        # Thông tin Vòng
        round_surf = INFO_FONT.render(f"Vòng {self.game.game_state.round} / {self.game.game_state.max_rounds_per_stage}", True, DISABLED_TEXT)
        screen.blit(round_surf, round_surf.get_rect(centerx=self.sidebar_rect.centerx, y=220))

        # Thông tin Vàng
        gold_surf = INFO_FONT.render(f"Vàng: {self.game.game_state.player_gold}", True, GOLD_HIGHLIGHT)
        screen.blit(gold_surf, gold_surf.get_rect(centerx=self.sidebar_rect.centerx, y=280))

        # Nút bấm ở cuối
        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)
        draw_themed_button(screen, self.button_rects["shop"], "Cửa hàng", GOLD_ACCENT, ROYAL_PURPLE_DARK, self.button_rects["shop"].collidepoint(mouse_pos_virtual), glow_color=GOLD_ACCENT, icon=self.ui_icons.get("icon_coin_bag")) # type: ignore
        draw_themed_button(screen, self.button_rects["back"], "Về Menu", pygame.Color(80,80,80), ROYAL_PURPLE_DARK, self.button_rects["back"].collidepoint(mouse_pos_virtual), icon=self.ui_icons.get("icon_back")) # type: ignore

    def _draw_main_content(self, screen):
        """Vẽ thẻ lựa chọn và các nút hành động ở khu vực chính."""
        current_round = self.game.game_state.round

        # --- Vẽ 3 Thẻ Lựa Chọn ---
        for i, rect in enumerate(self.card_rects):
            round_index = i + 1
            is_boss_round = (round_index == self.game.game_state.max_rounds_per_stage)
            is_current_choice = (round_index == current_round)
            is_past_round = (round_index < current_round)

            # Chuẩn bị thông tin để vẽ thẻ
            if is_boss_round:
                boss_style = self.game.game_state.bot.style
                boss_debuff = self.game.game_state.player_debuff
                
                label = "BOSS"
                title = f"ĐỐI ĐẦU: {boss_style.get('name', 'BOSS').upper()}"
                desc = f"Hiệu ứng: {boss_debuff['description']}" if boss_debuff else "Không có hiệu ứng đặc biệt."
                icon = "💀" # Icon đầu lâu cho Boss
                color = ERROR_RED
            else:
                label = "THƯỜNG"
                title = "TRẬN ĐẤU THƯỜNG"
                desc = "Đánh để nhận Vàng hoặc Bỏ qua để nhận Thưởng."
                icon = "⚔️" # Icon kiếm cho trận đấu thường
                color = ARCANE_GLOW

            # Vẽ thẻ với thông tin đã chuẩn bị
            self._draw_encounter_card(screen, rect, label, title, desc, icon, color, is_current_choice, is_past_round)

        # --- Vẽ Nút Hành Động ---
        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)
        if current_round == self.game.game_state.max_rounds_per_stage: # Nếu đang ở vòng boss
            draw_themed_button(screen, self.button_rects["start"], "CHẤP NHẬN THỬ THÁCH", ERROR_RED, ROYAL_PURPLE_DARK, self.button_rects["start"].collidepoint(mouse_pos_virtual), glow_color=ERROR_RED, icon=self.ui_icons.get("icon_play")) # type: ignore
            draw_themed_button(screen, self.button_rects["skip"], "BỎ QUA LỰA CHỌN", (50,50,60), (30,30,40), False) # type: ignore
        else:
            draw_themed_button(screen, self.button_rects["start"], "BẮT ĐẦU TRẬN ĐẤU", ARCANE_GLOW, ROYAL_PURPLE_DARK, self.button_rects["start"].collidepoint(mouse_pos_virtual), glow_color=ARCANE_GLOW, icon=self.ui_icons.get("icon_play")) # type: ignore
            draw_themed_button(screen, self.button_rects["skip"], "BỎ QUA LỰA CHỌN (+10 Vàng)", DISABLED_TEXT, ROYAL_PURPLE_DARK, self.button_rects["skip"].collidepoint(mouse_pos_virtual)) # type: ignore

    def _draw_encounter_card(self, screen, rect, label, title, desc, icon, color, is_current, is_past):
        """Vẽ một thẻ lựa chọn ải theo phong cách Balatro."""
        
        # Làm mờ các ải đã qua
        alpha = 100 if is_past else 255

        # Highlight ải hiện tại
        if is_current:
            highlight_rect = rect.inflate(12, 12)
            highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(highlight_surf, (color.r, color.g, color.b, 80), highlight_surf.get_rect(), border_radius=16)
            screen.blit(blur_surface(highlight_surf, 5), highlight_rect)

        # Vẽ bóng đổ
        shadow_rect = rect.move(6, 6)
        shadow_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, int(100 * (alpha/255))), shadow_surf.get_rect(), border_radius=15)
        screen.blit(blur_surface(shadow_surf, 5), shadow_rect)

        # Vẽ nền thẻ
        pygame.draw.rect(screen, (30, 35, 45), rect, border_radius=12)
        pygame.draw.rect(screen, (color.r, color.g, color.b, alpha), rect, width=2 if is_current else 1, border_radius=12)

        # Vẽ nhãn loại ải (THƯỞNG/BOSS)
        label_surf = BUTTON_FONT.render(label, True, color)
        label_surf.set_alpha(alpha)
        screen.blit(label_surf, label_surf.get_rect(centerx=rect.centerx, y=rect.y + 30))

        # Vẽ icon lớn
        icon_font = pygame.font.SysFont('segoeuisymbol', 100)
        icon_surf = icon_font.render(icon, True, color)
        icon_surf.set_alpha(180)
        screen.blit(icon_surf, icon_surf.get_rect(center=rect.center))

        # Vẽ tiêu đề chính
        title_surf = INFO_FONT.render(title, True, (WHITE_TEXT.r, WHITE_TEXT.g, WHITE_TEXT.b, alpha))
        screen.blit(title_surf, title_surf.get_rect(centerx=rect.centerx, bottom=rect.bottom - 60))

        # Vẽ mô tả phụ
        desc_surf = CARD_DESC_FONT.render(desc, True, (DISABLED_TEXT.r, DISABLED_TEXT.g, DISABLED_TEXT.b, alpha))
        screen.blit(desc_surf, desc_surf.get_rect(centerx=rect.centerx, bottom=rect.bottom - 30))