import chess
import random

# --- HỆ THỐNG TÍNH CÁCH BOT (AI PERSONALITY) ---
BotStyles = {
    "The Butcher": {
        "description": "Một kẻ hiếu chiến, luôn tìm cách ăn quân của bạn bằng mọi giá.",
        "capture_aggression": 2.5,  # Rất thích ăn quân
        "king_safety": 0.5,         # Ít quan tâm đến an toàn
        "center_control": 0.8,      # Không quá chú trọng trung tâm
        "trade_aversion": 0.7,      # Rất sẵn lòng trao đổi quân
    },
    "The Turtle": {
        "description": "Một bậc thầy phòng ngự, ưu tiên sự an toàn của Vua lên hàng đầu.",
        "capture_aggression": 0.8,  # Ngại ăn quân nếu rủi ro
        "king_safety": 3.0,         # Cực kỳ cẩn trọng
        "center_control": 1.5,      # Kiểm soát trung tâm để phòng ngự từ xa
        "trade_aversion": 2.0,      # Ghét việc mất quân của mình
    },
    "The Nemesis": {
        "description": "Một đối thủ có mối thù truyền kiếp với các Kỵ Sĩ.",
        "capture_aggression": 1.5,
        "king_safety": 1.0,
        "center_control": 1.0,
        "trade_aversion": 1.0,
        "hated_pieces": [chess.KNIGHT], # Ghét quân Mã
        "hate_bonus": 100,              # Điểm thưởng cực lớn khi ăn được quân bị ghét
    },
    "The Warden": { # Style mặc định cho Boss
        "name": "Kẻ Cai Ngục",
        "description": "Một đối thủ kỷ luật, áp đặt luật lệ của riêng mình lên bàn cờ.",
        "capture_aggression": 1.2, "king_safety": 1.5,
        "center_control": 1.2, "trade_aversion": 1.2,
    },
    "balanced": { # Giữ lại một preset cân bằng làm mặc định
        "description": "Một đối thủ cân bằng, không có điểm yếu rõ rệt.",
        "capture_aggression": 1.0, "king_safety": 1.0,
        "center_control": 1.0, "trade_aversion": 1.0,
    }
}

