import json
import os
import time

SAVE_FILE = "savegame.json"
SETTINGS_FILE = "settings.json"

def save_game(game_state):
    """Lưu trạng thái hiện tại của game vào file."""
    save_data = {
        "id": f"{game_state.current_seed}-{int(time.time())}", # Tạo ID duy nhất
        "seed": game_state.current_seed,
        "stage": game_state.stage,
        "player_gold": game_state.player_gold,
        "player_cards": game_state.player_cards,
        "reroll_cost": game_state.reroll_cost,
        "reroll_count": game_state.reroll_count,
        # Lưu thêm các chỉ số quan trọng khác nếu cần
    }
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(save_data, f, indent=4)
        print("Game đã được lưu.")
    except Exception as e:
        print(f"Lỗi khi lưu game: {e}")

def save_debug_log(game_state):
    """Lưu trạng thái game vào một file log riêng khi có lỗi xảy ra."""
    log_file = f"crash_log_{int(time.time())}.json"
    save_data = {
        "id": f"CRASH-{game_state.current_seed}-{int(time.time())}",
        "seed": game_state.current_seed,
        "stage": game_state.stage,
        "round": game_state.round,
        "player_gold": game_state.player_gold,
        "player_cards": game_state.player_cards,
        "shop_cards": game_state.shop_cards,
        "board_fen": game_state.board.fen(), # Thêm FEN của bàn cờ để biết chính xác vị trí quân cờ
        "player_debuff": game_state.player_debuff,
        "bot_style": game_state.bot.style,
        "turn_count": game_state.turn_count,
    }
    try:
        with open(log_file, 'w') as f:
            json.dump(save_data, f, indent=4)
        print(f"Đã lưu log gỡ lỗi vào file: {log_file}")
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi đang cố gắng lưu log gỡ lỗi: {e}")

def load_game(game_controller):
    """Tải trạng thái game từ file và cập nhật vào game object."""
    if not os.path.exists(SAVE_FILE):
        return False
    
    try:
        with open(SAVE_FILE, 'r') as f:
            save_data = json.load(f)
        
        game_state = game_controller.game_state
        # Tải lại seed và áp dụng nó ngay lập tức
        game_state.current_seed = save_data.get("seed", game_state.generate_random_seed())
        import random
        random.seed(game_state.current_seed)

        game_state.stage = save_data.get("stage", 1)
        game_state.player_gold = save_data.get("player_gold", 100)
        game_state.player_cards = save_data.get("player_cards", [])
        game_state.reroll_cost = save_data.get("reroll_cost", 5)
        game_state.reroll_count = save_data.get("reroll_count", 0)

        # SỬA LỖI: Làm mới lại shop ngay sau khi tải game với đúng seed và reroll_count.
        # Điều này đảm bảo shop luôn nhất quán khi tiếp tục game.
        game_controller.refresh_shop()
        print("Game đã được tải.")
        return True
    except Exception as e:
        print(f"Lỗi khi tải game: {e}")
        return False

def has_save_file():
    """Kiểm tra xem file save có tồn tại không."""
    return os.path.exists(SAVE_FILE)

def delete_save_file():
    """Xóa file save nếu nó tồn tại."""
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
        print("File save đã được xóa.")

def save_settings(game_state):
    """Lưu các cài đặt hiện tại vào file settings.json."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(game_state.settings, f, indent=4)
        print("Cài đặt đã được lưu.")
    except Exception as e:
        print(f"Lỗi khi lưu cài đặt: {e}")

def load_settings(game_state):
    """Tải cài đặt từ file và cập nhật vào game object."""
    if not os.path.exists(SETTINGS_FILE):
        # Nếu không có file, lưu cài đặt mặc định để tạo file
        save_settings(game_state)
        return

    try:
        with open(SETTINGS_FILE, 'r') as f:
            loaded_settings = json.load(f)
        
        # Cập nhật một cách an toàn, chỉ ghi đè các khóa tồn tại
        for category, settings in loaded_settings.items():
            if category in game_state.settings:
                # SỬA LỖI: Đảm bảo các khóa con cũng tồn tại trước khi cập nhật
                for key, value in settings.items():
                    if key in game_state.settings[category]:
                        game_state.settings[category][key] = value
        print("Cài đặt đã được tải.")
    except Exception as e:
        print(f"Lỗi khi tải cài đặt: {e}. Sử dụng cài đặt mặc định.")