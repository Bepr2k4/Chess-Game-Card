import chess
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from bot import SimpleBot
from animation_queue import AnimationQueue
from card_database import CARD_DATABASE

class GameState:
    """Lớp chứa toàn bộ dữ liệu trạng thái của game."""
    def __init__(self):
        self.board = chess.Board()
        self.player_color = chess.WHITE
        self.bot_color = chess.BLACK
        self.bot = SimpleBot(base_mistake_rate=0.35)

        # --- CHỈ SỐ NGƯỜI CHƠI ---
        self.settings = {
            "audio": {"master_volume": 0.8, "music_volume": 0.7, "sfx_volume": 0.9},
            "graphics": {"fullscreen": False, "v_sync": True, "resolution": f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}"}
        }
        self.restart_requested = False
        self.running = True # Cờ hiệu để chạy game
        self.player_gold = 100
        self.player_score = 0
        self.reroll_cost = 5
        self.reroll_count = 0
        self.current_seed = self.generate_random_seed()
        self.stage = 1
        self.round = 1
        self.max_rounds_per_stage = 3
        self.base_mistake_rate = 0.7

        # --- TRẠNG THÁI TRONG TRẬN ---
        self.targeting_card = None
        self.notifications = []
        self.sell_confirmation_card = None
        self.shop_notifications = []
        self.vfx_queue = []
        self.animation = None
        self.cursed_pieces = {}
        self.shielded_pieces = set() # Set để lưu các quân cờ được bảo vệ
        self.bot_emotion = "FOCUSED"
        self.active_curses = {}
        self.player_debuff = None # Debuff người chơi phải chịu trong trận boss
        self.boss_ability = None
        self.turn_count = 0
        self.coin_squares = []
        self.player_cards = []
        self.is_extra_turn_active = False
        self.time_stop_turns = 0
        self.time_stop_active = False
        self._card_database = CARD_DATABASE
        self.promotion_choice_square = None # Ô đang chờ phong cấp
        self.promotion_move_from = None # Ô bắt đầu của nước đi phong cấp
        self.shop_cards = []
        
        self.animation_queue = AnimationQueue(self)

        # --- Dữ liệu thống kê cho lượt chơi hiện tại ---
        self.run_stats = {
            "card_usage": {}, # { "card_id": count }
        }

        # --- Dữ liệu cho việc biến đổi tọa độ chuột ---
        self.mouse_scale = 1.0
        self.mouse_offset = (0, 0)

    def generate_random_seed(self, length=8):
        """Tạo một seed ngẫu nhiên gồm chữ và số."""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return "".join(random.choice(chars) for _ in range(length))

    def add_notification(self, message, type="default"):
        """Thêm một thông báo vào nhật ký."""
        self.notifications.insert(0, {"message": message, "type": type})
        if len(self.notifications) > 10:
            self.notifications.pop()