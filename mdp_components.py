#mdp_components.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import utils  # Import the utils module where shared functions now live

# ============================================================
# State Space Definitions
# ============================================================

@dataclass(frozen=True)
class HoleCards:
    """
    Represents the characteristics of a player's hole cards.

    Attributes:
      - classified: The hand notation (e.g., "AA", "AKs", "A2o", "85o").
      - suited: True if both cards have the same suit.
      - pair: True if both cards share the same rank.
      - connected: For non-pair hands, True if the two card ranks are consecutive
                   (Ace with 2 or Ace with King count as connected based on specific rules).
      - estimated_equity: The estimated winning equity (float between 0 and 1) versus a random hand.
    """
    classified: str
    suited: bool
    pair: bool
    connected: bool
    estimated_equity: float

@dataclass
class AgentState:
    """
    Represents the observable state for an agent during a poker hand.
    
    Components:
      - my_hole_cards: The agent's own hole cards (private information).
      - stack_sizes: A dictionary mapping each player's identifier (e.g., 'BTN', 'BB')
                     to their current stack size.
      - pot_size: The public current pot size.
      - position: 'BTN' or 'BB' to clearly indicate player's position
      - current_bet_to_call: How much the player needs to call
      - is_first_action: Whether this is the first action in the hand
      - betting_history: The public record of actions taken in the current hand.
      - structured_betting_history: Formatted betting history for reinforcement learning.
      - implied_probability: The minimum equity needed to make a call profitable.
      - last_raise_size: Size of the last raise (useful for action selection)
      
    Note:
      This state does NOT include the opponent's hole cards.
    """
    my_hole_cards: HoleCards
    stack_sizes: Dict[str, float]
    pot_size: float
    position: str  # 'BTN' or 'BB' to clearly indicate player's position
    current_bet_to_call: float  # How much the player needs to call
    is_first_action: bool  # Whether this is the first action in the hand
    betting_history: List[Any] = field(default_factory=list)
    structured_betting_history: Dict[str, Any] = None
    implied_probability: float = None
    last_raise_size: float = None  # Size of the last raise (useful for action selection)

# ============================================================
# Action Space Definitions
# ============================================================

class ActionType(Enum):
    FOLD = utils.ACTION_FOLD
    CALL = utils.ACTION_CALL
    CHECK = utils.ACTION_CHECK
    RAISE = utils.ACTION_RAISE

class PokerAction:
    """
    Represents an action in the player's available action space.
    
    Attributes:
        action_type: One of FOLD, CALL, CHECK, or RAISE.
        raise_amount: For RAISE actions, this indicates the raise size (in BB units or the all-in amount).
                      For non-raise actions, this value is None.
    """
    def __init__(self, action_type: ActionType, raise_amount: Optional[float] = None):
        self.action_type = action_type
        self.raise_amount = raise_amount

    def __repr__(self):
        if self.action_type == ActionType.RAISE:
            return f"PokerAction(RAISE, {self.raise_amount})"
        return f"PokerAction({self.action_type.value})"

    def to_dict(self):
        """Convert PokerAction to dictionary format compatible with utils module"""
        result = {'action_type': self.action_type.value}
        if self.raise_amount is not None:
            result['raise_amount'] = self.raise_amount
        return result

# ============================================================
# Utility Functions to Bridge Between Dictionary and Class Representations
# ============================================================

def dict_to_hole_cards(hole_cards_dict: Dict) -> HoleCards:
    """Convert hole cards dictionary to HoleCards dataclass instance"""
    return HoleCards(
        classified=hole_cards_dict['classified'],
        suited=hole_cards_dict['suited'],
        pair=hole_cards_dict['pair'],
        connected=hole_cards_dict['connected'],
        estimated_equity=hole_cards_dict['estimated_equity']
    )

def dict_to_agent_state(state_dict: Dict) -> AgentState:
    """Convert state dictionary from utils.get_state() to AgentState instance"""
    return AgentState(
        my_hole_cards=dict_to_hole_cards(state_dict['my_hole_cards']),
        stack_sizes=state_dict['stack_sizes'],
        pot_size=state_dict['pot_size'],
        position=state_dict['position'],
        current_bet_to_call=state_dict['current_bet_to_call'],
        is_first_action=state_dict['is_first_action'],
        betting_history=state_dict['betting_history'],
        structured_betting_history=state_dict['structured_betting_history'],
        implied_probability=state_dict['implied_probability'],
        last_raise_size=state_dict['last_raise_size']
    )

