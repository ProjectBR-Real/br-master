import uuid
from game import Game

class GameManager:
    """複数のゲームインスタンスを管理するクラス"""
    def __init__(self):
        self.games = {}

    def create_game(self, player_ids: list[int], custom_settings: dict = None) -> str:
        """
        新しいゲームを作成し、IDを返す。
        Args:
            player_ids (list[int]): 参加するプレイヤーIDのリスト
            custom_settings (dict): カスタム設定（弾数、アイテムなど）
        Returns:
            str: 生成されたゲームID
        """
        game_id = str(uuid.uuid4())[:8]
        new_game = Game(player_ids, custom_settings)
        new_game.game_id = game_id
        self.games[game_id] = new_game
        print(f"Game created with ID: {game_id}")
        return game_id

    def get_game(self, game_id: str) -> Game | None:
        """IDを指定してゲームインスタンスを取得する"""
        return self.games.get(game_id)

    def dispatch_action(self, game_id: str, action_data: dict):
        """外部から受信したアクションを適切なゲームに振り分ける"""
        game = self.get_game(game_id)
        if game:
            print(f"[GameManager] Dispatching action to game {game_id}: {action_data}")
            # ここで handle_action を呼び出す。スレッドセーフなキューを介して行うのが望ましい
            game.handle_action(action_data)
        else:
            print(f"[GameManager] Received action for non-existent game {game_id}")

    def end_game(self, game_id: str):
        """IDを指定してゲームを終了（削除）する"""
        if game_id in self.games:
            del self.games[game_id]
            print(f"Game {game_id} has ended.")

# シングルトンインスタンスとしてエクスポート
game_manager = GameManager()
