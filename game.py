from player import Player
from shotgun import Shotgun
from items import ITEMS
import logic
from game_config import config
from interface import hardware_interface

class Game:
    """ゲーム全体の進行と状態を管理する司令塔クラス"""
    def __init__(self, player_ids: list[int]):
        self.players = [Player(pid) for pid in player_ids]
        self.shotgun = Shotgun()
        self.game_id = ""
        self.round_number = 0
        self.current_player_index = 0

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def get_player_by_id(self, player_id: int) -> Player | None:
        return next((p for p in self.players if p.id == player_id), None)

    def start_new_round(self):
        self.round_number += 1
        print(f"\n--- Round {self.round_number} Starting ---")
        
        living_players = [p for p in self.players if p.lives > 0]
        items_to_distribute = logic.distribute_items(self.round_number, living_players)
        for player_id, item_names in items_to_distribute.items():
            player = self.get_player_by_id(player_id)
            if player:
                for name in item_names:
                    player.add_item(ITEMS[name])
                print(f"{player.name} received {len(item_names)} items.")
        
        self.reload_shotgun()

    def reload_shotgun(self):
        print("Reloading shotgun...")
        live_count, blank_count = logic.calculate_shell_counts(self.round_number)
        self.shotgun.load_shells(live_count, blank_count)
        print(f"Shotgun loaded with {live_count} live and {blank_count} blank shells.")

    def handle_action(self, action_data: dict):
        action = action_data.get('action')
        if action == 'shoot':
            target_id = action_data.get('target_id')
            if target_id is None: return
            self.shoot(int(target_id))
        elif action == 'use':
            item_name = action_data.get('item_name')
            kwargs = {'target_id': action_data.get('target_id')}
            self.use_item(item_name, **kwargs)

    def shoot(self, target_id: int):
        if not self.shotgun.chamber:
            print("Shotgun is empty! Starting new round.")
            self.start_new_round()
            return

        target_player = self.get_player_by_id(target_id)
        if not target_player or target_player.lives <= 0: return

        shell = self.shotgun.fire()
        print(f"{self.current_player.name} shoots at {target_player.name}...")
        hardware_interface.signal_shot_fired(self.game_id, self.current_player.id, shell)
        
        damage = 2 if self.shotgun.is_sawed_off else 1
        if self.shotgun.is_sawed_off: self.shotgun.is_sawed_off = False

        turn_ends = True
        if shell == 'live':
            print("It's a LIVE shell!")
            target_player.take_damage(damage)
            print(f"{target_player.name} takes {damage} damage! Lives: {target_player.lives}")
        else: # Blank shell
            print("It's a BLANK shell.")
            if target_player == self.current_player:
                turn_ends = False
                print("Turn continues.")
        
        if self.is_game_over(): return

        if turn_ends:
            self.next_turn()

    def use_item(self, item_name: str, **kwargs):
        player = self.current_player
        item = player.find_item(item_name)

        if not item:
            print(f"Item '{item_name}' not found.")
            hardware_interface.signal_item_use_result(
                self.game_id, player.id, item_name, False, "Item not found."
            )
            return

        print(f"{player.name} tries to use {item.name}...")
        success, message = item.use(self, **kwargs)

        hardware_interface.signal_item_use_result(
            self.game_id, player.id, item.name, success, message
        )

        if success:
            print(f"Success: {message}")
            player.remove_item(item_name)
            # 拡大鏡のように使用者だけが知るべき情報の場合、ここで個別通知も可能
            if item.name == "MagnifyingGlass":
                print(f"(To {player.name} only): {message}")
            print("Item used. You can now shoot.")
        else:
            print(f"Failed to use {item.name}: {message}")

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

        while self.current_player.skip_turns > 0 or self.current_player.lives <= 0:
            if self.current_player.skip_turns > 0:
                self.current_player.skip_turns -= 1
                print(f"{self.current_player.name} is skipped due to Handcuffs.")
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

        print(f"Turn passes to {self.current_player.name}.")

    def is_game_over(self) -> bool:
        end_condition = config.rules.get('end_condition', 'last_man_standing')
        living_players = [p for p in self.players if p.lives > 0]
        
        if end_condition == 'first_death':
            return len(living_players) < len(self.players)
        else: # last_man_standing
            return len(living_players) <= 1

    def get_winner(self) -> Player | None:
        if not self.is_game_over(): return None
        living_players = [p for p in self.players if p.lives > 0]
        
        end_condition = config.rules.get('end_condition', 'last_man_standing')
        if end_condition == 'first_death':
            return living_players[0] if len(living_players) == 1 else None
        else: # last_man_standing
            return living_players[0] if living_players else None

    def get_state(self) -> dict:
        players_state = [
            {'id': p.id, 'name': p.name, 'lives': p.lives, 'items': [item.name for item in p.items], 'is_skipped': p.skip_turns > 0}
            for p in self.players
        ]
        live_count, blank_count = self.shotgun.get_shell_counts()
        shotgun_state = {
            'live_shells': live_count,
            'blank_shells': blank_count,
            'is_sawed_off': self.shotgun.is_sawed_off
        }
        state = {
            'round': self.round_number,
            'players': players_state,
            'shotgun': shotgun_state,
            'current_player_id': self.current_player.id,
        }
        return state
