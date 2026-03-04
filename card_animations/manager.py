# Import các module animation cụ thể
from card_animations import default, knight_legion, time_stop, flash_move, trap_retaliation, trap_vengeance, shield_reversal, awakening, blessing_bloodthirst

# Tạo một dictionary để map ID thẻ bài với hàm vẽ animation tương ứng
ANIMATION_MAP = {
    "flash_move": flash_move.draw,
    "knight_legion": knight_legion.draw,
    "trap_vengeance": trap_vengeance.draw,
    "time_stop": time_stop.draw, # Animation mới cho Bẫy Ngưng Đọng
    "trap_placement": default.draw_trap_placement, # Animation chung khi đặt bẫy
    "shield_reversal": shield_reversal.draw, # Thêm animation mới
    "awakening": awakening.draw, # Animation "Thức Tỉnh"
    # SỬA LỖI: Sử dụng animation "Yểm Ấn Ký" độc đáo khi đặt bẫy
    "blessing_bloodthirst": blessing_bloodthirst.draw_placement,
    # SỬA LỖI: Thêm key cho animation kích hoạt thẻ mặc định để tránh lỗi
    "card_activation": default.draw,
}

def get_animation_function(card_id):
    """Lấy hàm animation dựa trên ID thẻ, nếu không có thì trả về hàm mặc định."""
    # SỬA LỖI: Đảm bảo luôn trả về một hàm hợp lệ, ngay cả khi card_id là None.
    return ANIMATION_MAP.get(card_id) if card_id in ANIMATION_MAP else default.draw