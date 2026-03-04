import pygame
from .base_screen import BaseScreen
from ui_elements import draw_themed_button
from ui_widgets import Slider, Toggle, Dropdown, SettingsLayout # Import các lớp widget mới
import drawing
from config import *
from save_manager import save_settings


class OptionsScreen(BaseScreen):
    def __init__(self, screen_manager, game, **kwargs):
        super().__init__(screen_manager, game, **kwargs)
        self.ui_icons = self.assets.get('ui_icons', {})
        self.apply_graphics_func = self.assets.get('apply_graphics_func')
        self.previous_screen_name = "MENU" # Mặc định quay về MENU

        # --- State của màn hình Options ---
        self.active_tab = "GRAPHICS" # Bắt đầu với tab Đồ họa để dễ kiểm tra
        self.settings_changed = False # Cờ hiệu để kích hoạt nút "Apply"
        self.restart_popup_active = False # Cờ hiệu cho popup yêu cầu khởi động lại
        # SỬA LỖI: Khởi tạo temp_settings ở đây để nó tồn tại qua các lần vào/ra màn hình
        self.temp_settings = {category: settings.copy() for category, settings in self.game.game_state.settings.items()}

        # --- UI Elements ---
        self.tab_rects = {}
        self.widgets = {} # Dictionary chứa các widget cho mỗi tab
        self.overlay_widgets = [] # Danh sách các widget cần vẽ trên cùng (VD: dropdown đang mở)
        self.layout_manager = None # Sẽ được khởi tạo trong recalculate_layout
        self.action_button_rects = {}

        # Không tạo widget ở đây nữa, sẽ tạo trong _recalculate_layout_and_widgets

    def _reset_temp_settings(self):
        """Reset lại cài đặt tạm thời từ cài đặt chính của game."""
        self.temp_settings = {category: settings.copy() for category, settings in self.game.game_state.settings.items()}
        self.settings_changed = False

    def on_enter(self, **kwargs):
        """Lưu lại màn hình trước đó khi vào màn hình Options."""
        self.previous_screen_name = kwargs.get("from_screen", "MENU")
        self.restart_popup_active = False
        self._reset_temp_settings() # Reset cài đặt tạm thời mỗi khi vào
        # Gọi hàm tính toán layout khi vào màn hình
        self._recalculate_layout_and_widgets(pygame.display.get_surface())

    def on_resize(self, new_size):
        """Ghi đè phương thức từ BaseScreen để tính toán lại layout."""
        self._recalculate_layout_and_widgets(pygame.display.get_surface())

    def _recalculate_layout_and_widgets(self, screen):
        """
        Tính toán lại toàn bộ layout và tạo lại các widget.
        Đây là phương thức trung tâm cho UI phản hồi.
        """
        screen_width, screen_height = SCREEN_WIDTH, SCREEN_HEIGHT
        
        # 1. Panel chính bao trùm toàn bộ
        panel_width, panel_height = 960, 640
        self.panel_rect = pygame.Rect(0, 0, panel_width, panel_height) # type: ignore
        self.panel_rect.center = (screen_width // 2, screen_height // 2)

        # 2. Sidebar cho các tab ở bên trái
        self.sidebar_rect = pygame.Rect(self.panel_rect.x, self.panel_rect.y, 240, self.panel_rect.height)
        # 3. Content Panel cho các tùy chọn ở bên phải
        self.content_rect = pygame.Rect(self.sidebar_rect.right, self.panel_rect.y, self.panel_rect.width - self.sidebar_rect.width, self.panel_rect.height)

        # 4. Khởi tạo Layout Manager với các quy tắc bất biến
        self.layout_manager = SettingsLayout(
            content_rect=self.content_rect,
            row_height=60,
            row_spacing=20,
            label_width=220, # Chiều rộng cố định cho vùng label
            padding_top=80)

        # Tạo lại các widget với vị trí/kích thước mới
        self.widgets.clear()
        self.widgets['AUDIO'] = self._create_audio_widgets(self.content_rect)
        self.widgets['GRAPHICS'] = self._create_graphics_widgets(self.content_rect)
        self._update_widgets_from_settings()
        # Thêm các tab khác ở đây

    def _create_audio_widgets(self, content_rect):
        widgets = []
        # Hàm callback để cập nhật setting tạm thời
        def on_volume_change(key):
            def callback(value):
                self.temp_settings['audio'][key] = round(value, 2)
                self.settings_changed = True
            return callback

        # Âm lượng tổng
        widgets.append({
            "label": "Âm lượng Tổng",
            "data_key": "master_volume", # Thêm key để dễ truy cập
            "widget": Slider(pygame.Rect(0,0, 300, 20), 0, 100, self.game.game_state.settings['audio']['master_volume'], on_volume_change('master_volume'), self.game)
        })
        # Thêm các slider khác ở đây nếu cần
        return widgets

    def _create_graphics_widgets(self, content_rect):
        widgets = []
        def on_toggle_change(key):
            def callback(value):
                self.temp_settings['graphics'][key] = value
                self.settings_changed = True
            return callback

        # Lấy danh sách độ phân giải hợp lệ
        modes = pygame.display.list_modes()
        # Lọc và định dạng lại, loại bỏ các độ phân giải quá nhỏ
        self.resolution_options = [f"{w}x{h}" for w, h in modes if w >= 1280 and h >= 720]
        self.resolution_options = sorted(list(set(self.resolution_options)), key=lambda x: int(x.split('x')[0]), reverse=True)

        widgets.append({
            "label": "Chế độ Toàn màn hình",
            "data_key": "fullscreen",
            "widget": Toggle(pygame.Rect(0,0,120,50), self.game.game_state.settings['graphics']['fullscreen'], on_toggle_change('fullscreen'), self.game)
        })
        widgets.append({
            "label": "Đồng bộ dọc (V-Sync)",
            "data_key": "v_sync",
            "widget": Toggle(pygame.Rect(0,0,120,50), self.game.game_state.settings['graphics']['v_sync'], on_toggle_change('v_sync'), self.game)
        })
        widgets.append({
            "label": "Độ phân giải",
            "data_key": "resolution",
            "widget": Dropdown(pygame.Rect(0,0,220,50), self.resolution_options, self.game.game_state.settings['graphics']['resolution'], on_toggle_change('resolution'), self.game)
        })
        return widgets

    def _update_widgets_from_settings(self):
        """Cập nhật trạng thái của widget từ self.temp_settings."""
        for widget_data in self.widgets.get("AUDIO", []):
            if isinstance(widget_data['widget'], Slider):
                data_key = widget_data.get("data_key")
                if data_key and data_key in self.temp_settings['audio']:
                    widget_data['widget'].set_value(self.temp_settings['audio'][data_key])
        
        for widget_data in self.widgets.get("GRAPHICS", []):
            if isinstance(widget_data['widget'], Toggle):
                data_key = widget_data.get("data_key")
                if data_key and data_key in self.temp_settings['graphics']:
                    widget_data['widget'].is_on = self.temp_settings['graphics'][data_key]
            if isinstance(widget_data['widget'], Dropdown):
                data_key = widget_data.get("data_key")
                if data_key and data_key in self.temp_settings['graphics']:
                    selected = self.temp_settings['graphics'][data_key]
                    # Đảm bảo tùy chọn đã lưu vẫn còn trong danh sách hợp lệ
                    widget_data['widget'].selected_option = selected if selected in self.resolution_options else self.resolution_options[0]

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.QUIT: # type: ignore
                self.game.game_state.running = False

            # Nếu popup đang hiện, nó sẽ bắt hết các sự kiện
            if self.restart_popup_active:
                self._handle_restart_popup_events(e)
                continue

            # Ưu tiên xử lý sự kiện cho các widget
            # Lặp ngược để dropdown đang mở được xử lý trước
            widget_handled = False
            for widget_data in reversed(self.widgets.get(self.active_tab, [])):
                if widget_data['widget'].handle_event(e):
                    widget_handled = True
                    # Đóng các dropdown khác nếu một widget được tương tác
                    self._close_other_dropdowns(widget_data['widget'])
                    # Vẫn cho phép _handle_general_events chạy để xử lý các nút bấm
                    # nhưng widget_handled sẽ ngăn nó xử lý lại.
                    break 

            # Xử lý các sự kiện chung (tab, nút bấm) sau khi đã xử lý widget.
            self._handle_general_events(e, widget_handled) # Sửa lỗi: widget_handled không được sử dụng đúng cách

    def _handle_restart_popup_events(self, e):
        """Xử lý sự kiện riêng cho popup yêu cầu khởi động lại."""
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.game.restart_requested = True
            self.game.running = False

    def _close_other_dropdowns(self, current_widget):
        """Đóng tất cả các dropdown khác ngoại trừ cái hiện tại."""
        for widgets_in_tab in self.widgets.values():
            for widget_data in widgets_in_tab:
                if isinstance(widget_data['widget'], Dropdown) and widget_data['widget'] is not current_widget:
                    widget_data['widget'].is_open = False

    def _handle_general_events(self, e, widget_handled): # Sửa lỗi: widget_handled không được sử dụng đúng cách
        """Xử lý các sự kiện không thuộc về widget."""
        # SỬA LỖI: Sử dụng tọa độ đã được biến đổi (e.pos)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: # type: ignore
            # Click vào Tab
            for tab_name, rect in self.tab_rects.items():
                if rect.collidepoint(e.pos):
                    self.active_tab = tab_name
                    return # Nếu click vào tab, không cần xử lý thêm

            # SỬA LỖI: Chỉ xử lý các nút hành động nếu không có widget nào được click
            if not widget_handled:
                if self.action_button_rects.get("save_exit") and self.action_button_rects["save_exit"].collidepoint(e.pos):
                    self._save_and_exit()
                elif self.action_button_rects.get("apply") and self.action_button_rects["apply"].collidepoint(e.pos) and self.settings_changed: # type: ignore
                    self.apply_graphics_func(self.temp_settings)
                    self._apply_settings()
                elif self.action_button_rects.get("default") and self.action_button_rects["default"].collidepoint(e.pos):
                    print("Reset to default clicked")

    def _apply_settings(self):
        """Áp dụng các thay đổi từ temp_settings vào game.settings."""
        self.game.game_state.settings = {category: settings.copy() for category, settings in self.temp_settings.items()}
        self.settings_changed = False
        print("Settings applied.")

    def _save_and_exit(self):
        """Xử lý logic khi nhấn nút Lưu & Thoát."""
        # SỬA LỖI: Phải áp dụng cài đặt đồ họa ngay lập tức, tương tự như nút "Apply".
        graphics_changed = self.game.game_state.settings['graphics'] != self.temp_settings['graphics']
        if graphics_changed:
            self.apply_graphics_func(self.temp_settings)

        # Áp dụng cài đặt vào game state và lưu ra file
        self._apply_settings()
        save_settings(self.game.game_state)

        self.screen_manager.switch_to(self.previous_screen_name)

    def draw(self, screen):
        # 1. Vẽ lại màn hình trước đó ở nền
        if self.previous_screen_name in self.screen_manager._screens:
            self.screen_manager._screens[self.previous_screen_name].draw(screen)

        # 2. Vẽ lớp phủ mờ
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # Nếu layout chưa được tính toán, hãy tính toán nó
        if not hasattr(self, 'panel_rect'):
            self._recalculate_layout_and_widgets(screen)

        # 3. Vẽ Panel chính và tiêu đề
        drawing.draw_panel_bezel(screen, self.panel_rect) # Dùng bezel đơn giản hơn
        pygame.draw.rect(screen, (30, 35, 45, 230), self.panel_rect) # Nền bán trong suốt
        title_text = MENU_FONT.render("CÀI ĐẶT", True, WHITE_TEXT)
        screen.blit(title_text, title_text.get_rect(centerx=self.panel_rect.centerx, y=self.panel_rect.y + 20))

        # 4. Vẽ các Tab
        self._draw_tabs(screen, self.panel_rect)

        # 5. Vẽ nội dung của Tab đang hoạt động
        self._draw_tab_content(screen, self.content_rect)

        # 6. Vẽ các nút hành động ở dưới
        self._draw_action_buttons(screen, self.panel_rect)

        # 7. SỬA LỖI: Vẽ các widget "nổi" (overlay) sau cùng
        for widget in self.overlay_widgets:
            widget.draw(screen)
        self.overlay_widgets.clear() # Xóa danh sách sau khi vẽ

        # 7. Vẽ popup yêu cầu khởi động lại (nếu cần)
        if self.restart_popup_active:
            self._draw_restart_popup(screen)

    def _draw_tabs(self, screen, panel_rect):
        tabs = [("GRAPHICS", "Đồ Họa"), ("AUDIO", "Âm Thanh"), ("CONTROLS", "Điều Khiển"), ("GAMEPLAY", "Gameplay")]
        tab_height, tab_width = 60, self.sidebar_rect.width - 40
        start_y = self.sidebar_rect.y + 80
        self.tab_rects.clear()

        for i, (key, text) in enumerate(tabs):
            rect = pygame.Rect(self.sidebar_rect.centerx - tab_width / 2, start_y + i * (tab_height + 10), tab_width, tab_height)
            self.tab_rects[key] = rect
            is_active = (self.active_tab == key)
            # SỬA LỖI: Sử dụng tọa độ ảo cho hover
            is_hovered = rect.collidepoint(drawing.get_transformed_mouse_pos(self.game.game_state))
            color = GOLD_ACCENT if is_active else pygame.Color(80,80,80)
            draw_themed_button(screen, rect, text, color, ROYAL_PURPLE_DARK, is_hovered)

    def _draw_tab_content(self, screen, content_rect):
        """Vẽ nội dung cho tab đang được chọn."""
        self.overlay_widgets.clear() # Xóa danh sách widget nổi của frame trước
        widgets_to_draw = self.widgets.get(self.active_tab, [])
        
        # Vẽ một đường phân cách tinh tế
        pygame.draw.line(screen, METALLIC_TRIM, (content_rect.left, content_rect.top), (content_rect.left, content_rect.bottom), 2)

        # --- SỬ DỤNG LAYOUT MANAGER ĐỂ VẼ ---
        for index, item in enumerate(widgets_to_draw):
            label_text = item['label']
            widget = item['widget']

            # 1. Lấy Rect cho Nhãn và vẽ
            label_surf = INFO_FONT.render(label_text, True, WHITE_TEXT)
            label_rect = self.layout_manager.get_label_rect(index, label_surf)
            screen.blit(label_surf, label_rect)

            # 2. Lấy Rect cho Widget và gán nó
            if isinstance(widget, Slider):
                control_rect = self.layout_manager.get_control_rect(index)
            else: # Toggle, Dropdown
                control_rect = self.layout_manager.get_control_rect(index, widget_width=widget.rect.width)
            
            # Gán Rect đã được tính toán cho widget
            # Widget sẽ tự căn giữa theo chiều dọc dựa trên rect này
            widget.rect.midleft = control_rect.midleft
            widget.rect.height = control_rect.height # Đảm bảo chiều cao nhất quán

            # 3. Vẽ Widget
            if isinstance(widget, Dropdown) and widget.is_open:
                self.overlay_widgets.append(widget)
            else:
                widget.draw(screen)

    def _draw_action_buttons(self, screen, panel_rect):
        self.action_button_rects.clear()
        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state) # type: ignore

        btn_width, btn_height = 150, 50
        padding = 20

        # Nút Lưu & Thoát
        save_exit_rect = pygame.Rect(panel_rect.right - btn_width - padding, panel_rect.bottom - btn_height - padding, btn_width, btn_height)
        draw_themed_button(screen, save_exit_rect, "Lưu & Thoát", ERROR_RED, ROYAL_PURPLE_DARK, save_exit_rect.collidepoint(mouse_pos_virtual))
        self.action_button_rects["save_exit"] = save_exit_rect # type: ignore

        # Nút Áp dụng
        apply_rect = pygame.Rect(save_exit_rect.x - btn_width - padding, save_exit_rect.y, btn_width, btn_height)
        apply_color = ARCANE_GLOW if self.settings_changed else pygame.Color(80,80,80)
        draw_themed_button(screen, apply_rect, "Áp dụng", apply_color, ROYAL_PURPLE_DARK, apply_rect.collidepoint(mouse_pos_virtual) and self.settings_changed)
        self.action_button_rects["apply"] = apply_rect # type: ignore

        # Nút Mặc định
        default_rect = pygame.Rect(panel_rect.x + padding, save_exit_rect.y, btn_width, btn_height)
        draw_themed_button(screen, default_rect, "Mặc Định", pygame.Color(80,80,80), ROYAL_PURPLE_DARK, default_rect.collidepoint(mouse_pos_virtual))
        self.action_button_rects["default"] = default_rect # type: ignore

    def _draw_restart_popup(self, screen):
        """Vẽ hộp thoại yêu cầu khởi động lại game."""
        # Lớp phủ mờ hơn
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 230))
        screen.blit(overlay, (0, 0))

        # Hộp thoại
        box_width, box_height = 600, 250
        box_rect = pygame.Rect(0, 0, box_width, box_height)
        box_rect.center = screen.get_rect().center
        drawing.draw_panel_bezel(screen, box_rect)
        pygame.draw.rect(screen, (30, 35, 45, 240), box_rect)
        
        title_surf = MENU_FONT.render("Cần Khởi Động Lại", True, GOLD_ACCENT)
        prompt_surf = INFO_FONT.render("Cài đặt đồ họa đã thay đổi. Game sẽ khởi động lại.", True, WHITE_TEXT)
        continue_surf = INFO_FONT.render("Nhấn phím bất kỳ để tiếp tục...", True, (150, 150, 150))
        screen.blit(title_surf, title_surf.get_rect(centerx=box_rect.centerx, y=box_rect.y + 40))
        screen.blit(prompt_surf, prompt_surf.get_rect(centerx=box_rect.centerx, y=box_rect.y + 110))
        screen.blit(continue_surf, continue_surf.get_rect(centerx=box_rect.centerx, y=box_rect.y + 160))
        box_width, box_height = 600, 250
        box_rect = pygame.Rect(0, 0, box_width, box_height)
        box_rect.center = screen.get_rect().center
        drawing.draw_panel_bezel(screen, box_rect)
        pygame.draw.rect(screen, (30, 35, 45, 240), box_rect)
        
        title_surf = MENU_FONT.render("Cần Khởi Động Lại", True, GOLD_ACCENT)
        prompt_surf = INFO_FONT.render("Cài đặt đồ họa đã thay đổi. Game sẽ khởi động lại.", True, WHITE_TEXT)
        continue_surf = INFO_FONT.render("Nhấn phím bất kỳ để tiếp tục...", True, (150, 150, 150))
        screen.blit(title_surf, title_surf.get_rect(centerx=box_rect.centerx, y=box_rect.y + 40))
        screen.blit(prompt_surf, prompt_surf.get_rect(centerx=box_rect.centerx, y=box_rect.y + 110))
        screen.blit(continue_surf, continue_surf.get_rect(centerx=box_rect.centerx, y=box_rect.y + 160))