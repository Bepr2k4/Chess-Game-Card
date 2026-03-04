import pygame
import random
from config import *

def draw(screen, vfx, card_images, piece_images):
    """Animation cho thẻ 'Nước Đi Chớp Nhoáng' - Phong cách Time Warp / Glitch."""
    progress = 1.0 - (vfx['timer'] / vfx['initial_timer'])
    card_img = card_images.get(vfx['card']['id'])
    # SỬA LỖI: Sử dụng hằng số vì giờ đây mọi thứ đều vẽ trên virtual_screen
    BOARD_RECT = get_board_rect()

    if not card_img: return

    # Giai đoạn 1: Glitch và thẻ lướt qua (0.0 -> 0.6)
    if progress < 0.6:
        p = progress / 0.6
        ease_p = 1 - (1 - p)**3

        # Hiệu ứng Glitch
        for _ in range(5):
            x = random.randint(BOARD_RECT.left, BOARD_RECT.right)
            y = random.randint(BOARD_RECT.top, BOARD_RECT.bottom)
            w = random.randint(50, 200)
            h = random.randint(2, 5)
            glitch_rect = pygame.Rect(x, y, w, h)
            # Dịch chuyển một phần màn hình
            offset_x = random.randint(-10, 10)
            screen.blit(screen, glitch_rect.move(offset_x, 0), glitch_rect, special_flags=pygame.BLEND_RGBA_ADD)

        # Thẻ lướt qua màn hình
        start_x = BOARD_RECT.left - 300
        end_x = BOARD_RECT.right + 300
        current_x = start_x + (end_x - start_x) * ease_p
        y_pos = BOARD_RECT.centery

        # Vệt mờ (Motion Blur)
        for i in range(3):
            blur_img = card_img.copy()
            blur_alpha = 100 - i * 30
            blur_img.set_alpha(blur_alpha)
            screen.blit(blur_img, blur_img.get_rect(center=(current_x - i * 30, y_pos)))

    # Giai đoạn 2: Dư ảnh quang sai (Chromatic Aberration) (0.6 -> 1.0)
    else:
        p = (progress - 0.6) / 0.4
        # Alpha cho các dư ảnh, mờ dần đi
        alpha = int(100 * (1 - p))
        
        # Tạo hiệu ứng "dư ảnh thời gian" an toàn hơn
        screen_copy = screen.copy()
        screen_copy.set_alpha(alpha)

        # Vẽ 2 bản sao mờ của màn hình ở các vị trí lệch nhau
        offset = 15 * p
        screen.blit(screen_copy, (offset, 0))
        screen.blit(screen_copy, (-offset, 0))