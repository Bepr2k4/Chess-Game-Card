import pygame
import chess
from config import *

def _clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))

def draw(screen, vfx, card_images, piece_images):
    """Animation triệu hồi cho thẻ 'Kỵ Sĩ Đoàn'."""
    progress = 1.0 - (vfx['timer'] / vfx['initial_timer'])
    
    # SỬA LỖI: Lấy board_rect và sq_size một cách động
    BOARD_RECT = get_board_rect()
    SQ_SIZE = get_sq_size(BOARD_RECT) # type: ignore
    
    # SỬA LỖI: Xác định vị trí dựa trên màu quân của người chơi
    player_color = vfx['game'].player_color # Lấy màu quân từ đối tượng game được truyền vào
    # SỬA LỖI: Logic giờ chỉ hy sinh 1 Tốt ở E2/E7
    if player_color == chess.WHITE:
        pawn_sq, knight_sq = chess.E2, chess.E2
        pawn_img_symbol = 'wP'
        knight_img_symbol = 'wN'
    else: # Người chơi là quân Đen
        pawn_sq, knight_sq = chess.E7, chess.E7
        pawn_img_symbol = 'bP'
        knight_img_symbol = 'bN'

    def get_draw_pos(square):
        r, c = 7 - chess.square_rank(square), chess.square_file(square)
        if player_color == chess.BLACK:
            r, c = 7 - r, 7 - c
        return (BOARD_RECT.x + c * SQ_SIZE + SQ_SIZE // 2, r * SQ_SIZE + SQ_SIZE // 2)

    pawn_pos = get_draw_pos(pawn_sq)
    knight_center_pos = get_draw_pos(knight_sq)

    # Giai đoạn 1: Tốt co lại (0.0 -> 0.2)
    if progress < 0.3:
        p = progress / 0.3
        pawn_img = piece_images[pawn_img_symbol]

        # Tốt co lại và mờ dần khi di chuyển vào trung tâm
        scale = 1.0 - p
        alpha = 255 * (1.0 - p)
        
        if scale <= 0: return # Dừng vẽ nếu đã biến mất hoàn toàn

        scaled_size = (int(SQ_SIZE * scale), int(SQ_SIZE * scale))
        scaled_pawn_img = pygame.transform.smoothscale(pawn_img, scaled_size)
        scaled_pawn_img.set_alpha(alpha)

        # Vẽ quân Tốt
        screen.blit(scaled_pawn_img, scaled_pawn_img.get_rect(center=pawn_pos))

    # Giai đoạn 2: Vòng tròn ma thuật (0.3 -> 0.7)
    if 0.3 <= progress < 0.7:
        p = (progress - 0.3) / 0.4 # progress trong giai đoạn này (0 -> 1)
        radius = int(SQ_SIZE * 0.7 * p)
        alpha = int(255 * (1 - p))
        # Vẽ 2 vòng tròn xoay ngược chiều nhau
        if alpha > 0:
            pygame.draw.circle(screen, (GOLD_ACCENT.r, GOLD_ACCENT.g, GOLD_ACCENT.b, alpha), knight_center_pos, radius, width=2)
            pygame.draw.circle(screen, (WHITE_TEXT.r, WHITE_TEXT.g, WHITE_TEXT.b, alpha // 2), knight_center_pos, int(radius * 0.6), width=2)

    # Giai đoạn 3: Mã giáng xuống (0.6 -> 1.0) - 40% thời gian
    if progress >= 0.3:
        # SỬA LỖI: Divisor phải là 0.7 (1.0 - 0.3) để p chạy từ 0 đến 1
        p = _clamp((progress - 0.3) / 0.7) # progress trong giai đoạn này (0 -> 1), được clamp để đảm bảo an toàn
        ease_p = 1 - (1 - p) ** 3 # Ease-out

        # Mã từ trên trời giáng xuống
        start_y = knight_center_pos[1] - 100
        current_y = start_y + (knight_center_pos[1] - start_y) * ease_p
        
        knight_img = piece_images[knight_img_symbol]
        scale = 0.5 + 0.5 * ease_p
        alpha = 255 * ease_p
        scaled_size = (int(SQ_SIZE * scale), int(SQ_SIZE * scale))
        scaled_img = pygame.transform.smoothscale(knight_img, scaled_size)
        scaled_img.set_alpha(alpha)
        screen.blit(scaled_img, scaled_img.get_rect(center=(knight_center_pos[0], current_y)))

        # Hiệu ứng shockwave khi đáp xuống
        # SỬA LỖI: Sử dụng ease_p và giới hạn giá trị để tránh lỗi alpha
        if ease_p > 0.5:
            shock_p = max(0, min(1, (ease_p - 0.5) / 0.5)) # Giới hạn shock_p từ 0 đến 1
            shock_radius = int(SQ_SIZE * shock_p)
            shock_alpha = int(150 * (1 - shock_p))
            pygame.draw.circle(screen, (WHITE_TEXT.r, WHITE_TEXT.g, WHITE_TEXT.b, shock_alpha), knight_center_pos, shock_radius, width=2)