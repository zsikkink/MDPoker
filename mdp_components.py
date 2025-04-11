#mdp_components.py

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

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
      - betting_history: The public record of actions taken in the current hand.
      - structured_betting_history: Formatted betting history for reinforcement learning.
      - implied_probability: The minimum equity needed to make a call profitable.
      
    Note:
      This state does NOT include the opponent's hole cards.
    """
    my_hole_cards: HoleCards
    stack_sizes: Dict[str, float]
    pot_size: float
    betting_history: List[Any] = field(default_factory=list)
    structured_betting_history: Dict[str, Any] = None
    implied_probability: float = None

# ============================================================
# State Formatting Functions for Reinforcement Learning
# ============================================================

def format_betting_history_for_rl(betting_history):
    """
    Converts the raw betting history into a structured format suitable for reinforcement learning.
    
    Args:
        betting_history (list): The raw betting history from the environment
        
    Returns:
        dict: A structured representation with the following keys:
            - num_actions: Total number of actions taken
            - num_raises: Number of raises
            - num_calls: Number of calls
            - num_checks: Number of checks
            - last_action_type: Encoded last action (0=none, 1=fold, 2=check, 3=call, 4=raise)
            - last_action_player: Encoded player (0=none, 1=BTN, 2=BB)
            - last_action_amount: Amount of the last action (0 for fold/check)
            - last_raise_size: Size of the last raise (0 if no raises)
            - btn_aggression: Ratio of raises to total actions by BTN
            - bb_aggression: Ratio of raises to total actions by BB
    """
    if not betting_history:
        return {
            "num_actions": 0,
            "num_raises": 0,
            "num_calls": 0,
            "num_checks": 0,
            "last_action_type": 0,  # 0 means no action yet
            "last_action_player": 0,  # 0 means no player yet
            "last_action_amount": 0,
            "last_raise_size": 0,
            "btn_aggression": 0,
            "bb_aggression": 0
        }
    
    # Count actions by type
    num_raises = sum(1 for action in betting_history if action['action'] == 'raise')
    num_calls = sum(1 for action in betting_history if action['action'] == 'call')
    num_checks = sum(1 for action in betting_history if action['action'] == 'check')
    
    # Get the last action information
    last_action = betting_history[-1]
    last_action_type = {
        'fold': 1,
        'check': 2,
        'call': 3,
        'raise': 4
    }.get(last_action['action'], 0)
    
    last_action_player = 1 if last_action['player'] == 'BTN' else 2
    last_action_amount = last_action.get('amount', 0) if 'amount' in last_action else 0
    
    # Calculate last raise size
    last_raise_size = 0
    for action in reversed(betting_history):
        if action['action'] == 'raise' and 'amount' in action:
            # Find the previous bet to calculate the raise size
            prev_bet = 0
            for prev_action in reversed(betting_history[:betting_history.index(action)]):
                if 'amount' in prev_action:
                    prev_bet = prev_action['amount']
                    break
            last_raise_size = action['amount'] - prev_bet
            break
    
    # Calculate aggression metrics
    btn_actions = [a for a in betting_history if a['player'] == 'BTN']
    bb_actions = [a for a in betting_history if a['player'] == 'BB']
    
    btn_aggression = sum(1 for a in btn_actions if a['action'] == 'raise') / len(btn_actions) if btn_actions else 0
    bb_aggression = sum(1 for a in bb_actions if a['action'] == 'raise') / len(bb_actions) if bb_actions else 0
    
    return {
        "num_actions": len(betting_history),
        "num_raises": num_raises,
        "num_calls": num_calls,
        "num_checks": num_checks,
        "last_action_type": last_action_type,
        "last_action_player": last_action_player,
        "last_action_amount": last_action_amount,
        "last_raise_size": last_raise_size,
        "btn_aggression": btn_aggression,
        "bb_aggression": bb_aggression
    }


def get_state_vector_for_rl(agent_state):
    """
    Converts an AgentState object into a fixed-size vector suitable for Q-learning.
    
    This function standardizes the state representation for reinforcement learning:
    1. All features are numerical (no categorical variables)  
    2. Most values are normalized to the [0,1] range
    3. The vector has a fixed length regardless of betting history
    4. The representation captures key poker features (hand strength, position, etc.)
    
    Args:
        agent_state (AgentState): The agent's state object
        
    Returns:
        list: A fixed-size vector of numerical values representing the state
    """
    # Extract structured betting history
    betting_info = agent_state.structured_betting_history
    
    # Create feature vector
    state_vector = [
        # Hand information
        agent_state.my_hole_cards.estimated_equity,  # Equity estimate
        int(agent_state.my_hole_cards.suited),       # Is suited (0 or 1)
        int(agent_state.my_hole_cards.pair),         # Is a pair (0 or 1)
        int(agent_state.my_hole_cards.connected),    # Is connected (0 or 1)
        
        # Stack and pot information
        agent_state.stack_sizes['BTN'] / 100,        # Normalize by starting stack
        agent_state.stack_sizes['BB'] / 100,         # Normalize by starting stack
        agent_state.pot_size / 100,                  # Normalize by starting stack
        
        # Implied probability
        agent_state.implied_probability if agent_state.implied_probability is not None else 0.0,
        
        # Betting history information
        betting_info['num_actions'] / 10,            # Normalize (unlikely to have more than 10 actions)
        betting_info['num_raises'] / 5,              # Normalize
        betting_info['num_calls'] / 5,               # Normalize
        betting_info['num_checks'] / 5,              # Normalize
        betting_info['last_action_type'] / 4,        # Normalize (4 action types)
        betting_info['last_action_player'] / 2,      # Normalize (2 players)
        betting_info['last_action_amount'] / 100,    # Normalize by typical max stack
        betting_info['last_raise_size'] / 50,        # Normalize by typical max raise
        betting_info['btn_aggression'],              # Already normalized (0 to 1)
        betting_info['bb_aggression']                # Already normalized (0 to 1)
    ]
    
    return state_vector

# ============================================================
# Action Space Definitions
# ============================================================

class ActionType(Enum):
    FOLD = "fold"
    CALL = "call"
    CHECK = "check"
    RAISE = "raise"

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

def get_available_actions(current_bet: float, player_stack: float, is_dealer: bool, 
                          last_raise_size: float = None, is_first_action: bool = True) -> List[PokerAction]:
    """
    Determines and returns the available actions for the current player given the current game state.
    
    Parameters:
      - current_bet (float): The bet amount that the player needs to call.
                             A value of 0 implies no additional wager is pending.
      - player_stack (float): The player's current stack (chips available for further bets).
      - is_dealer (bool): True if the player is in the dealer (BTN) position,
                          False if in the big blind (BB) position.
      - last_raise_size (float): The size of the last raise made, if any.
                                Default is None when no raises have been made yet.
      - is_first_action (bool): Whether this is the first action in the hand.
                               Default is True, meaning BTN's initial decision.
    
    Returns:
      A list of PokerAction instances that represent all available actions.
    """
    actions: List[PokerAction] = []
    
    # Fold is always an option.
    actions.append(PokerAction(ActionType.FOLD))
    
    # Determine Call vs. Check availability.
    if current_bet > 0:
        actions.append(PokerAction(ActionType.CALL))
    else:
        # In a pre-flop setting:
        # - The dealer (BTN) is assumed to act first and typically must call (matching the BB) even if no extra bet is pending.
        # - The BB, after seeing the dealer's action, is allowed to check.
        if is_dealer:
            actions.append(PokerAction(ActionType.CALL))
        else:
            actions.append(PokerAction(ActionType.CHECK))
    
    # Calculate how much the player has already contributed
    player_contribution = 0
    if is_dealer:
        player_contribution = 0.5  # BTN's posted blind
    else:
        player_contribution = 1.0  # BB's posted blind
    
    # Calculate how much the player would need to add to meet the current bet
    to_call = max(0, current_bet - player_contribution)
    
    # Available stack after calling
    remaining = player_stack - to_call
    
    # Raise options are only available if the player has chips left after calling
    if remaining > 0:
        # Determine minimum raise amount based on the situation
        min_raise_total = 0
        
        if is_first_action and is_dealer:
            # Initial raise by BTN must be at least 2 total
            min_raise_total = 2.0
        elif last_raise_size is not None:
            # Subsequent raises must at least double the last raise
            min_raise_total = current_bet + last_raise_size
        else:
            # If no previous raise (BB after BTN calls), minimum raise is 2
            min_raise_total = 2.0
        
        # Calculate how much additional the player needs to contribute for min raise
        min_raise_additional = min_raise_total - player_contribution
        
        # Discrete raise options, expressed in units of big blind
        # (representing the player's total contribution)
        raise_options = []
        
        # Start with the minimum raise
        if min_raise_additional <= remaining:
            raise_options.append(min_raise_total)
        
        # Add standard raise options that exceed the minimum
        standard_options = [2, 2.5, 3, 4, 5, 6, 8, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for option in standard_options:
            # Skip options below the minimum raise
            if option < min_raise_total:
                continue
            # Skip options that exceed the player's stack
            if option - player_contribution <= remaining:
                raise_options.append(option)
        
        # Add raise actions to the available actions list
        for option in raise_options:
            actions.append(PokerAction(ActionType.RAISE, raise_amount=option))
        
        # Always include an "all in" option if it's different from the other options
        all_in_amount = player_contribution + remaining
        if all_in_amount not in raise_options and all_in_amount > current_bet:
            actions.append(PokerAction(ActionType.RAISE, raise_amount=all_in_amount))
    
    return actions

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
    
    # Create structured betting history for RL
    structured_history = format_betting_history_for_rl(betting_history)
    
    # Construct the AgentState that an agent would observe.
    agent_state = AgentState(
        my_hole_cards=my_cards,
        stack_sizes=current_stacks,
        pot_size=current_pot,
        betting_history=betting_history,
        structured_betting_history=structured_history,
        implied_probability=0.25  # Example value: need 25% equity to call profitably
    )
    
    # Create a state vector for Q-learning
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