def action_dict_to_poker_action(action_dict: Dict) -> PokerAction:
    """Convert action dictionary from utils to PokerAction instance"""
    action_type = ActionType(action_dict['action_type'])
    raise_amount = action_dict.get('raise_amount')
    return PokerAction(action_type, raise_amount)

def get_available_actions(current_bet: float, player_stack: float, is_dealer: bool, 
                         last_raise_size: float = None, is_first_action: bool = True) -> List[PokerAction]:
    """
    Wrapper around utils.get_available_actions that returns PokerAction instances.
    """
    # Get actions in dictionary format from utils
    action_dicts = utils.get_available_actions(
        current_bet=current_bet,
        player_stack=player_stack,
        is_dealer=is_dealer,
        last_raise_size=last_raise_size,
        is_first_action=is_first_action
    )
    
    # Convert to PokerAction instances
    return [action_dict_to_poker_action(action_dict) for action_dict in action_dicts]

# ============================================================
# State vector creation for RL - now uses utils implementation
# ============================================================

def get_state_vector_for_rl(agent_state: AgentState) -> List[float]:
    """
    Creates a state vector for reinforcement learning from AgentState
    
    Args:
        agent_state: AgentState instance
        
    Returns:
        List of normalized feature values
    """
    # Convert AgentState to dictionary format that utils.get_state_vector_for_deep_rl expects
    state_dict = {
        'position': agent_state.position,
        'my_hole_cards': {
            'classified': agent_state.my_hole_cards.classified,
            'suited': agent_state.my_hole_cards.suited,
            'pair': agent_state.my_hole_cards.pair,
            'connected': agent_state.my_hole_cards.connected,
            'estimated_equity': agent_state.my_hole_cards.estimated_equity
        },
        'stack_sizes': agent_state.stack_sizes,
        'pot_size': agent_state.pot_size,
        'current_bet_to_call': agent_state.current_bet_to_call,
        'last_raise_size': agent_state.last_raise_size,
        'implied_probability': agent_state.implied_probability,
        'structured_betting_history': agent_state.structured_betting_history,
        'is_first_action': agent_state.is_first_action
    }
    
    # Use the utils function to generate the state vector
    return utils.get_state_vector_for_deep_rl(state_dict)


# ============================================================
# Example usage
# ============================================================
if __name__ == "__main__":
    # --- Agent State Example ---
    # Assume the agent's private hole cards are Ace-King suited.
    my_cards = HoleCards(
        classified="AKs",
        suited=True,
        pair=False,
        connected=True,
        estimated_equity=0.66  # Hypothetical equity value.
    )
    
    # Public state information: current stack sizes and pot size.
    current_stacks = {"BTN": 99.5, "BB": 99}
    current_pot = 1.5  # Fixed because the blinds (0.5 for BTN and 1 for BB) sum to 1.5.
    
    # Let's create a sample betting history
    betting_history = [
        {"player": "BTN", "action": "raise", "amount": 2.5},
        {"player": "BB", "action": "call", "amount": 2.5}
    ]
    
    # Create structured betting history for RL using the utils function
    structured_history = utils.format_betting_history_for_rl(betting_history)
    
    # Construct the AgentState that an agent would observe.
    agent_state = AgentState(
        my_hole_cards=my_cards,
        stack_sizes=current_stacks,
        pot_size=current_pot,
        position="BTN",
        current_bet_to_call=0,
        is_first_action=False,
        betting_history=betting_history,
        structured_betting_history=structured_history,
        implied_probability=0.25  # Example value: need 25% equity to call profitably
    )
    
    # Create a state vector for RL using our wrapper function
    state_vector = get_state_vector_for_rl(agent_state)
    print("\nRL State Vector:\n", state_vector)
    
    print("Agent State:", agent_state)
    
    # --- Action Space Example ---
    # Scenario 1: For the dealer (BTN) with a current bet of 1, and a stack of 99.5.
    actions_BTN = get_available_actions(current_bet=1, player_stack=99.5, is_dealer=True)
    print("\nAvailable actions for BTN (with a current bet of 1):", actions_BTN)
    
    # Scenario 2: For the big blind (BB) with no extra bet (current_bet=0) and a stack of 99.
    actions_BB = get_available_actions(current_bet=0, player_stack=99, is_dealer=False)
    print("\nAvailable actions for BB (with no extra bet):", actions_BB)