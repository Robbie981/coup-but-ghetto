from enum import Enum, auto
from typing import List, Optional
import random

STARTING_COINS = 2
STARTING_INFLUENCE = 2

COUP_COST = 7
ASSASSINATE_COST = 3
FORCED_COUP_COINS = 10

class Role(Enum):
    DUKE = auto()
    ASSASSIN = auto()
    CAPTAIN = auto()
    AMBASSADOR = auto()
    CONTESSA = auto()


# States of FSM
class Phase(Enum):
    WAITING_FOR_ACTION = auto()
    ACTION_DECLARED = auto()
    WAITING_FOR_CHALLENGE = auto()
    WAITING_FOR_BLOCK = auto()
    RESOLUTION = auto()
    GAME_OVER = auto()


class Action(Enum):
    INCOME = auto()
    FOREIGN_AID = auto()
    COUP = auto()
    TAX = auto()
    ASSASSINATE = auto()
    EXCHANGE = auto()
    STEAL = auto()

ACTION_TO_ROLE = {
    Action.TAX: Role.DUKE,
    Action.ASSASSINATE: Role.ASSASSIN,
    Action.STEAL: Role.CAPTAIN,
    Action.EXCHANGE: Role.AMBASSADOR,
}


class Player:
    def __init__(self, name: str):
        self.name: str = name
        self.coins: int = STARTING_COINS

        # Hidden influence cards
        self.influences: List[Role] = []

        # Publicly revealed (lost) influences
        self.revealed: List[Role] = []

    @property
    def alive(self) -> bool:
        return len(self.influences) > 0
    
    def influence_count(self) -> int:
        return len(self.influences)

    def lose_influence(self, role: Role):
        """
        Player loses a specific influence (chosen by player).
        This card becomes publicly revealed.
        """
        if role not in self.influences:
            raise ValueError(f"{self.name} does not have influence {role}")

        self.influences.remove(role)
        self.revealed.append(role)


class Deck:
    def __init__(self):
        self.cards: List[Role] = []

    def build(self):
        self.cards = (
            [Role.DUKE] * 3 +
            [Role.ASSASSIN] * 3 +
            [Role.CAPTAIN] * 3 +
            [Role.AMBASSADOR] * 3 +
            [Role.CONTESSA] * 3
        )
        random.shuffle(self.cards)

    def draw(self) -> Role:
        if not self.cards:
            raise RuntimeError("Deck is empty")
        return self.cards.pop()

    def return_card(self, role: Role):
        self.cards.append(role)
        random.shuffle(self.cards)


