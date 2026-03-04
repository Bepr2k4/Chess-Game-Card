import chess
import random

class FunBossAbilities:
    """
    Quản lý các kỹ năng đặc biệt và hiệu ứng bất lợi của Boss.
    """
    # --- ĐỊNH NGHĨA CÁC DEBUFF MÀ BOSS CÓ THỂ GÂY RA ---
    Debuffs = {
        "pawn_sacrifice": {
            "id": "pawn_sacrifice",
            "name": "Cống Phẩm",
            "description": "Bắt đầu trận đấu với việc mất đi 1 Tốt ngẫu nhiên."
        },
        "first_strike": {
            "id": "first_strike",
            "name": "Đòn Phủ Đầu",
            "description": "Đối thủ được đi nước đầu tiên."
        },
        "knight_ban": {
            "id": "knight_ban",
            "name": "Luật Lệ Của Vua",
            "description": "Tốt của bạn không thể phong cấp thành Mã."
        }
        # Thêm các debuff khác ở đây
    }

    """
    Quản lý logic cho các kỹ năng đặc biệt của Boss.
    Mỗi hàm trả về một "câu thoại" để hiển thị trên UI.
    """
    phrases = {
        "magician_start": [
            "Úm ba la... Tốt biến hình!",
            "Abra-ca-pawn-ra!",
            "Xem ta biến hai con chốt này thành gì nhé!",
            "Một chút ma thuật cho ván cờ thêm vui."
        ],
        "greed_capture": [
            "Hehe, của rơi!",
            "Tiền! Tiền! Ta yêu tiền!",
            "Bắt được rồi! Có dám vào nhặt không?",
            "Cảm ơn vì đã quyên góp."
        ],
        "greed_pickup": [
            "Ối, tiền của ta!",
            "Trả lại đây!",
            "Đồ trộm cắp!"
        ],
        "mirror_revive": [
            "Chưa hết đâu! Nhìn này!",
            "Gương Thần Phản Chiếu!",
            "Một đổi một, không ai thiệt nhé.",
            "Ta gọi mi từ cõi hư vô trở về!"
        ]
    }

    @staticmethod
    def apply_magician(board, bot_color, rng):
        """
        The Magician: Biến 2 Tốt thành Mã hoặc Tượng ngẫu nhiên.
        Kích hoạt: Đầu trận.
        """
        pawn_squares = list(board.pieces(chess.PAWN, bot_color))
        if len(pawn_squares) < 2:
            return None # Không đủ Tốt để biến hình

        # SỬA LỖI CÂN BẰNG GAME: Hy sinh 2 Tốt để tạo ra 1 quân cờ mới.
        # 1. Chọn 2 Tốt ngẫu nhiên để hy sinh.
        pawns_to_transform = rng.sample(pawn_squares, 2)
        pawn_square_1, pawn_square_2 = pawns_to_transform
        
        # 2. Xóa cả 2 Tốt khỏi bàn cờ.
        board.remove_piece_at(pawn_square_1)
        board.remove_piece_at(pawn_square_2)
        
        # 3. Chọn 1 trong 2 ô trống đó để triệu hồi quân cờ mới.
        summon_square = rng.choice([pawn_square_1, pawn_square_2])
        new_piece_type = rng.choice([chess.KNIGHT, chess.BISHOP])
        board.set_piece_at(summon_square, chess.Piece(new_piece_type, bot_color))

        return rng.choice(FunBossAbilities.phrases["magician_start"])

    @staticmethod
    def apply_greed_on_capture(game_state, move, rng):
        """
        The Greed: Rơi ra tiền khi ăn quân.
        Kích hoạt: Khi Bot ăn quân của người chơi.
        """
        # Ô bị ăn quân sẽ có tiền
        game_state.coin_squares.append(move.to_square)
        # Thêm animation rơi tiền
        vfx_data = {'type': 'money_drop', 'timer': 60, 'initial_timer': 60, 'game': game_state, 'pos': move.to_square}
        game_state.vfx_queue.append(vfx_data)
        return rng.choice(FunBossAbilities.phrases["greed_capture"])

    @staticmethod
    def check_greed_pickup(game, move, rng):
        """Kiểm tra xem người chơi có nhặt được tiền không."""
        if move.to_square in game.coin_squares:
            game.coin_squares.remove(move.to_square)
            gold_earned = rng.randint(3, 7) # Nhặt được 3-7 vàng
            game.player_gold += gold_earned
            return f"Bạn nhặt được {gold_earned} vàng! " + rng.choice(FunBossAbilities.phrases["greed_pickup"])
        return None

    @staticmethod
    def apply_mirror(game, captured_piece_type, rng):
        """
        The Mirror: Hồi sinh quân cờ bị ăn bằng cách hy sinh một quân Tốt.
        Kích hoạt: Khi người chơi ăn một quân cờ (không phải Tốt) của Bot.
        """
        # Điều kiện: Quân bị ăn không phải là Tốt hoặc Vua.
        if captured_piece_type == chess.PAWN or captured_piece_type == chess.KING:
            return None

        # Tìm một quân Tốt để hy sinh
        sacrifice_candidates = list(game.board.pieces(chess.PAWN, game.bot_color))
        if not sacrifice_candidates:
            return None # Không có Tốt để hy sinh

        # Thực hiện logic
        # 1. Chọn một quân Tốt ngẫu nhiên để hy sinh
        pawn_to_sacrifice_sq = rng.choice(sacrifice_candidates)
        
        # 2. Xóa quân Tốt đó
        game.board.remove_piece_at(pawn_to_sacrifice_sq)
        
        # 3. Hồi sinh quân cờ vừa bị ăn vào đúng vị trí của quân Tốt đã hy sinh
        game.board.set_piece_at(pawn_to_sacrifice_sq, chess.Piece(captured_piece_type, game.bot_color))

        return rng.choice(FunBossAbilities.phrases["mirror_revive"])