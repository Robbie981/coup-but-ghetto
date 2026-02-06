
## To dos
    - improve randomness of shuffling and dealing
    - choose random player to start, otherwise start with winner

## Game flow

Setup:
    - Add players (players class, takes user input)
    - Create/shuffle deck (should have 15 cards total)
    - Deal cards (2 each, so remaining cards in deck = 15 - (2 * num_players))
    - Give coins (2 each)

Normal gameplay (state machine):
    - Waiting for action (***NEXT STEP IS TO TEST THESE ACTIONS)
        - Income (take 1 coin)
        - Foreign Aid (take 2 coins) * can be blocked
        - Coup (7 coins to kill)
        - Tax (Take 3 coins)
        - Assassinate (3 coins to kill) * can be blocked
        - Exchange (check top 2 cards) <---- this one is hard to implement
        - Steal (take 2 coins from someone) * can be blocked

    - Wait for challenge
    - Wait for block
    - Resolution
    - Move to next player, waiting for action again
