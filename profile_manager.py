import json
import os

PROFILE_FILE = "profile.json"

def get_default_profile():
    """Trả về cấu trúc dữ liệu mặc định cho một hồ sơ mới."""
    return {
        "total_runs_started": 0,
        "total_wins": 0, # Số lần thắng cả một run (ví dụ: qua được tầng cuối)
        "highest_stage_reached": 1,
        "card_usage": {}, # { "card_id": count }
        "piece_moves": {}, # { "PIECE_TYPE": count }
        "run_history": [], # Danh sách các lượt chơi gần nhất
    }

def load_profile():
    """Tải dữ liệu hồ sơ người chơi từ file."""
    if not os.path.exists(PROFILE_FILE):
        return get_default_profile()
    try:
        with open(PROFILE_FILE, 'r') as f:
            profile_data = json.load(f)
        # Đảm bảo tất cả các key mặc định đều tồn tại
        default_data = get_default_profile()
        for key, value in default_data.items():
            if key not in profile_data:
                profile_data[key] = value
        return profile_data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Lỗi khi tải hồ sơ, tạo hồ sơ mới. Lỗi: {e}")
        return get_default_profile()

def save_profile(profile_data):
    """Lưu dữ liệu hồ sơ người chơi vào file."""
    try:
        with open(PROFILE_FILE, 'w') as f:
            json.dump(profile_data, f, indent=4)
        print("Hồ sơ người chơi đã được lưu.")
    except IOError as e:
        print(f"Lỗi khi lưu hồ sơ: {e}")

def update_profile_after_run(run_stats):
    """Cập nhật hồ sơ tổng với dữ liệu từ lượt chơi vừa kết thúc."""
    profile = load_profile()
    
    profile["total_runs_started"] += 1
    profile["highest_stage_reached"] = max(profile["highest_stage_reached"], run_stats.get("stage", 1))

    # Thêm lượt chơi hiện tại vào lịch sử và giới hạn ở 10 lượt gần nhất
    profile["run_history"].insert(0, run_stats)
    if len(profile["run_history"]) > 10:
        profile["run_history"].pop()
    
    for card_id, count in run_stats.get("card_usage", {}).items():
        profile["card_usage"][card_id] = profile["card_usage"].get(card_id, 0) + count
        
    save_profile(profile)