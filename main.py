import time
import threading
from game_manager import game_manager
from utils import display_game_state
from mock_inputs import get_player_action
from interface import hardware_interface

def run_interactive_game(game_id: str):
    """ユーザー入力で進行する単一のゲームループ"""
    game = game_manager.get_game(game_id)
    if not game:
        print(f"Game {game_id} not found.")
        return

    # ゲーム開始
    game.start_new_round()

    while not game.is_game_over():
        display_game_state(game.get_state())
        action_data = get_player_action(game.current_player.name)
        game.handle_action(action_data)
    print("\n--- GAME OVER ---")
    display_game_state(game.get_state())
    winner = game.get_winner()
    if winner:
        print(f"Winner is {winner.name}!")
    else:
        print("The game ends in a draw!")
    game_manager.end_game(game_id)

def main():
    """メインのエントリポイント"""
    # 3人プレイでゲームを開始
    player_ids = [1, 2, 3]
    print(f"Starting a {len(player_ids)}-player game.")
    game_id = game_manager.create_game(player_ids)
    run_interactive_game(game_id)

if __name__ == "__main__":
    main()
