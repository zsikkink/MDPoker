# environment.py

from mdp_components import (
    HoleCards, AgentState, PokerAction, ActionType, action_dict_to_poker_action
)
from utils import (
    shuffle_deck, deal, calculate_equity, classify_hand,
    calculate_reward_no_fold, calculate_reward_fold,
    get_available_actions, BB_actions,
    get_state, get_state_vector_for_deep_rl  # Assuming these functions exist in utils.
)

class PreflopHeadsUpEnv:
    """
    Environment to simulate a heads-up pre-flop Texas Hold'em hand.
    
    At the start of the hand, both players start with stacks of 100.
    The BTN posts a blind of 0.5 and the BB posts a blind of 1.
    Contributions are initialized as {BTN: 0.5, BB: 1}.
    A new deck is created, shuffled, and cards are dealt.
    
    On each turn, the active player's state is generated using get_state 
    followed by get_state_vector_for_deep_rl. The player then selects an action.
    
    - If BTN folds, calculate_reward_fold is called, rewards are assigned, 
      and the hand is reset.
    - If BTN calls, the contributions are updated to {BTN: 1, BB: 1}, 
      the betting history and BTN's stack are updated, and then BB_actions are used.
    - If BB checks, the hand ends immediately (calculate_reward_no_fold is called), 
      and the hand resets.
    - If any player raises, contributions, betting history, stack, and the pot are updated,
      the turn passes to the opponent and available actions are recalculated.
    """
    
    def __init__(self, default_stack=100, btn_post=0.5, bb_post=1):
        self.default_stack = default_stack
        self.btn_post = btn_post   # BTN posts 0.5
        self.bb_post = bb_post     # BB posts 1
        self.players = {}          # Dictionary with player's stack and position
        self.deck = []             # The deck of cards
        self.hands = None          # Tuple of dealt hands (BTN_hand, BB_hand)
        self.contributions = {}    # Dictionary of contributions for the current hand
        self.pot = 0               # Total chips in the pot (sum of contributions)
        self.betting_history = []  # List of action dictionaries
        self.current_bet = 0       # The highest bet required to call
        self.current_turn = None   # Which player's turn: "BTN" or "BB"
        self.last_raise_size = None  # Size of the last raise
        self.is_preflop = True     # Flag indicating the preflop betting round
        
        # Flag to signal that BTN’s first action was a call meeting the exact amount
        # (i.e., 0.5 to call) so that BB should use its dedicated actions.
        self.use_bb_actions = False

    def reset(self):
        """
        Resets the environment for a new hand.
        Initializes player stacks (after deducting blinds), posts blinds,
        resets contributions, shuffles the deck, and deals new hands.
        The current turn is set to BTN.
        
        Returns:
            tuple: (players, hands)
        """
        self.players = {
            "BTN": {"stack": self.default_stack - self.btn_post, "position": "BTN"},
            "BB":  {"stack": self.default_stack - self.bb_post, "position": "BB"}
        }
        self.contributions = {"BTN": self.btn_post, "BB": self.bb_post}
        self.pot = self.contributions["BTN"] + self.contributions["BB"]
        self.current_bet = self.bb_post  # The current highest bet is BB's blind (1).
        self.betting_history = []
        self.current_turn = "BTN"
        self.last_raise_size = None
        self.is_preflop = True
        
        # Reset the special flag.
        self.use_bb_actions = False
        
        self.deck = shuffle_deck()
        self.hands = deal(self.deck)
        return self.players, self.hands

    def step(self, action: PokerAction):
        """
        Process the action chosen by the current player and update the state.
        
        The function expects that before an action is chosen, the state vector is
        created via get_state and get_state_vector_for_deep_rl for the acting player.
        
        Args:
            action (PokerAction): The chosen action.
        
        Returns:
            tuple: (rewards, info, done)
                - rewards: Tuple (reward_BTN, reward_BB) computed based on the hand's outcome.
                - info: Dictionary with updated state information.
                - done (bool): Whether the hand is over.
        """
        current_player = self.current_turn
        opponent = "BB" if current_player == "BTN" else "BTN"
        
        # --- Handle Fold ---
        if action.action_type == ActionType.FOLD:
            self.betting_history.append({"player": current_player, "action": "fold"})
            reward_BTN, reward_BB = calculate_reward_fold(current_player, self.contributions)
            info = {
                "terminal_reason": "fold",
                "action_by": current_player,
                "betting_history": self.betting_history,
                "players": self.players,
                "contributions": self.contributions,
                "hands": self.hands
            }
            done = True
            return (reward_BTN, reward_BB), info, done

        # --- Handle Call or Check ---
        elif action.action_type in [ActionType.CALL, ActionType.CHECK]:
            additional = 0
            if action.action_type == ActionType.CALL:
                additional = self.current_bet - self.contributions[current_player]
                additional = max(additional, 0)
                self.betting_history.append({
                    "player": current_player, "action": "call", "amount": self.current_bet
                })
            else:
                self.betting_history.append({
                    "player": current_player, "action": "check"
                })
            
            # Update player's stack and contribution.
            self.players[current_player]["stack"] -= additional
            self.contributions[current_player] += additional
            self.pot = self.contributions["BTN"] + self.contributions["BB"]

            # --- Special logic for BTN's first action ---
            if current_player == "BTN" and len(self.betting_history) == 1 and action.action_type == ActionType.CALL:
                expected_call = self.bb_post - self.btn_post  # Expected: 1 - 0.5 = 0.5.
                if abs(additional - expected_call) < 1e-6:
                    self.use_bb_actions = True

            # --- Determine if hand should terminate ---
            hand_terminates = False
            if self.is_preflop and action.action_type == ActionType.CHECK and current_player == "BB":
                hand_terminates = True
            if len(self.betting_history) >= 2:
                had_raise = any(a['action'] == 'raise' for a in self.betting_history[:-1])
                if had_raise and action.action_type == ActionType.CALL:
                    hand_terminates = True

            if hand_terminates:
                equity_BTN, equity_BB = calculate_equity(self.hands[0], self.hands[1])
                reward_BTN, reward_BB = calculate_reward_no_fold(equity_BTN, equity_BB, self.contributions)
                info = {
                    "terminal_reason": "call/check",
                    "action_by": current_player,
                    "betting_history": self.betting_history,
                    "players": self.players,
                    "contributions": self.contributions,
                    "hands": self.hands
                }
                done = True
                return (reward_BTN, reward_BB), info, done
            else:
                self.current_turn = opponent
                info = {
                    "terminal_reason": None,
                    "action_by": current_player,
                    "betting_history": self.betting_history,
                    "players": self.players,
                    "contributions": self.contributions,
                    "current_bet": self.current_bet,
                    "use_bb_actions": self.use_bb_actions
                }
                done = False
                return (0, 0), info, done

        # --- Handle Raise ---
        elif action.action_type == ActionType.RAISE:
            raise_amount = action.raise_amount  # The new total bet for the current player.
            if raise_amount <= self.current_bet:
                raise ValueError("Raise amount must exceed the current bet.")

            additional = raise_amount - self.contributions[current_player]
            if additional > self.players[current_player]["stack"]:
                additional = self.players[current_player]["stack"]
                raise_amount = self.contributions[current_player] + additional

            self.last_raise_size = raise_amount - self.current_bet
            self.players[current_player]["stack"] -= additional
            self.contributions[current_player] += additional
            self.pot = self.contributions["BTN"] + self.contributions["BB"]
            self.current_bet = raise_amount

            self.betting_history.append({
                "player": current_player, "action": "raise", "amount": raise_amount
            })
            self.current_turn = opponent

            info = {
                "terminal_reason": None,
                "action_by": current_player,
                "betting_history": self.betting_history,
                "players": self.players,
                "contributions": self.contributions,
                "current_bet": self.current_bet
            }
            done = False
            return (0, 0), info, done

        else:
            raise ValueError("Invalid action type.")

    def get_current_legal_actions(self):
        """
        Returns the list of legal actions available to the current player.
        
        If the current player is BB and use_bb_actions is set (because BTN's first action was a call),
        then BB_actions from utils is used. Otherwise, get_available_actions is used with the arguments:
          - current_bet, player_stack, is_dealer, and opponent_contributions.
        
        The returned actions are converted from dictionaries (if needed) into PokerAction objects.
        """
        if self.current_turn == "BB" and self.use_bb_actions:
            actions = BB_actions(
                player_stack=self.players["BB"]["stack"],
                opponent_contributions=self.contributions["BTN"]
            )
        else:
            opponent = "BB" if self.current_turn == "BTN" else "BTN"
            actions = get_available_actions(
                current_bet=self.current_bet,
                player_stack=self.players[self.current_turn]["stack"],
                is_dealer=(self.current_turn == "BTN"),
                opponent_contributions=self.contributions[opponent]
            )
        # Convert each action to a PokerAction if they are dictionaries.
        converted_actions = []
        for act in actions:
            if isinstance(act, dict):
                converted_actions.append(action_dict_to_poker_action(act))
            else:
                converted_actions.append(act)
        return converted_actions


