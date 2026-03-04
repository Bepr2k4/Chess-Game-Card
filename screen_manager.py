import pygame


class ScreenManager:
    """
    Quản lý các màn hình và chuyển đổi giữa chúng.
    Thay thế cho cơ chế game_state dựa trên chuỗi.
    """
    def __init__(self, game):
        self.game = game
        self._screens = {}
        self.current_screen = None

    def add_screen(self, name, screen_instance):
        """Thêm một instance của màn hình vào trình quản lý."""
        self._screens[name] = screen_instance

    def switch_to(self, screen_name, **kwargs):
        """Chuyển sang một màn hình khác."""
        if screen_name in self._screens:
            if self.current_screen:
                self.current_screen.last_known_size = None # Reset khi chuyển màn hình
            self.current_screen = self._screens[screen_name]
            # Gọi hàm on_enter nếu màn hình có định nghĩa nó
            if hasattr(self.current_screen, 'on_enter'):
                self.current_screen.on_enter(**kwargs)
            # SỬA LỖI: Tính toán layout lần đầu tiên SAU KHI màn hình đã được khởi tạo hoàn chỉnh.
            # Điều này giải quyết lỗi thứ tự khởi tạo.
            self.current_screen.recalculate_layout(pygame.display.get_surface())
            print(f"Switching to {screen_name}")
        else:
            raise ValueError(f"Screen '{screen_name}' not found.")

    def handle_events(self, events, game_state):
        if self.current_screen:
            transformed_events = []
            for event in events:
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                    # Tạo một bản sao của event để không sửa đổi event gốc
                    transformed_event = pygame.event.Event(event.type, event.dict)
                    
                    # Áp dụng phép biến đổi ngược cho tọa độ chuột
                    # 1. Trừ offset (letterbox)
                    # 2. Chia cho scale
                    transformed_pos_x = int((event.pos[0] - game_state.mouse_offset[0]) / game_state.mouse_scale)
                    transformed_pos_y = int((event.pos[1] - game_state.mouse_offset[1]) / game_state.mouse_scale)
                    transformed_event.pos = (transformed_pos_x, transformed_pos_y)
                    transformed_events.append(transformed_event)
                else:
                    transformed_events.append(event)
            self.current_screen.handle_events(transformed_events) # type: ignore

    def update(self, dt):
        if self.current_screen:
            self.current_screen.update(dt)

    def draw(self, screen):
        if self.current_screen:
            self.current_screen.draw(screen)