class SimpleBot:
    def __init__(self, base_mistake_rate=0.1, style="balanced"):
        self.base_mistake_rate = base_mistake_rate # Tỉ lệ lỗi cơ bản khi tập trung
        self.mistake_rate = base_mistake_rate      # Tỉ lệ lỗi hiện tại, sẽ thay đổi theo cảm xúc
        if isinstance(style, str):
            self.style = BotStyles.get(style, BotStyles["balanced"]) # Lấy "tính cách" từ dictionary
        else:
            self.style = style # Cho phép gán một dictionary style tùy chỉnh (dành cho Boss)

    def get_piece_value(self, piece):
        if piece is None: return 0
        values = {chess.PAWN: 10, chess.KNIGHT: 32, chess.BISHOP: 33, 
                  chess.ROOK: 50, chess.QUEEN: 90, chess.KING: 20000}
        return values.get(piece.piece_type, 0)

    def update_emotional_state(self, board, bot_color):
        """Cập nhật tỷ lệ mắc lỗi dựa trên 'cảm xúc' của bot trong ván cờ."""
        # 1. Trạng thái PANIC (Hoảng loạn)
        king_square = board.king(bot_color)
        is_in_check = board.is_check()
        # Đếm số quân địch đang tấn công vua
        attackers_count = len(board.attackers(not bot_color, king_square))

        if is_in_check or attackers_count > 2:
            self.mistake_rate = 0.8
            return "PANIC"

        # 2. Trạng thái ARROGANT (Kiêu ngạo)
        player_color = not bot_color
        bot_material = 0
        player_material = 0
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            bot_material += len(board.pieces(piece_type, bot_color)) * self.get_piece_value(chess.Piece(piece_type, bot_color))
            player_material += len(board.pieces(piece_type, player_color)) * self.get_piece_value(chess.Piece(piece_type, player_color))
        
        material_advantage = (bot_material - player_material) / 10 # Chia cho 10 để tương ứng với giá trị quân cờ

        if material_advantage > 15:
            self.mistake_rate = 0.5
            return "ARROGANT"

        # 3. Trạng thái FOCUSED (Tập trung)
        self.mistake_rate = self.base_mistake_rate
        return "FOCUSED"

    def evaluate_move(self, board, move):
        """Đánh giá nước đi dựa trên 'tính cách' của Bot."""
        final_score = 0
        
        # SỬA LỖI: Đảm bảo 'weights' luôn là một dictionary
        if isinstance(self.style, str):
            weights = BotStyles.get(self.style, BotStyles["balanced"])
        else:
            weights = self.style
        
        # --- 1. Material (Ăn quân) ---
        if board.is_capture(move):
            if board.is_en_passant(move):
                captured_value = self.get_piece_value(chess.Piece(chess.PAWN, not board.turn))
            else:
                # Lấy quân cờ BỊ ĂN tại ô ĐẾN
                captured_piece = board.piece_at(move.to_square)
                captured_value = self.get_piece_value(captured_piece)

                # Xử lý cho "The Nemesis"
                if 'hated_pieces' in weights and captured_piece.piece_type in weights['hated_pieces']:
                    captured_value += weights['hate_bonus']
            
            final_score += captured_value * weights.get('capture_aggression', 1.0)

        # --- 2. Positioning (Vị trí) ---
        # Kiểm soát trung tâm
        center = [chess.E4, chess.D4, chess.E5, chess.D5]
        outer_center = [chess.C3, chess.D3, chess.E3, chess.F3, 
                        chess.C6, chess.D6, chess.E6, chess.F6]
        center_score = 0
        if move.to_square in center: center_score = 5
        elif move.to_square in outer_center: center_score = 2
        final_score += center_score * weights.get('center_control', 1.0)

        # --- 3. Safety (An toàn - Quan trọng!) ---
        # Giả lập đi thử nước cờ
        board.push(move)
        
        # Nếu nước đi này tạo ra một pha chiếu tướng (Check) -> Tốt (Gây áp lực)
        if board.is_check():
            # Điểm chiếu tướng cũng bị ảnh hưởng bởi mức độ hiếu chiến
            final_score += 15 * weights.get('capture_aggression', 1.0)
        
        # Đánh giá sự an toàn của ô vừa di chuyển đến
        safety_penalty = 0
        # SỬA LỖI: Logic đánh giá an toàn bị sai khi ăn quân.
        # Nó phải luôn tính đến giá trị của quân cờ TẤN CÔNG, không phải quân bị ăn.
        attacking_piece = board.piece_at(move.to_square) # Quân cờ của bot sau khi đã di chuyển
        if board.is_attacked_by(not board.turn, move.to_square): # Nếu ô đến bị đối phương tấn công
            # Điểm phạt phải dựa trên giá trị của quân cờ của MÌNH
            # đang đứng trên ô nguy hiểm đó.
            safety_penalty = self.get_piece_value(attacking_piece)

        board.pop() # Trả lại bàn cờ cũ

        final_score -= safety_penalty * weights.get('king_safety', 1.0) * weights.get('trade_aversion', 1.0)
        return final_score

    def choose_move(self, board, game_seed, stage, turn_count):
        legal_moves = list(board.legal_moves)
        if not legal_moves: return None

        # SỬA LỖI: Tạo một bộ sinh số ngẫu nhiên riêng cho lượt đi này của bot
        # Seed được tạo từ seed của game, stage, lượt đi và trạng thái bàn cờ (FEN)
        # Điều này đảm bảo bot sẽ luôn có hành vi ngẫu nhiên giống nhau cho cùng một tình huống.
        move_rng_seed = f"{game_seed}-{stage}-{turn_count}-{board.fen()}"
        rng = random.Random(move_rng_seed)

        # Tính điểm tất cả nước đi
        scored_moves = []
        for move in legal_moves:
            scored_moves.append((self.evaluate_move(board, move), move))

        # Sắp xếp từ Tốt nhất -> Tệ nhất
        scored_moves.sort(reverse=True, key=lambda x: x[0])

        # Thêm yếu tố nhiễu loạn (noise) SAU KHI đã sắp xếp, sử dụng RNG riêng
        for i in range(len(scored_moves)):
            scored_moves[i] = (scored_moves[i][0] + rng.uniform(-1, 1), scored_moves[i][1])
        
        # --- LOGIC MISTAKE MỚI ---
        # Thay vì cắt đôi danh sách, ta dùng logic "Trượt tay"
        
        # Nếu mistake_rate thấp (VD: 0.1 - Bot Khôn): 
        # Rất có khả năng chọn Top 1, thi thoảng chọn Top 2/3.
        
        # Nếu mistake_rate cao (VD: 0.9 - Bot Ngáo):
        # Chọn ngẫu nhiên lung tung.
        
        if rng.random() > self.mistake_rate:
            # Bot chơi tập trung: Chọn nước đi tốt nhất (Top 1)
            return scored_moves[0][1]
        else:
            # Bot mắc sai lầm:
            # Không chọn nước tốt nhất. Chọn một trong các nước còn lại.
            # Nhưng ưu tiên chọn các nước "gần tốt" (Top 2, Top 3) hơn là nước tệ hại.
            
            if len(scored_moves) > 1:
                # Loại bỏ nước tốt nhất ra khỏi lựa chọn
                remaining_moves = scored_moves[1:]
                
                # Cách chọn: Lấy ngẫu nhiên trong khoảng top 20% đến 50% số nước đi còn lại
                # Để đảm bảo nó không đi nước quá ngu (tự sát) nhưng cũng không tối ưu.
                limit = max(1, int(len(remaining_moves) * 0.5)) 
                chosen = rng.choice(remaining_moves[:limit])
                return chosen[1]
            else:
                return scored_moves[0][1] # Chỉ có 1 nước đi thì bắt buộc phải đi