import time
import threading
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_manager import GameManager

class HardwareInterface:
    """ハードウェア通信の窓口となるシングルトンクラス"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HardwareInterface, cls).__new__(cls)
            cls._instance.game_manager = None
        return cls._instance

    def register_game_manager(self, manager: 'GameManager'):
        """GameManagerのインスタンスを登録する"""
        self.game_manager = manager

    def _send_payload(self, payload: dict):
        """実際にデータを送信する共通メソッド"""
        # 実際の環境では、ここでWebSocketやシリアル通信ライブラリを呼び出す
        message_str = json.dumps(payload)
        print(f"[HW_IF] SEND: {message_str}")

    def send_game_state(self, game_id: str, game_state: dict):
        payload = {
            "type": "game_state",
            "game_id": game_id,
            "state": game_state
        }
        self._send_payload(payload)

    def signal_shot_fired(self, game_id: str, player_id: int, shell_type: str):
        payload = {
            "type": "shot_fired",
            "game_id": game_id,
            "player_id": player_id,
            "shell_type": shell_type
        }
        self._send_payload(payload)

    def signal_item_use_result(self, game_id: str, player_id: int, item_name: str, success: bool, message: str):
        """アイテム使用の結果をハードウェアに通知する"""
        payload = {
            "type": "item_result",
            "game_id": game_id,
            "player_id": player_id,
            "item_name": item_name,
            "success": success,
            "message": message
        }
        self._send_payload(payload)

    def _listener_thread(self):
        """外部からのデータ受信をシミュレートするスレッド"""
        print("[HW_IF] Listener thread started.")
        # (シミュレーション部分は変更なし)
        time.sleep(10) # デモ用に少し待機
        print("[HW_IF] Listener thread finished.")

    def start_listening(self):
        """データ受信スレッドを開始する"""
        if not hasattr(self, 'listener') or not self.listener.is_alive():
            self.listener = threading.Thread(target=self._listener_thread, daemon=True)
            self.listener.start()

# シングルトンインスタンス
hardware_interface = HardwareInterface()
