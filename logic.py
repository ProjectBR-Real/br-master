import random
from game_config import config

def calculate_shell_counts(round_number: int) -> tuple[int, int]:
    """設定ファイルに基づき、ラウンドごとの実弾と空砲の数を決定する"""
    counts = config.get_shell_counts(round_number)
    return counts[0], counts[1]

def distribute_items(round_number: int, players: list['Player']) -> dict[int, list[str]]:
    """設定ファイルに基づき、各プレイヤーにアイテムを配布する"""
    items_to_distribute = {}
    num_items_per_player = config.get_items_per_round(round_number)
    
    # 確率に基づいてアイテムリストを作成
    item_pool = []
    for item, weight in config.item_probabilities.items():
        item_pool.extend([item] * weight)

    for player in players:
        new_items = []
        # MAX_ITEMS_PER_PLAYER は config から取得すべきだが、一旦 player.py に移譲
        num_to_add = max(0, num_items_per_player - len(player.items))
        for _ in range(num_to_add):
            new_items.append(random.choice(item_pool))
        items_to_distribute[player.id] = new_items
        
    return items_to_distribute
