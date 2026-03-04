import chess
import random
from boss_abilities import FunBossAbilities
from animation_queue import MovePieceTask, VFXTask, RemovePieceTask
import pygame
from save_manager import save_game

def handle_player_move(game_controller, move_uci):
    """Xử lý nước đi của người chơi."""
    game_state = game_controller.game_state # Lấy state từ controller
    try:
        move = chess.Move.from_uci(move_uci)
        if move in game_state.board.legal_moves:
            game_state.animation = {
                'move': move,
                'start_time': pygame.time.get_ticks(),
                'duration': 200, # Nhanh hơn 1.5 lần
                'owner': 'player'
            }
            game_state.animation_queue.add(MovePieceTask(game_controller, move, owner='player', duration=200))
            return True
        return False
    except:
        return False

def handle_bot_move(game_controller):
    """Xử lý nước đi của Bot."""
    game_state = game_controller.game_state # Lấy state từ controller
    game_state.bot_emotion = game_state.bot.update_emotional_state(game_state.board, game_state.bot_color)

    if game_state.time_stop_turns > 0:
        game_state.add_notification("Lượt của Bot đã bị chặn!", type="boss")
        game_state.time_stop_turns -= 1
        return None

    chaos_card = next((card for card in game_state.player_cards if card.get('id') == 'chaos_curse' and card.get('active')), None)
    if chaos_card:
        chaos_card['active'] = False
        game_state.active_curses.pop('chaos_curse', None)
        legal_moves = list(game_state.board.legal_moves)
        if legal_moves:
            move = random.choice(legal_moves)
            game_state.animation = {
                'move': move,
                'start_time': pygame.time.get_ticks(),
                'duration': 200, # Nhanh hơn 1.5 lần
                'owner': 'bot'
            }
            game_state.animation_queue.add(MovePieceTask(game_controller, move, owner='bot', duration=200))
            game_state.add_notification("Bot di chuyển một cách hỗn loạn!", type="boss")
            return move

    move = game_state.bot.choose_move(game_state.board, game_state.current_seed, game_state.stage, game_state.turn_count)
    if move:
        is_capture = game_state.board.is_capture(move)
        game_state.animation = {
            'move': move,
            'start_time': pygame.time.get_ticks(),
            'duration': 200, # Nhanh hơn 1.5 lần
            'owner': 'bot'
        }
        game_state.animation_queue.add(MovePieceTask(game_controller, move, owner='bot', duration=200))
        
        stage_rng = random.Random(f"{game_state.current_seed}-{game_state.stage}")
        if game_state.boss_ability == "greed" and is_capture:
            # SỬA LỖI: Gọi hàm helper từ FunBossAbilities để xử lý logic và thông báo
            # Điều này cũng sẽ tạo ra vfx rơi tiền.
            FunBossAbilities.apply_greed_on_capture(game_state, move, stage_rng)
        return move
    else:
        game_state.board.turn = not game_state.board.turn
    return None

