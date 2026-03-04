import pygame
import random
import math
from config import *
from drawing import get_board_rect, get_sq_size
import chess

def draw(screen, vfx, card_images, piece_images):
    """
    Animation "Thức Tỉnh" khi một quân cờ nhận được Khiên Phép.
    """
    initial_timer = vfx['initial_timer']
    timer = vfx['timer']
    progress = 1.0 - (timer / initial_timer)
    ease_p = 1 - (1 - progress) ** 3 # Ease-out

    move = vfx['triggering_move']
    game_state = vfx['game']

    board_rect = get_board_rect()
    sq_size = get_sq_size(board_rect) # type: ignore
    r, c = 7 - chess.square_rank(move.to_square), chess.square_file(move.to_square)
    if game_state.player_color == chess.BLACK:
        r, c = 7 - r, 7 - c
    center_pos = pygame.Vector2(board_rect.x + c * sq_size + sq_size // 2, board_rect.y + r * sq_size + sq_size // 2)

    # 1. Cột sáng mờ dần
    radius = sq_size * 0.6 * ease_p
    height = sq_size * 3 * ease_p
    light_rect = pygame.Rect(center_pos.x - radius, center_pos.y - height / 2, radius * 2, height)
    alpha = 200 * (1 - progress)
    pygame.draw.ellipse(screen, (220, 230, 255, alpha), light_rect)

    # 2. Các hạt ánh sáng bay lên
    if 'particles' not in vfx:
        vfx['particles'] = [{'pos': center_pos + pygame.Vector2(random.uniform(-20, 20), random.uniform(-10, 10)), 'vy': random.uniform(-2, -4), 'life': random.uniform(0.5, 1.0)} for _ in range(30)]
    
    for p in vfx['particles']:
        p['pos'].y += p['vy']
        p['life'] -= game_state.dt
        if p['life'] > 0:
            pygame.draw.circle(screen, (255, 255, 255, 200 * (p['life'])), p['pos'], 2)