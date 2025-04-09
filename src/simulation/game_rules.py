"""
Game Rules Module

This module enforces the deterministic game rules for pre-flop Texas Hold'em poker,
handling the structured transitions between states based on player actions.
"""

from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Any


class Position(Enum):
    """Player positions in heads-up poker."""
    DEALER = 0  # Also Small Blind (SB)
    BIG_BLIND = 1  # BB


class Action(Enum):
    """Possible actions in pre-flop play."""
    FOLD = auto()
    CHECK = auto()
    CALL = auto() 
    RAISE = auto()  # Includes different raise sizes
    ALL_IN = auto()


class GameStage(Enum):
    """Stages of a poker hand."""
    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    TERMINAL = auto()  # Game ended (someone folded or hand reached showdown)


class GameState:
    """
    Represents the current state of the poker game.
    
    Attributes:
        hole_cards: Dictionary mapping player IDs to their hole cards
        positions: Dictionary mapping player IDs to their positions
        stack_sizes: Dictionary mapping player IDs to their chip counts
        pot_size: Current size of the pot
        betting_history: List of actions taken so far
        active_players: Set of player IDs still in the hand
        stage: Current stage of the game (preflop, flop, etc.)
        current_player: ID of the player whose turn it is
        winner: ID of the player who won (if game is terminal)
        last_raiser: ID of the player who last raised
        current_bet: Current bet amount that needs to be called
        player_bets: Dictionary tracking how much each player has bet in the current round
    """
    
    def __init__(self, 
                 player_ids: List[str],
                 hole_cards: Dict[str, Tuple],
                 stack_sizes: Dict[str, float],
                 blinds: Tuple[float, float] = (0.5, 1.0)):
        """
        Initialize a new game state at the beginning of pre-flop.
        
        Args:
            player_ids: List of player IDs
            hole_cards: Dictionary mapping player IDs to their hole cards
            stack_sizes: Dictionary mapping player IDs to their chip counts
            blinds: Tuple of (small blind, big blind) amounts
        """
        self.hole_cards = hole_cards
        self.positions = {
            player_ids[0]: Position.DEALER,  # First player is dealer (SB)
            player_ids[1]: Position.BIG_BLIND  # Second player is BB
        }
        self.stack_sizes = stack_sizes.copy()
        self.pot_size = blinds[0] + blinds[1]  # Initial pot is sum of blinds
        self.betting_history = []
        self.active_players = set(player_ids)
        self.stage = GameStage.PREFLOP
        
        # In preflop, dealer (SB) acts first
        self.current_player = player_ids[0]
        
        self.winner = None
        self.last_raiser = player_ids[1]  # BB is considered the last raiser initially
        self.current_bet = blinds[1]  # Current bet is BB amount
        
        # Track how much each player has bet in current round
        self.player_bets = {
            player_ids[0]: blinds[0],  # SB already posted
            player_ids[1]: blinds[1]   # BB already posted
        }
        
        # Deduct blinds from stack sizes
        self.stack_sizes[player_ids[0]] -= blinds[0]
        self.stack_sizes[player_ids[1]] -= blinds[1]
    
    def is_terminal(self) -> bool:
        """Check if the game state is terminal (hand is over)."""
        return self.stage == GameStage.TERMINAL
    
    def get_legal_actions(self) -> List[Action]:
        """
        Get the legal actions for the current player.
        
        Returns:
            List of legal Action objects
        """
        if self.is_terminal():
            return []
        
        legal_actions = [Action.FOLD]  # Always can fold
        
        player_bet = self.player_bets[self.current_player]
        opponent_bet = self.current_bet
        
        # If player has less chips than needed to call, they can only fold or all-in
        if self.stack_sizes[self.current_player] + player_bet < opponent_bet:
            legal_actions.append(Action.ALL_IN)
            return legal_actions
        
        # Player can call if they haven't matched the current bet
        if player_bet < opponent_bet:
            legal_actions.append(Action.CALL)
        
        # Check is only available in special pre-flop scenario:
        # When dealer has called, big blind has option to check
        if (self.stage == GameStage.PREFLOP and 
            self.positions[self.current_player] == Position.BIG_BLIND and
            player_bet == opponent_bet and
            len(self.betting_history) > 0 and
            self.betting_history[-1][1] == Action.CALL):
            legal_actions.append(Action.CHECK)
        
        # Player can raise if they have enough chips
        min_raise_size = opponent_bet * 2  # Minimum raise is double current bet
        if self.stack_sizes[self.current_player] + player_bet >= min_raise_size:
            legal_actions.append(Action.RAISE)
        
        # Player can go all-in if they have chips
        if self.stack_sizes[self.current_player] > 0:
            legal_actions.append(Action.ALL_IN)
            
        return legal_actions


