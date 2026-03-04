import pygame
import random
import math
from config import *
from drawing import get_board_rect, get_sq_size
import chess

def draw_placement(screen, vfx, card_images, piece_images):
    """
    Animation "Yểm Ấn Ký" khi đặt bẫy Blessing of Bloodthirst.
    """
    initial_timer = vfx['initial_timer']
    timer = vfx['timer']
    progress = 1.0 - (timer / initial_timer)
    ease_p = 1 - (1 - progress) ** 3 # Ease-out

    target_square = vfx['target_square']
    game_state = vfx['game']

    board_rect = get_board_rect()
    sq_size = get_sq_size(board_rect) # type: ignore
    r, c = 7 - chess.square_rank(target_square), chess.square_file(target_square)
    if game_state.player_color == chess.BLACK:
        r, c = 7 - r, 7 - c
    center_pos = pygame.Vector2(board_rect.x + c * sq_size + sq_size // 2, board_rect.y + r * sq_size + sq_size // 2)

    # Giai đoạn 1: Ấn ký xuất hiện và co lại (0.0 -> 1.0)
    current_radius = sq_size * 2 * (1 - ease_p)
    alpha = 255 * (1 - ease_p)

    if current_radius > 5:
        # Vẽ ấn ký (một ngôi sao 6 cánh đơn giản)
        num_points = 6
        for i in range(num_points * 2):
            radius = current_radius if i % 2 == 0 else current_radius * 0.5
            angle = (i / (num_points * 2)) * math.tau + (progress * 5)
            
            x = center_pos.x + radius * math.cos(angle)
            y = center_pos.y + radius * math.sin(angle)
            
            next_i = (i + 1) % (num_points * 2)
            next_radius = current_radius if next_i % 2 == 0 else current_radius * 0.5
            next_angle = (next_i / (num_points * 2)) * math.tau + (progress * 5)

            next_x = center_pos.x + next_radius * math.cos(next_angle)
            next_y = center_pos.y + next_radius * math.sin(next_angle)

            pygame.draw.line(screen, (ERROR_RED.r, ERROR_RED.g, ERROR_RED.b, alpha), (x, y), (next_x, next_y), 2)

    # Giai đoạn 2: Hào quang đỏ trên quân cờ (0.7 -> 1.0)
    if progress > 0.7:
        p = (progress - 0.7) / 0.3
        glow_alpha = 150 * (1 - p)
        pygame.draw.circle(screen, (ERROR_RED.r, ERROR_RED.g, ERROR_RED.b, glow_alpha), center_pos, sq_size * 0.5, 4)