def apply_move_effects(game_controller, move):
    """Áp dụng các hiệu ứng sau khi một nước đi được thực hiện."""
    game_state = game_controller.game_state # Lấy state từ controller
    is_capture = game_state.board.is_capture(move) # type: ignore
    captured_square = move.to_square
    moved_piece_color = game_state.board.color_at(move.from_square)
    captured_piece_before_move = game_state.board.piece_at(captured_square)
    moved_piece = game_state.board.piece_at(move.from_square)
    moved_from_square = move.from_square

    # SỬA LỖI: Logic lấy quân cờ bị ăn đã được viết lại hoàn toàn để xử lý mọi trường hợp,
    # đặc biệt là "en passant", nguyên nhân chính gây ra lỗi khiên phép.
    captured_piece_color = None
    if is_capture:
        if game_state.board.is_en_passant(move):
            # Vị trí của quân tốt bị ăn trong en passant
            down = -8 if moved_piece_color == chess.WHITE else 8
            en_passant_capture_square = move.to_square + down
            captured_piece_before_move = game_state.board.piece_at(en_passant_capture_square)
        if captured_piece_before_move:
            captured_piece_color = captured_piece_before_move.color

    # --- LOGIC KHIÊN PHÉP (ƯU TIÊN CAO NHẤT) ---
    if is_capture and captured_piece_color == game_state.player_color and captured_square in game_state.shielded_pieces:
        game_state.add_notification("Khiên Phép đã chặn đứng đòn tấn công!", "card_activation")
        game_state.shielded_pieces.remove(captured_square) # Xóa khiên sau khi dùng

        # Kích hoạt animation "quay ngược"
        vfx_data = {
            'type': 'shield_reversal', 'timer': 80, 'initial_timer': 80, # Nhanh hơn 1.5 lần
            'game': game_state, 'triggering_move': move
        }
        game_state.animation_queue.add(VFXTask(game_controller, vfx_data))
        # SỬA LỖI: Không push move, nhưng phải đảo lượt đi để trả lại lượt cho người chơi.
        # Nếu không, game sẽ bị kẹt ở lượt của Bot.
        game_state.board.turn = not game_state.board.turn
        return # Dừng hàm apply_move_effects tại đây.

    # --- LOGIC DI CHUYỂN LỜI NGUYỀN (CURSE MOVEMENT) ---
    # Thực hiện trước khi push move để kiểm tra `moved_from_square`
    if moved_from_square in game_state.cursed_pieces:
        trap_data = game_state.cursed_pieces.pop(moved_from_square)
        game_state.cursed_pieces[move.to_square] = trap_data

    game_state.board.push(move)

    # --- 2. HANDLE TRAP ACTIVATION (POST-MOVE) ---
    if is_capture and moved_piece_color == game_state.bot_color and captured_square in game_state.cursed_pieces:
        trap_data = game_state.cursed_pieces[captured_square]
        card = trap_data['card']
        if card.get("trigger") == "on_capture":
            game_state.cursed_pieces.pop(captured_square)
            game_state.add_notification(f"Bẫy '{card['name']}' đã được kích hoạt!", "card_activation")

            if card['id'] == 'trap_vengeance':
                # SỬA LỖI LOGIC: Bẫy phải phá hủy quân cờ TẤN CÔNG, mà sau khi di chuyển, nó đang ở `to_square`.
                vfx_data = {'type': 'trap_vengeance', 'card': card, 'timer': 80, 'initial_timer': 80, 'game': game_state, 'triggering_move': move}
                game_state.animation_queue.add(VFXTask(game_controller, vfx_data))
                game_state.animation_queue.add(RemovePieceTask(game_controller, move.to_square, reason_card=card))
            elif card.get("effect") == "skip_turn":
                game_state.time_stop_turns = 1
                # SỬA LỖI: Thêm animation cho Bẫy Ngưng Đọng
                vfx_data = {'type': 'time_stop', 'card': card, 'timer': 80, 'initial_timer': 80, 'game': game_state, 'triggering_move': move}
                game_state.animation_queue.add(VFXTask(game_controller, vfx_data))
                game_state.add_notification("Lượt của đối thủ bị chặn!", "boss")

            original_card = next((c for c in game_state.player_cards if c['id'] == card['id']), None)
            if original_card:
                original_card['active'] = False

    # --- 3. HANDLE OTHER CARD & GAME EFFECTS (POST-MOVE) ---
    flash_move_card = next((card for card in game_state.player_cards if card.get('id') == 'flash_move' and card.get('active')), None)
    if flash_move_card and not game_state.is_extra_turn_active:
        game_state.is_extra_turn_active = True
        game_state.board.turn = not game_state.board.turn
        game_state.time_stop_active = True
    elif game_state.is_extra_turn_active:
        game_state.is_extra_turn_active = False
        game_state.time_stop_active = False

    if game_state.boss_ability == "greed":
        stage_rng = random.Random(f"{game_state.current_seed}-{game_state.stage}")
        pickup_message = FunBossAbilities.check_greed_pickup(game_state, move, stage_rng)
        if pickup_message:
            game_state.add_notification(pickup_message, type="boss")

    # --- XỬ LÝ KHI QUÂN BỊ NGUYỀN TẤN CÔNG (on_attack) ---
    if is_capture and moved_piece_color == game_state.player_color and move.to_square in game_state.cursed_pieces:
        trap_data = game_state.cursed_pieces[move.to_square]
        card = trap_data['card']

        if card.get("trigger") == "on_attack":
            trap_data["kills"] += 1
            game_state.add_notification(f"'{card['name']}' đã tích lũy được {trap_data['kills']} điểm hạ gục.", "info")

            # Logic riêng cho "Ấn Ký Khát Máu"
            if card['id'] == 'blessing_bloodthirst' and trap_data["kills"] >= 2:
                # SỬA LỖI THIẾT KẾ: Biến hiệu ứng thành nội tại lặp lại, không bị tiêu hao.
                if move.to_square not in game_state.shielded_pieces:
                    trap_data["kills"] = 0 # Reset bộ đếm
                    game_state.add_notification(f"Quân cờ tại {chess.square_name(move.to_square)} nhận được KHIÊN PHÉP!", "card_activation")
                    vfx_data = {
                        'type': 'awakening', 'timer': 80, 'initial_timer': 80,
                        'game': game_state, 'triggering_move': move
                    }
                    game_state.animation_queue.add(VFXTask(game_controller, vfx_data))
                    game_state.shielded_pieces.add(move.to_square) # Thêm khiên phép vào quân cờ
                else:
                    game_state.add_notification("Quân cờ đã có Khiên Phép!", "info")

    if is_capture and moved_piece_color == game_state.bot_color:
        mirror_card = next((card for card in game_state.player_cards if card.get('id') == 'mirror_revive' and card.get('uses') > 0), None)
        if mirror_card and captured_piece_before_move and captured_piece_before_move.piece_type not in [chess.PAWN, chess.KING]:
            # SỬA LỖI LOGIC: Phải hồi sinh quân cờ của người chơi, không phải của Bot.
            sacrifice_candidates = list(game_state.board.pieces(chess.PAWN, game_state.player_color))
            if sacrifice_candidates:
                pawn_to_sacrifice_sq = random.choice(sacrifice_candidates)
                game_state.board.remove_piece_at(pawn_to_sacrifice_sq)
                game_state.board.set_piece_at(pawn_to_sacrifice_sq, chess.Piece(captured_piece_before_move.piece_type, game_state.player_color))
                mirror_card['uses'] = 0
                game_state.add_notification("Gương Phản Chiếu đã kích hoạt!", type="card_activation")
                vfx_data = {
                    'type': 'card_activation', 'card': mirror_card, 'timer': 95, 'initial_timer': 95, # Nhanh hơn 1.5 lần
                    'start_pos_sq': captured_square, 'end_pos_sq': pawn_to_sacrifice_sq, 'game': game_state
                }
                game_state.animation_queue.add(VFXTask(game_controller, vfx_data))

    if is_capture and moved_piece_color == game_state.player_color:
        if (moved_piece.piece_type == chess.PAWN and captured_piece_before_move.piece_type == chess.QUEEN) or \
           (moved_piece.piece_type == chess.KNIGHT and captured_piece_before_move.piece_type == chess.ROOK) or \
           (moved_piece.piece_type == chess.BISHOP and captured_piece_before_move.piece_type == chess.QUEEN):
            for trap_card in game_state.player_cards:
                if trap_card.get("type") == "trap" and trap_card.get("uses") == 0:
                    trap_card["uses"] = 1
                    game_state.add_notification(f"Nước đi xuất sắc! Đã hồi phục thẻ '{trap_card['name']}'.", type="game_event")
                    break

    game_state.turn_count += 1

    # --- 4. CHECK GAME OVER ---
    if game_state.board.is_game_over() and not game_state.time_stop_active:
        # SỬA LỖI: Việc lưu game giờ sẽ do end_of_match_rewards xử lý
        game_controller.end_of_match_rewards()