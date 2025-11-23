def get_player_action(player_name: str) -> dict:
    """
    ターミナルからプレイヤーの行動を受け取り、パースして辞書で返す。
    """
    while True:
        raw_input = input(f"> {player_name}, action (shoot [id], use [item]): ")
        parts = raw_input.lower().split()
        if not parts:
            continue
        
        command = parts[0]
        if command == 'shoot' and len(parts) == 2 and parts[1].isdigit():
            return {'action': 'shoot', 'target_id': int(parts[1])}
        elif command == 'use' and len(parts) > 1:
            item_name = parts[1].lower()
            if item_name == 'handcuffs' and len(parts) == 3 and parts[2].isdigit():
                return {'action': 'use', 'item_name': item_name, 'target_id': int(parts[2])}
            elif item_name != 'handcuffs':
                # 他のアイテムはターゲットを取らないと仮定
                return {'action': 'use', 'item_name': item_name}

        print("Invalid command. Use 'shoot <id>' or 'use <item_name> [<target_id>]'.")
