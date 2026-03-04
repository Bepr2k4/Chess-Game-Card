import pygame
import math
import random
import os
import chess
from config import *
from assets import get_piece_symbol
import drawing

# Optional wand sprite: if you put a PNG at `images/wand_sprite.png`, we'll use it.
WAND_SPRITE = None
WAND_SPRITE_TRIED = False

def _clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def _ease_out(p, power=3):
    return 1 - (1 - p) ** power

def _ease_in_out_quad(p):
    """Hàm easing mượt mà: chậm lúc đầu, nhanh ở giữa, chậm lúc cuối."""
    if p < 0.5:
        return 2 * p * p
    else:
        return -1 + (4 - 2 * p) * p


def _draw_star(surf, center, outer_r, inner_r, points, color, alpha=255):
    cx, cy = center
    vertices = []
    for i in range(points * 2):
        ang = (i / (points * 2.0)) * math.tau - math.pi / 2
        r = outer_r if i % 2 == 0 else inner_r
        x = int(cx + r * math.cos(ang))
        y = int(cy + r * math.sin(ang))
        vertices.append((x, y))
    star_s = pygame.Surface((outer_r * 2 + 4, outer_r * 2 + 4), pygame.SRCALPHA)
    offset = (outer_r + 2, outer_r + 2)
    poly = [(vx - cx + offset[0], vy - cy + offset[1]) for (vx, vy) in vertices]
    pygame.draw.polygon(star_s, (color[0], color[1], color[2], alpha), poly)
    surf.blit(star_s, (cx - offset[0], cy - offset[1]))


