import pygame
from config import *
from functools import lru_cache
from card_database import CARD_DATABASE

def wrap_text(text, font, max_width):
    """Hàm helper để tự động xuống dòng cho một đoạn text dài."""
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        # Thêm một dòng mới nếu gặp ký tự xuống dòng đặc biệt
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word
    lines.append(current_line.strip())
    return [line for line in lines if line]

def blur_surface(surface, radius):
    """
    Áp dụng hiệu ứng làm mờ. Sử dụng gaussian_blur nếu có,
    nếu không thì dùng phương pháp thay thế (phóng to/thu nhỏ).
    """
    if hasattr(pygame.transform, 'gaussian_blur'):
        # Sử dụng hàm gốc nếu có (Pygame 2.1.3+)
        return pygame.transform.gaussian_blur(surface, radius)
    else:
        # Phương pháp thay thế cho các phiên bản Pygame cũ hơn
        scale = 0.5
        surf_size = surface.get_size()
        scaled_surf = pygame.transform.smoothscale(surface, (int(surf_size[0] * scale), int(surf_size[1] * scale)))
        blurred_surf = pygame.transform.smoothscale(scaled_surf, surf_size)
        return blurred_surf

def draw_panel_bezel(screen, rect, border_radius=12):
    """Vẽ khung viền và nền panel theo phong cách Premium Fantasy."""
    # 1. Đổ bóng mềm, có chiều sâu
    shadow_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), border_radius=border_radius + 5)
    screen.blit(blur_surface(shadow_surf, 5), rect.move(8, 8))
    
    # 2. Nền kính mờ
    pygame.draw.rect(screen, (ROYAL_PURPLE_DARK.r, ROYAL_PURPLE_DARK.g, ROYAL_PURPLE_DARK.b, 220), rect, border_radius=border_radius)
    
    # 3. Viền vàng kim loại
    pygame.draw.rect(screen, GOLD_ACCENT, rect, width=2, border_radius=border_radius)
    # 4. Viền highlight bên trong
    inner_highlight_rect = rect.inflate(-4, -4)
    pygame.draw.rect(screen, (GOLD_HIGHLIGHT.r, GOLD_HIGHLIGHT.g, GOLD_HIGHLIGHT.b, 50), inner_highlight_rect, width=1, border_radius=border_radius - 2)

def draw_themed_button(screen, rect, text, main_color, shadow_color, is_hovered, is_pressed=False, glow_color=None, icon=None, alpha_multiplier=1.0): # type: ignore
    """Vẽ nút bấm với bóng đổ 2 lớp, glow, icon và hover kiểu Balatro mềm mại."""
    button_rect = rect.copy()
    shadow_offset = 4
    hover_offset = -4 # Nút nhích lên trên
    press_offset = 2  # Nút bị nhấn xuống

    # Xác định vị trí cuối cùng của nút và bóng
    final_button_pos = button_rect.topleft
    if is_pressed:
        final_button_pos = (button_rect.x + press_offset, button_rect.y + press_offset)
    elif is_hovered:
        final_button_pos = (button_rect.x, button_rect.y + hover_offset)

    # Tạo một surface tạm để vẽ nút, cho phép điều chỉnh alpha tổng thể
    button_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    temp_rect = button_surface.get_rect() # Rect để vẽ bên trong surface tạm

    # 1. Vẽ bóng đổ
    hard_shadow_rect = pygame.Rect(shadow_offset, shadow_offset, temp_rect.width, temp_rect.height)
    pygame.draw.rect(button_surface, shadow_color, hard_shadow_rect, border_radius=10)

    # 2. Xử lý hiệu ứng hover
    current_main_color = main_color
    if is_hovered:
        # Tăng độ sáng của nút
        current_main_color = main_color.lerp(WHITE_TEXT, 0.15) # type: ignore
        # Thêm hiệu ứng glow
        if glow_color:
            # Vẽ glow lên một surface riêng để không bị ảnh hưởng bởi alpha của nút
            glow_rect = rect.inflate(10, 10)
            glow_rect.topleft = (final_button_pos[0] - 5, final_button_pos[1] - 5)
            glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (glow_color.r, glow_color.g, glow_color.b, 80), glow_surf.get_rect(), border_radius=15)
            screen.blit(glow_surf, glow_rect.topleft)
    
    # 3. Vẽ thân nút
    pygame.draw.rect(button_surface, current_main_color, temp_rect, border_radius=8)
    pygame.draw.rect(button_surface, shadow_color, temp_rect, width=3, border_radius=8) # Viền dày

    # Font chữ đậm, có viền tối 1px để dễ đọc
    text_surf = BUTTON_FONT.render(text, True, WHITE_TEXT) # type: ignore
    text_shadow_surf = BUTTON_FONT.render(text, True, (0,0,0,100)) # type: ignore
    
    # Vẽ icon nếu có
    if icon:
        icon_size = temp_rect.height - 20
        scaled_icon = pygame.transform.smoothscale(icon, (icon_size, icon_size)) # type: ignore
        if text: # Nếu có cả text và icon, đặt icon bên trái
            icon_rect = scaled_icon.get_rect(centery=temp_rect.centery, left=15)
            text_rect = text_surf.get_rect(centery=temp_rect.centery, left=icon_rect.right + 15)
        else: # Nếu chỉ có icon, căn nó vào giữa
            icon_rect = scaled_icon.get_rect(center=temp_rect.center)
            text_rect = text_surf.get_rect(center=temp_rect.center) # Để text_surf trống không vẽ gì
        button_surface.blit(scaled_icon, icon_rect) # Vẽ icon
    else:
        text_rect = text_surf.get_rect(center=temp_rect.center)
    
    if text: # Chỉ vẽ text nếu nó tồn tại
        button_surface.blit(text_shadow_surf, text_rect.move(1,1))
        button_surface.blit(text_surf, text_rect)

    # Áp dụng alpha tổng thể và vẽ lên màn hình chính
    button_surface.set_alpha(int(255 * alpha_multiplier))
    screen.blit(button_surface, final_button_pos)

