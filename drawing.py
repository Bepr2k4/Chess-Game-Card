import pygame
import chess
from config import *
from bot import BotStyles
import random
from assets import get_piece_symbol
from card_animations.manager import get_animation_function
from ui_elements import draw_themed_button, draw_themed_card, draw_panel_bezel, blur_surface, draw_tooltip, wrap_text

import math

# --- CACHING FOR PERFORMANCE ---
_scaled_piece_cache = {} # Cache cho các ảnh quân cờ đã được scale
_scaled_background_cache = {} # Cache cho ảnh nền đã được scale
# Cache cho các hàm mới
_logo_cache = None

# Global cache for rune texture
_rune_texture_cache = {} # { (width, height): surface }

def _get_cached_rune_texture(panel_width, panel_height):
    global _rune_texture_cache
    cache_key = (panel_width, panel_height)
    if cache_key not in _rune_texture_cache:
        print(f"Cache arcane rune texture for size {cache_key}...") # noqa: T201
        texture_size = (panel_width, panel_height + 50) # +50 for scrolling
        rune_surf = pygame.Surface(texture_size, pygame.SRCALPHA)
        # Họa tiết cờ vua (Rook & Knight)
        chess_motifs = ["♜", "♞"]
        for _ in range(25):
            motif = random.choice(chess_motifs)
            font = pygame.font.SysFont('segoeuisymbol', random.randint(18, 30))
            motif_surf = font.render(motif, True, (ARCANE_GLOW.r, ARCANE_GLOW.g, ARCANE_GLOW.b, random.randint(15, 40)))
            rune_surf.blit(motif_surf, (random.randint(0, texture_size[0]), random.randint(0, texture_size[1])))
        # Rune hình học
        for _ in range(40):
            x, y, size, alpha = random.randint(0, texture_size[0]), random.randint(0, texture_size[1]), random.randint(2, 4), random.randint(20, 50)
            pygame.draw.rect(rune_surf, (ARCANE_GLOW.r, ARCANE_GLOW.g, ARCANE_GLOW.b, alpha), (x, y, size, size), 1)
        _rune_texture_cache[cache_key] = rune_surf
    return _rune_texture_cache[cache_key]

def draw_responsive_background(screen, raw_background_image):
    """
    Vẽ ảnh nền và scale nó cho vừa với màn hình.
    Sử dụng cache để tối ưu hiệu năng.
    """
    screen_size = screen.get_size()
    if screen_size not in _scaled_background_cache:
        print(f"Cache background for size {screen_size}...")
        if not raw_background_image: # Nếu không có ảnh, cache một màu nền
            surf = pygame.Surface(screen_size)
            surf.fill(GAME_BG)
            _scaled_background_cache[screen_size] = surf
            return
        _scaled_background_cache[screen_size] = pygame.transform.smoothscale(raw_background_image, screen_size)
    
    screen.blit(_scaled_background_cache[screen_size], (0, 0))

# --- State cho Animation chung cho các panel ---
_panel_anim_time = 0.0
_current_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2) # Vị trí hiện tại của panel (dùng cho hiệu ứng float)
_target_panel_pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2) # Vị trí mục tiêu của panel (dùng cho hiệu ứng float)
_menu_entry_anim_progress = 0.0 # Tiến độ animation khi panel mới xuất hiện (scale-in)
_light_sweep_timer = 0.0 # Bộ đếm thời gian cho hiệu ứng quét sáng
_light_sweep_active = False # Cờ hiệu cho biết hiệu ứng quét sáng đang hoạt động

def get_transformed_mouse_pos(game_state):
    """
    Trả về vị trí chuột hiện tại đã được biến đổi sang tọa độ virtual screen.
    Dùng cho các hiệu ứng hover.
    """
    mouse_pos_actual = pygame.mouse.get_pos()
    return ((mouse_pos_actual[0] - game_state.mouse_offset[0]) / game_state.mouse_scale,
            (mouse_pos_actual[1] - game_state.mouse_offset[1]) / game_state.mouse_scale)

def draw_board(screen):
    """Vẽ các ô vuông của bàn cờ."""
    # Thêm bóng đổ cho bàn cờ để tạo cảm giác "nổi"
    board_shadow_rect = get_board_rect().move(8, 8)
    shadow_surf = pygame.Surface(board_shadow_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0,0,0, 100), shadow_surf.get_rect(), border_radius=15)
    screen.blit(blur_surface(shadow_surf, 8), board_shadow_rect)
    board_rect = get_board_rect()
    sq_size = get_sq_size(board_rect)
    # Đổi màu bàn cờ thành trắng và xanh lá cây cổ điển
    colors = [pygame.Color(238, 238, 210), pygame.Color(118, 150, 86)]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            # Tính toán lại rect để khớp tuyệt đối với BOARD_RECT
            pygame.draw.rect(screen, color, (board_rect.x + c * sq_size, board_rect.y + r * sq_size, sq_size, sq_size))

