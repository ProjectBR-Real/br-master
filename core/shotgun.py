import random
from hardware.comms import network_manager

class Shotgun:
    """
    ショットガンの状態を管理するデータクラス。
    """
    def __init__(self):
        self.chamber: list[str] = [] # 'live' or 'blank' の文字列リスト
        self.is_sawed_off: bool = False # 鋸が使われているか

    def load_shells(self, live_count: int, blank_count: int):
        """
        Gameクラスから実弾と空砲の数を受け取り、シャッフルして装填する。
        Args:
            live_count (int): 実弾の数
            blank_count (int): 空砲の数
        """
        shells = ['live'] * live_count + ['blank'] * blank_count
        random.shuffle(shells)
        self.chamber = shells

    def fire(self) -> str | None:
        """
        薬室の先頭から弾を1つ取り出し、その種類を文字列で返す。
        Returns:
            str | None: 'live' または 'blank'。弾がなければNone。
        """
        if not self.chamber:
            return None
        shell = self.chamber.pop(0)
        
        # ネットワーク経由でトリガー送信 (非同期)
        def send_trigger():
            try:
                print(f"Sending trigger: FIRE:{shell}")
                response = network_manager.send_command("shotgun", f"FIRE:{shell}")
                print(f"Shotgun response: {response}")
            except Exception as e:
                print(f"Hardware communication failed (non-fatal): {e}")

        import threading
        threading.Thread(target=send_trigger, daemon=True).start()

        # 鋸の効果は1回限り
        if self.is_sawed_off:
            self.is_sawed_off = False
        return shell

    def eject_shell(self) -> str | None:
        """
        （ビール用）薬室の先頭から弾を1つ取り出し、その種類を返す。
        Returns:
            str | None: 'live' または 'blank'。弾がなければNone。
        """
        if not self.chamber:
            return None
        return self.chamber.pop(0)

    def peek_next_shell(self) -> str | None:
        """
        （拡大鏡用）薬室の先頭の弾の種類を、削除せずに文字列で返す。
        Returns:
            str | None: 'live' または 'blank'。弾がなければNone。
        """
        if not self.chamber:
            return None
        return self.chamber[0]

    def get_shell_counts(self) -> tuple[int, int]:
        """
        現在の薬室内の実弾と空砲の数をタプルで返す。
        Returns:
            tuple[int, int]: (実弾の数, 空砲の数)
        """
        return (self.chamber.count('live'), self.chamber.count('blank'))
