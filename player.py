from __future__ import annotations
import typing
from game_config import config

if typing.TYPE_CHECKING:
    from items import Item

class Player:
    """
    プレイヤーの状態を管理するデータクラス。
    """
    def __init__(self, player_id: int):
        """
        Args:
            player_id (int): プレイヤーID (1-4)
        """
        self.id: int = player_id
        print(f"DEBUG: Initializing Player {player_id} with NEW CODE")
        self.name: str = f"Player {player_id}"
        self.lives: int = config.rules['initial_lives']
        self.max_lives: int = config.rules['max_lives']
        self.items: list['Item'] = []
        self.skip_turns: int = 0

    def take_damage(self, amount: int):
        """
        ダメージ量を受け取り、ライフを減らす。
        """
        self.lives -= amount

    def heal(self, amount: int):
        """
        回復量を受け取り、ライフを増やす。上限を超えない。
        """
        self.lives = min(self.lives + amount, config.rules['max_lives'])

    def add_item(self, item_obj: 'Item'):
        """
        アイテムオブジェクトを所持品に追加する。
        """
        self.items.append(item_obj)

    def find_item(self, item_name: str) -> 'Item' | None:
        """
        アイテム名を元に所持品からアイテムオブジェクトを探して返す。
        """
        for item in self.items:
            if item.name.lower() == item_name.lower():
                return item
        return None

    def remove_item(self, item_name: str):
        """
        アイテム名を元に所持品からアイテムを削除する。
        """
        item_to_remove = self.find_item(item_name)
        if item_to_remove:
            self.items.remove(item_to_remove)