def draw_pieces(screen, game, piece_images):
    """Vẽ các quân cờ lên bàn cờ."""
    board = game.board # game ở đây là game_state
    player_color = game.player_color
    board_rect = get_board_rect()
    sq_size = get_sq_size(board_rect)

    # Kiểm tra xem cache có cần được làm mới không (khi sq_size thay đổi)
    if not _scaled_piece_cache or _scaled_piece_cache.get('size') != sq_size:
        _scaled_piece_cache.clear()
        _scaled_piece_cache['size'] = sq_size
        for symbol, img in piece_images.items():
            _scaled_piece_cache[symbol] = pygame.transform.smoothscale(img, (sq_size, sq_size))


    for r in range(DIMENSION):
        for c in range(DIMENSION):
            # Lật bàn cờ nếu người chơi là quân Đen
            if player_color == chess.WHITE:
                square = chess.square(c, 7 - r)
                draw_pos = (board_rect.x + c * sq_size, board_rect.y + r * sq_size)
            else: # player is Black
                square = chess.square(7 - c, r)
                draw_pos = (board_rect.x + c * sq_size, board_rect.y + r * sq_size)

            # Nếu một quân cờ đang trong quá trình animation, không vẽ nó ở ô bắt đầu
            if game.animation and square == game.animation['move'].from_square:
                continue

            # Nếu animation "Kỵ Sĩ Đoàn" đang chạy, không vẽ các quân cờ ở các ô liên quan
            # SỬA LỖI: Kiểm tra an toàn, vì không phải vfx nào cũng có key 'card'
            is_knight_legion_vfx = any(vfx.get('card', {}).get('id') == 'knight_legion' for vfx in game.vfx_queue)

            if is_knight_legion_vfx:
                # SỬA LỖI: Chỉ ẩn quân Tốt, không ẩn quân Mã sau khi đã biến hình
                piece_at_square = board.piece_at(square)
                if game.player_color == chess.WHITE:
                    hidden_square = chess.E2
                else: # Người chơi là quân Đen
                    hidden_square = chess.E7
                if square == hidden_square and piece_at_square and piece_at_square.piece_type == chess.PAWN:
                    continue

            # Nếu đang trong animation board_reveal, không vẽ quân cờ
            # CHỈ khi hiệu ứng "giáng thế" đang diễn ra.
            # Sửa lỗi: Chỉ không vẽ khi bàn cờ đang "nở" ra
            reveal_progress = 1.0 - (game.board_reveal_timer / 120) if hasattr(game, 'board_reveal_timer') and game.board_reveal_timer > 0 else 1.0
            if reveal_progress < 0.8: # Không vẽ quân cờ cho đến khi giai đoạn "hiện hình" bắt đầu
                continue

            piece = board.piece_at(square)
            if piece:
                piece_symbol = get_piece_symbol(piece)
                if piece_symbol in _scaled_piece_cache:
                    # --- VẼ HIỆU ỨNG KHIÊN PHÉP ---
                    if square in game.shielded_pieces:
                        shield_radius = sq_size * 0.55
                        # Hiệu ứng "thở" nhẹ
                        pulse = math.sin(pygame.time.get_ticks() * 0.005) * 3
                        current_radius = shield_radius + pulse
                        # Vẽ một vòng tròn mờ ảo bao quanh quân cờ
                        shield_surf = pygame.Surface((current_radius * 2, current_radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(shield_surf, (173, 216, 230, 90), (current_radius, current_radius), current_radius)
                        screen.blit(shield_surf, (draw_pos[0] + sq_size/2 - current_radius, draw_pos[1] + sq_size/2 - current_radius))

                    screen.blit(_scaled_piece_cache[piece_symbol], pygame.Rect(draw_pos[0], draw_pos[1], sq_size, sq_size))

def draw_highlights(screen, game, selected_square):
    """Vẽ các ô được highlight (ô đang chọn và các nước đi hợp lệ)."""
    if selected_square is not None:
        board_rect = get_board_rect()
        sq_size = get_sq_size(board_rect)
        r, c = selected_square
        
        # Chuyển đổi tọa độ logic sang tọa độ vẽ, có xét đến việc lật bàn cờ
        draw_r, draw_c = r, c
        if game.player_color == chess.BLACK:
            draw_r, draw_c = 7 - r, 7 - c

        s = pygame.Surface((sq_size, sq_size), pygame.SRCALPHA) # noqa: F841
        s.fill((255, 255, 0, 100))  # Màu vàng trong suốt
        screen.blit(s, (board_rect.x + draw_c * sq_size, board_rect.y + draw_r * sq_size))

        # from_sq sử dụng tọa độ logic (r, c) không bị ảnh hưởng bởi việc lật bàn cờ # game ở đây là game_state
        board = game.board
        from_sq = chess.square(c, 7 - r)
        for move in board.legal_moves:
            if move.from_square == from_sq:
                # Lấy tọa độ logic của ô đến
                to_r, to_c = 7 - chess.square_rank(move.to_square), chess.square_file(move.to_square)
                
                # Chuyển đổi sang tọa độ vẽ
                draw_to_r, draw_to_c = to_r, to_c
                if game.player_color == chess.BLACK:
                    draw_to_r, draw_to_c = 7 - to_r, 7 - to_c

                center_x, center_y = board_rect.x + draw_to_c * sq_size + sq_size // 2, board_rect.y + draw_to_r * sq_size + sq_size // 2
                
                # Vẽ chấm tròn cho nước đi thường, vòng tròn cho nước ăn quân
                if board.is_capture(move):
                    pygame.draw.circle(screen, (0, 0, 0, 70), (center_x, center_y), sq_size // 2, width=4)
                else:
                    pygame.draw.circle(screen, (0, 0, 0, 70), (center_x, center_y), sq_size // 6)

def draw_game_state(screen, game, selected_square, piece_images, card_images):
    """Điều phối việc vẽ toàn bộ trạng thái màn hình chơi game theo đúng thứ tự."""
    screen.fill(GAME_BG)

    # SỬA LỖI: Thay đổi thứ tự vẽ. Vẽ trap slot TRƯỚC khi vẽ notification
    # để notification không vẽ đè lên.
    trap_slot_rects = draw_trap_slots(screen, game, card_images)
    draw_notifications(screen, game)
    draw_board(screen)
    draw_highlights(screen, game, selected_square)
    draw_pieces(screen, game, piece_images)
    mouse_pos_virtual = get_transformed_mouse_pos(game) # game ở đây là game_state
    draw_sidebar(screen, game, card_images, mouse_pos_virtual)
    card_rects = draw_bottom_panel(screen, game, card_images, mouse_pos_virtual)

    return card_rects, trap_slot_rects

def draw_trap_slots(screen, game, card_images):
    """Vẽ các ô chứa thẻ Bẫy đã trang bị ở nửa dưới panel thông báo."""
    notification_rect = get_notification_rect()
    # SỬA LỖI: Vẽ khung viền cho nửa dưới của panel
    trap_panel_rect = pygame.Rect(notification_rect.x, notification_rect.centery, notification_rect.width, notification_rect.height / 2)
    draw_panel_bezel(screen, trap_panel_rect)

    trap_area_rect = trap_panel_rect.inflate(-20, -20)
    # Vẽ tiêu đề cho khu vực bẫy
    title_text = INFO_FONT.render("Thẻ Bẫy", True, WHITE_TEXT)
    screen.blit(title_text, title_text.get_rect(centerx=trap_area_rect.centerx, y=trap_area_rect.y + 15))

    slot_rects = []
    card_height = 140
    card_width = int(card_height * (5/7))
    
    # Lấy các thẻ trap từ danh sách thẻ của người chơi
    traps_to_display = [card for card in game.player_cards if card.get("type") == "trap"]

    for i in range(2): # Luôn vẽ 2 ô
        slot_x = trap_area_rect.centerx - card_width - 10 if i == 0 else trap_area_rect.centerx + 10
        slot_y = trap_area_rect.y + 60
        rect = pygame.Rect(slot_x, slot_y, card_width, card_height)
        
        if i < len(traps_to_display):
            card = traps_to_display[i]
            draw_themed_card(screen, rect, card, rect.collidepoint(pygame.mouse.get_pos()), card_images)
            slot_rects.append((rect, card))
        else:
            pygame.draw.rect(screen, (40, 45, 55, 150), rect, border_radius=12)
            pygame.draw.rect(screen, (80, 90, 110, 200), rect, width=1, border_radius=12)
    return slot_rects

def draw_sidebar(screen, game, card_images, mouse_pos_virtual):
    """Vẽ sidebar với các Panel con cho Boss và Stats."""
    sidebar_rect = get_sidebar_rect()
    draw_panel_bezel(screen, sidebar_rect)

    bot_panel_rect = pygame.Rect(sidebar_rect.x, sidebar_rect.y, sidebar_rect.width, sidebar_rect.height * 0.7)
    stats_panel_rect = pygame.Rect(sidebar_rect.x, bot_panel_rect.bottom, sidebar_rect.width, sidebar_rect.height * 0.3)
    
    # SỬA LỖI: Xử lý trường hợp style là một chuỗi
    bot_style = game.bot.style # game ở đây là game_state
    if isinstance(bot_style, str):
        bot_style = BotStyles.get(bot_style, BotStyles["balanced"])

    boss_name = bot_style.get('name', 'The Challenger')
    boss_name_text = MENU_FONT.render(boss_name, True, GOLD_ACCENT)
    screen.blit(boss_name_text, boss_name_text.get_rect(centerx=bot_panel_rect.centerx, y=bot_panel_rect.y + bot_panel_rect.height * 0.05)) # type: ignore

    bot_avatar_pos = (bot_panel_rect.centerx, bot_panel_rect.centery + 40)
    draw_bot_emotion(screen, game.bot_emotion, bot_avatar_pos)

    if 'ui_icons' in globals() and ui_icons.get('icon_coin_bag'):
        # --- Khu vực chỉ số người chơi ---
        player_stats_y_start = stats_panel_rect.y + 20
        icon_size = 28
        line_height = 40
        
        # Vàng
        gold_icon = pygame.transform.smoothscale(ui_icons['icon_coin_bag'], (icon_size, icon_size)) # type: ignore
        screen.blit(gold_icon, (stats_panel_rect.x + 20, player_stats_y_start))
        gold_text = INFO_FONT.render(str(game.player_gold), True, GOLD_ACCENT) # type: ignore # game ở đây là game_state
        screen.blit(gold_text, (stats_panel_rect.x + 20 + icon_size + 10, player_stats_y_start + 2))
        
        # Tầng (hiển thị dạng chữ, không dùng icon)
        stage_text = INFO_FONT.render(f"Tầng: {game.stage}", True, WHITE_TEXT) # type: ignore # game ở đây là game_state
        screen.blit(stage_text, (stats_panel_rect.x + 20, player_stats_y_start + line_height))

def draw_bottom_panel(screen, game, card_images, mouse_pos_virtual):
    """Vẽ dải thẻ bài trong UI_INVENTORY, với hiệu ứng hover."""
    board_rect = get_board_rect()
    bottom_panel_rect = get_bottom_panel_rect(board_rect)
    panel_color = (20, 24, 30)
    pygame.draw.rect(screen, panel_color, bottom_panel_rect, border_radius=10)
    line_color = (80, 90, 110)
    pygame.draw.line(screen, line_color, bottom_panel_rect.topleft, bottom_panel_rect.topright, 2)

    card_rects = []
    # SỬA LỖI: Chỉ vẽ các thẻ không phải là trap
    cards = [card for card in game.player_cards if card.get("type") != "trap"] # game ở đây là game_state
    if not cards: return card_rects

    card_height = bottom_panel_rect.height * 0.85 # Giảm kích thước thẻ một chút
    card_width = int(card_height * (5 / 7))
    padding = 20
    total_width = (card_width * len(cards)) + (padding * (len(cards) - 1))
    start_x = bottom_panel_rect.centerx - total_width / 2 # type: ignore
    base_y = bottom_panel_rect.centery - card_height / 2 # Tọa độ Y cơ bản

    for i, card in enumerate(cards):
        card_x = start_x + i * (card_width + padding)
        card_y = base_y
        
        original_card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        is_hovered = original_card_rect.collidepoint(mouse_pos_virtual)
        
        # SỬA LỖI: Hiệu ứng hover mới
        final_card_rect = original_card_rect.copy()
        if is_hovered:
            # Phóng to và nhích lên
            final_card_rect = original_card_rect.inflate(original_card_rect.width * 0.1, original_card_rect.height * 0.1)
            final_card_rect.centery = original_card_rect.centery - 20

        # Vẽ hiệu ứng 'Glow' và 'Shadow' TRƯỚC khi vẽ thẻ bài
        if is_hovered:
            # Đổ bóng
            shadow_rect = final_card_rect.move(4, 6)
            shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 100), shadow_surf.get_rect(), border_radius=15)
            screen.blit(blur_surface(shadow_surf, 4), shadow_rect)
            # Hào quang
            glow_rect = final_card_rect.inflate(15, 15)
            glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (GOLD_ACCENT.r, GOLD_ACCENT.g, GOLD_ACCENT.b, 120), glow_surf.get_rect(), border_radius=18)
            screen.blit(blur_surface(glow_surf, 5), glow_rect)

        card_rects.append((final_card_rect, card))
        draw_themed_card(screen, final_card_rect, card, is_hovered, card_images) # type: ignore

    return card_rects

def get_hovered_card(card_rects, mouse_pos):
    """Xác định thẻ nào đang được di chuột qua từ danh sách rects."""
    for rect, card in reversed(card_rects): # Lặp ngược để ưu tiên thẻ trên cùng
        if rect.collidepoint(mouse_pos):
            return card
    return None

# Cache cho các thông báo đã được xử lý xuống dòng
_notification_cache = {}

def draw_notifications(screen, game):
    """Vẽ một khu vực nhật ký thông báo trong UI."""
    # SỬA LỖI: Chỉ vẽ khung cho nửa trên của panel
    notification_rect = get_notification_rect()
    top_half_rect = pygame.Rect(notification_rect.x, notification_rect.y, notification_rect.width, notification_rect.height / 2)
    draw_panel_bezel(screen, top_half_rect)
    
    log_box_rect = top_half_rect.inflate(-20, -20)
    y_offset = log_box_rect.y + 10

    # Bảng màu cho các loại thông báo
    notification_colors = {
        "default": WHITE_TEXT, # type: ignore
        "info": WHITE_TEXT, # type: ignore
        "shop": SUCCESS_GREEN, # type: ignore
        "card_activation": GOLD_ACCENT, # type: ignore
        "boss": ERROR_RED, # type: ignore
        "error": ERROR_RED, # type: ignore
        "game_event": GOLD_ACCENT, # type: ignore
    }

    # SỬA LỖI HIỆU NĂNG: Chỉ xử lý lại text khi danh sách thông báo thay đổi.
    # Tạo một "chữ ký" cho danh sách thông báo hiện tại.
    notification_signature = "".join([n['message'] for n in game.notifications]) # game ở đây là game_state
    
    if notification_signature not in _notification_cache:
        processed_notifications = []
        for i, notif_data in enumerate(game.notifications):
            message = notif_data["message"]
            notif_type = notif_data["type"]

            if i == 0:
                font = INFO_FONT
            else:
                font = CARD_DESC_FONT
            
            lines = wrap_text(f"- {message}", font, log_box_rect.width - 20)
            processed_notifications.append({'lines': lines, 'type': notif_type, 'index': i})
        _notification_cache[notification_signature] = processed_notifications
    
    processed_notifications = _notification_cache[notification_signature]

    for notif in processed_notifications:
        if y_offset > log_box_rect.bottom - 20:
            break # Dừng lại nếu không còn đủ chỗ

        i = notif['index']
        notif_type = notif['type']

        # Dòng mới nhất màu trắng sáng, các dòng cũ mờ dần
        if i == 0:
            font = INFO_FONT
            color = notification_colors.get(notif_type, WHITE_TEXT) # type: ignore
        else:
            font = CARD_DESC_FONT
            t = min(1.0, i / 8.0) # SỬA LỖI: Mờ dần chậm hơn (trong 8 dòng)
            base_color = notification_colors.get(notif_type, WHITE_TEXT) # type: ignore
            color = base_color.lerp(pygame.Color(80, 80, 80), t) # Xám đậm hơn
        
        # Vẽ các dòng đã được tách
        for line in notif['lines']:
            text_surf = font.render(line, True, color) # Sử dụng font hiện tại
            screen.blit(text_surf, (log_box_rect.x + 10, y_offset))
            y_offset += text_surf.get_height() + 2 # Giảm khoảng cách giữa các dòng

def _draw_bouncing_info(screen, label_surf, value_surf, line_rect, scale):
    """Hàm helper để vẽ một dòng thông tin với hiệu ứng nảy."""
    # Scale label
    scaled_label = pygame.transform.smoothscale(label_surf, (int(label_surf.get_width() * scale), int(label_surf.get_height() * scale)))
    label_rect = scaled_label.get_rect(centery=line_rect.centery, left=line_rect.left + 50)
    screen.blit(scaled_label, label_rect)

    # Scale value
    scaled_value = pygame.transform.smoothscale(value_surf, (int(value_surf.get_width() * scale), int(value_surf.get_height() * scale)))
    value_rect = scaled_value.get_rect(centery=line_rect.centery, right=line_rect.right - 50)
    screen.blit(scaled_value, value_rect)


def draw_seed_input_box(screen, user_text):
    """Vẽ hộp thoại để người chơi nhập seed."""
    screen_size = screen.get_size()

    # Hộp thoại
    # Sửa lỗi: Tính toán kích thước và vị trí một cách linh động
    box_width, box_height = min(600, screen_size[0] * 0.8), min(300, screen_size[1] * 0.6)
    box_rect = pygame.Rect(0, 0, box_width, box_height)
    box_rect.center = screen.get_rect().center
    pygame.draw.rect(screen, FANTASY_DARK_BG, box_rect, border_radius=15)
    pygame.draw.rect(screen, METALLIC_TRIM, box_rect, width=2, border_radius=15)

    # Tiêu đề
    title_text = MENU_FONT.render("NHẬP SEED", True, WHITE_TEXT) # type: ignore
    screen.blit(title_text, title_text.get_rect(centerx=box_rect.centerx, y=box_rect.y + 30))

    # Trường nhập liệu
    input_rect = pygame.Rect(box_rect.centerx - 200, box_rect.centery - 25, 400, 50)
    pygame.draw.rect(screen, METALLIC_TRIM, input_rect, border_radius=8)
    pygame.draw.rect(screen, FANTASY_DARK_BG, input_rect.inflate(-4, -4), border_radius=6)
    text_surface = INFO_FONT.render(user_text, True, WHITE_TEXT) # type: ignore
    screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))

    # Nút bấm
    confirm_button = pygame.Rect(box_rect.centerx - 160, box_rect.bottom - 80, 150, 50)
    back_button = pygame.Rect(box_rect.centerx + 10, box_rect.bottom - 80, 150, 50)
    draw_themed_button(screen, confirm_button, "Xác nhận", ARCANE_GLOW, ROYAL_PURPLE_DARK, confirm_button.collidepoint(pygame.mouse.get_pos())) # type: ignore
    draw_themed_button(screen, back_button, "Quay lại", pygame.Color(80,80,80), ROYAL_PURPLE_DARK, back_button.collidepoint(pygame.mouse.get_pos())) # type: ignore

    return confirm_button, back_button