def draw_themed_card(screen, rect, card_data, is_hovered, card_images): # type: ignore
    """Vẽ một thẻ bài bằng hình ảnh, với hiệu ứng hover."""
    card_id = card_data['id']
    rarity = card_data.get("rarity", "Common")
    border_color = RARITY_COLORS.get(rarity, WHITE_TEXT) # type: ignore

    # --- Vẽ Khung Thẻ ---
    # Lớp nền tối
    pygame.draw.rect(screen, ROYAL_PURPLE_DARK, rect, border_radius=12) # type: ignore
    # Viền ngoài theo độ hiếm
    pygame.draw.rect(screen, border_color, rect, width=2, border_radius=12)
    # Viền trong vàng kim loại
    inner_border_rect = rect.inflate(-6, -6)
    pygame.draw.rect(screen, GOLD_ACCENT, inner_border_rect, width=1, border_radius=8) # type: ignore

    # --- Khu vực ảnh ---
    art_rect = pygame.Rect(inner_border_rect.x + 5, inner_border_rect.y + 5, inner_border_rect.width - 10, inner_border_rect.height * 0.5)
    pygame.draw.rect(screen, (10,10,15), art_rect) # Nền đen cho ảnh
    
    if card_id in card_images:
        card_img = card_images[card_id]
        # Scale ảnh để vừa với khu vực art_rect
        scaled_art = pygame.transform.smoothscale(card_img, art_rect.size)
        screen.blit(scaled_art, art_rect.topleft)

    # --- Khu vực Tên Thẻ (giờ chiếm phần còn lại của thẻ) ---
    name_area_rect = pygame.Rect(inner_border_rect.x, art_rect.bottom, inner_border_rect.width, inner_border_rect.bottom - art_rect.bottom)
    
    # SỬA LỖI: Tự động giảm kích thước font nếu tên quá dài
    font_to_use = CARD_FONT
    wrapped_name_lines = wrap_text(card_data['name'].upper(), font_to_use, name_area_rect.width - 10)
    total_text_height = sum(font_to_use.size(line)[1] for line in wrapped_name_lines)

    if total_text_height > name_area_rect.height - 8: # Nếu text quá cao, dùng font nhỏ hơn
        font_to_use = CARD_DESC_FONT
        wrapped_name_lines = wrap_text(card_data['name'].upper(), font_to_use, name_area_rect.width - 10)
        total_text_height = sum(font_to_use.size(line)[1] for line in wrapped_name_lines)
    
    # Căn giữa khối text theo chiều dọc
    line_y = name_area_rect.centery - total_text_height / 2
    
    for line in wrapped_name_lines:
        name_text = font_to_use.render(line, True, border_color)
        screen.blit(name_text, name_text.get_rect(centerx=name_area_rect.centerx, y=line_y))
        line_y += name_text.get_height()

    # --- Số lượt sử dụng (Viên ngọc) ---
    gem_radius = 12
    gem_center = (rect.right - gem_radius - 5, rect.top + gem_radius + 5)
    # Vẽ bóng cho viên ngọc
    pygame.draw.circle(screen, (0,0,0,100), (gem_center[0]+2, gem_center[1]+2), gem_radius)
    # Vẽ viên ngọc
    gem_color = border_color.lerp(pygame.Color("white"), 0.3) # type: ignore
    pygame.draw.circle(screen, gem_color, gem_center, gem_radius)
    # Vẽ viền và highlight
    pygame.draw.circle(screen, GOLD_HIGHLIGHT, gem_center, gem_radius, 1) # type: ignore
    pygame.draw.circle(screen, GOLD_HIGHLIGHT, (gem_center[0]-3, gem_center[1]-3), 3) # type: ignore
    # Vẽ số
    uses_text = BUTTON_FONT.render(str(card_data['uses']), True, ROYAL_PURPLE_DARK) # type: ignore
    screen.blit(uses_text, uses_text.get_rect(center=gem_center))