class GameState:
    def __init__(self, player_names: List[str]):
        if not (2 <= len(player_names) <= 6):
            raise ValueError("Coup requires 2-6 players")

        self.players: List[Player] = [Player(name) for name in player_names]
        self.deck = Deck()

        self.turn_index: int = 0
        self.phase: Phase = Phase.WAITING_FOR_ACTION

        # Pending action info (used during challenges / blocks)
        self.pending_action: Optional[Action] = None
        self.pending_actor: Optional[Player] = None
        self.pending_target: Optional[Player] = None

        self._start_game()

    def _start_game(self):
        self.deck.build()

        for player in self.players:
            for _ in range(STARTING_INFLUENCE):
                player.influences.append(self.deck.draw())

    def current_player(self) -> Player:
        return self.players[self.turn_index]

    def _get_player_by_name(self, name: str) -> Player:
        for p in self.players:
            if p.name == name:
                return p
        raise ValueError(f"No such player: {name}")

    def advance_turn(self):
        """
        Move to the next alive player.
        """
        num_players = len(self.players)
        for _ in range(num_players):
            self.turn_index = (self.turn_index + 1) % num_players
            if self.players[self.turn_index].alive:
                break

    def apply_action(
        self,
        actor_name: str,
        action: Action,
        target_name: Optional[str] = None,
    ):
        # --- Phase check ---
        if self.phase != Phase.WAITING_FOR_ACTION:
            raise RuntimeError("Not ready for a new action")

        actor = self._get_player_by_name(actor_name)

        # --- Turn check ---
        if actor != self.current_player():
            raise RuntimeError("It is not your turn")

        # --- Forced coup rule ---
        if actor.coins >= FORCED_COUP_COINS and action != Action.COUP:
            raise RuntimeError("Must coup when holding 10 or more coins")

        target = None
        if target_name:
            target = self._get_player_by_name(target_name)
            if not target.alive:
                raise RuntimeError("Target player is already eliminated")

        # --- Cost validation ---
        if action == Action.ASSASSINATE and actor.coins < ASSASSINATE_COST:
            raise RuntimeError("Not enough coins to assassinate")

        if action == Action.COUP and actor.coins < COUP_COST:
            raise RuntimeError("Not enough coins to coup")

        # --- Store pending action ---
        self.pending_action = action
        self.pending_actor = actor
        self.pending_target = target

        # --- Decide next phase ---
        if action in (
            Action.TAX,
            Action.STEAL,
            Action.ASSASSINATE,
            Action.EXCHANGE,
        ):
            # These actions involve a role claim
            self.phase = Phase.WAITING_FOR_CHALLENGE

        elif action == Action.FOREIGN_AID:
            # Blockable but not challengeable
            self.phase = Phase.WAITING_FOR_BLOCK

        else:
            # Income and Coup resolve immediately
            self.phase = Phase.RESOLUTION

    def resolve_action(self):
        if self.phase != Phase.RESOLUTION:
            raise RuntimeError("Action not ready to resolve")

        action = self.pending_action
        actor = self.pending_actor
        target = self.pending_target

        if action == Action.INCOME:
            actor.coins += 1

        elif action == Action.FOREIGN_AID:
            actor.coins += 2

        elif action == Action.TAX:
            actor.coins += 3

        elif action == Action.STEAL:
            stolen = min(2, target.coins)
            target.coins -= stolen
            actor.coins += stolen

        elif action == Action.ASSASSINATE:
            actor.coins -= ASSASSINATE_COST
            # influence loss handled later (after block)

        elif action == Action.COUP:
            actor.coins -= COUP_COST
            # influence loss handled later

        elif action == Action.EXCHANGE:
            # Draw two cards; choice handled later
            self.exchange_cards = [
                self.deck.draw(),
                self.deck.draw(),
            ]
            self.awaiting_exchange_choice = True

        # Cleanup + next turn
        self.pending_action = None
        self.pending_actor = None
        self.pending_target = None

        self.awaiting_exchange_choice = False
        self.exchange_cards = []

        self.advance_turn()

        if self._check_game_over():
            self.phase = Phase.GAME_OVER
        else:
            self.phase = Phase.WAITING_FOR_ACTION

    def _check_game_over(self) -> bool:
        alive = [p for p in self.players if p.alive]
        return len(alive) <= 1
    
    def apply_challenge(self, challenger_name: str):
        if self.phase != Phase.WAITING_FOR_CHALLENGE:
            raise RuntimeError("No action available to challenge")

        challenger = self._get_player_by_name(challenger_name)
        actor = self.pending_actor
        action = self.pending_action

        if challenger == actor:
            raise RuntimeError("Cannot challenge yourself")

        required_role = ACTION_TO_ROLE.get(action)
        if required_role is None:
            raise RuntimeError("This action cannot be challenged")

        # --- Check if actor actually has the role ---
        if required_role in actor.influences:
            # Challenge FAILED — challenger loses influence
            self._handle_failed_challenge(challenger)

            # Actor reveals role, returns it, draws new one
            actor.influences.remove(required_role)
            actor.revealed.append(required_role)
            self.deck.return_card(required_role)
            actor.influences.append(self.deck.draw())

            # Action succeeds
            self.phase = Phase.RESOLUTION

        else:
            # Challenge SUCCESSFUL — actor loses influence
            self._handle_failed_challenge(actor)

            # Action is canceled
            self._clear_pending_action()
            self.advance_turn()

            if self._check_game_over():
                self.phase = Phase.GAME_OVER
            else:
                self.phase = Phase.WAITING_FOR_ACTION

    def _handle_failed_challenge(self, player: Player):
        # For now, auto-lose first influence
        lost = player.influences[0]
        player.lose_influence(lost)

    def _clear_pending_action(self):
        self.pending_action = None
        self.pending_actor = None
        self.pending_target = None
