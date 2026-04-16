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


class Phase(Enum):
    WAITING_FOR_ACTION = auto()
    ACTION_DECLARED = auto()
    WAITING_FOR_CHALLENGE = auto()
    WAITING_FOR_BLOCK = auto()
    RESOLUTION = auto()
    GAME_OVER = auto()
    LOBBY = auto()


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
            [Role.DUKE] * 3
            + [Role.ASSASSIN] * 3
            + [Role.CAPTAIN] * 3
            + [Role.AMBASSADOR] * 3
            + [Role.CONTESSA] * 3
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

        self.players: List[Player] = [Player(name.upper()) for name in player_names]
        self.deck = Deck()

        self.turn_index: int = 0
        self.phase: Phase = Phase.WAITING_FOR_ACTION

        # Pending action info
        self.pending_action: Optional[Action] = None
        self.pending_actor: Optional[Player] = None
        self.pending_target: Optional[Player] = None

        # Exchange state
        self.awaiting_exchange_choice: bool = False
        self.exchange_cards: List[Role] = []

        self._start_game()

    def _start_game(self):
        self.deck.build()

        for player in self.players:
            for _ in range(STARTING_INFLUENCE):
                player.influences.append(self.deck.draw())

    def current_player(self) -> Player:
        return self.players[self.turn_index]

    def _get_player_by_name(self, name: str) -> Player:
        name = name.upper()
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
        # --- Global validation ---
        if self.phase != Phase.WAITING_FOR_ACTION:
            raise RuntimeError("Not ready for a new action")

        actor = self._get_player_by_name(actor_name)

        if actor != self.current_player():
            raise RuntimeError("It is not your turn")

        # Forced coup rule
        if actor.coins >= FORCED_COUP_COINS and action != Action.COUP:
            raise RuntimeError("Must coup when holding 10 or more coins")

        target = self._resolve_target(actor, target_name)

        # --- Action-specific validation ---
        if action == Action.INCOME:
            self._validate_income(actor)

        elif action == Action.FOREIGN_AID:
            self._validate_foreign_aid(actor)

        elif action == Action.COUP:
            self._validate_coup(actor, target)

        elif action == Action.TAX:
            self._validate_tax(actor)

        elif action == Action.ASSASSINATE:
            self._validate_assassinate(actor, target)

        elif action == Action.EXCHANGE:
            self._validate_exchange(actor)

        elif action == Action.STEAL:
            self._validate_steal(actor, target)

        else:
            raise RuntimeError(f"Unsupported action: {action}")

        # --- Store pending action ---
        self.pending_action = action
        self.pending_actor = actor
        self.pending_target = target

        # --- Decide next phase ---
        self.phase = self._phase_for_action(action)

    def _resolve_target(
        self,
        actor: Player,
        target_name: Optional[str],
    ) -> Optional[Player]:
        if target_name is None:
            return None

        target = self._get_player_by_name(target_name)

        if not target.alive:
            raise RuntimeError("Target player is already eliminated")

        if target == actor:
            raise RuntimeError("Cannot target yourself")

        return target

    def _phase_for_action(self, action: Action) -> Phase:
        if action in (
            Action.TAX,
            Action.STEAL,
            Action.ASSASSINATE,
            Action.EXCHANGE,
        ):
            return Phase.WAITING_FOR_CHALLENGE

        if action == Action.FOREIGN_AID:
            return Phase.WAITING_FOR_BLOCK

        return Phase.RESOLUTION

    def _validate_income(self, actor: Player):
        pass

    def _validate_foreign_aid(self, actor: Player):
        pass

    def _validate_coup(self, actor: Player, target: Optional[Player]):
        if target is None:
            raise RuntimeError("Coup requires a target")

        if actor.coins < COUP_COST:
            raise RuntimeError("Not enough coins to coup")

    def _validate_tax(self, actor: Player):
        pass

    def _validate_assassinate(self, actor: Player, target: Optional[Player]):
        if target is None:
            raise RuntimeError("Assassinate requires a target")

        if actor.coins < ASSASSINATE_COST:
            raise RuntimeError("Not enough coins to assassinate")

    def _validate_exchange(self, actor: Player):
        pass

    def _validate_steal(self, actor: Player, target: Optional[Player]):
        if target is None:
            raise RuntimeError("Steal requires a target")

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
            # Influence loss handled later after block/challenge flow

        elif action == Action.COUP:
            actor.coins -= COUP_COST
            lost_influence = target.influences[0]  # TODO: have player select which influence to lose, right now it auto loses the first one in the list
            target.lose_influence(lost_influence)

        # TODO: yeash exchange is just broken...
        elif action == Action.EXCHANGE:
            self.exchange_cards = [
                self.deck.draw(),
                self.deck.draw(),
            ]
            self.awaiting_exchange_choice = True  # TODO: have player select which influence to exchange
        # Reset exchange state for now
        self.awaiting_exchange_choice = False
        self.exchange_cards = []

        self._finish_turn()

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

        # Actor actually has the required role -> challenge fails
        if required_role in actor.influences:
            self._handle_failed_challenge(challenger)

            # Actor reveals the card, returns it, and redraws
            actor.influences.remove(required_role)
            actor.revealed.append(required_role)
            self.deck.return_card(required_role)
            actor.influences.append(self.deck.draw())

            # Claimed action continues
            self.phase = Phase.RESOLUTION

        # Actor does not have the role -> challenge succeeds
        else:
            self._handle_failed_challenge(actor)
            self._finish_turn()

    def _handle_failed_challenge(self, player: Player):
        # For now, auto-lose first influence
        lost = player.influences[0]
        player.lose_influence(lost)

    def _clear_pending_action(self):
        self.pending_action = None
        self.pending_actor = None
        self.pending_target = None

    def _check_game_over(self) -> bool:
        alive = [p for p in self.players if p.alive]
        return len(alive) <= 1
    
    def pass_block(self):
        if self.phase != Phase.WAITING_FOR_BLOCK:
            raise RuntimeError("Not waiting for a block")

        # Nobody blocked, so action can now resolve
        self.phase = Phase.RESOLUTION

    def apply_block(self, blocker_name: str):
        if self.phase != Phase.WAITING_FOR_BLOCK:
            raise RuntimeError("Not waiting for a block")

        blocker = self._get_player_by_name(blocker_name)

        if not blocker.alive:
            raise RuntimeError("Dead player cannot block")

        if blocker == self.pending_actor:
            raise RuntimeError("You cannot block your own action")

        # TODO: Add support to block other actions, for now only support FOREIGN_AID block
        if self.pending_action != Action.FOREIGN_AID:
            raise RuntimeError("Only FOREIGN_AID block is implemented right now")
        
        # TODO: Later this block itself can be challenged, should transition into waiting for challenge
        # Block succeeds immediately for now
        self._finish_turn()
            
    def _finish_turn(self):
        self._clear_pending_action()
        self.advance_turn()

        if self._check_game_over():
            self.phase = Phase.GAME_OVER
        else:
            self.phase = Phase.WAITING_FOR_ACTION