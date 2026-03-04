import pygame
import os
import chess
import sys
from config import PIECE_SYMBOLS # type: ignore

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả dev và PyInstaller """
    try:
        # PyInstaller tạo một thư mục tạm và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_piece_symbol(piece):
    """Lấy ký hiệu cho quân cờ để tải ảnh."""
    color = 'w' if piece.color == chess.WHITE else 'b'
    piece_type = piece.symbol().upper()
    return f"{color}{piece_type}"

def load_piece_images():
    """Tải hình ảnh các quân cờ từ thư mục cục bộ."""
    piece_images = {}
    pieces_dir = resource_path(os.path.join('images', 'pieces'))
    for symbol in PIECE_SYMBOLS: # type: ignore
        try:
            img_path = os.path.join(pieces_dir, f"{symbol}.png")
            img = pygame.image.load(img_path).convert_alpha()
            # Sửa lỗi: Chỉ tải ảnh, không scale ở đây. Việc scale sẽ được thực hiện động trong hàm draw.
            piece_images[symbol] = img
        except pygame.error as e:
            print(f"Lỗi khi tải ảnh cho quân {symbol} từ file: {e}")
    return piece_images

def load_card_images(card_list):
    """Tải hình ảnh các thẻ bài từ file cục bộ."""
    card_images = {}
    cards_dir = resource_path(os.path.join('images', 'cards'))
    for card_info in card_list:
        card_id = card_info['id']
        card_name = card_info['name'] # Giữ lại để in thông báo lỗi
        try:
            img_path = os.path.join(cards_dir, f"{card_id}.png")
            card_images[card_id] = pygame.image.load(img_path)
        except pygame.error:
            print(f"Cảnh báo: Không tìm thấy ảnh cho thẻ '{card_name}' tại '{img_path}'. Sẽ sử dụng màu thay thế.")
    return card_images

def load_emotion_icons():
    """Tải hình ảnh các icon cảm xúc của Bot."""
    emotion_icons = {}
    icons_dir = resource_path(os.path.join('images', 'icons'))
    for emotion in ["focused", "arrogant", "panic"]:
        try:
            img_path = os.path.join(icons_dir, f"{emotion}.png")
            emotion_icons[emotion.upper()] = pygame.image.load(img_path).convert_alpha()
        except pygame.error:
            print(f"Cảnh báo: Không tìm thấy ảnh cho cảm xúc '{emotion}' tại '{img_path}'.")
            emotion_icons[emotion.upper()] = None # Để xử lý nếu thiếu ảnh
    return emotion_icons

def load_ui_icons():
    """Tải các icon cho giao diện người dùng (Vàng, Tầng)."""
    ui_icons = {}
    icons_dir = resource_path(os.path.join('images', 'icons'))
    for icon_name in ["stage", "icon_knight_white", "icon_knight_black", "icon_coin_bag", "icon_play", "icon_options", "icon_quit", "icon_back"]:
        try:
            img_path = os.path.join(icons_dir, f"{icon_name}.png")
            ui_icons[icon_name] = pygame.image.load(img_path).convert_alpha()
        except pygame.error:
            print(f"Cảnh báo: Không tìm thấy ảnh cho icon UI '{icon_name}' tại '{img_path}'.")
            ui_icons[icon_name] = None # Gán None để không gây lỗi khi sử dụng
    return ui_icons