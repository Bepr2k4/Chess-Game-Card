import pygame
from collections import deque
import chess
import random

class Task:
    """Lớp cơ sở cho một tác vụ trong hàng đợi animation."""
    def __init__(self, game):
        self.game = game
        self.started = False
        self.finished = False

    def start(self):
        self.started = True

    def update(self, screen, piece_images, card_images):
        pass

    def is_finished(self):
        return self.finished

class MovePieceTask(Task):
    """Tác vụ di chuyển một quân cờ."""
    def __init__(self, game, move, owner='player', duration=200): # Nhanh hơn 1.5 lần
        super().__init__(game)
        self.move = move
        self.owner = owner
        self.duration = duration

    def start(self):
        super().start()
        # Không làm gì ở đây nữa, việc tạo animation đã được chuyển sang game.py

    def update(self, screen, piece_images, card_images):
        # SỬA LỖI: Nhiệm vụ duy nhất của Task này là áp dụng nước đi vào logic bàn cờ
        # sau khi animation (được quản lý bởi vòng lặp draw) đã hoàn tất.
        # Animation kết thúc khi game.animation là None.

        if self.game.game_state.animation is None:
            self.game.apply_move(self.move)
            # SỬA LỖI DEADLOCK: Sau khi áp dụng nước đi và thêm các hiệu ứng vào hàng đợi, tác vụ này hoàn thành.
            self.finished = True

class VFXTask(Task):
    """Tác vụ hiển thị một hiệu ứng hình ảnh (VFX)."""
    def __init__(self, game, vfx_data):
        super().__init__(game)
        self.vfx_data = vfx_data
        self.vfx_data['is_task'] = True # Đánh dấu để không bị xóa ngay

    def start(self):
        super().start()
        self.game.game_state.vfx_queue.append(self.vfx_data) # Đã đúng, không cần sửa

    def update(self, screen, piece_images, card_images):
        # SỬA LỖI DEADLOCK: Nhiệm vụ của Task này chỉ là thêm VFX vào hàng đợi.
        # Vòng đời của VFX (timer, xóa) sẽ do hàm draw_vfx quản lý.
        # Do đó, Task này hoàn thành ngay lập tức.
        self.finished = True

class KnightLegionTask(Task):
    """Tác vụ đặc biệt cho animation và logic của thẻ Kỵ Sĩ Đoàn."""
    def __init__(self, game, card, pawn_sq, knight_sq):
        super().__init__(game)
        self.card = card
        self.pawn_sq = pawn_sq
        self.knight_sq = knight_sq
        self.summoned = False # Cờ hiệu để đảm bảo chỉ triệu hồi 1 lần
        self.vfx_data = {
            'type': 'card_activation',
            'card': self.card,
            'timer': 75,       # Nhanh hơn 1.5 lần
            'initial_timer': 75,
            'is_task': True # Đánh dấu để không bị xóa ngay
        }

    def start(self):
        super().start()
        self.game.game_state.vfx_queue.append(self.vfx_data)

    def update(self, screen, piece_images, card_images):
        # Hàm draw_vfx sẽ tự xử lý việc vẽ
        # SỬA LỖI DEADLOCK: Task này phải tự quản lý timer của mình để biết khi nào kết thúc.
        # Nó không thể dựa vào logic của VFXTask thông thường.
        self.vfx_data['timer'] -= 1
        # Khi animation kết thúc, thực hiện logic game
        if self.vfx_data['timer'] <= 0 and not self.summoned:
            self.game._finalize_knight_legion(self.pawn_sq, self.knight_sq)
            self.summoned = True # Đánh dấu đã triệu hồi
            self.finished = True

class WaitTask(Task):
    """Tác vụ chờ đợi một khoảng thời gian."""
    def __init__(self, game, duration_ms):
        super().__init__(game)
        self.duration = duration_ms
        self.start_time = 0

    def start(self):
        super().start()
        self.start_time = pygame.time.get_ticks()

    def update(self, screen, piece_images, card_images):
        if pygame.time.get_ticks() - self.start_time >= self.duration:
            self.finished = True

class NotificationTask(Task):
    """Tác vụ hiển thị một thông báo."""
    def __init__(self, game, message, type="default"):
        super().__init__(game)
        self.message = message
        self.type = type

    def start(self):
        super().start()
        self.game.add_notification(self.message, self.type)
        self.finished = True # Tác vụ này hoàn thành ngay lập tức

class RemovePieceTask(Task):
    """Tác vụ xóa một quân cờ tại một ô cụ thể."""
    def __init__(self, game, square_to_remove, reason_card=None):
        super().__init__(game)
        self.square = square_to_remove
        self.reason_card = reason_card

    def start(self):
        super().start()
        try:
            # Kiểm tra xem có quân cờ ở đó không trước khi xóa
            if self.game.game_state.board.piece_at(self.square):
                self.game.game_state.board.remove_piece_at(self.square)
                if self.reason_card:
                    self.game.add_notification("Quân cờ của đối thủ đã bị tiêu diệt bởi bẫy!", "boss")
            # SỬA LỖI DEADLOCK: Không can thiệp vào game.animation ở đây.
        finally:
            self.finished = True

class DestroyPieceTask(Task):
    """Tác vụ tìm và phá hủy một quân cờ dựa trên các điều kiện."""
    def __init__(self, game, piece_type, color, exclude_squares=None, reason_card=None, rng=None):
        super().__init__(game)
        self.piece_type = piece_type
        self.color = color
        self.exclude_squares = exclude_squares if exclude_squares is not None else []
        self.reason_card = reason_card
        self.rng = rng if rng is not None else random # Sử dụng RNG mặc định nếu không được cung cấp

    def start(self):
        super().start()
        try:
            candidate_squares = list(self.game.game_state.board.pieces(self.piece_type, self.color))
            # SỬA LỖI: Loại bỏ nhiều ô thay vì chỉ một
            candidate_squares = [sq for sq in candidate_squares if sq not in self.exclude_squares]

            if candidate_squares:
                # SỬA LỖI: Sử dụng RNG đã được gieo mầm để đảm bảo tính nhất quán
                piece_to_destroy_square = self.rng.choice(candidate_squares)
                self.game.game_state.board.remove_piece_at(piece_to_destroy_square)
                if self.reason_card:
                    self.game.add_notification(f"Đối thủ cũng mất một quân {chess.piece_name(self.piece_type)}!", "boss")
            else:
                if self.reason_card:
                    self.game.add_notification(f"Bẫy '{self.reason_card.get('name')}' không tìm thấy mục tiêu phù hợp!", "info")
        finally:
            self.finished = True

class AnimationQueue:
    """Quản lý và thực thi một chuỗi các tác vụ animation."""
    def __init__(self, game):
        self.game = game
        self.tasks = deque()
        self.active_task = None

    def add(self, task):
        """Thêm một tác vụ vào hàng đợi."""
        self.tasks.append(task)

    def update(self, screen, piece_images, card_images):
        """Cập nhật hàng đợi, được gọi mỗi frame."""
        if self.active_task is None and self.tasks:
            self.active_task = self.tasks.popleft()
            self.active_task.start()

        if self.active_task:
            self.active_task.update(screen, piece_images, card_images)
            if self.active_task.is_finished():
                self.active_task = None

    def is_active(self):
        """Kiểm tra xem hàng đợi có đang bận không."""
        return self.active_task is not None or len(self.tasks) > 0

    def clear(self):
        """Xóa tất cả các tác vụ khỏi hàng đợi."""
        self.tasks.clear()
        self.active_task = None