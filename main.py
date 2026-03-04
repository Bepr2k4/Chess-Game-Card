import pygame
import sys
import os
import time
import traceback # Import traceback để in lỗi chi tiết
import game

from game import ChessGame
from config import *
from assets import load_piece_images, load_card_images, load_emotion_icons, load_ui_icons

# SỬA LỖI: Import module 'drawing' để có thể gán thuộc tính,
# và import các hàm cần thiết một cách tường minh.
import drawing
from save_manager import load_game, has_save_file, load_settings, save_debug_log
from screen_manager import ScreenManager
from card_database import CARD_DATABASE
# SỬA LỖI: Import từ package 'screens'
from screens.menu_screen import MenuScreen
from screens.run_setup_screen import RunSetupScreen
from screens.shop_screen import ShopScreen
from screens.choose_side_screen import ChooseSideScreen
from screens.confirm_new_game_screen import ConfirmNewGameScreen
from screens.seed_input_screen import SeedInputScreen
from screens.playing_screen import PlayingScreen
from screens.pause_menu_screen import PauseMenuScreen
from screens.transition_screen import TransitionScreen
from screens.options_screen import OptionsScreen
from screens.game_over_screen import GameOverScreen
from screens.profile_screen import ProfileScreen

def check_assets():
    """Kiểm tra sự tồn tại của các file và thư mục tài nguyên quan trọng."""
    assets_ok = True
    # Kiểm tra fonts
    if not os.path.exists(PIXEL_FONT_PATH):
        print(f"Lỗi: Không tìm thấy file font '{os.path.basename(PIXEL_FONT_PATH)}' tại '{PIXEL_FONT_PATH}'")
        assets_ok = False
    if not os.path.exists(CLEAN_FONT_PATH):
        print(f"Lỗi: Không tìm thấy file font '{os.path.basename(CLEAN_FONT_PATH)}' tại '{CLEAN_FONT_PATH}'")
        assets_ok = False

    # Kiểm tra các thư mục chứa ảnh
    script_dir = os.path.dirname(__file__)
    image_dirs_to_check = ['images', 'images/cards', 'images/icons', 'images/pieces']
    for dir_name in image_dirs_to_check:
        dir_path = os.path.join(script_dir, dir_name)
        if not os.path.isdir(dir_path):
            print(f"Lỗi: Không tìm thấy thư mục tài nguyên '{dir_name}' tại '{dir_path}'")
            assets_ok = False

    # Kiểm tra các file icon quan trọng, nhưng chỉ cảnh báo nếu thiếu
    icons_dir = os.path.join(script_dir, 'images', 'icons')
    for icon_name in ["icon_play.png", "icon_options.png", "icon_quit.png", "icon_back.png"]:
        icon_path = os.path.join(icons_dir, icon_name)
        if not os.path.exists(icon_path):
            print(f"Cảnh báo: Không tìm thấy file icon '{icon_name}' tại '{icon_path}'. Nút bấm sẽ không có icon.")
            
    return assets_ok