# -------------------------------------------------------------
# CÁC HÀM KHÔI PHỤC (RESTORED FUNCTIONS)
# -------------------------------------------------------------

# -------------------------------------------------------------
# CÁC HÀM VẼ MENU MỚI (THEO YÊU CẦU)
# -------------------------------------------------------------

def draw_balatro_filter(screen):
    screen_width, screen_height = screen.get_size()
    filter_surf = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)

    # Chỉ giữ lại hiệu ứng Scanline rất nhẹ
    for y in range(0, screen_height, 3):
        pygame.draw.line(filter_surf, (0, 0, 0, random.randint(3, 6)), (0, y), (screen_width, y), 1) # Opacity cực nhẹ

    screen.blit(filter_surf, (0, 0))

def draw_fantasy_menu_logo(screen, dt):
    """
    Vẽ logo theo phong cách fantasy, sử dụng font hiện có nhưng với hiệu ứng mới.
    Sử dụng cache để tối ưu hiệu năng.
    """
    global _logo_cache, _cached_logo_rect, _panel_anim_time
    screen_width, screen_height = screen.get_size()
    # Animation "thở" nhẹ cho logo
    scale_factor = 1.0 + math.sin(_panel_anim_time * 1.5) * 0.01 # Co giãn 1%

    if _logo_cache is None:
        print("Cache Logo Menu…") # noqa: T201
        text_surf = MENU_FONT.render("CHESS ROGUE", True, WHITE_TEXT) # type: ignore
        base = pygame.Surface(text_surf.get_rect().inflate(30, 30).size, pygame.SRCALPHA)
        center_x, center_y = base.get_rect().center

        # 1. Stroke/Outline (Vẽ viền đen dày hơn)
        outline_surf = MENU_FONT.render("CHESS ROGUE", True, (0, 0, 0))
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]:
             base.blit(outline_surf, outline_surf.get_rect(center=(center_x + dx, center_y + dy)))

        # 2. Glow (Vẽ hào quang)
        glow = MENU_FONT.render("CHESS ROGUE", True, ARCANE_GLOW) # type: ignore
        glow.set_alpha(150)
        glow_blurred = blur_surface(glow, 2)
        base.blit(glow_blurred, glow_blurred.get_rect(center=base.get_rect().center))

        # 3. Main Text (Vẽ chữ chính)
        base.blit(text_surf, text_surf.get_rect(center=base.get_rect().center))

        # Slight rotation
        _logo_cache = pygame.transform.rotate(base, 3)
        _cached_logo_rect = _logo_cache.get_rect()

    # Áp dụng animation co giãn
    scaled_size = (_cached_logo_rect.width * scale_factor, _cached_logo_rect.height * scale_factor)
    scaled_logo = pygame.transform.smoothscale(_logo_cache, scaled_size)
    logo_display_rect = scaled_logo.get_rect(centerx=screen_width // 2, y=120)

    screen.blit(scaled_logo, logo_display_rect)

def draw_fantasy_menu_panel(screen, dt):
    menu_panel_rect = get_menu_panel_rect(screen.get_width(), screen.get_height())
    return _draw_animated_panel(screen, dt, menu_panel_rect.size, 80) # Original offset

def draw_run_setup_panel(screen, dt):
    """Vẽ panel cho màn hình Run Setup với kích thước cố định và căn giữa."""
    # SỬA LỖI: Sử dụng kích thước cố định để khóa cứng layout.
    panel_size = (800, 550)
    return _draw_animated_panel(screen, dt, panel_size, 0)

def _draw_animated_panel(screen, dt, panel_size, panel_center_offset_y):
    """Vẽ một panel nổi theo phong cách dark fantasy với viền kim loại, hiệu ứng kính mờ và rune ma thuật, có animation."""
    global _panel_anim_time, _current_panel_pos, _target_panel_pos, _menu_entry_anim_progress, _light_sweep_timer, _light_sweep_active

    screen_width, screen_height = screen.get_size()
    _panel_anim_time += dt

    # --- Animation "Soft Float" ---
    sway_x = math.sin(_panel_anim_time * 0.15) * 3 # Tần số thấp, biên độ nhỏ
    sway_y = math.cos(_panel_anim_time * 0.2) * 2  # Tần số và biên độ khác nhau để tạo quỹ đạo phức tạp hơn
    _target_panel_pos = pygame.Vector2(screen_width // 2 + sway_x, screen_height // 2 + panel_center_offset_y + sway_y)

    lerp_speed = 2.0
    _current_panel_pos.x += (_target_panel_pos.x - _current_panel_pos.x) * lerp_speed * dt
    _current_panel_pos.y += (_target_panel_pos.y - _current_panel_pos.y) * lerp_speed * dt
    
    panel_rect = pygame.Rect(0, 0, panel_size[0], panel_size[1])
    panel_rect.center = _current_panel_pos # Gán vị trí đã được làm mượt

    # --- Animation "Scale-in" khi mới xuất hiện ---
    if _menu_entry_anim_progress < 1.0:
        _menu_entry_anim_progress = min(1.0, _menu_entry_anim_progress + dt * 2.0) # Tốc độ animation
        eased_p = 1 - (1 - _menu_entry_anim_progress) ** 3 # Ease-out
        current_scale = 1.02 - (0.02 * eased_p)
    else:
        # Animation "thở" nhẹ sau khi đã xuất hiện
        current_scale = 1.0 + math.sin(_panel_anim_time * 1.2) * 0.005 # Co giãn 0.5%

    scaled_size = (int(panel_rect.width * current_scale), int(panel_rect.height * current_scale))

    # --- Hiệu ứng "Glow Pulse" ---
    pulse_alpha = 40 + math.sin(_panel_anim_time * 0.5) * 25 # Alpha dao động chậm từ 15 đến 65
    glow_surf = pygame.Surface(scaled_size, pygame.SRCALPHA)
    pygame.draw.rect(glow_surf, (ARCANE_GLOW.r, ARCANE_GLOW.g, ARCANE_GLOW.b, pulse_alpha), glow_surf.get_rect(), border_radius=25)
    screen.blit(blur_surface(glow_surf, 5), panel_rect.center - pygame.Vector2(glow_surf.get_size()) / 2)

    # Đổ bóng mềm, có chiều sâu
    shadow_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (0, 0, 0, 100), shadow_surf.get_rect(), border_radius=25)
    screen.blit(blur_surface(shadow_surf, 8), panel_rect.move(10, 15))

    # Surface chính của panel
    panel_surf = pygame.Surface(scaled_size, pygame.SRCALPHA)

    # Nền kính mờ tối màu
    # SỬA LỖI: Dùng draw.rect thay vì fill để có thể bo góc cho cả nền
    pygame.draw.rect(panel_surf, (FANTASY_DARK_BG.r, FANTASY_DARK_BG.g, FANTASY_DARK_BG.b, 200), panel_surf.get_rect(), border_radius=22)

    # Hiệu ứng rune ma thuật (cache)
    # SỬA LỖI: Cache texture dựa trên kích thước gốc của panel, không phải kích thước đã scale.
    # Điều này ngăn việc tạo lại texture mỗi frame và loại bỏ hiện tượng giật, lag.
    current_rune_texture = _get_cached_rune_texture(panel_size[0], panel_size[1])
    
    # Rune di chuyển chậm
    scroll_y = (_panel_anim_time * 15) % current_rune_texture.get_height()
    panel_surf.blit(current_rune_texture, (0, scroll_y))
    panel_surf.blit(current_rune_texture, (0, scroll_y - current_rune_texture.get_height()))

    # Viền kim loại (metallic trim)
    pygame.draw.rect(panel_surf, METALLIC_TRIM, panel_surf.get_rect(), width=3, border_radius=22) # type: ignore
    pygame.draw.rect(panel_surf, METALLIC_HIGHLIGHT, panel_surf.get_rect().inflate(-3, -3), width=1, border_radius=20)

    # --- Hiệu ứng "Arcane Light Sweep" ---
    _light_sweep_timer -= dt
    if _light_sweep_timer <= 0 and not _light_sweep_active:
        _light_sweep_active = True
        _light_sweep_timer = 1.0 # Thời gian hiệu ứng diễn ra
    
    if _light_sweep_active:
        sweep_p = 1.0 - _light_sweep_timer
        sheen_width = 80
        sheen_x = -sheen_width + sweep_p * (panel_surf.get_width() + sheen_width * 2)
        
        # Vẽ vệt sáng lên panel_surf, nó sẽ tự động được cắt cúp
        pygame.draw.line(panel_surf, (255, 255, 255, 30), (sheen_x, 0), (sheen_x - sheen_width, panel_surf.get_height()), 8)
        if _light_sweep_timer <= 0:
            _light_sweep_active = False
            _light_sweep_timer = random.uniform(8.0, 10.0) # Reset bộ đếm

    display_rect = panel_surf.get_rect(center=panel_rect.center) # noqa: F841
    screen.blit(panel_surf, display_rect)
    return display_rect

def draw_disabled_fantasy_menu_button(screen, rect, text, icon):
    """Vẽ một phiên bản bị vô hiệu hóa (màu xám) của nút bấm fantasy."""
    button_rect = rect.copy()
    
    # Màu xám cho trạng thái vô hiệu hóa
    disabled_color = pygame.Color(40, 45, 55)
    disabled_trim = pygame.Color(60, 65, 75)
    disabled_text_color = pygame.Color(100, 110, 120)

    # Đổ bóng
    shadow_rect = button_rect.move(4, 6)
    pygame.draw.rect(screen, (0, 0, 0, 120), shadow_rect, border_radius=16)

    # Nền nút
    pygame.draw.rect(screen, disabled_color, button_rect, border_radius=14)

    # Viền
    pygame.draw.rect(screen, disabled_trim, button_rect, width=2, border_radius=14)

    # Text và Icon
    label = INFO_FONT.render(text, True, disabled_text_color) # type: ignore
    
    if icon:
        icon_copy = icon.copy()
        icon_copy.fill(disabled_text_color, special_flags=pygame.BLEND_RGB_MULT)
        icon_size = button_rect.height - 28
        scaled_icon = pygame.transform.smoothscale(icon_copy, (icon_size, icon_size))
        icon_rect = scaled_icon.get_rect(centery=button_rect.centery, left=button_rect.left + 20)
        lrect = label.get_rect(centery=button_rect.centery, left=icon_rect.right + 15)
        screen.blit(scaled_icon, icon_rect)
    else:
        lrect = label.get_rect(center=button_rect.center)

    screen.blit(label, lrect)
# -------------------------------------------------------------
# CÁC HÀM CŨ (GIỮ LẠI)
# -------------------------------------------------------------

def draw_vfx(screen, game, card_images, piece_images):
    """Vẽ các hiệu ứng hình ảnh trong hàng đợi."""
    # SỬA LỖI: Import ở đây để tránh circular import
    # SỬA LỖI: Tạo một bản sao để lặp qua, vì chúng ta sẽ xóa phần tử khỏi list gốc.
    # Điều này cũng đảm bảo timer được giảm một cách nhất quán.
    for vfx in list(game.vfx_queue):
        vfx['timer'] -= 1
    active_vfx = []
    for vfx in game.vfx_queue:
        if vfx['type'] == 'card_activation':
            # SỬA LỖI: Logic lấy animation đã được chuyển vào đây
            animation_key = vfx.get('type') or vfx.get('card', {}).get('id')
            animation_func = get_animation_function(animation_key)
            if animation_func:
                # Trường hợp đặc biệt cho các thẻ không có animation riêng
                if animation_func == get_animation_function('card_activation'):
                     get_animation_function('card_activation')(screen, vfx, card_images, piece_images)

            # --- LOGIC ANIMATION CHO GƯƠNG PHẢN CHIẾU ---
            if vfx['card']['id'] == 'mirror_revive':
                progress = 1.0 - (vfx['timer'] / vfx['initial_timer'])
                game_state = vfx['game']
                # Lấy tọa độ pixel từ tọa độ ô cờ, sử dụng layout cố định
                board_rect = get_board_rect()
                sq_size = get_sq_size(board_rect)
                
                def get_draw_pos(square):
                    r, c = 7 - chess.square_rank(square), chess.square_file(square)
                    if game_state.player_color == chess.BLACK:
                        r, c = 7 - r, 7 - c
                    return pygame.Vector2(board_rect.x + c * sq_size + sq_size // 2, board_rect.y + r * sq_size + sq_size // 2)

                start_pos = get_draw_pos(vfx['start_pos_sq'])
                end_pos = get_draw_pos(vfx['end_pos_sq'])

                # Giai đoạn 1: Gương vỡ (0.0 -> 0.4)
                if progress < 0.4:
                    p = progress / 0.4
                    if 'shards' not in vfx:
                        vfx['shards'] = []
                        for _ in range(20):
                            angle = random.uniform(0, math.tau)
                            speed = random.uniform(80, 150)
                            vfx['shards'].append({
                                'pos': start_pos.copy(),
                                'vel': pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                                'size': random.randint(4, 10)
                            })
                    for shard in vfx['shards']:
                        shard['pos'] += shard['vel'] * game_state.dt
                        alpha = 255 * (1 - p)
                        pygame.draw.rect(screen, (200, 220, 255, alpha), (shard['pos'].x, shard['pos'].y, shard['size'], shard['size']))

                # Giai đoạn 2: Mảnh vỡ hội tụ (0.2 -> 0.7)
                if 0.2 < progress < 0.7:
                    p = (progress - 0.2) / 0.5
                    eased_p = 1 - (1 - p) ** 2
                    for shard in vfx.get('shards', []):
                        current_pos = shard['pos'].lerp(end_pos, eased_p)
                        pygame.draw.line(screen, (180, 200, 255, 150), end_pos, current_pos, 2)

                # Giai đoạn 3: Hồi sinh (0.6 -> 1.0)
                if progress > 0.6:
                    p = (progress - 0.6) / 0.4
                    eased_p = 1 - (1 - p) ** 4
                    # Cột sáng
                    radius = sq_size * 0.8 * eased_p
                    height = sq_size * 2 * eased_p
                    light_rect = pygame.Rect(end_pos.x - radius, end_pos.y - height / 2, radius * 2, height)
                    alpha = 200 * (1 - p)
                    pygame.draw.ellipse(screen, (220, 230, 255, alpha), light_rect)

            # --- LOGIC ANIMATION CHO KỴ SĨ ĐOÀN ---
            elif vfx['card']['id'] == 'knight_legion':
                # Gọi trực tiếp hàm vẽ của Kỵ Sĩ Đoàn
                get_animation_function('knight_legion')(screen, vfx, card_images, piece_images)

            # --- LOGIC ANIMATION CHO BẪY PHẢN KÍCH ---
            elif vfx['card']['id'] == 'trap_retaliation':
                progress = 1.0 - (vfx['timer'] / vfx['initial_timer'])
                eased_progress = 1 - (1 - progress) ** 3 # Ease-out

                # Lấy vị trí avatar của bot
                sidebar_rect = get_sidebar_rect()
                bot_panel_height = sidebar_rect.height * 0.7
                bot_panel_rect = pygame.Rect(sidebar_rect.x, sidebar_rect.y, sidebar_rect.width, bot_panel_height)
                end_pos = pygame.Vector2(bot_panel_rect.centerx, bot_panel_rect.centery + 40)

                board_rect = get_board_rect()
                start_pos = pygame.Vector2(board_rect.center) # Giả định bắt đầu từ giữa bàn cờ

                # Vẽ sợi xích
                chain_color = ERROR_RED
                points = []
                # SỬA LỖI: Logic vẽ sợi xích bị sai, cần sửa lại
                if eased_progress > 0:
                    num_segments = 20
                    for i in range(num_segments + 1):
                        p = i / num_segments
                        point = start_pos.lerp(current_pos, p)
                        # Thêm hiệu ứng uốn lượn
                        point.y += math.sin(p * math.pi * 2 + vfx['timer'] * 0.2) * 10 * (1 - p)
                        points.append(point)
                    if len(points) > 1:
                        # SỬA LỖI: current_pos không được định nghĩa
                        current_pos = start_pos.lerp(end_pos, eased_progress)
                        pygame.draw.aalines(screen, chain_color, False, points, 2)
        elif vfx['type'] == 'money_drop':
            # Logic vẽ hiệu ứng rơi tiền được tích hợp trực tiếp ở đây
            progress = 1.0 - (vfx['timer'] / vfx['initial_timer'])
            if 'particles' not in vfx:
                vfx['particles'] = []
                # SỬA LỖI: Sử dụng board_rect và sq_size động
                board_rect = get_board_rect()
                sq_size = get_sq_size(board_rect)
                r, c = 7 - chess.square_rank(vfx['pos']), chess.square_file(vfx['pos'])
                if vfx['game'].player_color == chess.BLACK: # type: ignore
                    r, c = 7 - r, 7 - c
                start_pos = (board_rect.x + c * sq_size + sq_size // 2, board_rect.y + r * sq_size + sq_size // 2)
                for _ in range(15):
                    vfx['particles'].append({
                        'x': start_pos[0] + random.uniform(-15, 15),
                        'y': start_pos[1] + random.uniform(-15, 15),
                        'vy': random.uniform(-2, -4), # type: ignore
                        'size': random.randint(4, 8)
                    })
            for p in vfx['particles']:
                p['y'] += p['vy'] # type: ignore
                alpha = 255 * (1 - progress)
                pygame.draw.circle(screen, (GOLD_ACCENT.r, GOLD_ACCENT.g, GOLD_ACCENT.b, alpha), (p['x'], p['y']), p['size']) # type: ignore
        else: # Các loại VFX khác (trap_placement, awakening, shield_reversal, trap_vengeance)
            animation_key = vfx.get('type')
            animation_func = get_animation_function(animation_key)
            if animation_func:
                animation_func(screen, vfx, card_images, piece_images)

        if vfx['timer'] > 0:
            active_vfx.append(vfx)

    game.vfx_queue = active_vfx # game ở đây là game_state

def draw_animation(screen, game, piece_images):
    """Vẽ animation di chuyển quân cờ."""
    if not game.animation:
        return

    board_rect = get_board_rect()
    sq_size = get_sq_size(board_rect)
    move = game.animation['move']
    start_time = game.animation['start_time']
    duration = game.animation['duration']
    elapsed = pygame.time.get_ticks() - start_time
    progress = min(elapsed / duration, 1.0) # type: ignore
    owner = game.animation.get('owner', 'player')

    piece_to_move = game.board.piece_at(move.from_square) # Lấy quân cờ từ vị trí BẮT ĐẦU # game ở đây là game_state
    if not piece_to_move: # Nếu không có quân cờ nào ở đó (trường hợp hiếm), hủy animation
        game.animation = None
        return

    def get_draw_pos(square):
        r, c = 7 - chess.square_rank(square), chess.square_file(square)
        if game.player_color == chess.BLACK:
            r, c = 7 - r, 7 - c # type: ignore
        return (board_rect.x + c * sq_size, board_rect.y + r * sq_size)

    # --- LOGIC ANIMATION RIÊNG BIỆT CHO TỪNG QUÂN CỜ ---
    start_pos = get_draw_pos(move.from_square)
    end_pos = get_draw_pos(move.to_square)

    # --- LOGIC ANIMATION CHO NHẬP THÀNH (CASTLING) ---
    if game.board.is_castling(move):
        # Xác định vị trí của Xe
        if move.to_square == chess.G1: # White kingside
            rook_start_sq, rook_end_sq = chess.H1, chess.F1
        elif move.to_square == chess.C1: # White queenside
            rook_start_sq, rook_end_sq = chess.A1, chess.D1
        elif move.to_square == chess.G8: # Black kingside
            rook_start_sq, rook_end_sq = chess.H8, chess.F8
        else: # Black queenside
            rook_start_sq, rook_end_sq = chess.A8, chess.D8

        rook_start_pos = get_draw_pos(rook_start_sq)
        rook_end_pos = get_draw_pos(rook_end_sq)
        rook_piece = game.board.piece_at(rook_start_sq)

        # Animation cho Vua
        king_img = piece_images.get(get_piece_symbol(piece_to_move))
        king_x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
        king_y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
        screen.blit(king_img, (king_x, king_y))

        # Animation cho Xe
        if rook_piece:
            rook_img = piece_images.get(get_piece_symbol(rook_piece))
            rook_x = rook_start_pos[0] + (rook_end_pos[0] - rook_start_pos[0]) * progress
            rook_y = rook_start_pos[1] + (rook_end_pos[1] - rook_start_pos[1]) * progress
            screen.blit(rook_img, (rook_x, rook_y))
        
        # Bỏ qua phần animation còn lại
        if progress >= 1.0:
            game.animation = None
        return


    if piece_to_move.piece_type == chess.KNIGHT:
        # Animation nhảy theo đường cong cho Mã
        control_point_x = start_pos[0] + (end_pos[0] - start_pos[0]) * 0.5
        control_point_y = start_pos[1] + (end_pos[1] - start_pos[1]) * 0.5 - 90
        current_x = (1 - progress)**2 * start_pos[0] + 2 * (1 - progress) * progress * control_point_x + progress**2 * end_pos[0]
        current_y = (1 - progress)**2 * start_pos[1] + 2 * (1 - progress) * progress * control_point_y + progress**2 * end_pos[1]
    else:
        # Animation di chuyển thẳng cho các quân khác
        if piece_to_move.piece_type in [chess.QUEEN, chess.ROOK]:
            # Hậu và Xe di chuyển rất nhanh
            eased_progress = 1 - (1 - progress) ** 5 # Ease-out cực mạnh
        else: # Tốt, Tượng, Vua
            if owner == 'player':
                eased_progress = 1 - (1 - progress) ** 4 # Ease-out nhanh
            else:
                eased_progress = progress ** 2 # Ease-in chậm

        current_x = start_pos[0] + (end_pos[0] - start_pos[0]) * eased_progress
        current_y = start_pos[1] + (end_pos[1] - start_pos[1]) * eased_progress

    # Hiệu ứng nảy lên và đáp xuống
    bounce = math.sin(progress * math.pi) * 0.3
    scale_factor = 1.0 + bounce
    scaled_size = (int(sq_size * scale_factor), int(sq_size * scale_factor))
    piece_symbol = get_piece_symbol(piece_to_move)
    piece_img = piece_images.get(piece_symbol)
    scaled_piece_img = pygame.transform.smoothscale(piece_img, scaled_size)
    blit_pos = scaled_piece_img.get_rect(center=(current_x + sq_size // 2, current_y + sq_size // 2))
    screen.blit(scaled_piece_img, blit_pos)
    
    if progress >= 1.0:
        # SỬA LỖI: Chỉ reset animation, không trả về giá trị.
        # Việc áp dụng nước đi sẽ do MovePieceTask xử lý.
        game.animation = None

def get_promotion_choice_rects(game_state):
    """Tính toán và trả về Rect của các nút lựa chọn phong cấp."""
    board_rect = get_board_rect()
    sq_size = get_sq_size(board_rect)
    
    promotion_square = game_state.promotion_choice_square
    if promotion_square is None:
        return {}

    # Lấy tọa độ vẽ của ô phong cấp
    r, c = 7 - chess.square_rank(promotion_square), chess.square_file(promotion_square)
    if game_state.player_color == chess.BLACK:
        r, c = 7 - r, 7 - c
    
    panel_width = sq_size * 4 + 10 * 3
    panel_height = sq_size + 20
    panel_x = board_rect.x + c * sq_size + sq_size // 2 - panel_width // 2
    panel_y = board_rect.y + r * sq_size + sq_size // 2 - panel_height // 2

    # Đảm bảo panel không tràn ra ngoài màn hình
    panel_x = max(10, min(panel_x, SCREEN_WIDTH - panel_width - 10))
    panel_y = max(10, min(panel_y, SCREEN_HEIGHT - panel_height - 10))

    # Kiểm tra debuff cấm phong Mã
    debuff = game_state.player_debuff
    knight_promotion_banned = debuff and debuff['id'] == 'knight_ban'

    choice_rects = {}
    choices = ['q', 'r', 'b', 'n']
    for i, piece_char in enumerate(choices):
        if not (knight_promotion_banned and piece_char == 'n'):
            rect = pygame.Rect(panel_x + 10 + i * (sq_size + 10), panel_y + 10, sq_size, sq_size)
            choice_rects[piece_char] = rect
    return choice_rects

def draw_promotion_choice(screen, game_state):
    """Vẽ giao diện lựa chọn quân cờ để phong cấp."""
    choice_rects = get_promotion_choice_rects(game_state)
    if not choice_rects:
        return

    # Vẽ panel nền
    panel_rect = list(choice_rects.values())[0].unionall(list(choice_rects.values()))
    panel_rect.inflate_ip(20, 20)
    draw_panel_bezel(screen, panel_rect)

    # Kiểm tra debuff cấm phong Mã
    debuff = game_state.player_debuff
    knight_promotion_banned = debuff and debuff['id'] == 'knight_ban'

    # Vẽ các lựa chọn
    for piece_char, rect in choice_rects.items():
        piece_symbol = ('w' if game_state.player_color == chess.WHITE else 'b') + piece_char.upper()
        if piece_symbol in _scaled_piece_cache:
            piece_image = _scaled_piece_cache[piece_symbol].copy()
            if knight_promotion_banned and piece_char == 'n':
                piece_image.set_alpha(80) # Làm mờ lựa chọn bị cấm
            screen.blit(piece_image, rect)

def draw_bot_emotion(screen, emotion_state, avatar_center):
    """Vẽ Avatar, Cảm xúc và khung radar trang trí cho Bot."""
    if 'emotion_icons' not in globals(): return # Bỏ qua nếu icon chưa được tải

    # --- Khung Radar ---
    radar_radius = 80
    emotion_colors = {"PANIC": ERROR_RED, "ARROGANT": GOLD_ACCENT, "FOCUSED": ARCANE_GLOW} # type: ignore
    radar_color = emotion_colors.get(emotion_state, ARCANE_GLOW) # type: ignore
    scan_angle = (pygame.time.get_ticks() / 10) % 360
    scan_surface = pygame.Surface((radar_radius * 2, radar_radius * 2), pygame.SRCALPHA)
    pygame.draw.arc(scan_surface, (radar_color.r, radar_color.g, radar_color.b, 50), scan_surface.get_rect(), math.radians(scan_angle - 45), math.radians(scan_angle), radar_radius)
    screen.blit(scan_surface, scan_surface.get_rect(center=avatar_center))
    pygame.draw.circle(screen, (radar_color.r, radar_color.g, radar_color.b, 150), avatar_center, radar_radius, 2)
    pygame.draw.circle(screen, (radar_color.r, radar_color.g, radar_color.b, 80), avatar_center, radar_radius * 0.6, 1)

    # --- Avatar ---
    avatar_radius = 40
    if emotion_state == "PANIC":
        avatar_center = (avatar_center[0] + random.randint(-3, 3), avatar_center[1] + random.randint(-3, 3))
    pygame.draw.circle(screen, pygame.Color(40,40,50), avatar_center, avatar_radius)
    pygame.draw.circle(screen, WHITE_TEXT, avatar_center, avatar_radius, 2) # type: ignore
    icon = emotion_icons.get(emotion_state.upper())
    if icon:
        scaled_icon = pygame.transform.smoothscale(icon, (avatar_radius, avatar_radius))
        screen.blit(scaled_icon, scaled_icon.get_rect(center=avatar_center))

def draw_active_curses(screen, game):
    """Vẽ các hiệu ứng hình ảnh cho các lời nguyền đang ảnh hưởng đến Bot."""
    if 'chaos_curse' in game.active_curses:
        curse_data = game.active_curses['chaos_curse']
        curse_data['timer'] += game.dt # Tăng timer dựa trên delta time # game ở đây là game_state
        timer = curse_data['timer']

        # Lấy vị trí avatar của bot
        sidebar_rect = get_sidebar_rect()
        bot_panel_height = sidebar_rect.height * 0.7
        bot_panel_rect = pygame.Rect(sidebar_rect.x, sidebar_rect.y, sidebar_rect.width, bot_panel_height)
        center = pygame.Vector2(bot_panel_rect.centerx, bot_panel_rect.centery + 40)

        # Vẽ vòng xoáy hỗn loạn
        num_particles = 40
        max_radius = 100
        for i in range(num_particles):
            # Tính toán vị trí và thuộc tính của mỗi hạt
            angle = (i / num_particles) * math.tau + timer * (2 + (i % 5) * 0.2)
            distance = (max_radius * 0.4) + (math.sin(timer * 1.5 + i) * 0.5 + 0.5) * (max_radius * 0.6)
            x = center.x + math.cos(angle) * distance
            y = center.y + math.sin(angle) * distance
            
            # Kích thước và màu sắc thay đổi theo thời gian
            size = 2 + (math.sin(timer * 3 + i) * 0.5 + 0.5) * 3
            color = pygame.Color(120, 50, 220).lerp(pygame.Color(20, 0, 40), math.sin(timer + i) * 0.5 + 0.5)
            
            pygame.draw.circle(screen, color, (x, y), size)