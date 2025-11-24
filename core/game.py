from .player import Player
from .shotgun import Shotgun
from .items import ITEMS
from . import logic
from .game_config import config
from hardware.interface import hardware_interface
import time
import json
import os
from datetime import datetime
import copy

class Game:
    """ゲーム全体の進行と状態を管理する司令塔クラス"""
    def __init__(self, player_ids: list[int], custom_settings: dict = None):
        self.players = [Player(pid) for pid in player_ids]
        self.shotgun = Shotgun()
        self.game_id = ""
        self.round_number = 0
        self.current_player_index = 0
        self.custom_settings = custom_settings or {}
        
        # Logging
        self.logs = []
        self.start_time = datetime.now()
        self.log_event("GAME_START", f"Game started with players: {player_ids}")
        
        # Admin Messages
        self.messages = [] # List of {timestamp, message}
        self.messages = [] # List of {timestamp, message}
        self.is_terminated = False
        
        # Undo History
        self.history = []

        # Interaction State (for Handcuffs etc)
        self.pending_interaction = None # { 'type': 'select_target', 'source': player_id, 'item': item_name }
        
        # Last Action (for UI Popups)
        self.last_action = None # { 'type', 'source', 'target', 'item', 'result', 'timestamp' }

    def set_pending_interaction(self, interaction_type: str, source_id: int, item_name: str):
        self.pending_interaction = {
            'type': interaction_type,
            'source': source_id,
            'item': item_name
        }
        self.log_event("INTERACTION_START", f"Interaction started: {interaction_type} by Player {source_id}")

    def clear_pending_interaction(self):
        if self.pending_interaction:
            self.log_event("INTERACTION_END", "Interaction cleared/cancelled.")
            self.pending_interaction = None

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    def get_player_by_id(self, player_id: int) -> Player | None:
        return next((p for p in self.players if p.id == player_id), None)

    def log_event(self, event_type: str, message: str):
        """イベントをログに記録する"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "type": event_type,
            "message": message,
            "round": self.round_number
        }
        self.logs.append(log_entry)
        print(f"[{timestamp}] [{event_type}] {message}")

    def broadcast_message(self, message: str, duration: int = None):
        """全プレイヤー（タブレット）にメッセージを送信"""
        self.messages.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "content": message,
            "duration": duration
        })
        self.log_event("ADMIN_MESSAGE", message)

    def force_end(self):
        """ゲームを強制終了する"""
        self.is_terminated = True
        self.log_event("GAME_TERMINATED", "Game was forcibly terminated by admin.")
        self.save_logs()

    def save_logs(self):
        """ログをファイルに保存する"""
        os.makedirs("logs", exist_ok=True)
        filename = f"logs/game_{self.game_id}_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)
        print(f"Logs saved to {filename}")

    def start_new_round(self):
        if self.is_terminated: return

        self.round_number += 1
        self.log_event("ROUND_START", f"Round {self.round_number} Starting")
        
        living_players = [p for p in self.players if p.lives > 0]
        items_to_distribute = logic.distribute_items(self.round_number, living_players, self.custom_settings)
        
        for player_id, item_names in items_to_distribute.items():
            player = self.get_player_by_id(player_id)
            if player:
                for name in item_names:
                    player.add_item(ITEMS[name])
                self.log_event("ITEM_DISTRIBUTION", f"{player.name} received {len(item_names)} items: {item_names}")
        
        self.reload_shotgun()

    def reload_shotgun(self):
        self.log_event("SHOTGUN_RELOAD", "Reloading shotgun...")
        live_count, blank_count = logic.calculate_shell_counts(self.round_number, self.custom_settings)
        self.shotgun.load_shells(live_count, blank_count)
        self.log_event("SHOTGUN_LOADED", f"Shotgun loaded with {live_count} live and {blank_count} blank shells.")

    def handle_action(self, action_data: dict):
        if self.is_terminated: return

        # Save state before action
        self.save_checkpoint()

        action = action_data.get('action')
        if action == 'shoot':
            target_id = action_data.get('target_id')
            if target_id is None: return
            self.shoot(int(target_id))
        elif action == 'use':
            item_name = action_data.get('item_name')
            kwargs = {'target_id': action_data.get('target_id')}
            self.use_item(item_name, **kwargs)
        
        # Clear interaction if action was successful (or attempted)
        # We might want to be more specific, but for now, any action clears the pending state
        self.clear_pending_interaction()

    def shoot(self, target_id: int):
        # Auto-reload check removed from start to allow "click" on empty if we wanted, 
        # but here we want to prevent shooting if empty, though it should have auto-reloaded.
        if not self.shotgun.chamber:
            self.log_event("SHOTGUN_EMPTY", "Shotgun is empty! Reloading...")
            self.start_new_round()
            return

        target_player = self.get_player_by_id(target_id)
        if not target_player or target_player.lives <= 0: return

        # Check saw state BEFORE firing, because fire() might reset it (depending on implementation)
        # But to be safe and clear, we capture the state here.
        is_sawed_off = self.shotgun.is_sawed_off
        
        shell = self.shotgun.fire()
        self.log_event("ACTION_SHOOT", f"{self.current_player.name} shoots at {target_player.name}...")
        hardware_interface.signal_shot_fired(self.game_id, self.current_player.id, shell)
        
        # Calculate damage based on config
        base_damage = 1
        damage_multiplier = config.config.get('item_effects', {}).get('saw_damage_multiplier', 2)
        damage = (base_damage * damage_multiplier) if is_sawed_off else base_damage
        
        # If shotgun.fire() didn't reset it, we might need to. 
        # shotgun.py says "Saw effect is one time", so it likely resets it.
        # But let's rely on the captured variable.

        turn_ends = True
        result_msg = ""
        if shell == 'live':
            self.log_event("RESULT_LIVE", "It's a LIVE shell!")
            target_player.take_damage(damage)
            self.log_event("DAMAGE", f"{target_player.name} takes {damage} damage! Lives: {target_player.lives}")
            result_msg = f"LIVE ROUND! {damage} DAMAGE"
        else: # Blank shell
            self.log_event("RESULT_BLANK", "It's a BLANK shell.")
            result_msg = "BLANK ROUND"
            if target_player == self.current_player:
                turn_ends = False
                self.log_event("TURN_CONTINUE", "Turn continues.")
        
        self.last_action = {
            'type': 'shoot',
            'source': self.current_player.name,
            'target': target_player.name,
            'result': result_msg,
            'timestamp': time.time()
        }

        if self.is_game_over(): 
            self.save_logs()
            return

        # Auto-Reload Check: If chamber is now empty, reload immediately
        if not self.shotgun.chamber:
             self.log_event("SHOTGUN_EMPTY", "Chamber is empty. Starting new round sequence...")
             # We wait a brief moment or just trigger it. 
             # Since this is a turn-based API, we just update the state.
             self.start_new_round()
             # If we reload, the turn order might reset or continue? 
             # Usually new round = items distributed + reload.
             # Turn usually passes to next player or stays? 
             # In standard rules, if you shoot blank at self, you keep turn.
             # If you shoot live, turn passes.
             # If empty, new round starts. Who starts? 
             # Usually the person who just played or next? 
             # Let's assume turn passes if it was live, or if it was blank at other.
             # If blank at self and empty -> New round, but whose turn?
             # Let's stick to standard flow: Handle turn change FIRST, then reload if needed?
             # Or Reload FIRST?
             # If we reload, we give items.
             pass

        if turn_ends:
            self.next_turn()
        
        # Re-check empty after turn change to be safe, or just do it here.
        # If we did start_new_round above, we might not want to next_turn?
        # Actually, start_new_round doesn't change turn index usually.
        # But if the round ends, does the turn pass?
        # Let's assume turn logic handles "who goes next".
        # If the gun is empty, we MUST reload.
        if not self.shotgun.chamber and not self.is_game_over():
             self.start_new_round()

    def use_item(self, item_name: str, **kwargs):
        player = self.current_player
        item = player.find_item(item_name)

        if not item:
            self.log_event("ITEM_FAIL", f"Item '{item_name}' not found.")
            return

        self.log_event("ACTION_USE_ITEM", f"{player.name} tries to use {item.name}...")
        success, message = item.use(self, **kwargs)

        hardware_interface.signal_item_use_result(
            self.game_id, player.id, item.name, success, message
        )

        if success:
            self.log_event("ITEM_SUCCESS", f"Success: {message}")
            player.remove_item(item_name)
            
            # Special handling for Beer (ejected shell) and Magnifying Glass (inspected shell)
            # The 'message' from item.use() usually contains the result.
            # We'll use that for the popup.
            
            self.last_action = {
                'type': 'item',
                'source': player.name,
                'item': item.name,
                'result': message,
                'timestamp': time.time()
            }
            
            if item.name == "MagnifyingGlass":
                # TODO: Send private info to player tablet
                pass
        else:
            self.log_event("ITEM_FAIL", f"Failed to use {item.name}: {message}")

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

        while self.current_player.skip_turns > 0 or self.current_player.lives <= 0:
            if self.current_player.skip_turns > 0:
                self.current_player.skip_turns -= 1
                self.log_event("TURN_SKIP", f"{self.current_player.name} is skipped due to Handcuffs.")
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

        self.log_event("TURN_CHANGE", f"Turn passes to {self.current_player.name}.")

    def is_game_over(self) -> bool:
        if self.is_terminated: return True

        end_condition = config.rules.get('end_condition', 'last_man_standing')
        living_players = [p for p in self.players if p.lives > 0]
        
        if end_condition == 'first_death':
            is_over = len(living_players) < len(self.players)
        else: # last_man_standing
            is_over = len(living_players) <= 1
        
        if is_over:
             winner = self.get_winner()
             if winner:
                 self.log_event("GAME_OVER", f"Winner is {winner.name}!")
             else:
                 self.log_event("GAME_OVER", "Game ends in a draw.")
        
        return is_over

    def get_winner(self) -> Player | None:
        # Removed recursive call to self.is_game_over()
        living_players = [p for p in self.players if p.lives > 0]
        
        end_condition = config.rules.get('end_condition', 'last_man_standing')
        if end_condition == 'first_death':
            # In first_death, if someone died, the game is over. 
            # But who is the winner? Usually the last one alive or everyone else?
            # If it's "first death loses", then everyone else wins? 
            # Or maybe this mode implies 1v1? 
            # Let's assume for now if it's not last_man_standing, we just return None or top survivor.
            return living_players[0] if len(living_players) == 1 else None
        else: # last_man_standing
            return living_players[0] if len(living_players) == 1 else None

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
            'current_player_index': self.current_player_index,
            'is_terminated': self.is_terminated,
            'messages': self.messages,
            'logs': self.logs[-10:], # Send last 10 logs for UI
            'pending_interaction': self.pending_interaction,
            'last_action': self.last_action
        }
        return state

    def save_checkpoint(self):
        """現在のゲーム状態を履歴に保存する"""
        # Deepcopy is expensive, but safe for this scale
        state_snapshot = {
            'players': copy.deepcopy(self.players),
            'shotgun': copy.deepcopy(self.shotgun),
            'round_number': self.round_number,
            'current_player_index': self.current_player_index,
            'is_terminated': self.is_terminated,
            'logs': copy.deepcopy(self.logs),
            'messages': copy.deepcopy(self.messages)
        }
        self.history.append(state_snapshot)
        # Limit history size to prevent memory issues
        if len(self.history) > 50:
            self.history.pop(0)
        print(f"[Undo] Checkpoint saved. History size: {len(self.history)}")

    def undo(self) -> bool:
        """1つ前の状態に戻す"""
        if not self.history:
            print("[Undo] No history to undo.")
            return False
        
        last_state = self.history.pop()
        self.players = last_state['players']
        self.shotgun = last_state['shotgun']
        self.round_number = last_state['round_number']
        self.current_player_index = last_state['current_player_index']
        self.is_terminated = last_state['is_terminated']
        self.logs = last_state['logs']
        self.messages = last_state['messages']
        
        self.log_event("UNDO", "Game state reverted to previous checkpoint.")
        return True
