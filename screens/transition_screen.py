import pygame
from .base_screen import BaseScreen
from transitions import draw_vs_transition, draw_board_reveal
from config import *

class TransitionScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        super().__init__(screen_manager, game, **kwargs)
        self.piece_images = self.assets.get('piece_images')
        self.timer = 0
        self.duration = 240 # Tổng thời gian chuyển cảnh (khoảng 4 giây ở 60 FPS)

    def on_enter(self):
        """Được gọi mỗi khi chuyển đến màn hình này."""
        self.timer = self.duration
        # Áp dụng hiệu ứng thẻ passive ngay khi bắt đầu chuyển cảnh
        self.game.apply_passive_cards() # game ở đây là game_controller

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT: # type: ignore
                self.game.game_state.running = False

    def update(self, dt):
        self.timer -= 1
        if self.timer <= 0:
            self.screen_manager.switch_to("PLAYING")

    def _draw(self, screen):
        screen.fill(GAME_BG)
        # Animation "VS." diễn ra trong nửa đầu
        if self.timer > self.duration / 2:
            # Cần import draw_pieces từ drawing
            # from drawing import draw_pieces # Không cần thiết
            draw_vs_transition(screen, self.game.game_state, self.timer - (self.duration / 2))
        # Animation "Bàn cờ xuất hiện"
        else:
            from drawing import draw_pieces
            draw_board_reveal(screen, self.game.game_state, self.piece_images, self.timer, draw_pieces)