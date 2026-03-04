CARD_DATABASE = [
    # Thẻ Common
    {"id": "pawn_trade", "name": "Giao Dịch Tốt", "price": 5, "rarity": "Common", "type": "active", "uses": 1, "description": "Hy sinh 1 Tốt của bạn để nhận 6 vàng."},
    # Thẻ Rare
    {"id": "knight_economy", "name": "Kinh Tế Kỵ Sĩ", "price": 15, "rarity": "Rare", "type": "passive", "uses": -1, "description": "Bắt đầu trận đấu với 3 vàng cho mỗi Mã bạn có."},
    {"id": "knight_legion", "name": "Kỵ Sĩ Đoàn", "price": 18, "rarity": "Rare", "type": "passive", "uses": 1, "description": "Nhận ngay 1 Mã thêm, nhưng mất 1 Tốt. (Hiệu ứng tức thì, dùng 1 lần)"},
    # Thẻ Legendary
    {"id": "flash_move", "name": "Nước Đi Chớp Nhoáng", "price": 45, "rarity": "Legendary", "type": "active", "uses": 1, "description": "Đi 2 lượt liên tiếp. Không thể chiếu hết trong lượt đi thêm."},
    {"id": "mirror_revive", "name": "Gương Phản Chiếu", "price": 50, "rarity": "Legendary", "type": "passive", "uses": 1, "description": "Khi một quân cờ (không phải Tốt) của bạn bị ăn, hy sinh 1 Tốt để hồi sinh nó. (1 lần/trận)"},
    {"id": "chaos_curse", "name": "Lời Nguyền Hỗn Loạn", "price": 40, "rarity": "Legendary", "type": "active", "uses": 1, "description": "Buộc đối thủ thực hiện một nước đi ngẫu nhiên trong lượt tiếp theo của họ."},
    # Thẻ Nguyền Rủa (Debuff cho Bot)
    {"id": "trap_vengeance", "name": "Bẫy Đồng Quy Vu Tận", "price": 22, "rarity": "Rare", "type": "trap", "uses": 1, "trigger": "on_capture", "effect": "destroy_attacker", "description": "Nguyền rủa một quân cờ. Nếu bị đối thủ ăn, quân cờ tấn công đó sẽ bị phá hủy ngay lập tức."},
    {"id": "trap_time_warp", "name": "Bẫy Ngưng Đọng", "price": 25, "rarity": "Rare", "type": "trap", "uses": 1, "trigger": "on_capture", "effect": "skip_turn", "description": "Nguyền rủa một quân cờ. Nếu bị đối thủ ăn, đối thủ sẽ bị mất lượt tiếp theo."},
    {"id": "blessing_bloodthirst", "name": "Ấn Ký Khát Máu", "price": 40, "rarity": "Legendary", "type": "trap", "uses": 1, "trigger": "on_attack", "effect": "gain_shield", "description": "Yểm ấn ký lên một quân cờ. Nếu nó ăn được 2 quân địch, nó sẽ nhận được một Khiên Phép (miễn nhiễm 1 lần bị ăn)."},
]