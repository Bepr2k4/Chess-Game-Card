import pygame
import random
import math
import chess
from config import *
from drawing import get_board_rect, get_sq_size, get_piece_symbol

def draw(screen, vfx, card_images, piece_images):
    """Animation cho Khiên Phép: Time Reversal."""
    initial_timer = vfx['initial_timer']
    timer = vfx['timer']
    progress = 1.0 - (timer / initial_timer)
    move = vfx['triggering_move']
    game_state = vfx['game']

    # Lấy quân cờ đã tấn công (từ vị trí BẮT ĐẦU của nước đi)
    attacking_piece = game_state.board.piece_at(move.from_square)
    attacking_piece_img = None
    if attacking_piece:
        attacking_piece_img = piece_images.get(get_piece_symbol(attacking_piece))

    board_rect = get_board_rect()
    sq_size = get_sq_size(board_rect) # type: ignore

    def get_draw_pos(square):
        r, c = 7 - chess.square_rank(square), chess.square_file(square)
        if game_state.player_color == chess.BLACK:
            r, c = 7 - r, 7 - c
        return (board_rect.x + c * sq_size, board_rect.y + r * sq_size)

    start_pos = get_draw_pos(move.from_square)
    end_pos = get_draw_pos(move.to_square)

    # --- Giai đoạn 1: Khiên vỡ (0.0 -> 0.5) ---
    if progress < 0.5:
        p = progress / 0.5
        center = (end_pos[0] + sq_size // 2, end_pos[1] + sq_size // 2)
        
        # Vẽ khiên
        shield_radius = sq_size * 0.6 * (1 - p)
        shield_alpha = 255 * (1 - p)
        if shield_alpha > 0:
            pygame.draw.circle(screen, (173, 216, 230, shield_alpha), center, shield_radius, 4)

        # Hiệu ứng vỡ
        if 'shards' not in vfx:
            vfx['shards'] = []
            for _ in range(30):
                angle = random.uniform(0, math.tau)
                speed = random.uniform(50, 150)
                vfx['shards'].append({
                    'pos': pygame.Vector2(center),
                    'vel': pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                    'size': random.randint(2, 5)
                })
        for shard in vfx['shards']:
            shard['pos'] += shard['vel'] * game_state.dt
            pygame.draw.rect(screen, (173, 216, 230, shield_alpha), (*shard['pos'], shard['size'], shard['size']))

    # --- Giai đoạn 2: Thời gian quay ngược (0.3 -> 1.0) ---
    if progress > 0.3:
        p = (progress - 0.3) / 0.7
        eased_p = p * p # Ease-in

        # Nội suy vị trí của quân cờ tấn công, đi ngược từ end_pos về start_pos
        current_pos = (
            end_pos[0] + (start_pos[0] - end_pos[0]) * eased_p,
            end_pos[1] + (start_pos[1] - end_pos[1]) * eased_p
        )

        # Vẽ các dư ảnh mờ dần
        for i in range(5):
            trail_p = max(0, p - i * 0.05)
            trail_pos = (
                end_pos[0] + (start_pos[0] - end_pos[0]) * trail_p,
                end_pos[1] + (start_pos[1] - end_pos[1]) * trail_p
            )
            alpha = 150 * (1 - (p - trail_p) * 20)
            if alpha > 0:
                if attacking_piece_img:
                    # Vẽ dư ảnh của quân cờ
                    trail_img = attacking_piece_img.copy()
                    trail_img.set_alpha(alpha)
                    screen.blit(trail_img, trail_pos)

        # Vẽ quân cờ chính đang di chuyển ngược
        if attacking_piece_img:
            screen.blit(attacking_piece_img, current_pos)