def apply_graphics_settings(game_settings, current_screen=None):
    """Áp dụng các cài đặt đồ họa vào cửa sổ game."""
    flags = pygame.RESIZABLE # Bật cờ cho phép thay đổi kích thước cửa sổ
    
    # Đọc độ phân giải từ settings
    try:
        res_str = game_settings.get('graphics', {}).get('resolution', f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        w, h = map(int, res_str.split('x'))
        size = (w, h)
    except ValueError:
        size = (SCREEN_WIDTH, SCREEN_HEIGHT) # Fallback

    if game_settings.get('graphics', {}).get('fullscreen', False):
        flags |= pygame.FULLSCREEN # Thêm cờ fullscreen, không ghi đè
    
    vsync = 1 if game_settings.get('graphics', {}).get('v_sync', True) else 0
    print(f"Applying graphics settings: size={size}, fullscreen={flags!=0}, vsync={vsync}")
    # Trả về surface mới
    return pygame.display.set_mode(size, flags, vsync=vsync)

def main():
    # --- 1. KIỂM TRA TÀI NGUYÊN TRƯỚC KHI KHỞI TẠO PYGAME ---
    if not check_assets():
        # Chờ người dùng đọc lỗi
        time.sleep(5)
        return # Thoát nếu thiếu tài nguyên

    # --- 2. KHỞI TẠO PYGAME VÀ CỬA SỔ (Thứ tự chuẩn) ---
    os.environ['SDL_VIDEO_CENTERED'] = '1' # Đảm bảo cửa sổ game luôn được căn giữa
    pygame.init()
    pygame.display.set_caption("Cờ Vua")
    clock = pygame.time.Clock()
    
    game = ChessGame()

    # Tải cài đặt (nếu có)
    load_settings(game.game_state)

    # --- 3. TẠO CỬA SỔ GAME ---
    screen = apply_graphics_settings(game.game_state.settings) # Khởi tạo lần đầu


    # --- TẠO VIRTUAL SCREEN ---
    # Đây là "thế giới game" thật của bạn, có kích thước cố định.
    virtual_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    # --- 4. TẢI TÀI NGUYÊN (SAU KHI ĐÃ CÓ MÀN HÌNH) ---
    piece_images = load_piece_images()
    card_images = load_card_images(CARD_DATABASE) # Sử dụng game instance đã tạo
    emotion_icons = load_emotion_icons()
    ui_icons = load_ui_icons()
    drawing.emotion_icons = emotion_icons
    drawing.ui_icons = ui_icons
    raw_background_image = None
    try:
        images_dir = os.path.join(os.path.dirname(__file__), 'images')
        raw_background_image = pygame.image.load(os.path.join(images_dir, "background.png")).convert()
    except pygame.error:
        print("Cảnh báo: Không tìm thấy 'background.png'.")

    # Tải game nếu có file save
    has_save = load_game(game)


    game.running = True # Cờ hiệu để chạy game
    
    # --- Khởi tạo Screen Manager ---
    screen_manager = ScreenManager(game)

    # Tạo các instance của màn hình và thêm vào manager
    # Truyền các tài nguyên dùng chung vào cho các màn hình
    shared_assets = {
        'raw_background_image': raw_background_image, # Truyền ảnh gốc, chưa scale
        'piece_images': piece_images,
        'card_images': card_images,
        'emotion_icons': emotion_icons,
        'ui_icons': ui_icons,
        'has_save_func': has_save_file, # Truyền hàm để kiểm tra
        'apply_graphics_func': apply_graphics_settings # Truyền hàm để áp dụng cài đặt
    }
    menu_screen = MenuScreen(screen_manager, game, **shared_assets)
    screen_manager.add_screen("MENU", menu_screen)
    
    # Thêm các màn hình khác
    screen_manager.add_screen("RUN_SETUP", RunSetupScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("SHOP", ShopScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("CHOOSE_SIDE", ChooseSideScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("CONFIRM_NEW_GAME", ConfirmNewGameScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("SEED_INPUT", SeedInputScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("PLAYING", PlayingScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("PAUSE_MENU", PauseMenuScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("TRANSITION_TO_PLAY", TransitionScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("GAME_OVER", GameOverScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("OPTIONS", OptionsScreen(screen_manager, game, **shared_assets))
    screen_manager.add_screen("PROFILE", ProfileScreen(screen_manager, game, **shared_assets))

    # Bắt đầu với màn hình Menu
    screen_manager.switch_to("MENU")
    
    # --- Vòng lặp chính của game (State Machine) --- #
    while game.game_state.running:
        # 1. KIỂM SOÁT FPS & DELTA TIME
        # Giới hạn game ở 60 FPS. clock.tick() trả về thời gian (ms) từ lần gọi trước.
        # Chuyển sang giây (chia cho 1000) để có delta time chuẩn.
        dt = clock.tick(60) / 1000.0
        game.game_state.dt = dt # Lưu dt để các hệ thống khác (animation) có thể sử dụng

        # (Tùy chọn cho dev) Log FPS để kiểm tra hiệu năng
        # print(f"FPS: {clock.get_fps():.2f}")

        # 2. XỬ LÝ SỰ KIỆN (với tọa độ chuột đã được biến đổi)
        events = pygame.event.get()
        screen_manager.handle_events(events, game.game_state)

        # Xử lý sự kiện thay đổi kích thước cửa sổ ở cấp cao nhất
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                # SỬA LỖI: Chỉ áp dụng lại cài đặt nếu kích thước thực sự thay đổi # type: ignore
                if screen.get_size() != event.size:
                    screen = apply_graphics_settings(game.game_state.settings) # Áp dụng cài đặt mới
                    if screen_manager.current_screen: # type: ignore
                        screen_manager.current_screen.on_resize(event.size)

        # 3. CẬP NHẬT LOGIC GAME
        screen_manager.update(dt)

        # 4. VẼ LÊN VIRTUAL SCREEN
        screen_manager.draw(virtual_screen)

        # 5. SCALE VÀ HIỂN THỊ LÊN MÀN HÌNH THẬT
        # Đây là bước cuối cùng và quan trọng nhất để hiển thị mọi thứ.
        screen.fill((0, 0, 0)) # Xóa màn hình thật với màu đen (cho letterbox)

        # Tính toán tỉ lệ và vị trí để giữ nguyên aspect ratio
        scale_x = screen.get_width() / virtual_screen.get_width()
        scale_y = screen.get_height() / virtual_screen.get_height()
        scale = min(scale_x, scale_y)
        scaled_width = int(virtual_screen.get_width() * scale)
        scaled_height = int(virtual_screen.get_height() * scale) # type: ignore
        scaled_surf = pygame.transform.smoothscale(virtual_screen, (scaled_width, scaled_height))
        blit_pos = ((screen.get_width() - scaled_width) / 2, (screen.get_height() - scaled_height) / 2)
        screen.blit(scaled_surf, blit_pos)
        
        # SỬA LỖI: Cập nhật thông tin scale và offset để các module khác có thể sử dụng
        game.game_state.mouse_scale = scale
        game.game_state.mouse_offset = blit_pos

        pygame.display.flip() # Cập nhật màn hình

    if game.game_state.restart_requested:
        main() # Gọi lại hàm main # type: ignore

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # In ra lỗi chi tiết nhất có thể
        print("\n--- LỖI KHÔNG MONG MUỐN XẢY RA ---")
        print(f"Lỗi: {e}")
        print("\n--- DẤU VẾT LỖI (TRACEBACK) ---")
        traceback.print_exc()
        # Tự động lưu lại trạng thái game khi crash để gỡ lỗi
        save_debug_log(game.game_state)
        # Giữ cửa sổ console mở để người dùng có thể đọc lỗi
        input("\nNhấn Enter để thoát...")
    finally:
        pygame.quit()
        sys.exit()
