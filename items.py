from __future__ import annotations
import typing

if typing.TYPE_CHECKING:
    from game import Game

class Item:
    """全てのアイテムの基底クラス"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def use(self, game: 'Game', **kwargs) -> tuple[bool, str]:
        """
        アイテムを使用する。
        :return: (成功したか, メッセージ) のタプル
        """
        raise NotImplementedError("This method should be overridden by subclasses")

class Cigarette(Item):
    def __init__(self):
        super().__init__("Cigarette", "ライフを1回復する")

    def use(self, game: 'Game', **kwargs) -> tuple[bool, str]:
        player = game.current_player
        if player.lives >= player.max_lives:
            return False, "Health is already full."
        
        player.heal(1)
        message = f"{player.name} restored 1 life."
        return True, message

class Beer(Item):
    def __init__(self):
        super().__init__("Beer", "弾を1発排出する")

    def use(self, game: 'Game', **kwargs) -> tuple[bool, str]:
        if not game.shotgun.chamber:
            return False, "Shotgun chamber is empty."
            
        shell = game.shotgun.eject_shell()
        message = f"Ejected a {shell} shell."
        return True, message

class Saw(Item):
    def __init__(self):
        super().__init__("Saw", "次の射撃ダメージを2倍にする")

    def use(self, game: 'Game', **kwargs) -> tuple[bool, str]:
        if game.shotgun.is_sawed_off:
            return False, "The shotgun is already sawed-off."
            
        game.shotgun.is_sawed_off = True
        message = "The next shot will be sawed-off."
        return True, message

class Handcuffs(Item):
    def __init__(self):
        super().__init__("Handcuffs", "相手のターンを1回スキップ")

    def use(self, game: 'Game', **kwargs) -> tuple[bool, str]:
        target_id = kwargs.get('target_id')
        if target_id is None:
            return False, "Handcuffs require a target player."

        target_player = game.get_player_by_id(target_id)
        if not target_player or target_player.lives <= 0:
            return False, f"Invalid or defeated target: {target_id}"
        
        if target_player.skip_turns > 0:
            return False, f"{target_player.name} is already handcuffed."

        target_player.skip_turns += 1
        message = f"{target_player.name} will be skipped for 1 turn."
        return True, message

class MagnifyingGlass(Item):
    def __init__(self):
        super().__init__("MagnifyingGlass", "次の弾の種類を見る")

    def use(self, game: 'Game', **kwargs) -> tuple[bool, str]:
        if not game.shotgun.chamber:
            return False, "Shotgun chamber is empty."
            
        shell = game.shotgun.peek_next_shell()
        message = f"The next shell is: {shell}."
        # このアイテムは相手に情報を与えないので、使用者のみに結果を伝えるべき
        # game.py側でハンドリングする想定
        return True, message

# --- Item Definitions ---
# インスタンスを生成して、名前をキーとして辞書に格納
ITEMS = {
    "cigarette": Cigarette(),
    "beer": Beer(),
    "saw": Saw(),
    "handcuffs": Handcuffs(),
    "magnifyingglass": MagnifyingGlass(),
}
