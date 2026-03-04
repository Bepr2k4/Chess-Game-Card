import chess
import random
from boss_abilities import FunBossAbilities
from animation_queue import KnightLegionTask
from save_manager import save_game
import drawing

# TÁI CẤU TRÚC: Import các module logic mới
from game_state import GameState
from card_database import CARD_DATABASE
from save_manager import save_game
import game_logic
from save_manager import delete_save_file
import card_manager
import shop_manager
from profile_manager import update_profile_after_run
from bot import BotStyles

class ChessGame: # Lớp này giờ đóng vai trò là Controller
    def __init__(self):
        self.game_state = GameState()

    def start_new_run(self):
        """Bắt đầu một lượt chơi mới, xử lý toàn bộ logic khởi tạo."""
        delete_save_file()
        self.game_state.current_seed = self.generate_random_seed()
        # Reset lại run_stats cho lượt chơi mới
        self.game_state.run_stats = {
            "card_usage": {},
        }
        # SỬA LỖI: Không sử dụng random.seed() toàn cục. Mọi hành động ngẫu nhiên phải dùng RNG riêng.
        self.refresh_shop() 
        save_game(self.game_state)
        # Các logic reset khác sẽ được xử lý trong reset_board khi bắt đầu trận đấu

    def generate_random_seed(self, length=8):
        return self.game_state.generate_random_seed(length)

    def player_move(self, move_uci):
        return game_logic.handle_player_move(self, move_uci)

    def apply_move(self, move):
        """Áp dụng nước đi vào bàn cờ và xử lý logic thẻ bài."""
        game_logic.apply_move_effects(self, move)

    def activate_card(self, card_name):
        """Kích hoạt một thẻ bài nếu còn lượt sử dụng."""
        return card_manager.activate_card(self, card_name)

    def resolve_card_target(self, square):
        """Xử lý logic sau khi người chơi chọn mục tiêu cho thẻ."""
        card_manager.resolve_card_target(self, square)

    def track_card_usage(self, card_id):
        """Ghi nhận việc một thẻ bài đã được sử dụng."""
        stats = self.game_state.run_stats["card_usage"]
        stats[card_id] = stats.get(card_id, 0) + 1

    def add_notification(self, message, type="default"):
        self.game_state.add_notification(message, type)

    def add_shop_notification(self, message, type="shop"):
        """Thêm một thông báo vào nhật ký của shop."""
        shop_manager.add_shop_notification(self.game_state, message, type)

    def bot_move(self):
        game_logic.handle_bot_move(self)

    def buy_reroll(self):
        """Mua lượt làm mới shop với chi phí tăng dần."""
        shop_manager.buy_reroll(self.game_state)

    def buy_card(self, card_name):
        """Mua một thẻ bài từ shop."""
        shop_manager.buy_card(self.game_state, card_name)

    def sell_card(self, card_name):
        """Bán một thẻ bài đang sở hữu để nhận lại vàng."""
        # Tạm thời giữ lại logic này ở đây vì nó đơn giản
        # ...

    def get_sell_price(self, card_name):
        """Tính toán và trả về giá bán của một thẻ bài."""
        card_to_check = next((c for c in self.game_state.player_cards if c['name'] == card_name), None)
        if not card_to_check:
            return 0

        original_card_data = next((c for c in CARD_DATABASE if c['id'] == card_to_check['id']), None)
        if not original_card_data:
            return 0
        return int(original_card_data['price'] / 1.7)

    def end_of_match_rewards(self):
        """Tính và cộng vàng sau khi kết thúc một ván đấu."""
        result = self.get_game_result()
        if result == "WIN":
            self.game_state.add_notification("Bạn đã thắng!", type="game_event")
            self._calculate_win_rewards()

            is_boss_round = (self.game_state.round == self.game_state.max_rounds_per_stage)
            if is_boss_round:
                self.game_state.stage += 1
                self.game_state.round = 1
                # Cập nhật profile khi thắng một tầng
                run_summary = {
                    "result": "WIN_STAGE",
                    "stage": self.game_state.stage -1,
                    "seed": self.game_state.current_seed,
                    "card_usage": self.game_state.run_stats["card_usage"]
                }
                update_profile_after_run(run_summary)
                # Reset lại thống kê thẻ bài cho tầng mới
                self.game_state.run_stats["card_usage"] = {}

                self.game_state.add_notification(f"Đã qua Tầng {self.game_state.stage - 1}! Shop được làm mới.", "game_event")
                self.refresh_shop() # Làm mới shop sau mỗi tầng
            else:
                self.game_state.round += 1
            
            # SỬA LỖI: Chỉ lưu game khi thắng
            save_game(self.game_state)
        else: # Thua hoặc hòa
            self.game_state.add_notification("Lượt chơi của bạn đã kết thúc.", "error")
            # Cập nhật profile với các chỉ số của run vừa thua (hoặc hòa)
            run_summary = {
                "result": "LOSE",
                "stage": self.game_state.stage,
                "round": self.game_state.round,
                "seed": self.game_state.current_seed,
                "card_usage": self.game_state.run_stats["card_usage"],
            }
            update_profile_after_run(run_summary)
            delete_save_file()

    def _calculate_win_rewards(self):
        """Hàm helper để tính toán phần thưởng khi thắng."""
        base_gold = 10 # Vàng cơ bản cho mỗi trận
        interest = min(self.game_state.player_gold // 10, 5) # 1 vàng cho mỗi 10 vàng, tối đa 5
        
        # 1 vàng cho mỗi quân cờ còn lại của người chơi
        piece_bonus = 0
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
            piece_bonus += len(self.game_state.board.pieces(piece_type, self.game_state.player_color))

        total_earned = base_gold + interest + piece_bonus
        self.game_state.player_gold += total_earned
        self.game_state.add_notification(f"Bạn nhận được {total_earned} vàng!", type="game_event")

    def claim_reward_and_skip(self):
        """Xử lý logic khi người chơi bỏ qua một vòng đấu."""
        skip_gold = 10 # Phần thưởng bỏ lượt
        self.game_state.player_gold += skip_gold
        self.game_state.round += 1
        # TODO: Thêm logic nhận phần thưởng đặc biệt (ví dụ: thẻ bài) ở đây
        self.add_notification(f"Bỏ qua, nhận {skip_gold} vàng. Chuẩn bị cho vòng tiếp theo.", "info")
        save_game(self.game_state) # Lưu lại tiến trình sau khi bỏ qua

    def prepare_new_match(self):
        """
        Chuẩn bị thông tin cho trận đấu tiếp theo (Boss, debuff).
        Được gọi khi vào màn hình RunSetupScreen.
        """
        # Reset debuff cũ
        self.game_state.player_debuff = None

        # Tạo một bộ sinh số ngẫu nhiên riêng cho việc chọn boss/debuff
        match_rng = random.Random(f"{self.game_state.current_seed}-{self.game_state.stage}-{self.game_state.round}")

        # Gán Boss và debuff nếu là vòng boss
        if self.game_state.round == self.game_state.max_rounds_per_stage:
            # Gán debuff cho người chơi
            available_debuffs = list(FunBossAbilities.Debuffs.keys())
            debuff_id = match_rng.choice(available_debuffs)
            self.game_state.player_debuff = FunBossAbilities.Debuffs[debuff_id]

            debuff_to_style_map = {
                "pawn_sacrifice": "The Butcher",
                "first_strike": "The Nemesis",
                "knight_ban": "The Turtle",               
                }
            # SỬA LỖI: Sử dụng một style mặc định hợp lý hơn cho Boss.
            boss_style_name = debuff_to_style_map.get(debuff_id, "The Warden")
            self.game_state.bot.style = BotStyles.get(boss_style_name)
        else:
            # SỬA LỖI: Luôn gán một style cho bot ở các vòng thường để UI hiển thị đúng.
            # Ở đây, chúng ta có thể chọn một style "cân bằng" làm mặc định.
            self.game_state.bot.style = BotStyles.get("balanced")

    def get_game_result(self):
        """Tính và cộng vàng sau khi kết thúc một ván đấu."""
        """
        Xác định kết quả của ván cờ và trả về "WIN", "LOSE", hoặc "DRAW".
        Đây là "nguồn chân lý duy nhất" cho việc xác định kết quả.
        """
        result_str = self.game_state.board.result()
        if self.game_state.board.is_checkmate():
            if self.game_state.board.turn == self.game_state.bot_color:
                return "WIN"
            else:
                return "LOSE"
        elif "1-0" in result_str and self.game_state.player_color == chess.WHITE:
            return "WIN"
        elif "0-1" in result_str and self.game_state.player_color == chess.BLACK:
            return "WIN"
        elif result_str == "*": # Game chưa kết thúc
            return None
        else: # Hòa hoặc Thua trong các trường hợp khác
            return "LOSE"

    def reset_board(self):
        """Reset bàn cờ cho trận đấu mới."""
        # Xác định màu quân của bot dựa trên lựa chọn của người chơi
        self.game_state.bot_color = not self.game_state.player_color
        self.game_state.board.reset()
        # Cập nhật độ khó của bot dựa trên stage
        # Giảm 0.1 mỗi stage, tối thiểu là 0.1
        new_mistake_rate = max(0.1, self.game_state.base_mistake_rate - (self.game_state.stage - 1) * 0.1)
        self.game_state.bot.base_mistake_rate = new_mistake_rate # Cập nhật tỉ lệ lỗi CƠ BẢN

        # Khôi phục trạng thái và lượt dùng cho các thẻ bài
        for player_card in self.game_state.player_cards:
            original_card_data = next((card for card in CARD_DATABASE if card['id'] == player_card['id']), None)
            if original_card_data:
                player_card['uses'] = original_card_data['uses']
            player_card['active'] = False # Reset trạng thái kích hoạt

        # Reset các trạng thái trong trận
        self.game_state.is_extra_turn_active = False
        self.game_state.time_stop_turns = 0
        self.game_state.time_stop_active = False
        self.game_state.turn_count = 0
        self.game_state.coin_squares.clear()
        self.game_state.cursed_pieces.clear()
        self.game_state.active_curses.clear()

        # --- ÁP DỤNG DEBUFF LÊN NGƯỜI CHƠI ---
        if self.game_state.player_debuff:
            debuff_id = self.game_state.player_debuff['id']
            if debuff_id == 'pawn_sacrifice':
                pawns = list(self.game_state.board.pieces(chess.PAWN, self.game_state.player_color))
                if pawns:
                    # SỬA LỖI: Seed cho debuff phải bao gồm cả stage và round để đảm bảo tính duy nhất.
                    # Điều này đảm bảo ở mỗi tầng khác nhau, quân tốt bị hy sinh cũng sẽ khác nhau.
                    debuff_rng = random.Random(f"{self.game_state.current_seed}-debuff-{self.game_state.stage}-{self.game_state.round}")
                    pawn_to_remove = debuff_rng.choice(pawns)
                    self.game_state.board.remove_piece_at(pawn_to_remove)
            elif debuff_id == 'first_strike':
                self.game_state.board.turn = self.game_state.bot_color

    def refresh_shop(self):
        """Làm mới shop với 2 thẻ ngẫu nhiên từ kho."""
        shop_manager.refresh_shop(self.game_state)

    def apply_passive_cards(self):
        """Áp dụng hiệu ứng của các thẻ nội tại (passive) vào đầu trận."""
        for card in self.game_state.player_cards:
            if card["type"] == "passive":
                # Thẻ dùng một lần, áp dụng và tiêu hao ngay
                if card["id"] == "knight_legion" and card["uses"] > 0: # noqa: F841
                    # SỬA LỖI: Chỉ hy sinh 1 Tốt
                    if self.game_state.player_color == chess.WHITE:
                        pawn_sq_to_sacrifice, knight_sq = chess.E2, chess.E2
                    else: # Người chơi là quân Đen
                        pawn_sq_to_sacrifice, knight_sq = chess.E7, chess.E7
                    
                    self.game_state.add_notification("Kỵ Sĩ Đoàn đã vào vị trí!", type="card_activation")
                    # SỬA LỖI: Không thay đổi bàn cờ ngay, mà tạo một Task để xử lý cả animation và logic
                    self.game_state.animation_queue.add(KnightLegionTask(self, card, pawn_sq_to_sacrifice, knight_sq))
                    card['uses'] = 0 # Đánh dấu đã sử dụng

                # Thẻ có hiệu ứng lặp lại mỗi trận (uses = -1)
                if card["id"] == "knight_economy": # noqa: F841
                    # Tính vàng dựa trên số Mã của người chơi
                    knight_count = len(self.game_state.board.pieces(chess.KNIGHT, self.game_state.player_color))
                    gold_earned = knight_count * 3
                    self.game_state.player_gold += gold_earned
                    if gold_earned > 0:
                        self.game_state.add_notification(f"Kinh Tế Kỵ Sĩ: Nhận {gold_earned} vàng từ {knight_count} Mã.", type="card_activation")

    def apply_debuff_to_bot(self, debuff, card):
        """Áp dụng hiệu ứng debuff lên bot."""
        if "mistake_rate" in debuff:
            self.game_state.bot.base_mistake_rate = debuff["mistake_rate"]
            self.game_state.add_notification(f"Bot bị ảnh hưởng bởi '{card['name']}'!", type="boss")
        if "style" in debuff:
            self.game_state.bot.style = debuff["style"]
            self.game_state.add_notification(f"Bot bị ảnh hưởng bởi '{card['name']}'!", type="boss")

    def _finalize_knight_legion(self, pawn_sq, knight_sq):
        """Hàm helper để thực sự thay đổi bàn cờ sau khi animation Kỵ Sĩ Đoàn kết thúc."""
        self.game_state.board.remove_piece_at(pawn_sq)
        self.game_state.board.set_piece_at(knight_sq, chess.Piece(chess.KNIGHT, self.game_state.player_color))

    def draw_piece_animation(self, screen, piece_images):
        """Phương thức bao bọc để gọi hàm vẽ animation từ module drawing."""
        return drawing.draw_animation(screen, self.game_state, piece_images)
