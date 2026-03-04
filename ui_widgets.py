import pygame
from config import *
from ui_elements import draw_themed_button
import drawing

class SettingsLayout:
    """
    Quản lý toàn bộ bố cục cho màn hình Settings theo dạng hàng (row-based).
    Đây là "nguồn chân lý duy nhất" cho vị trí của các widget.
    """
    def __init__(self, content_rect, row_height, row_spacing, label_width, padding_top):
        self.content_rect = content_rect
        self.row_height = row_height
        self.row_spacing = row_spacing
        self.label_width = label_width
        self.padding_top = padding_top
        
        # Vùng cho nhãn (bên trái)
        self.label_zone_x = self.content_rect.x + 40
        
        # Vùng cho widget điều khiển (bên phải)
        self.control_zone_x = self.label_zone_x + self.label_width + 20
        self.control_zone_width = self.content_rect.right - 40 - self.control_zone_x

    def get_row_rect(self, index):
        """Lấy Rect cho toàn bộ một hàng dựa trên chỉ số của nó."""
        y = self.content_rect.y + self.padding_top + index * (self.row_height + self.row_spacing)
        return pygame.Rect(self.content_rect.x, y, self.content_rect.width, self.row_height)

    def get_label_rect(self, index, label_surf):
        """Lấy Rect cho nhãn, căn giữa theo chiều dọc trong hàng."""
        row_rect = self.get_row_rect(index)
        label_rect = label_surf.get_rect(midleft=(self.label_zone_x, row_rect.centery))
        return label_rect

    def get_control_rect(self, index, widget_width=None):
        """Lấy Rect cho widget điều khiển, căn giữa theo chiều dọc trong hàng."""
        row_rect = self.get_row_rect(index)
        if widget_width:
            # Nếu widget có chiều rộng cố định (Toggle, Dropdown), căn lề phải
            return pygame.Rect(self.control_zone_x + self.control_zone_width - widget_width, row_rect.y, widget_width, self.row_height)
        else:
            # Nếu không (Slider), nó sẽ chiếm gần hết không gian
            return pygame.Rect(self.control_zone_x, row_rect.y, self.control_zone_width - 80, self.row_height)

class Slider:
    """
    Widget thanh trượt cho phép người dùng chọn một giá trị trong một khoảng.
    """
    def __init__(self, rect, min_val, max_val, initial_val, on_change_callback, game):
        self.rect = pygame.Rect(rect)
        self.knob_rect = pygame.Rect(0, 0, 20, 30)
        self.min_val = min_val
        self.max_val = max_val
        self.on_change_callback = on_change_callback
        self.is_dragging = False
        self.set_value(initial_val)
        self.game = game # Lưu tham chiếu đến game controller

    def set_value(self, value):
        """Đặt giá trị của slider (0.0 to 1.0)."""
        self.value = max(0.0, min(1.0, value))
        self.knob_rect.centery = self.rect.centery
        self.knob_rect.centerx = self.rect.x + self.rect.width * self.value

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) or self.knob_rect.collidepoint(event.pos):
                self.is_dragging = True
                self._update_value_from_pos(event.pos)
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            self._update_value_from_pos(event.pos)
            return True
        return False

    def _update_value_from_pos(self, pos):
        new_value = (pos[0] - self.rect.x) / self.rect.width
        self.set_value(new_value)
        self.on_change_callback(self.value)

    def draw(self, screen):
        # --- HỆ THỐNG VẼ BẤT BIẾN CHO SLIDER ---
        # 1. Tính toán lại vị trí Knob dựa trên giá trị hiện tại
        # Điều này đảm bảo knob luôn đúng vị trí, bất kể rect của slider ở đâu
        self.knob_rect.centery = self.rect.centery
        self.knob_rect.centerx = self.rect.x + self.rect.width * self.value

        # 2. Vẽ Track (rãnh trượt)
        track_height = 8
        track_rect = pygame.Rect(self.rect.x, self.rect.centery - track_height // 2, self.rect.width, track_height)
        pygame.draw.rect(screen, ROYAL_PURPLE_DARK, track_rect, border_radius=4)

        # 3. Vẽ Filled Track (phần đã lấp đầy)
        filled_width = self.knob_rect.centerx - track_rect.x
        filled_rect = pygame.Rect(track_rect.x, track_rect.y, filled_width, track_rect.height)
        pygame.draw.rect(screen, ARCANE_GLOW, filled_rect, border_radius=4)

        # 4. Vẽ Knob (nút kéo)
        pygame.draw.rect(screen, WHITE_TEXT, self.knob_rect, border_radius=6)

        # 5. Vẽ giá trị số bên phải
        display_value = int(self.min_val + (self.max_val - self.min_val) * self.value)
        value_text = INFO_FONT.render(str(display_value), True, WHITE_TEXT)
        text_rect = value_text.get_rect(midleft=(self.rect.right + 20, self.rect.centery)) # Vị trí tương đối với rect của slider
        screen.blit(value_text, text_rect)

class Toggle:
    """
    Widget nút bật/tắt cho các giá trị boolean.
    """
    def __init__(self, rect, initial_state, on_change_callback, game):
        self.rect = pygame.Rect(rect)
        self.is_on = initial_state
        self.on_change_callback = on_change_callback
        self.game = game

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_on = not self.is_on
                self.on_change_callback(self.is_on)
                return True
        return False

    def draw(self, screen):
        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)
        is_hovered = self.rect.collidepoint(mouse_pos_virtual)

        if self.is_on:
            text = "BẬT"
            color = ARCANE_GLOW
        else:
            text = "TẮT"
            color = pygame.Color(80, 80, 80)
        
        draw_themed_button(screen, self.rect, text, color, ROYAL_PURPLE_DARK, is_hovered)

