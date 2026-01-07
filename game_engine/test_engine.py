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
      -> ex: action STEAL Bob
      -> ex: action COUP Alice

  challenge <PLAYER>
      -> challenge pending action
      -> ex: challenge Bob

  resolve
      -> resolve current action

  quit
      -> exit
""")

def print_game_summary(gs: GameState):
    print("\n========== GAME STATE ==========")
    print(f"Phase: {gs.phase.name}")
    print(f"Current player: {gs.current_player().name}")
    print("--------------------------------")

    print("\n========== DECK ==========")
    print(f"Deck size: {len(gs.deck.cards)}")
    print(f"Deck: {[r.name.lower() for r in gs.deck.cards]}")
    print("--------------------------------")

    print("\n========== PLAYERS ==========")
    for p in gs.players:
        print(f"name= {p.name:8} | "
            f"influences={[r.name.lower() for r in p.influences]} | "
            f"revealed={[r.name for r in p.revealed]} | "
            f"alive={p.alive} | "
            f"num coins={p.coins}"
        )
    print("--------------------------------\n")

def main():
    print("=== Coup Engine Test Harness ===")

    names = input("Enter player names (comma separated): ")
    players = [n.strip() for n in names.split(",") if n.strip()]

    gs = GameState(players)

    print_game_summary(gs)

    while True:
        try:
            cmd = input("> ").strip().split()

            if not cmd:
                continue

            match cmd[0]:
                case "quit":
                    break

                case "help":
                    help_menu()

                case "show state":
                    print_game_summary(gs)

                case "action":
                    # action TAX Bob
                    action = Action[cmd[1]]
                    target = cmd[2] if len(cmd) > 2 else None
                    gs.apply_action(gs.current_player().name, action, target)
                    print("Action declared.")

                case "challenge":
                    gs.apply_challenge(cmd[1])
                    print("Challenge processed.")

                case "resolve":
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
