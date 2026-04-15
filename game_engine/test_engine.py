from coup_engine import (
    GameState,
    Action,
    Phase,
    Role,
)

def help_menu():
    print("""
Commands:
  state
      -> print game state

  action <ACTION> [TARGET]
      -> declare action
      -> ex: action TAX
      -> ex: action STEAL BOB
      -> ex: action COUP ALICE

  challenge <PLAYER>
      -> challenge pending action
      -> ex: challenge BOB

  resolve
      -> resolve current action

  exit
      -> exit
""")

def print_game_summary(gs: GameState):
    print("\n========== GAME STATE ==========")
    print(f"Phase: {gs.phase.name}")
    print(f"Current player: {gs.current_player().name}")
    print("--------------------------------")

    print("\n========== PENDING ACTION ==========")
    print(f"Pending action: {gs.pending_action.name if gs.pending_action else None}")
    print(f"Pending actor: {gs.pending_actor.name if gs.pending_actor else None}")
    print(f"Pending target: {gs.pending_target.name if gs.pending_target else None}")
    print("--------------------------------")

    print("\n========== DECK ==========")
    print(f"Deck size: {len(gs.deck.cards)}")
    print(f"Deck: {[r.name.lower() for r in gs.deck.cards]}")
    print("--------------------------------")

    print("\n========== PLAYERS ==========")
    for p in gs.players:
        print(
            f"name={p.name:8} | "
            f"influences={[r.name.lower() for r in p.influences]} | "
            f"revealed={[r.name.lower() for r in p.revealed]} | "
            f"alive={p.alive} | "
            f"coins={p.coins}"
        )
    print("--------------------------------\n")

def main():
    print("=== Coup Engine Test Harness ===")

    names = input("Enter player names (comma separated): ")
    players = [n.strip() for n in names.split(",") if n.strip()]

    gs = GameState(players)

    help_menu()
    print_game_summary(gs)

    while True:
        try:
            cmd = input("> ").upper().strip().split()

            if not cmd:
                continue

            match cmd[0]:
                case "EXIT":
                    break

                case "HELP":
                    help_menu()

                case "STATE":
                    print_game_summary(gs)

                case "ACTION":
                    action = Action[cmd[1]]
                    target = cmd[2] if len(cmd) > 2 else None
                    gs.apply_action(gs.current_player().name, action, target)
                    print("Action declared.")

                case "CHALLENGE":
                    gs.apply_challenge(cmd[1])
                    print("Challenge processed.")

                case "RESOLVE":
                    gs.resolve_action()
                    print("Action resolved.")

                case _:
                    print("Unknown command.")

        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
        except Exception as e:
            print("ERROR:", e)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye.")