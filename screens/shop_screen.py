import pygame
from .base_screen import BaseScreen
import drawing
from config import *
from ui_elements import draw_sell_confirmation_box, draw_tooltip, draw_themed_button, wrap_text

class ShopScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        self.button_rects = {}
        super().__init__(screen_manager, game, **kwargs)
        self.raw_background_image = self.assets.get('raw_background_image')
        self.card_images = self.assets.get('card_images')
        self.ui_icons = self.assets.get('ui_icons', {})

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT: # type: ignore
                self.game.game_state.running = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                # Ưu tiên xử lý hộp thoại xác nhận trước
                if self.game.game_state.sell_confirmation_card:
                    confirm_button, _ = draw_sell_confirmation_box(pygame.display.get_surface(), self.game.game_state, pygame.mouse.get_pos())
                    if confirm_button and confirm_button.collidepoint(e.pos):
                        self.game.sell_card(self.game.game_state.sell_confirmation_card['name'])
                    self.game.game_state.sell_confirmation_card = None # Đóng hộp thoại khi click bất cứ đâu
                    continue

                if self.button_rects.get("back") and self.button_rects["back"].collidepoint(e.pos):
                    self.screen_manager.switch_to("RUN_SETUP")
                elif self.button_rects.get("reroll") and self.button_rects["reroll"].collidepoint(e.pos):
                    self.game.buy_reroll()
                
                # Lấy lại rects được tính toán trong frame mới nhất
                item_rects, player_card_rects = self._get_current_card_rects(pygame.display.get_surface())

                # Bán thẻ (chuột phải)
                if e.button == 3:
                    for rect, card in player_card_rects:
                        if rect.collidepoint(e.pos):
                            self.game.game_state.sell_confirmation_card = card
                            break
                # Mua thẻ (chuột trái)
                elif e.button == 1:
                    for rect, card in item_rects:
                        if rect.collidepoint(e.pos):
                            self.game.buy_card(card['name'])

    def recalculate_layout(self, screen):
        self.button_rects.clear()

        # Nút bấm
        # SỬA LỖI: Luôn tính toán layout dựa trên kích thước của màn hình ảo
        back_button = pygame.Rect(0, 0, 220, 55)
        back_button.center = (SCREEN_WIDTH * 0.35, SCREEN_HEIGHT * 0.95)
        reroll_button = pygame.Rect(0, 0, 220, 55)
        reroll_button.center = (SCREEN_WIDTH * 0.65, SCREEN_HEIGHT * 0.95)
        self.button_rects = {"back": back_button, "reroll": reroll_button}

    def _draw(self, screen):
        drawing.draw_responsive_background(screen, self.raw_background_image)
        drawing.draw_balatro_filter(screen)
        
        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)

        title_text = MENU_FONT.render("Shop Thẻ Bài", True, WHITE_TEXT) # type: ignore
        # SỬA LỖI: Sử dụng hằng số từ config.py thay vì biến cục bộ không được định nghĩa
        screen.blit(title_text, title_text.get_rect(centerx=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT * 0.05))
        gold_text = INFO_FONT.render(f"Vàng: {self.game.game_state.player_gold}", True, GOLD_ACCENT)
        screen.blit(gold_text, (SCREEN_WIDTH * 0.04, SCREEN_HEIGHT * 0.05))

        # --- Vẽ thông báo của shop ---
        # SỬA LỖI: Di chuyển thông báo lên góc trên bên phải để không che khuất shop
        log_box_rect = pygame.Rect(SCREEN_WIDTH * 0.7, SCREEN_HEIGHT * 0.02, SCREEN_WIDTH * 0.28, 120)
        y_offset = log_box_rect.y
        for i, notif_data in enumerate(self.game.game_state.shop_notifications):
            if y_offset > log_box_rect.bottom - 20: break

            message = notif_data["message"]
            notif_type = notif_data["type"]
            
            color_map = {"shop": SUCCESS_GREEN, "error": ERROR_RED, "info": WHITE_TEXT}
            color = color_map.get(notif_type, WHITE_TEXT)

            # Thông báo cũ mờ dần
            alpha = max(0, 255 - i * 80)
            color.a = alpha
            text_surf = INFO_FONT.render(f"- {message}", True, color)
            screen.blit(text_surf, (log_box_rect.x, y_offset))
            y_offset += text_surf.get_height() + 2

        # Lấy layout thẻ bài được tính toán lại mỗi frame
        item_rects, player_card_rects = self._get_current_card_rects(screen) # Screen ở đây là virtual_screen

        # --- Vẽ Panel Shop ---
        shop_panel_rect = pygame.Rect(SCREEN_WIDTH * 0.03, SCREEN_HEIGHT * 0.18, SCREEN_WIDTH * 0.45, SCREEN_HEIGHT * 0.7)
        drawing.draw_panel_bezel(screen, shop_panel_rect)
        shop_title_text = INFO_FONT.render("Vật phẩm trong Shop", True, WHITE_TEXT)
        screen.blit(shop_title_text, (shop_panel_rect.x + 20, shop_panel_rect.y - 30))

        for rect, card in item_rects: # type: ignore
            is_hovered = rect.collidepoint(mouse_pos_virtual)
            # Vẽ một panel nhỏ cho mỗi vật phẩm
            listing_bg_color = ROYAL_PURPLE_LIGHT if is_hovered else (35, 38, 52)
            pygame.draw.rect(screen, listing_bg_color, rect, border_radius=8)
            if is_hovered:
                pygame.draw.rect(screen, ARCANE_GLOW, rect, width=1, border_radius=8)

            card_rect = pygame.Rect(rect.x + 20, rect.centery - 70, int(140 * (5/7)), 140)
            drawing.draw_themed_card(screen, card_rect, card, False, self.card_images)
            
            # --- Vẽ tên thẻ (có xuống dòng) và giá tiền ---
            text_area_x = card_rect.right + 25
            text_area_width = rect.right - text_area_x - 20
            
            # Tên thẻ
            name_color = RARITY_COLORS.get(card['rarity'], WHITE_TEXT)
            wrapped_name_lines = wrap_text(card['name'].upper(), CARD_FONT, text_area_width)
            line_y = rect.y + 20 # Dịch lên một chút
            for line in wrapped_name_lines:
                name_text = CARD_FONT.render(line, True, name_color)
                screen.blit(name_text, (text_area_x, line_y))
                line_y += name_text.get_height()

            # Giá tiền (vẽ bên dưới tên)
            price_text = INFO_FONT.render(f"{card['price']} vàng", True, GOLD_ACCENT) # type: ignore
            screen.blit(price_text, (text_area_x, line_y + 5))
            line_y += price_text.get_height() + 15 # Thêm khoảng cách

            # Mô tả thẻ
            wrapped_desc_lines = wrap_text(card['description'], CARD_DESC_FONT, text_area_width) # type: ignore
            for line in wrapped_desc_lines:
                desc_text = CARD_DESC_FONT.render(line, True, WHITE_TEXT) # type: ignore
                screen.blit(desc_text, (text_area_x, line_y))
                line_y += desc_text.get_height()

        # --- Vẽ Panel Kho đồ ---
        inventory_panel_rect = pygame.Rect(SCREEN_WIDTH * 0.52, SCREEN_HEIGHT * 0.18, SCREEN_WIDTH * 0.45, SCREEN_HEIGHT * 0.7)
        drawing.draw_panel_bezel(screen, inventory_panel_rect)
        inventory_title_text = INFO_FONT.render("Kho đồ của bạn", True, WHITE_TEXT)
        screen.blit(inventory_title_text, (inventory_panel_rect.x + 20, inventory_panel_rect.y - 30))

        for card_rect, card in player_card_rects: # type: ignore
            drawing.draw_themed_card(screen, card_rect, card, card_rect.collidepoint(mouse_pos_virtual), self.card_images)

        back_button = self.button_rects.get("back")
        reroll_button = self.button_rects.get("reroll")
        if not back_button or not reroll_button: return
        
        draw_themed_button(screen, back_button, "Quay Lại", DISABLED_TEXT, ROYAL_PURPLE_DARK, back_button.collidepoint(mouse_pos_virtual), icon=self.ui_icons.get("icon_back")) # type: ignore
        draw_themed_button(screen, reroll_button, f"Làm mới ({self.game.game_state.reroll_cost}G)", ARCANE_GLOW, ROYAL_PURPLE_DARK, reroll_button.collidepoint(mouse_pos_virtual), glow_color=ARCANE_GLOW) # type: ignore

        # --- Vẽ các lớp trên cùng (Tooltip và Hộp thoại) ---
        shop_interaction_frozen = bool(self.game.game_state.sell_confirmation_card)

        # SỬA LỖI: Tooltip chỉ hiển thị cho các thẻ trong kho đồ, không hiển thị cho shop
        hovered_inventory_card = drawing.get_hovered_card(player_card_rects, mouse_pos_virtual)
        if hovered_inventory_card and not shop_interaction_frozen:
            draw_tooltip(screen, hovered_inventory_card, mouse_pos_virtual, hint_text="(Chuột phải để bán)")
        
        if shop_interaction_frozen:
            draw_sell_confirmation_box(screen, self.game.game_state, mouse_pos_virtual)

    def _get_current_card_rects(self, screen):
        """Tính toán và trả về layout thẻ bài hiện tại. Được gọi mỗi frame."""
        item_rects = []
        player_card_rects = []

        # Khu vực Shop
        shop_panel_rect = pygame.Rect(SCREEN_WIDTH * 0.03, SCREEN_HEIGHT * 0.18, SCREEN_WIDTH * 0.45, SCREEN_HEIGHT * 0.7)
        # SỬA LỖI: Tăng kích thước thẻ trong shop để lấp đầy không gian
        num_items = len(self.game.game_state.shop_cards) if len(self.game.game_state.shop_cards) > 0 else 1
        padding_y = 20
        total_padding = (num_items + 1) * padding_y
        listing_width = shop_panel_rect.width - 40
        # SỬA LỖI: Giới hạn chiều cao tối đa của item để tránh bị phình to
        listing_height = min(200, (shop_panel_rect.height - total_padding) / num_items)

        start_x = shop_panel_rect.x + 20
        start_y = shop_panel_rect.y + padding_y
        for i, card in enumerate(self.game.game_state.shop_cards):
            listing_rect = pygame.Rect(start_x, start_y + i * (listing_height + padding_y), listing_width, listing_height)
            if listing_rect.bottom > shop_panel_rect.bottom - 20: break
            item_rects.append((listing_rect, card))

        # Khu vực Kho đồ
        inventory_panel_rect = pygame.Rect(SCREEN_WIDTH * 0.52, SCREEN_HEIGHT * 0.18, SCREEN_WIDTH * 0.45, SCREEN_HEIGHT * 0.7)
        inventory_x_start = inventory_panel_rect.x + 20
        inventory_y_start = inventory_panel_rect.y + 20
        max_cols = 3 # Giảm số cột để thẻ to hơn
        
        for i, card in enumerate(self.game.game_state.player_cards):
            col, row = i % max_cols, i // max_cols
            # SỬA LỖI: Tăng kích thước thẻ trong kho đồ
            card_height, card_width = 140, int(140 * (5/7))
            card_rect = pygame.Rect(inventory_x_start + col * (card_width + 25), inventory_y_start + row * (card_height + 40), card_width, card_height)
            if card_rect.bottom > inventory_panel_rect.bottom - 20: break
            player_card_rects.append((card_rect, card))
            
            # Vẽ tên thẻ bên dưới (có xuống dòng)
            name_color = RARITY_COLORS.get(card['rarity'], WHITE_TEXT)
            wrapped_name_lines = wrap_text(card['name'], CARD_DESC_FONT, card_width)
            line_y = card_rect.bottom + 5
            for line in wrapped_name_lines:
                name_text = CARD_DESC_FONT.render(line, True, name_color)
                text_rect = name_text.get_rect(centerx=card_rect.centerx, y=line_y)
                screen.blit(name_text, text_rect)
                line_y += name_text.get_height()
        
        return item_rects, player_card_rects