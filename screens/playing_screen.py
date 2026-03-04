import pygame
import chess
from .base_screen import BaseScreen
import drawing
from config import *
from ui_elements import draw_sell_confirmation_box, draw_tooltip

class PlayingScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        super().__init__(screen_manager, game, **kwargs)
        self.piece_images = self.assets.get('piece_images')
        self.card_images = self.assets.get('card_images')
        self.selected_square = None
        self.player_clicks = []
        self.card_rects = []
        self.trap_slot_rects = [] # Thêm rect cho các ô trap

    def _handle_board_click(self, e):
        """Xử lý logic khi người chơi click vào bàn cờ."""
        # SỬA LỖI: Không cần lấy surface thật, vì tọa độ chuột đã được scale (nếu cần)
        board_rect = get_board_rect()
        sq_size = get_sq_size(board_rect)
        col = (e.pos[0] - board_rect.x) // sq_size
        row = (e.pos[1] - board_rect.y) // sq_size

        if not (0 <= col < DIMENSION and 0 <= row < DIMENSION):
            return

        if self.game.game_state.player_color == chess.BLACK:
            row, col = 7 - row, 7 - col # type: ignore

        # Xử lý khi đang chọn mục tiêu cho thẻ bài
        if self.game.game_state.targeting_card:
            square = chess.square(col, 7 - row)
            self.game.resolve_card_target(square)
            return

        # Xử lý di chuyển quân cờ
        if self.selected_square == (row, col):
            self.selected_square = None
            self.player_clicks = []
        else:
            self.selected_square = (row, col)
            self.player_clicks.append(self.selected_square)
            # SỬA LỖI: Kiểm tra và thêm thông báo cho các nước đi đặc biệt
            from_sq = chess.square(col, 7 - row)
            has_castling = False
            has_en_passant = False
            for move in self.game.game_state.board.legal_moves:
                if move.from_square == from_sq:
                    if self.game.game_state.board.is_castling(move): has_castling = True
                    if self.game.game_state.board.is_en_passant(move): has_en_passant = True
            if has_castling:
                self.game.add_notification("Bạn có thể thực hiện Nhập Thành!", "game_event")
            if has_en_passant:
                self.game.add_notification("Bạn có thể Bắt Tốt Qua Đường!", "game_event")

        if len(self.player_clicks) == 2:
            start_sq = chess.square(self.player_clicks[0][1], 7 - self.player_clicks[0][0])
            end_sq = chess.square(self.player_clicks[1][1], 7 - self.player_clicks[1][0])
            move_uci = f"{chess.square_name(start_sq)}{chess.square_name(end_sq)}"
            
            piece = self.game.game_state.board.piece_at(start_sq)
            if piece and piece.piece_type == chess.PAWN and (chess.square_rank(end_sq) in [0, 7]):
                # THAY ĐỔI: Không tự động phong Hậu, mà kích hoạt trạng thái chọn phong cấp
                self.game.game_state.promotion_choice_square = end_sq
                self.game.game_state.promotion_move_from = start_sq
                return # Dừng lại và chờ người chơi chọn
            if not self.game.player_move(move_uci):
                self.player_clicks.pop()
                self.selected_square = self.player_clicks[0]
            else:
                self.selected_square = None
                self.player_clicks = []

    def _handle_card_click(self, e):
        """Xử lý logic khi người chơi click vào một thẻ bài."""
        # Xử lý click vào thẻ trên tay
        for rect, card in self.card_rects:
            if rect.collidepoint(e.pos):
                if e.button == 1 and self.game.game_state.board.turn == self.game.game_state.player_color:
                    if card['type'] == 'active':
                        self.game.activate_card(card['name'])
                    elif card['type'] == 'trap': # Kích hoạt trap từ tay
                        # Click chuột trái vào thẻ trap trên tay không làm gì cả
                        pass
                elif e.button == 3: # Chuột phải
                    self.game.game_state.sell_confirmation_card = card

                # Reset các lựa chọn khác khi click vào thẻ
                self.player_clicks = []
                self.selected_square = None
                return True
        
        # Xử lý click vào thẻ trap đã trang bị
        for rect, card in self.trap_slot_rects:
            if rect.collidepoint(e.pos):
                if e.button == 1 and self.game.game_state.board.turn == self.game.game_state.player_color:
                    self.game.activate_card(card['name']) # Kích hoạt bẫy từ slot
                # Chuột phải vào slot không làm gì cả
                return True
        return False

    def handle_events(self, events):
        is_animating = self.game.game_state.animation_queue.is_active()
        is_player_turn = self.game.game_state.board.turn == self.game.game_state.player_color

        for e in events:
            if e.type == pygame.QUIT:
                self.game.game_state.running = False

            # --- XỬ LÝ LỰA CHỌN PHONG CẤP ---
            if self.game.game_state.promotion_choice_square is not None and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                choice_rects = drawing.get_promotion_choice_rects(self.game.game_state) # Không cần screen
                
                # Kiểm tra debuff cấm phong Mã
                debuff = self.game.game_state.player_debuff
                knight_promotion_banned = debuff and debuff['id'] == 'knight_ban'

                for piece_char, rect in choice_rects.items():
                    if rect.collidepoint(e.pos) and not (knight_promotion_banned and piece_char == 'n'):
                        start_sq = self.game.game_state.promotion_move_from
                        end_sq = self.game.game_state.promotion_choice_square
                        move_uci = f"{chess.square_name(start_sq)}{chess.square_name(end_sq)}{piece_char}"
                        
                        self.game.player_move(move_uci)
                        
                        # Reset trạng thái
                        self.game.game_state.promotion_choice_square = None
                        self.game.game_state.promotion_move_from = None
                        self.selected_square = None
                        self.player_clicks = []
                        return # Đã xử lý, dừng lại
            
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.screen_manager.switch_to("PAUSE_MENU")
                return # Dừng xử lý các sự kiện khác

            # Xử lý click cho hộp thoại xác nhận bán thẻ
            if self.game.game_state.sell_confirmation_card and e.type == pygame.MOUSEBUTTONDOWN:
                # SỬA LỖI: Không cần truyền screen, vì hàm này chỉ tính toán Rect
                confirm_button, _ = draw_sell_confirmation_box(pygame.display.get_surface(), self.game.game_state, e.pos)
                if confirm_button and confirm_button.collidepoint(e.pos):
                    self.game.sell_card(self.game.game_state.sell_confirmation_card['name'])
                self.game.game_state.sell_confirmation_card = None
                continue
            
            if e.type == pygame.MOUSEBUTTONDOWN and not is_animating and self.game.game_state.promotion_choice_square is None:
                # SỬA LỖI: Ưu tiên xử lý hủy đặt bẫy bằng chuột phải TRƯỚC TIÊN
                # để tránh xung đột với các hành động chuột phải khác (như bán thẻ).
                if e.button == 3 and self.game.game_state.targeting_card:
                    card = self.game.game_state.targeting_card
                    if card['type'] == 'trap':
                        card['uses'] += 1 # Hoàn lại lượt sử dụng
                    self.game.game_state.targeting_card = None
                    self.game.add_notification(f"Đã hủy đặt '{card['name']}'.", "info")
                    self.selected_square = None # Reset lựa chọn ô cờ
                    continue

                # Nếu không phải là hành động hủy, tiếp tục xử lý các click khác
                if self._handle_card_click(e):
                    continue
                
                if is_player_turn:
                    self._handle_board_click(e)

    def update(self, dt):
        self.game.game_state.animation_queue.update(pygame.display.get_surface(), self.piece_images, self.card_images)
        if not self.game.game_state.animation_queue.is_active():
            # Sửa lỗi: Chỉ cần kiểm tra is_game_over, không cần get_game_result
            if self.game.game_state.board.is_game_over() and not self.game.game_state.time_stop_active:
                self.screen_manager.switch_to("GAME_OVER")
            elif not self.game.game_state.board.turn == self.game.game_state.player_color:
                self.game.bot_move()

    def _draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        self.card_rects, self.trap_slot_rects = drawing.draw_game_state(screen, self.game.game_state, self.selected_square, self.piece_images, self.card_images) # Nhận lại trap_slot_rects
        drawing.draw_notifications(screen, self.game.game_state) # type: ignore
        # SỬA LỖI: Khôi phục việc gọi hàm draw_vfx để quản lý vòng đời animation
        drawing.draw_vfx(screen, self.game.game_state, self.card_images, self.piece_images)

        drawing.draw_active_curses(screen, self.game.game_state) # Vẽ các hiệu ứng lời nguyền đang tồn tại

        # SỬA LỖI: Vẽ animation di chuyển quân cờ trong vòng lặp draw
        # Hàm draw_piece_animation sẽ tự kiểm tra xem self.game.animation có tồn tại không
        self.game.draw_piece_animation(screen, self.piece_images)

        # Vẽ giao diện lựa chọn phong cấp nếu cần
        if self.game.game_state.promotion_choice_square is not None:
            drawing.draw_promotion_choice(screen, self.game.game_state) # Screen ở đây là virtual_screen

        hovered_card_data = drawing.get_hovered_card(self.card_rects + self.trap_slot_rects, mouse_pos)
        if hovered_card_data and not self.game.game_state.sell_confirmation_card:
            draw_tooltip(screen, hovered_card_data, mouse_pos) # Không có gợi ý ở màn hình chơi
        
        if self.game.game_state.sell_confirmation_card:
            draw_sell_confirmation_box(screen, self.game.game_state, mouse_pos)