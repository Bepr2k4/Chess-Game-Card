import pygame
import math
from config import *

def draw(screen, vfx, card_images, piece_images):
    """Animation cho thẻ 'Bẫy Phản Kích' - Sợi xích ma thuật."""
    progress = 1.0 - (vfx['timer'] / vfx['initial_timer'])
    eased_progress = 1 - (1 - progress) ** 3 # Ease-out

    # Lấy vị trí avatar của bot
    sidebar_rect = get_sidebar_rect()
    bot_panel_height = sidebar_rect.height * 0.7
    bot_panel_rect = pygame.Rect(sidebar_rect.x, sidebar_rect.y, sidebar_rect.width, bot_panel_height)
    end_pos = pygame.Vector2(bot_panel_rect.centerx, bot_panel_rect.centery + 40)

    # Lấy vị trí bắt đầu (vị trí quân cờ tấn công)
    board_rect = get_board_rect()
    start_pos = pygame.Vector2(board_rect.center) # Giả định bắt đầu từ giữa bàn cờ

    # Nội suy vị trí đầu của sợi xích
    current_pos = start_pos.lerp(end_pos, eased_progress)

    # Vẽ sợi xích
    chain_color = ERROR_RED
    points = []
    length = (current_pos - start_pos).length()
    if length > 0:
        num_segments = 20
        for i in range(num_segments + 1):
            p = i / num_segments
            point = start_pos.lerp(current_pos, p)
            point.y += math.sin(p * math.pi * 2 + vfx['timer'] * 0.2) * 10 * (1 - p)
            points.append(point)
        if len(points) > 1:
            pygame.draw.aalines(screen, chain_color, False, points, 2)