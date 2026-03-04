import chess
from animation_queue import VFXTask


def activate_card(game_controller, card_name):
    """Kích hoạt một thẻ bài nếu còn lượt sử dụng."""
    game_state = game_controller.game_state
    # SỬA LỖI: Ngăn người chơi kích hoạt thẻ mới khi đang trong chế độ chọn mục tiêu.
    if game_state.targeting_card:
        game_state.add_notification("Bạn phải hoàn thành việc chọn mục tiêu trước!", type="error")
        return False

    card = next((c for c in game_state.player_cards if c['name'] == card_name), None)
    if card and card["uses"] > 0:
        if card['id'] == 'flash_move':
            game_state.add_notification("Nước Đi Chớp Nhoáng: Bạn có 2 lượt đi liên tiếp!", type="card_activation")
        elif card['id'] == 'chaos_curse':
            game_state.add_notification("Lời Nguyền Hỗn Loạn đã được gieo rắc!", type="card_activation")
            game_state.active_curses['chaos_curse'] = {'timer': 0}
        elif card['id'] == 'pawn_trade' or card['type'] == 'trap':
            game_state.targeting_card = card
            if card['type'] == 'trap':
                game_state.add_notification(f"Đặt '{card_name}': Chọn một quân cờ. (Chuột phải để hủy)", type="info")
                card['uses'] -= 1
            else:
                game_state.add_notification("Chọn một quân Tốt để hy sinh.", type="info")
            return True

        card["uses"] -= 1
        game_controller.track_card_usage(card['id']) # THEO DÕI THỐNG KÊ
        card["active"] = True
        vfx_data = {'type': 'card_activation', 'card': card, 'timer': 60, 'initial_timer': 60} # Nhanh hơn 1.5 lần
        game_state.animation_queue.add(VFXTask(game_controller, vfx_data))
        game_state.add_notification(f"Đã kích hoạt thẻ '{card_name}'!", type="card_activation")
        return True
    return False

def resolve_card_target(game_controller, square):
    """Xử lý logic sau khi người chơi chọn mục tiêu cho thẻ."""
    game_state = game_controller.game_state
    if not game_state.targeting_card:
        return

    card_id = game_state.targeting_card['id']
    if card_id == 'pawn_trade':
        piece = game_state.board.piece_at(square)
        if piece and piece.piece_type == chess.PAWN and piece.color == game_state.player_color:
            game_state.board.remove_piece_at(square)
            game_state.player_gold += 6
            game_controller.track_card_usage(card_id) # THEO DÕI THỐNG KÊ
            game_state.add_notification("Đã hy sinh Tốt và nhận 6 vàng.", type="card_activation")
            game_state.targeting_card['active'] = True
            game_state.targeting_card = None
    elif game_state.targeting_card['type'] == 'trap':
        piece = game_state.board.piece_at(square)
        if piece and piece.color == game_state.player_color:
            if square in game_state.cursed_pieces:
                game_state.add_notification("Quân cờ này đã có một bẫy!", type="error")
                return
            game_state.cursed_pieces[square] = {"card": game_state.targeting_card, "kills": 0}
            game_state.targeting_card['active'] = True
            # SỬA LỖI: Thêm animation khi đặt bẫy thành công
            vfx_data = {
                'type': 'trap_placement', # SỬA LỖI: Dùng một type chung cho animation đặt bẫy
                'timer': 60, 'initial_timer': 60, 'game': game_state, # Nhanh hơn 1.5 lần
                'target_square': square # Truyền ô mục tiêu cho animation
            }
            game_state.animation_queue.add(VFXTask(game_controller, vfx_data))
            game_state.add_notification(f"Đã đặt bẫy '{game_state.targeting_card['name']}' lên quân cờ tại {chess.square_name(square)}.", type="info")
            game_state.targeting_card = None