# --- Main interactive loop for playing from both player's perspective ---
if __name__ == '__main__':
    env = PreflopHeadsUpEnv()
    
    while True:  # Main game loop for repeated hands.
        players, hands = env.reset()
        print("\n======== New Hand Started ========")
        print("Initial Hands:", hands)
        print("Initial Contributions:", env.contributions)
        print("Initial Pot:", env.pot)
        
        done = False
        
        # Continue until the hand ends.
        while not done:
            current_player = env.current_turn
            
            # Select the appropriate hole cards.
            if current_player == "BTN":
                player_hand = hands[0]
            else:  # current_player is "BB"
                player_hand = hands[1]
            
            # Generate the state and convert it into a state vector.
            state = get_state(
                current_player,
                player_hand,
                {p: env.players[p]["stack"] for p in env.players},
                env.contributions,
                env.betting_history,
                is_first_action=(len(env.betting_history) == 0)
            )
            state_vector = get_state_vector_for_deep_rl(state)
            
            # Label the features.
            feature_labels = [
                "Position Encoding (1=BTN, 0=BB)",
                "Estimated Equity",
                "Is Suited (0/1)",
                "Is Pair (0/1)",
                "Is Connected (0/1)",
                "Premium Hand Indicator (>0.70 equity)",
                "Premium Pair Indicator (AA/KK/QQ)",
                "Own Stack (Normalized / 100)",
                "Opponent Stack (Normalized / 100)",
                "Pot Size (Normalized / 100)",
                "Stack-to-Pot Ratio (SPR)",
                "Current Bet-to-Call (Normalized / 100)",
                "Last Raise Size (Normalized / 100)",
                "Implied Probability",
                "BTN Aggression",
                "BB Aggression",
                "Number of Raises (Normalized / 5)",
                "Is First Action (0/1)"
            ]
            
            # Print the active player's state with labels.
            print(f"\nThis is the {current_player}'s state:")
            print("State Vector (features an RL agent would observe):")
            for label, value in zip(feature_labels, state_vector):
                print(f"  {label}: {value}")
            print(f"Current Pot: {env.pot}")
            print(f"Current Bet: {env.current_bet}")
            print(f"{current_player} Contribution: {env.contributions[current_player]}")
            print(f"{current_player} Stack: {env.players[current_player]['stack']}")
            print("Betting History:", env.betting_history)
            
            # Display legal actions for the active player.
            legal_actions = env.get_current_legal_actions()
            print("\nAvailable actions:")
            for idx, act in enumerate(legal_actions):
                if act.action_type == ActionType.RAISE:
                    print(f"  {idx}: {act.action_type.value} (raise amount: {act.raise_amount})")
                else:
                    print(f"  {idx}: {act.action_type.value}")
            
            # Prompt the user for an action choice.
            choice = input("Enter the number of your chosen action: ")
            try:
                choice = int(choice)
                chosen_action = legal_actions[choice]
            except Exception as e:
                print("Invalid input. Please try again.")
                continue
            
            # Process the chosen action.
            rewards, info, done = env.step(chosen_action)
            print("\nAction processed. Updated state info:")
            print("Betting History:", env.betting_history)
            print("Current Contributions:", env.contributions)
            print("Player Stacks:", {p: env.players[p]["stack"] for p in env.players})
            print("Current Bet:", env.current_bet)
        
        # Hand is over; display final rewards.
        print("\n========= Hand Finished =========")
        print("Final Rewards:")
        print("  BTN Reward:", rewards[0])
        print("  BB Reward:", rewards[1])
        
        play_again = input("\nPlay another hand? (y/n): ")
        if play_again.lower() != 'y':
            print("Exiting game. Goodbye!")
            break