class GameRules:
    """
    Enforces the deterministic rules of pre-flop Texas Hold'em poker.
    
    This class handles transitions between game states based on player actions,
    applying the deterministic rules of the game.
    """
    
    @staticmethod
    def validate_action(state: GameState, player_id: str, action: Action, raise_amount: Optional[float] = None) -> bool:
        """
        Validate if an action is legal in the current game state.
        
        Args:
            state: Current game state
            player_id: ID of the player taking the action
            action: The action being taken
            raise_amount: Amount to raise (only used for RAISE action)
            
        Returns:
            True if the action is valid, False otherwise
        """
        if state.is_terminal():
            return False
            
        if player_id != state.current_player:
            return False
            
        legal_actions = state.get_legal_actions()
        if action not in legal_actions:
            return False
            
        # Additional validation for raise amounts
        if action == Action.RAISE and raise_amount is not None:
            min_raise = state.current_bet * 2
            if raise_amount < min_raise:
                return False
            if raise_amount > state.stack_sizes[player_id] + state.player_bets[player_id]:
                return False
                
        return True
    
    @staticmethod
    def apply_action(state: GameState, player_id: str, action: Action, 
                     raise_amount: Optional[float] = None) -> GameState:
        """
        Apply an action to the current game state and return the new state.
        
        Args:
            state: Current game state
            player_id: ID of the player taking the action
            action: The action being taken
            raise_amount: Amount to raise (only used for RAISE action)
            
        Returns:
            New game state after applying the action
        """
        # Validate action first
        if not GameRules.validate_action(state, player_id, action, raise_amount):
            raise ValueError(f"Invalid action {action} for player {player_id} in current state")
        
        # Create a new state to avoid modifying the original
        new_state = GameState(
            player_ids=list(state.positions.keys()),
            hole_cards=state.hole_cards,
            stack_sizes=state.stack_sizes.copy()
        )
        
        # Copy all other state attributes
        new_state.positions = state.positions.copy()
        new_state.pot_size = state.pot_size
        new_state.betting_history = state.betting_history.copy()
        new_state.active_players = state.active_players.copy()
        new_state.stage = state.stage
        new_state.current_player = state.current_player
        new_state.winner = state.winner
        new_state.last_raiser = state.last_raiser
        new_state.current_bet = state.current_bet
        new_state.player_bets = state.player_bets.copy()
        
        # Apply the action
        if action == Action.FOLD:
            GameRules._apply_fold(new_state, player_id)
        elif action == Action.CHECK:
            GameRules._apply_check(new_state, player_id)
        elif action == Action.CALL:
            GameRules._apply_call(new_state, player_id)
        elif action == Action.RAISE:
            GameRules._apply_raise(new_state, player_id, raise_amount)
        elif action == Action.ALL_IN:
            GameRules._apply_all_in(new_state, player_id)
        
        # Record the action in betting history
        action_record = (player_id, action)
        if action == Action.RAISE or action == Action.ALL_IN:
            action_record = (player_id, action, raise_amount)
        new_state.betting_history.append(action_record)
        
        # Determine next player or state transition
        GameRules._update_game_stage(new_state)
        
        return new_state
    
    @staticmethod
    def _apply_fold(state: GameState, player_id: str) -> None:
        """
        Apply a fold action.
        
        Args:
            state: Current game state
            player_id: ID of the player folding
        """
        # Remove player from active players
        state.active_players.remove(player_id)
        
        # Determine winner (the only remaining player)
        opponent_id = next(pid for pid in state.positions if pid != player_id)
        state.winner = opponent_id
        
        # Set stage to terminal
        state.stage = GameStage.TERMINAL
    
    @staticmethod
    def _apply_check(state: GameState, player_id: str) -> None:
        """
        Apply a check action.
        
        Args:
            state: Current game state
            player_id: ID of the player checking
        """
        # No changes to pot or bets, just update current player
        opponent_id = next(pid for pid in state.positions if pid != player_id)
        state.current_player = opponent_id
    
    @staticmethod
    def _apply_call(state: GameState, player_id: str) -> None:
        """
        Apply a call action.
        
        Args:
            state: Current game state
            player_id: ID of the player calling
        """
        # Calculate call amount
        call_amount = state.current_bet - state.player_bets[player_id]
        
        # Update player's stack and bet
        state.stack_sizes[player_id] -= call_amount
        state.player_bets[player_id] += call_amount
        
        # Update pot size
        state.pot_size += call_amount
        
        # Update current player
        opponent_id = next(pid for pid in state.positions if pid != player_id)
        state.current_player = opponent_id
    
    @staticmethod
    def _apply_raise(state: GameState, player_id: str, raise_amount: float) -> None:
        """
        Apply a raise action.
        
        Args:
            state: Current game state
            player_id: ID of the player raising
            raise_amount: Total amount the player is raising to
        """
        # Calculate the actual amount to add
        current_bet = state.player_bets[player_id]
        amount_to_add = raise_amount - current_bet
        
        # Update player's stack and bet
        state.stack_sizes[player_id] -= amount_to_add
        state.player_bets[player_id] = raise_amount
        
        # Update pot size
        state.pot_size += amount_to_add
        
        # Update current bet and last raiser
        state.current_bet = raise_amount
        state.last_raiser = player_id
        
        # Update current player
        opponent_id = next(pid for pid in state.positions if pid != player_id)
        state.current_player = opponent_id
    
    @staticmethod
    def _apply_all_in(state: GameState, player_id: str) -> None:
        """
        Apply an all-in action.
        
        Args:
            state: Current game state
            player_id: ID of the player going all-in
        """
        # All-in amount is the player's remaining stack plus their current bet
        all_in_amount = state.stack_sizes[player_id] + state.player_bets[player_id]
        
        # Calculate the actual amount to add
        current_bet = state.player_bets[player_id]
        amount_to_add = state.stack_sizes[player_id]
        
        # Update player's stack and bet
        state.stack_sizes[player_id] = 0
        state.player_bets[player_id] = all_in_amount
        
        # Update pot size
        state.pot_size += amount_to_add
        
        # If all-in amount is greater than current bet, update current bet
        if all_in_amount > state.current_bet:
            state.current_bet = all_in_amount
            state.last_raiser = player_id
        
        # Update current player
        opponent_id = next(pid for pid in state.positions if pid != player_id)
        state.current_player = opponent_id
    
    @staticmethod
    def _update_game_stage(state: GameState) -> None:
        """
        Update the game stage based on the current state.
        
        Args:
            state: Current game state
        """
        # If there's only one active player, game is terminal
        if len(state.active_players) == 1:
            state.stage = GameStage.TERMINAL
            state.winner = next(iter(state.active_players))
            return
        
        # If both players are all-in, proceed to showdown
        if all(stack == 0 for stack in state.stack_sizes.values()):
            # In a real game, we'd deal all remaining community cards
            # But for our pre-flop model, we just transition to terminal
            state.stage = GameStage.TERMINAL
            # Winner will be determined by equity or actual showdown
            return
        
        # Check conditions for pre-flop to flop transition
        if state.stage == GameStage.PREFLOP:
            # Check if betting is completed (all players have matched the bet)
            all_bets_matched = all(bet == state.current_bet for bet in state.player_bets.values())
            
            # If big blind checks or all bets are matched, proceed to flop
            if (all_bets_matched and 
                (len(state.betting_history) > 0 and 
                 state.betting_history[-1][1] == Action.CHECK or
                 state.betting_history[-1][1] == Action.CALL)):
                state.stage = GameStage.FLOP
                # Reset bets for next round
                state.player_bets = {player: 0 for player in state.player_bets}
                state.current_bet = 0
                
                # In flop, dealer acts first
                dealer_id = next(pid for pid, pos in state.positions.items() 
                              if pos == Position.DEALER)
                state.current_player = dealer_id


