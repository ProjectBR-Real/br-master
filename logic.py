import random
from game_config import config

def calculate_shell_counts(round_number: int, custom_settings: dict = None) -> tuple[int, int]:
    """
    ラウンドごとの実弾と空砲の数を決定する。
    custom_settingsが指定されている場合はそれを優先する。
    """
    if custom_settings:
        if 'shell_counts' in custom_settings:
            # custom_settings['shell_counts'] は {'live': int, 'blank': int} を想定
            return custom_settings['shell_counts']['live'], custom_settings['shell_counts']['blank']
        
        if 'total_shells' in custom_settings or 'live_ratio' in custom_settings:
            # Load defaults from config if not specified
            default_total = 8 # Default max
            default_ratio = 0.5
            
            total = custom_settings.get('total_shells', default_total)
            ratio = custom_settings.get('live_ratio', default_ratio)
            
            # Ensure limits
            total = max(2, min(total, 8)) # Min 2 (1 each), Max 8 (shotgun capacity)
            
            live_count = int(total * ratio)
            # Ensure at least 1 live and 1 blank if total >= 2
            if live_count < 1: live_count = 1
            if live_count > total - 1: live_count = total - 1
            
            blank_count = total - live_count
            return live_count, blank_count

    counts = config.get_shell_counts(round_number)
    return counts[0], counts[1]

def distribute_items(round_number: int, players: list['Player'], custom_settings: dict = None) -> dict[int, list[str]]:
    """
    各プレイヤーにアイテムを配布する。
    custom_settingsが指定されている場合はそれを優先する。
    """
    items_to_distribute = {}
    
    if custom_settings and 'items_per_round' in custom_settings:
        num_items_per_player = custom_settings['items_per_round']
    else:
        num_items_per_player = config.get_items_per_round(round_number)
    
    # 確率に基づいてアイテムリストを作成
    item_pool = []
    
    if custom_settings and 'item_probabilities' in custom_settings:
        probs = custom_settings['item_probabilities']
    else:
        probs = config.item_probabilities

    for item, weight in probs.items():
        item_pool.extend([item] * weight)

    for player in players:
        new_items = []
        # 所持数制限ロジック（簡易）
        num_to_add = max(0, num_items_per_player - len(player.items))
        for _ in range(num_to_add):
            if item_pool:
                new_items.append(random.choice(item_pool))
        items_to_distribute[player.id] = new_items
        
    return items_to_distribute
