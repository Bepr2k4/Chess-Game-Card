import pygame
import os

pygame.font.init()

# --- Kích thước & Layout Toàn cục ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
DIMENSION = 8

# --- BỐ CỤC GIAO DIỆN ĐỘNG (DYNAMIC LAYOUT) ---
# Chuyển các Rect cố định thành các hàm để tính toán lại dựa trên kích thước màn hình
def get_notification_rect():
    # Chiếm 20% chiều rộng bên trái
    return pygame.Rect(SCREEN_WIDTH * 0.01, SCREEN_HEIGHT * 0.02, SCREEN_WIDTH * 0.2, SCREEN_HEIGHT * 0.96)

def get_board_rect():
    # SỬA LỖI: Tối ưu hóa kích thước bàn cờ
    # Kích thước bàn cờ sẽ là giá trị nhỏ nhất giữa (80% chiều cao) và (45% chiều rộng)
    board_size = min(SCREEN_HEIGHT * 0.8, SCREEN_WIDTH * 0.45)
    # Căn giữa theo chiều ngang
    board_x = (SCREEN_WIDTH - board_size) / 2
    # Dịch bàn cờ lên một chút để có không gian cho panel dưới
    return pygame.Rect(board_x, SCREEN_HEIGHT * 0.01, board_size, board_size)

def get_sq_size(board_rect):
    return board_rect.width // DIMENSION

def get_bottom_panel_rect(board_rect):
    # SỬA LỖI: Đặt vị trí và kích thước một cách rõ ràng hơn
    return pygame.Rect(board_rect.x, board_rect.bottom + 10, board_rect.width, 120)

def get_sidebar_rect():
    # Chiếm 20% chiều rộng bên phải
    return pygame.Rect(SCREEN_WIDTH * 0.79, SCREEN_HEIGHT * 0.02, SCREEN_WIDTH * 0.2, SCREEN_HEIGHT * 0.96)

def get_menu_panel_rect(screen_width, screen_height):
    rect = pygame.Rect(0, 0, 380, 360) # Giữ kích thước cố định
    rect.center = (screen_width // 2, screen_height // 2 + 80) # Căn giữa và dịch xuống
    return rect

# --- BẢNG MÀU HOÀNG GIA (ROYAL COLOR PALETTE) ---
ROYAL_PURPLE_DARK = pygame.Color("#2a2a3a") # type: ignore # Nền chính
ROYAL_PURPLE_LIGHT = pygame.Color("#4a4a6a") # Nền phụ
GOLD_ACCENT = pygame.Color("#f0c475")      # Viền, văn bản quan trọng
GOLD_HIGHLIGHT = pygame.Color("#fff5e1")   # Highlight cho vàng
ARCANE_GLOW = pygame.Color("#a0d2eb")       # Hào quang ma thuật
WHITE_TEXT = pygame.Color("#e0e0e0")       # Văn bản thông thường
DISABLED_TEXT = pygame.Color("#7a7a8c")    # Văn bản/Icon bị vô hiệu hóa
SUCCESS_GREEN = pygame.Color("#75f0a0")
ERROR_RED = pygame.Color("#f07575")

GAME_BG = ROYAL_PURPLE_DARK

# --- Fantasy Menu UI Colors ---
FANTASY_DARK_BG = pygame.Color(22, 25, 38)
METALLIC_TRIM = pygame.Color(70, 78, 95)
METALLIC_HIGHLIGHT = pygame.Color(130, 140, 160)

RARITY_COLORS = {
    "Common": WHITE_TEXT,
    "Rare": ARCANE_GLOW,
    "Legendary": GOLD_ACCENT
,
}

# --- Fonts (Sử dụng tệp .ttf) ---
import sys # Import sys để sử dụng trong resource_path

# Hàm resource_path đã được định nghĩa trong assets.py, nhưng chúng ta cần nó ở đây trước khi
# các hằng số font được khởi tạo. Tốt nhất là định nghĩa nó ở một nơi chung hoặc ở đây.
# Để đơn giản, tôi sẽ định nghĩa lại nó ở đây.
def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả dev và PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

PIXEL_FONT_PATH = resource_path(os.path.join("fonts", "SairaStencilOne-Regular.ttf"))
CLEAN_FONT_PATH = resource_path(os.path.join("fonts", "NotoSans-Regular.ttf"))
MENU_FONT = pygame.font.Font(PIXEL_FONT_PATH, 40)
BUTTON_FONT = pygame.font.Font(PIXEL_FONT_PATH, 28)
CARD_FONT = pygame.font.Font(PIXEL_FONT_PATH, 20)
INFO_FONT = pygame.font.Font(CLEAN_FONT_PATH, 22)
CARD_DESC_FONT = pygame.font.Font(CLEAN_FONT_PATH, 16)
PIECE_SYMBOLS = [f"{color}{piece}" for color in "wb" for piece in "PRNBQK"]