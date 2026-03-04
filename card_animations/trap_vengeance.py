import pygame
import random
import math
from config import *
import chess
from drawing import get_board_rect, get_sq_size


def draw(screen, vfx, card_images, piece_images):
    """
    Animation cho thẻ 'Bẫy Đồng Quy Vu Tận' - Hiệu ứng Kích Hoạt Tối Thượng.
    """
    initial_timer = vfx['initial_timer']
    timer = vfx['timer']
    progress = 1.0 - (timer / initial_timer)
    
    # --- Giai đoạn 1: Năng lượng nén lại (0.0 -> 0.3) ---
    if progress < 0.3:
        p = progress / 0.3
        center = vfx['triggering_move'].to_square # SỬA LỖI: Lấy nước đi từ triggering_move
        board_rect = get_board_rect()
        sq_size = get_sq_size(board_rect)
        r, c = 7 - chess.square_rank(center), chess.square_file(center)
        if vfx['game'].player_color == chess.BLACK: # vfx['game'] ở đây là game_state
            r, c = 7 - r, 7 - c
        center_pos = (board_rect.x + c * sq_size + sq_size // 2, board_rect.y + r * sq_size + sq_size // 2)

        # Vòng xoáy năng lượng Tím Thẩm
        for i in range(5):
            radius = (150 - i * 20) * (1 - p)
            alpha = 100 + 155 * p
            pygame.draw.circle(screen, (120, 40, 200, alpha), center_pos, radius, width=3)

    # --- Giai đoạn 2: Bùng nổ (0.3 -> 0.4) ---
    if 0.3 <= progress < 0.4:
        # Chớp sáng Trắng cực mạnh
        flash_alpha = 255 * (1 - ((progress - 0.3) / 0.1))
        flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        flash_surf.fill((255, 255, 255, flash_alpha))
        screen.blit(flash_surf, (0, 0))

    # --- Giai đoạn 3: Xé toạc không gian (0.4 -> 1.0) ---
    if progress > 0.4:
        p = (progress - 0.4) / 0.6
        center = vfx['triggering_move'].to_square # SỬA LỖI: Lấy nước đi từ triggering_move
        board_rect = get_board_rect()
        sq_size = get_sq_size(board_rect)
        r, c = 7 - chess.square_rank(center), chess.square_file(center)
        if vfx['game'].player_color == chess.BLACK: # vfx['game'] ở đây là game_state
            r, c = 7 - r, 7 - c
        center_pos = (board_rect.x + c * sq_size + sq_size // 2, board_rect.y + r * sq_size + sq_size // 2)

        # Rung màn hình
        shake_offset = (random.randint(-8, 8) * (1-p), random.randint(-8, 8) * (1-p))
        screen.blit(screen, shake_offset)

        # Các tia năng lượng sắc nét
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            length = random.uniform(100, 400) * (1 - p**2) # Ngắn dần
            start_point = (center_pos[0] + math.cos(angle) * 20, center_pos[1] + math.sin(angle) * 20)
            end_point = (start_point[0] + math.cos(angle) * length, start_point[1] + math.sin(angle) * length)
            color = random.choice([ERROR_RED, pygame.Color(255, 0, 128), GOLD_HIGHLIGHT])
            alpha = 200 * (1 - p)
            pygame.draw.line(screen, (color.r, color.g, color.b, alpha), start_point, end_point, random.randint(2, 4))