def draw_board_reveal(screen, game, piece_images, timer, draw_pieces_func):
    """Hiệu ứng mở màn: cây gậy phép thuật anime gõ, vòng tròn ma thuật xuất hiện, và triệu hồi các quân cờ.

    Thiết kế stages:
    - 0.25 - 0.60 : Vòng tròn ma thuật dần hiện, tầng vòng xoay và rune
    - 0.60 - 1.00 : Tia sáng triệu hồi cho từng quân cờ; quân cờ phóng to + mờ dần vào vị trí
    """
    # Make logical duration longer so reveal is slower and more dramatic.
    duration = 70 # Nhanh hơn
    progress = _clamp(1.0 - (timer / duration))
    game.board_reveal_timer = timer
    # SỬA LỖI: Sử dụng hằng số vì giờ đây mọi thứ đều vẽ trên virtual_screen
    board_rect = get_board_rect()
    sq_size = get_sq_size(board_rect)
    center = board_rect.center

    # Vẽ nền
    # PLAY_BACKGROUND_IMAGE đã bị vô hiệu hóa, nên chúng ta chỉ cần vẽ màu nền
    # cho toàn bộ màn hình vì các thành phần khác sẽ vẽ đè lên.
    screen_rect = screen.get_rect()

    # --- Stage 0: Fade out white flash (0.0 - 0.1) ---
    # This stage happens at the very beginning of draw_board_reveal
    # to smoothly transition from the white flash of draw_vs_transition.
    fade_out_duration_p = 0.1 # 10% of draw_board_reveal's duration
    if progress < fade_out_duration_p: # game ở đây là game_state
        rune_texture = drawing._get_cached_rune_texture(screen_rect.width, screen_rect.height)
        # Trong lúc mờ dần, vẫn vẽ nền họa tiết bên dưới
        if rune_texture:
            scroll_y = (pygame.time.get_ticks() / 100) % rune_texture.get_height()
            rune_clone = rune_texture.copy()
            rune_clone.set_alpha(15) # Rất mờ
            screen.blit(rune_clone, (0, scroll_y))
            screen.blit(rune_clone, (0, scroll_y - rune_texture.get_height()))

        fade_p = _clamp(progress / fade_out_duration_p) # goes from 0 to 1
        fade_alpha = int(255 * (1.0 - fade_p)) # goes from 255 to 0
        screen.fill(pygame.Color(30, 25, 45)) # Nền mới
        if fade_alpha > 0:
            fade_surf = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
            fade_surf.fill((255, 255, 255, fade_alpha))
            screen.blit(fade_surf, (0, 0))
        return # Don't draw other stages yet
    else:
        screen.fill(pygame.Color(30, 25, 45)) # Nền mới
        rune_texture = drawing._get_cached_rune_texture(screen_rect.width, screen_rect.height)
        # Vẽ nền họa tiết rune mờ ảo
        if rune_texture:
            scroll_y = (pygame.time.get_ticks() / 100) % rune_texture.get_height()
            rune_clone = rune_texture.copy()
            rune_clone.set_alpha(15) # Rất mờ
            screen.blit(rune_clone, (0, scroll_y))
            screen.blit(rune_clone, (0, scroll_y - rune_texture.get_height()))

    
    # Adjust progress for subsequent stages to start after fade-out
    adjusted_progress = _clamp((progress - fade_out_duration_p) / (1.0 - fade_out_duration_p))

    # Vẽ nền cho khu vực bàn cờ
    pygame.draw.rect(screen, GAME_BG, board_rect)

    # --- Stage 1: Magic circle build (using adjusted_progress) ---
    magic_circle_end_p = 0.8 # relative to adjusted_progress
    if adjusted_progress < magic_circle_end_p:
        p = _clamp(adjusted_progress / magic_circle_end_p)
        ease_p = _ease_in_out_quad(p)
        
        base_radius = int(min(board_rect.width, board_rect.height) * 0.32)
        glow_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

        # nhiều vòng đồng tâm xoay ngược chiều nhau - tăng alpha và width để rõ hơn
        ring_counts = 4
        for i in range(ring_counts):
            t = (pygame.time.get_ticks() / 1000.0) * (0.45 + i * 0.45)
            radius = int(base_radius * (0.45 + 0.9 * (i / ring_counts) + 0.5 * ease_p)) - i * 6
            alpha = int(230 * (1.0 - i * 0.18) * ease_p)
            width = 5 + i
            start_ang = t * (1 if i % 2 == 0 else -1)
            rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
            pygame.draw.arc(glow_surf, (GOLD_ACCENT.r, GOLD_ACCENT.g, GOLD_ACCENT.b, alpha), rect, start_ang, start_ang + math.pi * (0.9 + 0.25 * ease_p), width)

            # rune lớn hơn quanh vành
            rune_count = 14 - i * 2
            for j in range(rune_count):
                ang = start_ang + (j / rune_count) * (math.pi * 2)
                rx = int(center[0] + (radius - 18) * math.cos(ang))
                ry = int(center[1] + (radius - 18) * math.sin(ang))
                rune_alpha = int(240 * ease_p * (0.6 + 0.4 * math.sin(ang * 2 + t * 2)))
                pygame.draw.circle(glow_surf, (WHITE_TEXT.r, WHITE_TEXT.g, WHITE_TEXT.b, rune_alpha), (rx, ry), 5) # type: ignore

        # ánh sáng nền mềm - tăng sức mạnh glow
        for i in range(4):
            rr = int(base_radius * (0.5 + 0.2 * i) * (0.6 + 0.4 * ease_p))
            a = int(140 * (1 - i * 0.2) * ease_p)
            pygame.draw.circle(glow_surf, (GOLD_ACCENT.r, GOLD_ACCENT.g, GOLD_ACCENT.b, a), center, rr)

        # Vòng tròn chủ đạo rõ nét ở giữa
        main_circle_alpha = int(255 * ease_p)
        pygame.draw.circle(glow_surf, (GOLD_ACCENT.r, GOLD_ACCENT.g, GOLD_ACCENT.b, main_circle_alpha), center, int(base_radius * 0.95), width=6)

        screen.blit(glow_surf, (0, 0))

        # Vẽ ngôi sao ma pháp ở giữa vòng tròn (tạo điểm nhấn)
        star_outer = int(base_radius * 0.35 * ease_p) # Ngôi sao lớn dần
        star_inner = int(star_outer * 0.45) 
        _draw_star(screen, center, star_outer, star_inner, 5, (255, 255, 255), alpha=int(220 * ease_p))

        # một vài hạt sáng bắn ra (ít hơn nhưng sáng hơn)
        for k in range(20): # Tăng số lượng hạt sáng
            ang = (k / 12.0) * math.pi * 2 + (pygame.time.get_ticks() / 600.0)
            rr = int(base_radius * (0.55 + 0.25 * random.random()) * ease_p)
            sx = int(center[0] + rr * math.cos(ang))
            sy = int(center[1] + rr * math.sin(ang))
            sa = int(200 * (0.4 + 0.6 * random.random()) * ease_p)
            pygame.draw.circle(screen, (255, 255, 255, sa), (sx, sy), 3)

    # --- Stage 2: Summon pieces (using adjusted_progress) ---
    summon_pieces_start_p = 0.7 # relative to adjusted_progress
    if adjusted_progress >= summon_pieces_start_p:
        p = _clamp((adjusted_progress - summon_pieces_start_p) / (1.0 - summon_pieces_start_p))
        ease_p = _ease_in_out_quad(p)

        # Vẽ vòng tròn ma thuật cuối cùng với glow mạnh
        final_radius = int(min(board_rect.width, board_rect.height) * 0.32)
        final_s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for i in range(5):
            r_val = int(final_radius * (0.6 + 0.12 * i))
            a = int(120 * (1 - i * 0.15) * ease_p)
            pygame.draw.circle(final_s, (GOLD_ACCENT.r, GOLD_ACCENT.g, GOLD_ACCENT.b, a), center, r_val, width=2)
        screen.blit(final_s, (0, 0))

        # Triệu hồi từng quân cờ từ tâm vòng tròn
        board = game.board # noqa: F841

        # Prepare one beam surface for all beams this frame to avoid creating many surfaces.
        beam_surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

        # Increase delay multiplier so summons are more staggered and fewer pieces animate at once.
        delay_multiplier = 2.2 # This calculation is relative, so it's okay

        for r in range(DIMENSION):
            for c in range(DIMENSION):
                sq = chess.square(c, DIMENSION - 1 - r)
                piece = board.piece_at(sq)
                if not piece:
                    continue

                # vị trí ô (pixel)
                sq_center = (board_rect.x + c * sq_size + sq_size // 2, board_rect.y + r * sq_size + sq_size // 2)

                # delay dựa trên khoảng cách tới tâm (những ô gần tâm xuất hiện trước)
                dx = (sq_center[0] - center[0]) / board_rect.width
                dy = (sq_center[1] - center[1]) / board_rect.height
                dist = math.sqrt(dx * dx + dy * dy)
                # chuẩn hoá khoảng delay; multiplier làm cho tổng khoảng rộng hơn
                delay = _clamp(dist * delay_multiplier, 0.0, 0.85)

                local_p = _clamp((p - delay) / (1.0 - delay))
                visual_p = _ease_in_out_quad(local_p)
                if visual_p <= 0:
                    continue

                # Vẽ tia sáng từ tâm đến ô (vẽ lên beam_surf)
                beam_alpha = int(200 * visual_p * (1.0 - dist * 0.6))
                bx, by = sq_center
                pygame.draw.line(beam_surf, (255, 255, 255, beam_alpha), center, (bx, by), width=3)

                # Vẽ quân cờ scale + fade in
                try:
                    symbol = get_piece_symbol(piece)
                    if symbol in piece_images:
                        base_img = piece_images[symbol]
                    else:
                        base_img = None
                except Exception:
                    base_img = None

                # Optimization: for early spawn stages, draw a lightweight glow instead of scaling image.
                if base_img:
                    if visual_p < 0.6:
                        glow_r = int(sq_size * (0.1 + 0.7 * visual_p)) # Bắt đầu nhỏ hơn, lớn nhanh hơn
                        ga = int(200 * visual_p) # Glow sáng hơn
                        gs = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
                        pygame.draw.circle(gs, (255, 255, 255, ga), (glow_r + 1, glow_r + 1), glow_r)
                        screen.blit(gs, (sq_center[0] - glow_r - 1, sq_center[1] - glow_r - 1))
                    else:
                        # Near final stage: scale image (fewer will be scaled due to staggering)
                        scale = 0.4 + 0.7 * visual_p # Bắt đầu lớn hơn, tăng trưởng chậm hơn
                        size = max(1, int(sq_size * scale))
                        # Avoid scaling when almost full size
                        if size >= sq_size - 2:
                            img = base_img.copy()
                            img.set_alpha(int(255 * visual_p))
                        else:
                            img = pygame.transform.smoothscale(base_img, (size, size))
                            img.set_alpha(int(255 * visual_p))
                        pos = (sq_center[0] - img.get_width() // 2, sq_center[1] - img.get_height() // 2)
                        bounce = int(8 * (1 - (visual_p - 0.6) ** 2)) if visual_p < 1.0 else 0
                        screen.blit(img, (pos[0], pos[1] - int((1 - visual_p) * 12) - bounce))

        # Blit the single beam surface once
        screen.blit(beam_surf, (0, 0))

        # Bàn cờ mờ dần hiện ra phía sau các hiệu ứng nhưng bằng mặt nạ bán kính từ tâm
        board_surface = screen # Vẽ trực tiếp lên màn hình
        colors = [pygame.Color(238, 238, 210), pygame.Color(118, 150, 86)]

        # reveal radius grows with ease_board; cells outside radius get 0 alpha
        ease_board_val = _clamp((progress - 0.7) / 0.3)
        ease_board = _ease_in_out_quad(ease_board_val)
        reveal_radius = max(10, int(min(board_rect.width, board_rect.height) * 0.6 * ease_board)) # Tăng bán kính một chút

        for rr in range(DIMENSION):
            for cc in range(DIMENSION):
                cell_center = (board_rect.x + cc * sq_size + sq_size // 2, board_rect.y + rr * sq_size + sq_size // 2)
                dist_px = math.hypot(cell_center[0] - center[0], cell_center[1] - center[1])
                if dist_px > reveal_radius:
                    continue
                # alpha falls off with distance so rim reveals later
                cell_p = _clamp((1.0 - (dist_px / max(1, reveal_radius))) * ease_board)
                if cell_p <= 0.02:
                    continue
                color = colors[((rr + cc) % 2)]
                s = pygame.Surface((sq_size, sq_size), pygame.SRCALPHA)
                s.fill((color.r, color.g, color.b, int(255 * cell_p)))
                board_surface.blit(s, (board_rect.x + cc * sq_size, board_rect.y + rr * sq_size))

    # khi hoàn tất
    if progress >= 1.0:
        game.board_reveal_timer = 0

def draw_vs_transition(screen, game, timer):
    """Vẽ animation chuyển cảnh 'VS' theo phong cách triệu hồi đấu trường ma thuật."""
    screen_rect = screen.get_rect()
    duration = 70 # Nhanh hơn
    progress = 1.0 - (timer / duration)
    ease_p = _ease_in_out_quad(progress) # This ease_p is for the overall transition

    # --- Giai đoạn 1: Màn hình tối lại ---
    overlay_alpha = int(230 * ease_p)
    overlay = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
    overlay.fill((30, 25, 45, overlay_alpha)) # Nền mới
    screen.blit(overlay, (0, 0))

    rune_texture = drawing._get_cached_rune_texture(screen_rect.width, screen_rect.height)
    # Thêm nền họa tiết rune mờ ảo, chuyển động
    if rune_texture:
        scroll_y = (pygame.time.get_ticks() / 100) % rune_texture.get_height()
        rune_clone = rune_texture.copy()
        rune_clone.set_alpha(15) # Rất mờ
        screen.blit(rune_clone, (0, scroll_y))
        screen.blit(rune_clone, (0, scroll_y - rune_texture.get_height()))

    # --- Lấy thông tin và icon ---
    player_icon = drawing.ui_icons.get("icon_knight_white")
    bot_icon = drawing.ui_icons.get("icon_knight_black") # game ở đây là game_state
    bot_name = game.bot.style.get('name', 'The Challenger') # type: ignore
    bot_description = game.bot.style.get('description', '')

    # --- Giai đoạn 2: Tên và Mô tả hiện ra (0.3 - 0.9) ---
    avatar_p = _ease_out(_clamp((progress - 0.3) / 0.6), 3)
    if avatar_p > 0:
        # Tên
        player_name_text = MENU_FONT.render("PLAYER", True, WHITE_TEXT)
        bot_name_text = MENU_FONT.render(bot_name.upper(), True, WHITE_TEXT)
        player_name_text.set_alpha(255 * avatar_p)
        bot_name_text.set_alpha(255 * avatar_p)
        
        # Vẽ tên Player
        player_name_rect = player_name_text.get_rect(centerx=screen_rect.width * 0.25, centery=screen_rect.centery)
        screen.blit(player_name_text, player_name_rect)
        # Vẽ tên Bot
        bot_name_rect = bot_name_text.get_rect(centerx=screen_rect.width * 0.75, centery=screen_rect.centery - 20)
        screen.blit(bot_name_text, bot_name_rect)

        # Vẽ mô tả của Bot
        if bot_description:
            words = bot_description.split(' ')
            lines = []
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                if CARD_DESC_FONT.size(test_line)[0] < 250: # Giới hạn chiều rộng
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)
            
            for i, line in enumerate(lines):
                desc_text = CARD_DESC_FONT.render(line, True, (200, 200, 220))
                desc_text.set_alpha(200 * avatar_p)
                screen.blit(desc_text, desc_text.get_rect(centerx=screen_rect.width * 0.75, y=bot_name_rect.bottom + 5 + i * 20))

    # --- Giai đoạn 3: Ánh sáng hội tụ và bùng nổ (0.7 - 1.0) ---
    if progress > 0.7:
        gather_p = _clamp((progress - 0.7) / 0.3) # Progress for this stage
        gather_ease_p = _ease_in_out_quad(gather_p)

        # Ánh sáng hội tụ từ hai bên
        light_radius = 50 * gather_ease_p
        light_alpha = int(200 * gather_ease_p)
        
        # Từ Player
        player_light_pos = pygame.Vector2(screen_rect.width * 0.25, screen_rect.centery)
        current_player_light_pos = player_light_pos.lerp(screen_rect.center, gather_ease_p)
        pygame.draw.circle(screen, (ARCANE_GLOW.r, ARCANE_GLOW.g, ARCANE_GLOW.b, light_alpha), current_player_light_pos, light_radius) # type: ignore

        # Từ Bot
        bot_light_pos = pygame.Vector2(screen_rect.width * 0.75, screen_rect.centery)
        current_bot_light_pos = bot_light_pos.lerp(screen_rect.center, gather_ease_p)
        pygame.draw.circle(screen, (ERROR_RED.r, ERROR_RED.g, ERROR_RED.b, light_alpha), current_bot_light_pos, light_radius)

        # Hiệu ứng bùng nổ ánh sáng trắng khi đạt đỉnh
        if progress > 0.9: # Last 10% of the transition
            flash_p = _clamp((progress - 0.9) / 0.1) # Goes from 0 to 1 in the last 10%
            flash_alpha = int(255 * flash_p) # Fades to full white
            flash_surf = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, flash_alpha))
            screen.blit(flash_surf, (0, 0))

            # Rung màn hình nhẹ tại đỉnh điểm
            if flash_p > 0.5: # Only shake when flash is bright
                shake_offset = (random.randint(-5, 5), random.randint(-5, 5))
                screen.blit(screen, shake_offset)