# Cache cho tooltip để tối ưu hiệu năng
@lru_cache(maxsize=128)
def _get_wrapped_tooltip_lines(desc, font, max_width):
    """Hàm helper được cache để tính toán việc xuống dòng cho tooltip."""
    return wrap_text(desc, font, max_width)

def draw_tooltip(screen, card_data, mouse_pos, hint_text=None): # type: ignore
    """Vẽ hộp mô tả với vị trí thông minh phía trên lá bài."""
    screen_width, screen_height = screen.get_size()
    desc = card_data['description']
    if hint_text:
        desc += f"\n{hint_text}"
    
    # SỬA LỖI HIỆU NĂNG: Sử dụng hàm helper đã được cache
    max_width = 300
    lines = _get_wrapped_tooltip_lines(desc, CARD_DESC_FONT, max_width - 20)
    
    # Tính toán kích thước hộp thoại dựa trên text đã được xuống dòng
    total_height = sum(CARD_DESC_FONT.size(line)[1] for line in lines) + (len(lines) - 1) * 3
    max_line_width = max(CARD_DESC_FONT.size(line)[0] for line in lines)

    padding = 10
    box_width = max_line_width + padding * 2
    box_height = total_height + padding * 2
    
    # Vị trí mặc định: Phía trên con trỏ chuột
    rect = pygame.Rect(mouse_pos[0] - box_width // 2, mouse_pos[1] - box_height - 15, box_width, box_height)

    # Điều chỉnh nếu tràn ra ngoài màn hình
    if rect.left < 10: rect.left = 10
    if rect.right > screen_width - 10:
        rect.right = screen_width - 10
    if rect.top < 10: # Nếu tràn lên trên, lật xuống dưới
        rect.top = mouse_pos[1] + 25

    # Vẽ nền panel
    draw_panel_bezel(screen, rect)
    
    y_offset = rect.y + padding
    for line in lines:
        line_surf = CARD_DESC_FONT.render(line, True, WHITE_TEXT) # type: ignore
        screen.blit(line_surf, (rect.x + padding, y_offset))
        y_offset += line_surf.get_height() + 3

def draw_sell_confirmation_box(screen, game, mouse_pos): # type: ignore
    """Vẽ hộp thoại xác nhận bán thẻ."""
    if not game.sell_confirmation_card:
        return None, None

    # Vẽ một lớp phủ mờ # game ở đây là game_state
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Kích thước và vị trí hộp thoại
    box_width, box_height = 500, 250 # type: ignore
    box_rect = pygame.Rect(0, 0, box_width, box_height)
    box_rect.center = screen.get_rect().center

    # Vẽ hộp thoại
    draw_panel_bezel(screen, box_rect)

    # Hiển thị văn bản
    card_name = game.sell_confirmation_card['name']
    sell_price = get_sell_price(game, card_name) # Sử dụng hàm helper
    
    title_text = INFO_FONT.render(f"Bán thẻ '{card_name}'?", True, WHITE_TEXT) # type: ignore
    price_text = INFO_FONT.render(f"Bạn sẽ nhận lại {sell_price} vàng.", True, GOLD_ACCENT) # type: ignore
    screen.blit(title_text, title_text.get_rect(centerx=box_rect.centerx, y=box_rect.y + 30))
    screen.blit(price_text, price_text.get_rect(centerx=box_rect.centerx, y=box_rect.y + 70))

    # Vẽ các nút
    confirm_button = pygame.Rect(box_rect.centerx - 160, box_rect.bottom - 80, 150, 50)
    cancel_button = pygame.Rect(box_rect.centerx + 10, box_rect.bottom - 80, 150, 50)

    draw_themed_button(screen, confirm_button, "Xác nhận", ERROR_RED, pygame.Color(133, 49, 49), confirm_button.collidepoint(mouse_pos)) # type: ignore
    draw_themed_button(screen, cancel_button, "Hủy", pygame.Color(80, 80, 80), pygame.Color(40, 40, 40), cancel_button.collidepoint(mouse_pos))

    return confirm_button, cancel_button

def get_sell_price(game_state, card_name):
    """Tính toán và trả về giá bán của một thẻ bài."""
    card_to_check = next((c for c in game_state.player_cards if c['name'] == card_name), None)
    if not card_to_check:
        return 0

    original_card_data = next((c for c in CARD_DATABASE if c['id'] == card_to_check['id']), None)
    if not original_card_data:
        return 0
    return int(original_card_data['price'] / 1.7)