def calculate_reward(state: GameState, player_id: str, equity_calculator=None) -> float:
    """
    Calculate the reward for a player based on the current game state.
    
    Args:
        state: Current game state
        player_id: ID of the player to calculate reward for
        equity_calculator: Optional function to calculate equity between hands
        
    Returns:
        Reward value for the player
    """
    if not state.is_terminal() and state.stage == GameStage.PREFLOP:
        # If game is still in pre-flop, no immediate reward
        return 0
    
    # If game is terminal due to fold, winner gets pot
    if state.is_terminal() and state.winner is not None:
        if state.winner == player_id:
            return state.pot_size
        else:
            return -state.pot_size
    
    # If game moved to flop, calculate reward based on equity
    if state.stage == GameStage.FLOP:
        # Get player hands
        player_hand = state.hole_cards[player_id]
        opponent_id = next(pid for pid in state.positions if pid != player_id)
        opponent_hand = state.hole_cards[opponent_id]
        
        # If equity calculator is provided, use it
        if equity_calculator:
            player_equity, opponent_equity = equity_calculator(player_hand, opponent_hand)
        else:
            # Fallback to simple estimation (not accurate)
            player_equity = 0.5
            opponent_equity = 0.5
        
        # Apply formula: R_i = (2*e_i - 1) * P
        reward = (2 * player_equity - 1) * state.pot_size
        return reward
    
    # Default case (shouldn't reach here)
    return 0