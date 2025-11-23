import socket
import time
from core.game_config import config

class NetworkManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NetworkManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.timeout = 5.0

    def send_command(self, device_name: str, command: str) -> str | None:
        """
        指定されたデバイスにコマンドを送信し、レスポンスを待機する。
        Args:
            device_name (str): config.jsonで定義されたデバイス名
            command (str): 送信するコマンド文字列
        Returns:
            str | None: レスポンス文字列。エラー時はNone。
        """
        device_config = config.get_device_config(device_name)
        if not device_config:
            print(f"Device configuration for '{device_name}' not found.")
            return None

        target_ip = device_config.get('ip')
        port = device_config.get('port')

        if not target_ip or not port:
             print(f"Invalid configuration for '{device_name}': IP or Port missing.")
             return None

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((target_ip, port))
                s.sendall(command.encode('utf-8'))
                
                # レスポンス受信
                data = s.recv(1024)
                if not data:
                    return None
                return data.decode('utf-8').strip()
        except Exception as e:
            print(f"Network Error ({device_name}): {e}")
            return None

# シングルトンインスタンス
network_manager = NetworkManager()
