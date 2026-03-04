import pygame
import random
import math
from config import *

def _ease_out(p, power=3):
    """A simple easing function."""
    return 1 - (1 - p) ** power
def draw(screen, vfx, card_images, piece_images):
    """Animation cho hiệu ứng 'Thời Gian Ngưng Đọng' - Phong cách Clockwork Vortex."""
    progress = 1.0 - (vfx['timer'] / vfx['initial_timer'])

    # SỬA LỖI: Lấy board_rect và các màu một cách động
    BOARD_RECT = get_board_rect()
    GAME_WHITE, GAME_BLUE = WHITE_TEXT, ARCANE_GLOW # type: ignore

    center_pos = BOARD_RECT.center

    # Giai đoạn 1: Desaturate màn hình (làm xám màu) & Mặt đồng hồ xuất hiện (0.0 -> 0.7)
    if progress < 0.95:  # Giữ hiệu ứng xám màu trong gần như toàn bộ animation
        desat_p = min(1.0, progress / 0.2)  # Làm xám màu nhanh
        desat_surf = screen.copy()
        desat_surf.fill((128, 128, 128), special_flags=pygame.BLEND_RGB_MULT) # Use MULT for a better desaturation effect
        desat_surf.set_alpha(int(100 * desat_p))
        screen.blit(desat_surf, (0, 0))

        if progress < 0.7:
            clock_p = min(1.0, progress / 0.7)
            ease_clock_p = _ease_out(clock_p, 3)

            radius = int(BOARD_RECT.width * 0.4 * ease_clock_p) # type: ignore
            alpha = int(200 * ease_clock_p)

            # Vẽ các vòng tròn đồng tâm cho mặt đồng hồ
            for i in range(3):
                r_offset = i * 10
                circle_alpha = max(0, alpha - i * 50) # Đảm bảo alpha không bao giờ âm
                pygame.draw.circle(screen, (GAME_WHITE.r, GAME_WHITE.g, GAME_WHITE.b, circle_alpha), center_pos, radius - r_offset, 1)

            # Vẽ các tick mark (đơn giản hóa)
            for i in range(12):
                angle = i * math.pi / 6
                start_x = center_pos[0] + (radius - 5) * math.cos(angle - math.pi / 2)
                start_y = center_pos[1] + (radius - 5) * math.sin(angle - math.pi / 2)
                end_x = center_pos[0] + radius * math.cos(angle - math.pi / 2)
                end_y = center_pos[1] + radius * math.sin(angle - math.pi / 2)
                pygame.draw.line(screen, (GAME_WHITE.r, GAME_WHITE.g, GAME_WHITE.b, alpha), (start_x, start_y), (end_x, end_y), 1)

            # Vẽ các số La Mã
            roman_numerals = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
            for i, numeral in enumerate(roman_numerals):
                angle = i * math.pi / 6
                x = center_pos[0] + (radius - 30) * math.cos(angle - math.pi / 2)
                y = center_pos[1] + (radius - 30) * math.sin(angle - math.pi / 2)
                numeral_text = BUTTON_FONT.render(numeral, True, (GAME_WHITE.r, GAME_WHITE.g, GAME_WHITE.b, alpha))
                screen.blit(numeral_text, numeral_text.get_rect(center=(x, y)))

            # Kim đồng hồ quay ngược
            minute_angle = -progress * 2000  # Quay rất nhanh
            hour_angle = -progress * 500

            # Draw minute hand
            pygame.draw.line(screen, (GAME_WHITE.r, GAME_WHITE.g, GAME_WHITE.b, alpha), center_pos,
                             (center_pos[0] + (radius * 0.8) * math.cos(math.radians(minute_angle - 90)),
                              center_pos[1] + (radius * 0.8) * math.sin(math.radians(minute_angle - 90))), 4)
            # Draw hour hand
            pygame.draw.line(screen, (GAME_WHITE.r, GAME_WHITE.g, GAME_WHITE.b, alpha), center_pos,
                             (center_pos[0] + (radius * 0.5) * math.cos(math.radians(hour_angle - 90)),
                              center_pos[1] + (radius * 0.5) * math.sin(math.radians(hour_angle - 90))), 6)

            # Central pivot
            pygame.draw.circle(screen, (GAME_WHITE.r, GAME_WHITE.g, GAME_WHITE.b, alpha), center_pos, 8)

    # Giai đoạn 3: Thẻ bài trồi lên và hiệu ứng kết thúc (0.7 -> 1.0)
    if progress > 0.7:
        card_p = (progress - 0.7) / 0.3
        ease_card_p = _ease_out(card_p, 3)

        # Flash khi kim đồng hồ snap về 12
        if card_p < 0.2:
            flash_alpha = int(255 * (1 - card_p / 0.2))
            # Sử dụng kích thước cuối cùng của đồng hồ làm kích thước flash (dựa trên chiều rộng bàn cờ)
            final_radius = int(BOARD_RECT.width * 0.4) # type: ignore
            flash_surface = pygame.Surface((final_radius * 2, final_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(flash_surface, (255, 255, 255, flash_alpha), (final_radius, final_radius), final_radius)
            screen.blit(flash_surface, flash_surface.get_rect(center=center_pos))

        # Thay thế ảnh thẻ bằng text "TIME STOP"
        alpha = int(255 * ease_card_p)  # Fade in
        scale = 0.5 + 0.5 * ease_card_p  # Scale up

        font = pygame.font.Font(PIXEL_FONT_PATH, int(80 * scale))
        text_surf = font.render("TIME STOP", True, (GOLD_ACCENT.r, GOLD_ACCENT.g, GOLD_ACCENT.b, alpha))
        screen.blit(text_surf, text_surf.get_rect(center=center_pos))

    # Final fade out of all elements (0.95 -> 1.0)
    if progress > 0.95:
        fade_p = (progress - 0.95) / 0.05
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(255 * fade_p)))
        screen.blit(overlay, (0, 0))