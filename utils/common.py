import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_game_state(game_state: dict):
    """
    Gameクラスから受け取った状態の辞書を元に、画面表示を行う。
    """
    # clear_screen()
    print("========================================")
    print(f"ROUND {game_state['round']}\n")

    # Players
    for player in game_state['players']:
        lives_str = '❤️' * player['lives'] if player['lives'] > 0 else '💀'
        items_str = ', '.join(player['items']) if player['items'] else 'None'
        status_str = " (SKIPPED)" if player['is_skipped'] else ""
        print(f"{player['name']} (ID: {player['id']}): {lives_str} | Items: {items_str}{status_str}")
    print("")

    # Shotgun
    sg = game_state['shotgun']
    print(f"Shotgun: [ {sg['live_shells']} Live | {sg['blank_shells']} Blank ]")
    if sg['is_sawed_off']:
        print("SAWED-OFF! Next shot deals double damage.")
    print("\n----------------------------------------")
    
    # Turn
    current_player_id = game_state['current_player_id']
    current_player = next((p for p in game_state['players'] if p['id'] == current_player_id), None)
    current_player_name = current_player['name'] if current_player else "Unknown"
    print(f"Turn: {current_player_name}")
    print("========================================")