import pygame
from config import *
import random
import chess
import math

def draw_trap_placement(screen, vfx, card_images, piece_images):
    """Animation đặt bẫy: Vòng tròn rune co lại."""
    initial_timer = vfx['initial_timer']
    timer = vfx['timer']
    BOARD_RECT = get_board_rect()
    SQ_SIZE = get_sq_size(BOARD_RECT) # type: ignore
    progress = 1.0 - (timer / initial_timer)
    ease_p = 1 - (1 - progress)**3

    target_square = vfx['target_square']
    game_state = vfx['game']
    r, c = 7 - chess.square_rank(target_square), chess.square_file(target_square)
    if game_state.player_color == chess.BLACK:
        r, c = 7 - r, 7 - c
    center_pos = pygame.Vector2(BOARD_RECT.x + c * SQ_SIZE + SQ_SIZE // 2, BOARD_RECT.y + r * SQ_SIZE + SQ_SIZE // 2) # type: ignore

    base_color = ARCANE_GLOW

    # Vòng tròn rune co lại vào quân cờ
    radius = int(SQ_SIZE * 1.5 * (1 - ease_p))
    alpha = 255 * (1 - ease_p)

    if radius > 5 and alpha > 10: # type: ignore
        pygame.draw.circle(screen, (base_color.r, base_color.g, base_color.b, alpha), center_pos, radius, 3)
        for i in range(5):
            angle = i * (math.tau / 5) + progress * 10
            x = center_pos.x + radius * math.cos(angle)
            y = center_pos.y + radius * math.sin(angle)
            pygame.draw.circle(screen, (base_color.r, base_color.g, base_color.b, alpha), (x, y), 4)

def _clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))

def draw(screen, vfx, card_images, piece_images):
    """Animation mặc định mới: Triệu hồi từ Cổng không gian."""
    initial_timer = vfx['initial_timer']
    timer = vfx['timer']
    card = vfx['card']

    # SỬA LỖI: Lấy board_rect một cách động
    BOARD_RECT = get_board_rect()
    progress = 1.0 - (timer / initial_timer) # Tiến độ từ 0.0 đến 1.0
    center_pos = BOARD_RECT.center
    base_color = RARITY_COLORS.get(card['rarity'], WHITE_TEXT)
    
    # Giai đoạn 1: Vòng xoáy năng lượng xuất hiện (0.0 -> 0.6)
    if progress < 0.6:
        p = progress / 0.6
        ease_p = 1 - (1 - p) ** 3 # Ease-out
        
        # Vẽ các hạt năng lượng bay ra từ tâm
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(50, 200) * ease_p
            particle_pos = (center_pos[0] + math.cos(angle) * radius, center_pos[1] + math.sin(angle) * radius)
            alpha = int(200 * (1 - p))
            pygame.draw.circle(screen, (base_color.r, base_color.g, base_color.b, alpha), particle_pos, random.randint(2, 4))

    # Giai đoạn 2: Thẻ bài trồi lên từ tâm (0.3 -> 1.0)
    if progress > 0.3:
        p = _clamp((progress - 0.3) / 0.7) # SỬA LỖI: Giới hạn giá trị của p để tránh lỗi số thực
        ease_p = 1 - (1 - p) ** 4 # Ease-out mạnh hơn

        if card['id'] in card_images:
            card_img = card_images[card['id']]
            
            # Thẻ phóng to và rõ dần
            scale = 0.2 + 0.8 * ease_p
            alpha = int(255 * ease_p)
            
            scaled_size = (int(350 * scale), int(350 * 7/5 * scale))
            scaled_img = pygame.transform.smoothscale(card_img, scaled_size)
            scaled_img.set_alpha(alpha)
            
            img_rect = scaled_img.get_rect(center=center_pos)
            screen.blit(scaled_img, img_rect)

            # Hiệu ứng lóe sáng khi thẻ xuất hiện hoàn toàn
            if p > 0.8:
                flash_p = (p - 0.8) / 0.2
                flash_alpha = int(150 * (1 - flash_p))
                flash_surf = pygame.Surface(scaled_size, pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, flash_alpha))
                screen.blit(flash_surf, img_rect, special_flags=pygame.BLEND_RGBA_ADD)