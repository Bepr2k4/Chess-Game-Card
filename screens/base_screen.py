class BaseScreen:
    """
    Lớp cơ sở cho tất cả các màn hình trong game.
    Định nghĩa một giao diện chung để ScreenManager có thể tương tác.
    """
    def __init__(self, screen_manager, game, **kwargs):
        self.screen_manager = screen_manager
        self.game = game
        # Nhận các tài nguyên dùng chung
        self.assets = kwargs
        self.last_known_size = None # Lưu lại kích thước màn hình cuối cùng (của virtual_screen)

    def handle_events(self, events):
        """Xử lý input của người dùng (chuột, bàn phím)."""
        raise NotImplementedError

    def update(self, dt):
        """Cập nhật logic của màn hình (ví dụ: animation)."""
        pass # Không phải màn hình nào cũng cần update

    def draw(self, screen):
        """
        Kiểm tra kích thước màn hình và gọi hàm vẽ cụ thể.
        Đây là nơi kích hoạt recalculate_layout một cách tự động.
        SỬA LỖI HIỆU NĂNG: Chỉ tính toán lại layout khi kích thước thay đổi.
        """ # SỬA LỖI: Logic này đã được chuyển ra ngoài, hàm draw chỉ cần gọi _draw.
        self._draw(screen)

    def on_resize(self, new_size):
        """Xử lý khi kích thước cửa sổ thay đổi. Các lớp con có thể override."""
        # Hàm này sẽ được gọi bởi main loop, và nó sẽ kích hoạt việc tính toán lại layout
        self.last_known_size = None # Đánh dấu để draw() có thể tính toán lại

    def recalculate_layout(self, screen):
        """Tính toán lại vị trí và kích thước của các thành phần UI. Lớp con phải implement."""
        pass

    def _draw(self, screen):
        """Hàm vẽ thực tế, lớp con phải override."""
        raise NotImplementedError