class Dropdown:
    """
    Widget dropdown cho phép chọn một tùy chọn từ danh sách.
    """
    def __init__(self, rect, options, initial_option, on_change_callback, game):
        self.rect = pygame.Rect(rect)
        self.options = options
        self.selected_option = initial_option
        self.on_change_callback = on_change_callback
        self.is_open = False
        self.option_rects = []
        self.game = game
        # --- Thuộc tính cho thanh cuộn ---
        self.scroll_offset = 0
        self.max_visible_items = 5 # Giới hạn số lượng item hiển thị
        self.is_dragging_scrollbar = False
        self.scrollbar_handle_y_offset = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            
            if self.is_open and len(self.options) > self.max_visible_items:
                # Lấy các rect của thanh cuộn từ hàm draw
                _, scrollbar_handle_rect = self._get_scrollbar_rects()
                if scrollbar_handle_rect and scrollbar_handle_rect.collidepoint(event.pos):
                    self.is_dragging_scrollbar = True
                    self.scrollbar_handle_y_offset = event.pos[1] - scrollbar_handle_rect.y
                    return True

            if self.is_open:
                # Lấy rect của khu vực danh sách
                list_rect = self._get_list_rect()
                # Nếu click ra ngoài cả nút chính và danh sách, đóng lại
                if not self.rect.collidepoint(event.pos) and not list_rect.collidepoint(event.pos):
                    self.is_open = False
                    return False # Cho phép các nút khác nhận sự kiện

            if self.is_open:
                for i, option_rect in enumerate(self.option_rects):
                    if option_rect.collidepoint(event.pos):
                        self.selected_option = self.options[i]
                        self.on_change_callback(self.selected_option)
                        self.is_open = False
                        return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging_scrollbar:
                self.is_dragging_scrollbar = False
                return True

        if event.type == pygame.MOUSEMOTION and self.is_dragging_scrollbar:
            scrollbar_rect, _ = self._get_scrollbar_rects()
            total_content_height = len(self.options) * self.rect.height
            visible_height = self.max_visible_items * self.rect.height
            
            # Tính toán vị trí mới của handle
            new_handle_y = event.pos[1] - self.scrollbar_handle_y_offset
            # Giới hạn vị trí handle trong rãnh cuộn
            new_handle_y = max(scrollbar_rect.y, min(new_handle_y, scrollbar_rect.bottom - self._get_scrollbar_handle_height()))
            
            # Chuyển đổi vị trí handle thành scroll_offset
            scroll_percentage = (new_handle_y - scrollbar_rect.y) / (scrollbar_rect.height - self._get_scrollbar_handle_height())
            self.scroll_offset = -scroll_percentage * (total_content_height - visible_height)
            return True

        if self.is_open and event.type == pygame.MOUSEWHEEL:
            total_content_height = len(self.options) * self.rect.height
            visible_height = self.max_visible_items * self.rect.height
            max_scroll = total_content_height - visible_height

            if max_scroll > 0:
                self.scroll_offset -= event.y * 20 # event.y là 1 hoặc -1
                # Giới hạn scroll_offset
                self.scroll_offset = max(-max_scroll, min(0, self.scroll_offset))
                return True

        return False

    def draw(self, screen):
        mouse_pos_virtual = drawing.get_transformed_mouse_pos(self.game.game_state)
        is_hovered = self.rect.collidepoint(mouse_pos_virtual)

        # Vẽ hộp chính
        draw_themed_button(screen, self.rect, self.selected_option, pygame.Color(80,80,80), ROYAL_PURPLE_DARK, is_hovered)

        # Vẽ mũi tên
        arrow_points = [(self.rect.right - 20, self.rect.centery - 5),
                        (self.rect.right - 10, self.rect.centery - 5),
                        (self.rect.right - 15, self.rect.centery + 5)]
        if self.is_open:
             arrow_points = [(self.rect.right - 20, self.rect.centery + 5),
                             (self.rect.right - 10, self.rect.centery + 5),
                             (self.rect.right - 15, self.rect.centery - 5)]
        pygame.draw.polygon(screen, WHITE_TEXT, arrow_points)

        # Vẽ danh sách tùy chọn nếu đang mở
        if self.is_open:
            list_rect = self._get_list_rect()
            
            # Tạo một surface tạm để cắt cúp (clipping)
            list_surface = pygame.Surface(list_rect.size, pygame.SRCALPHA)
            
            # Vẽ nền cho danh sách
            pygame.draw.rect(list_surface, pygame.Color(40,45,60, 240), list_surface.get_rect(), border_radius=8)
            pygame.draw.rect(list_surface, ROYAL_PURPLE_DARK, list_surface.get_rect(), width=2, border_radius=8)

            self.option_rects = []
            for i, option in enumerate(self.options):
                # Tính toán rect tương đối với list_surface
                option_local_rect = pygame.Rect(0, i * self.rect.height + self.scroll_offset, self.rect.width, self.rect.height)
                
                # Rect toàn cục để bắt sự kiện chuột
                option_global_rect = option_local_rect.move(list_rect.topleft)
                self.option_rects.append(option_global_rect)

                option_hovered = option_global_rect.collidepoint(mouse_pos_virtual)
                bg_color = ROYAL_PURPLE_LIGHT if option_hovered else pygame.Color(60,65,80)
                
                pygame.draw.rect(list_surface, bg_color, option_local_rect)
                text_surf = INFO_FONT.render(option, True, WHITE_TEXT)
                list_surface.blit(text_surf, text_surf.get_rect(center=option_local_rect.center))

            # Vẽ thanh cuộn nếu cần
            if len(self.options) > self.max_visible_items:
                self._draw_scrollbar(list_surface)

            # Vẽ surface danh sách lên màn hình chính
            screen.blit(list_surface, list_rect.topleft)

    def _get_list_rect(self):
        """Tính toán Rect cho khu vực danh sách thả xuống."""
        visible_item_count = min(len(self.options), self.max_visible_items)
        list_height = visible_item_count * self.rect.height
        return pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, list_height)

    def _get_scrollbar_rects(self):
        """Tính toán Rect cho thanh cuộn và tay cầm."""
        list_rect = self._get_list_rect()
        scrollbar_width = 15
        scrollbar_rect = pygame.Rect(list_rect.right - scrollbar_width - 2, list_rect.y + 2, scrollbar_width, list_rect.height - 4)
        
        handle_height = self._get_scrollbar_handle_height()
        
        total_content_height = len(self.options) * self.rect.height
        visible_height = self.max_visible_items * self.rect.height
        max_scroll = total_content_height - visible_height
        
        scroll_percentage = self.scroll_offset / -max_scroll if max_scroll > 0 else 0
        handle_y = scrollbar_rect.y + (scrollbar_rect.height - handle_height) * scroll_percentage
        
        scrollbar_handle_rect = pygame.Rect(scrollbar_rect.x, handle_y, scrollbar_width, handle_height)
        return scrollbar_rect, scrollbar_handle_rect

    def _get_scrollbar_handle_height(self):
        """Tính toán chiều cao của tay cầm thanh cuộn."""
        visible_ratio = self.max_visible_items / len(self.options)
        return max(20, self._get_list_rect().height * visible_ratio) # Chiều cao tối thiểu là 20px

    def _draw_scrollbar(self, surface):
        """Vẽ thanh cuộn lên một surface cho trước."""
        scrollbar_rect, scrollbar_handle_rect = self._get_scrollbar_rects()
        # Chuyển đổi tọa độ về tương đối với surface
        scrollbar_local_rect = scrollbar_rect.move(-self._get_list_rect().x, -self._get_list_rect().y)
        scrollbar_handle_local_rect = scrollbar_handle_rect.move(-self._get_list_rect().x, -self._get_list_rect().y)

        # Vẽ rãnh cuộn
        pygame.draw.rect(surface, ROYAL_PURPLE_DARK, scrollbar_local_rect, border_radius=6)
        # Vẽ tay cầm
        pygame.draw.rect(surface, DISABLED_TEXT, scrollbar_handle_local_rect, border_radius=6)