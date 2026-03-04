import random
from card_database import CARD_DATABASE

def add_shop_notification(game_state, message, type="shop"):
    """Thêm một thông báo vào nhật ký của shop."""
    game_state.shop_notifications.insert(0, {"message": message, "type": type})
    if len(game_state.shop_notifications) > 5:
        game_state.shop_notifications.pop()

def buy_reroll(game_state):
    """Mua lượt làm mới shop với chi phí tăng dần."""
    if game_state.player_gold >= game_state.reroll_cost:
        game_state.player_gold -= game_state.reroll_cost
        add_shop_notification(game_state, f"Đã làm mới shop với giá {game_state.reroll_cost} vàng.")
        game_state.reroll_count += 1
        game_state.reroll_cost += 5
        refresh_shop(game_state)
        return True
    else:
        add_shop_notification(game_state, f"Không đủ vàng! Cần {game_state.reroll_cost} vàng.", type="error")
        return False

def buy_card(game_state, card_name):
    """Mua một thẻ bài từ shop."""
    for shop_card in game_state.shop_cards:
        if shop_card["name"] == card_name:
            if game_state.player_gold >= shop_card["price"]:
                new_card = shop_card.copy()
                if new_card.get("type") == "trap":
                    if len([c for c in game_state.player_cards if c.get("type") == "trap"]) >= 2:
                        add_shop_notification(game_state, "Bạn chỉ có thể sở hữu tối đa 2 thẻ Bẫy!", type="error")
                        return False
                else:
                    if len([c for c in game_state.player_cards if c.get("type") != "trap"]) >= 7:
                        add_shop_notification(game_state, "Bạn chỉ có thể sở hữu tối đa 7 thẻ thường!", type="error")
                        return False
                
                game_state.player_gold -= shop_card["price"]
                game_state.player_cards.append(new_card)
                add_shop_notification(game_state, f"Đã mua thẻ '{card_name}'!")
                game_state.shop_cards.remove(shop_card)
                return True
            else:
                add_shop_notification(game_state, "Không đủ vàng!", type="error")
                return False
    return False

def sell_card(game_state, card_name):
    """Bán một thẻ bài đang sở hữu để nhận lại vàng."""
    # ... (logic bán thẻ)
    pass

def refresh_shop(game_state):
    """Làm mới shop với 2 thẻ ngẫu nhiên từ kho."""
    shop_rng_seed = f"{game_state.current_seed}-shop-{game_state.reroll_count}"
    shop_rng = random.Random(shop_rng_seed)
    
    owned_card_ids = {card['id'] for card in game_state.player_cards}
    available_cards = [card for card in CARD_DATABASE if card['id'] not in owned_card_ids]
    available_cards.sort(key=lambda card: card['id'])
    
    num_to_sample = min(len(available_cards), 2)
    game_state.shop_cards = shop_rng.sample(available_cards, num_to_sample)