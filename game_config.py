import json

class GameConfig:
    _instance = None

    def __new__(cls, config_file='config.json'):
        if cls._instance is None:
            cls._instance = super(GameConfig, cls).__new__(cls)
            cls._instance._load_config(config_file)
        return cls._instance

    def _load_config(self, config_file):
        with open(config_file, 'r') as f:
            self.config = json.load(f)

    @property
    def rules(self):
        return self.config['game_rules']

    def get_shell_counts(self, round_number: int) -> list[int]:
        round_str = str(round_number)
        return self.config['shell_counts_by_round'].get(round_str, self.config['shell_counts_by_round']['default'])

    def get_items_per_round(self, round_number: int) -> int:
        round_str = str(round_number)
        return self.config['item_distribution']['items_per_round'].get(round_str, self.config['item_distribution']['items_per_round']['default'])

    @property
    def item_probabilities(self) -> dict:
        return self.config['item_distribution']['item_probabilities']

# シングルトンインスタンスとしてエクスポート
config = GameConfig()
