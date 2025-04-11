#environment.py

from mdp_components import HoleCards, AgentState, PokerAction, ActionType, get_available_actions
from utils import shuffle_deck, deal, calculate_equity, classify_hand, calculate_reward_no_fold, calculate_reward_fold

class PreflopHeadsUpEnv:
    """
    Environment to simulate a heads-up pre-flop Texas Hold'em hand,
    with two players: BTN and BB. On each new hand, each player's stack is set to 100 minus
    their posted blind (BTN posts 0.5, BB posts 1). The contributions dict is initialized 
    with BTN contributing 0.5 and BB contributing 1. The action order alternates starting with BTN.
    """

    def __init__(self, default_stack=100, btn_post=0.5, bb_post=1):
        """
        Initialize the environment with default settings.

        Args:
            default_stack (float): The starting stack before posting blinds.
            btn_post (float): The blind amount posted by BTN.
            bb_post (float): The blind amount posted by BB.
        """
        self.default_stack = default_stack
        self.btn_post = btn_post   # BTN posts 0.5
        self.bb_post = bb_post     # BB posts 1
        self.players = {}          # Holds players' info (stack and position)
        self.deck = []             # The deck of cards
        self.hands = None          # Tuple of dealt hands: (BTN_hand, BB_hand)
        self.contributions = {}    # Dictionary of chip contributions per hand
        self.pot = 0               # Redundant variable for backward compatibility; always sync with contributions
        self.betting_history = []  # Public record of actions taken during the hand
        self.current_bet = 0       # Current highest bet required to call (the outstanding contribution)
        self.current_turn = None   # Whose turn is it? ("BTN" or "BB")
        self.last_raise_size = None  # Track the size of the last raise
        self.is_preflop = True     # Flag to track if we're in the preflop betting round

    def reset(self):
        """
        Resets the environment for a new hand:
          - Reinitializes player stacks (deducting the blinds)
          - Posts blinds and sets the initial contributions dictionary
          - Shuffles the deck and deals new hands
          - Sets the current turn to BTN

        Returns:
            tuple: (players, hands)
                players: A dictionary with entries for "BTN" and "BB".
                hands: A tuple (BTN_hand, BB_hand), each a 4-character string.
        """
        # Initialize players with their stacks after posting blinds.
        self.players = {
            "BTN": {"stack": self.default_stack - self.btn_post, "position": "BTN"},
            "BB":  {"stack": self.default_stack - self.bb_post, "position": "BB"}
        }
        # Post blinds via the contributions dictionary.
        self.contributions = {"BTN": self.btn_post, "BB": self.bb_post}
        # The pot is computed as the sum of contributions.
        self.pot = self.contributions["BTN"] + self.contributions["BB"]
        # The highest bet to call is the BB's posted blind.
        self.current_bet = self.bb_post
        # Clear the betting history.
        self.betting_history = []
        # The action starts with BTN.
        self.current_turn = "BTN"
        # Reset the last raise size
        self.last_raise_size = None
        # Set preflop flag
        self.is_preflop = True

        # Shuffle the deck and deal the hands.
        self.deck = shuffle_deck()
        self.hands = deal(self.deck)
        return self.players, self.hands

    def step(self, action: PokerAction):
        """
        Processes an action by the player whose turn it is and updates the state accordingly.
        
        Depending on the action:
          - Fold: Terminates the hand, awarding rewards based on contributions.
          - Call/Check: May complete the hand or pass action to the opponent depending on context.
          - Raise: Updates the player's stack, contributions, betting history, and passes the turn.

        Args:
            action (PokerAction): The action chosen by the current player.
            
        Returns:
            tuple: (rewards, info, done)
                rewards: A tuple (reward_BTN, reward_BB). Returns (0, 0) if the hand is not terminal.
                info: A dictionary containing the updated state information.
                done (bool): Whether the hand is over.
        """
        current_player = self.current_turn
        opponent = "BB" if current_player == "BTN" else "BTN"

        # --- Handle Fold ---
        if action.action_type == ActionType.FOLD:
            # Record the fold in the betting history
            self.betting_history.append({
                "player": current_player,
                "action": "fold"
            })
            
            # In the fold case, the folding player's reward is negative their committed chips,
            # and the opponent's reward is positive that same amount.
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
                
                # Record the call in the betting history
                self.betting_history.append({
                    "player": current_player,
                    "action": "call",
                    "amount": self.current_bet
                })
            else:
                # Record the check in the betting history
                self.betting_history.append({
                    "player": current_player,
                    "action": "check"
                })
                
            # Update the player's stack and contributions.
            self.players[current_player]["stack"] -= additional
            self.contributions[current_player] += additional
            # Sync pot with contributions.
            self.pot = self.contributions["BTN"] + self.contributions["BB"]

            # FIXED LOGIC: The hand only terminates in specific cases
            # Case 1: BB checks after BTN calls (both players have had a chance to act)
            # Case 2: Either player calls after a raise (both players have had at least one chance to act)
            hand_terminates = False
            
            # In preflop, if BB checks (after BTN called), the hand ends
            if self.is_preflop and action.action_type == ActionType.CHECK and current_player == "BB":
                hand_terminates = True
            
            # If there has been a raise and a player calls that raise, the hand ends
            if len(self.betting_history) >= 2:
                # Check if there has been a raise and this action is a call
                previous_raises = any(action['action'] == 'raise' for action in self.betting_history[:-1])
                current_is_call = action.action_type == ActionType.CALL
                if previous_raises and current_is_call:
                    hand_terminates = True

            if hand_terminates:
                # The hand terminates, calculate rewards
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
                # The hand continues, pass turn to the opponent
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

        # --- Handle Raise ---
        elif action.action_type == ActionType.RAISE:
            # The raise amount must be greater than the current bet.
            raise_amount = action.raise_amount  # New total bet for the current player.
            if raise_amount <= self.current_bet:
                raise ValueError("Raise amount must exceed the current bet.")

            # Compute the additional chips required.
            additional = raise_amount - self.contributions[current_player]
            # If the player doesn't have enough chips, adjust to all-in.
            if additional > self.players[current_player]["stack"]:
                additional = self.players[current_player]["stack"]
                raise_amount = self.contributions[current_player] + additional

            # Calculate the size of this raise (how much more than the current bet)
            self.last_raise_size = raise_amount - self.current_bet

            # Update stack and contributions for the current player.
            self.players[current_player]["stack"] -= additional
            self.contributions[current_player] += additional
            # Sync pot with contributions.
            self.pot = self.contributions["BTN"] + self.contributions["BB"]
            # Update current bet to the new raised amount.
            self.current_bet = raise_amount

            # Record the raise in the betting history.
            self.betting_history.append({
                "player": current_player,
                "action": "raise",
                "amount": raise_amount
            })

            # Pass the turn to the opponent.
            self.current_turn = opponent

            info = {
                "terminal_reason": None,
                "action_by": current_player,
                "betting_history": self.betting_history,
                "players": self.players,
                "contributions": self.contributions,
                "current_bet": self.current_bet
            }
            done = False  # The hand is not yet over.
            return (0, 0), info, done

        else:
            raise ValueError("Invalid action type.")

# --------------------------------------------------
# Interactive Play Mode (User can choose to play as BTN or BB)
# --------------------------------------------------
if __name__ == "__main__":
    import sys
    from mdp_components import get_available_actions, HoleCards
    from utils import classify_hand

    # Create the environment with a starting stack of 100, BTN posting 0.5, and BB posting 1.
    env = PreflopHeadsUpEnv(default_stack=100, btn_post=0.5, bb_post=1)
    
    def print_player_state(players, hands, betting_history, player_position):
        """Prints the player's state (only information visible to the player)"""
        # Get player's hand index (0 for BTN, 1 for BB)
        player_hand_idx = 0 if player_position == "BTN" else 1
        player_hand = hands[player_hand_idx]
        
        # Classify the hand to get more information
        classified, suited, pair, connected, equity = classify_hand(player_hand)
        
        # Create a HoleCards object for display
        hole_cards = HoleCards(
            classified=classified,
            suited=suited,
            pair=pair,
            connected=connected,
            estimated_equity=equity
        )
        
        # Create an AgentState object for display
        agent_state = AgentState(
            my_hole_cards=hole_cards,
            stack_sizes={
                "BTN": players["BTN"]["stack"],
                "BB": players["BB"]["stack"]
            },
            pot_size=env.pot,
            betting_history=betting_history.copy()
        )
        
        print("\n" + "="*60)
        print(f"YOUR STATE ({player_position}):")
        print(f"  Hand: {player_hand} (Classified as {classified})")
        print(f"  Estimated Equity: {equity:.2f}")
        print(f"  Your Stack: {players[player_position]['stack']}")
        print(f"  Opponent Stack: {players['BB' if player_position == 'BTN' else 'BTN']['stack']}")
        print(f"  Pot Size: {env.pot}")
        print(f"  Your Contribution: {env.contributions[player_position]}")
        print(f"  Opponent Contribution: {env.contributions['BB' if player_position == 'BTN' else 'BTN']}")
        
        if betting_history:
            print("  Betting History:")
            for action in betting_history:
                action_desc = f"    {action['player']} {action['action']}"
                if 'amount' in action:
                    action_desc += f" to {action['amount']}"
                print(action_desc)
        print("="*60)
    
    def get_player_action(available_actions):
        """Prompts the user to select an action"""
        print("\nYour available actions:")
        for i, action in enumerate(available_actions):
            if action.action_type == ActionType.RAISE:
                print(f"  {i+1}. RAISE to {action.raise_amount}")
            else:
                print(f"  {i+1}. {action.action_type.value.upper()}")
        
        while True:
            try:
                choice_input = input("\nEnter the number of your action (or 'quit' to exit): ")
                if choice_input.lower() == 'quit':
                    print("\nThanks for playing!")
                    sys.exit(0)
                    
                choice = int(choice_input)
                if 1 <= choice <= len(available_actions):
                    return available_actions[choice-1]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                if choice_input.lower() == 'quit':
                    print("\nThanks for playing!")
                    sys.exit(0)
                print("Please enter a number.")
    
    def get_ai_action(available_actions, ai_hand):
        """Simple AI strategy for the opponent"""
        # For now, just use a simple strategy: 
        # - If AI has a good hand (equity > 0.6), raise if possible
        # - If AI has a medium hand (equity > 0.5), call
        # - Otherwise, check if possible or fold
        
        _, _, _, _, equity = classify_hand(ai_hand)
        
        if equity > 0.6:
            # Look for a raise action
            raise_actions = [a for a in available_actions 
                             if a.action_type == ActionType.RAISE]
            if raise_actions:
                # Choose a moderate raise
                raise_actions.sort(key=lambda a: a.raise_amount)
                return raise_actions[min(1, len(raise_actions)-1)]  # Second smallest raise or smallest if only one
        
        if equity > 0.5:
            # Look for call
            for action in available_actions:
                if action.action_type == ActionType.CALL:
                    return action
            # If can't call, check if possible
            for action in available_actions:
                if action.action_type == ActionType.CHECK:
                    return action
        
        # Check if possible
        for action in available_actions:
            if action.action_type == ActionType.CHECK:
                return action
        
        # Call if necessary
        for action in available_actions:
            if action.action_type == ActionType.CALL:
                return action
        
        # Fold as last resort
        return next(a for a in available_actions if a.action_type == ActionType.FOLD)
    
    def print_hand_result(rewards, info, hands, player_position):
        """Prints the result of the hand with both estimated and calculated equity values"""
        btn_hand = hands[0]
        bb_hand = hands[1]
        
        print("\n" + "="*60)
        print("HAND COMPLETE")
        print(f"Terminal Reason: {info['terminal_reason']}")
        print(f"Final Pot: {info['contributions']['BTN'] + info['contributions']['BB']}")
        
        # Get the table-based equity estimates
        btn_classified, _, _, _, btn_equity_estimate = classify_hand(btn_hand)
        bb_classified, _, _, _, bb_equity_estimate = classify_hand(bb_hand)
        
        # Calculate the actual equity using the equity calculator
        try:
            btn_equity_actual, bb_equity_actual = calculate_equity(btn_hand, bb_hand)
            equity_calc_success = True
        except Exception as e:
            print(f"Note: Could not calculate precise equity: {e}")
            btn_equity_actual = btn_equity_estimate
            bb_equity_actual = bb_equity_estimate
            equity_calc_success = False
        
        print("\nHANDS REVEALED:")
        print(f"  BTN: {btn_hand} (Classified as {btn_classified})")
        print(f"  BB: {bb_hand} (Classified as {bb_classified})")
        
        print("\nEQUITY COMPARISON:")
        print(f"  BTN: Estimated: {btn_equity_estimate:.3f}  |  " + 
              (f"Calculated: {btn_equity_actual:.3f}" if equity_calc_success else "Calculation failed"))
        print(f"  BB:  Estimated: {bb_equity_estimate:.3f}  |  " + 
              (f"Calculated: {bb_equity_actual:.3f}" if equity_calc_success else "Calculation failed"))
        
        # Display rewards
        print("\nREWARDS:")
        print(f"  BTN: {rewards[0]:.2f}" + (" (YOU)" if player_position == "BTN" else ""))
        print(f"  BB: {rewards[1]:.2f}" + (" (YOU)" if player_position == "BB" else ""))
        print("="*60)
        
        input("\nPress Enter to play next hand...")
    
    def get_btn_actions_after_bb_call(env, players):
        """Get available actions for BTN after BB calls a raise"""
        available_actions = []
        
        # First, add FOLD
        available_actions.append(PokerAction(ActionType.FOLD))
        
        # Then add CALL
        available_actions.append(PokerAction(ActionType.CALL))
        
        # Then add RAISE options if the player has enough chips
        player_stack = players["BTN"]["stack"]
        current_bet = env.current_bet
        player_contribution = env.contributions["BTN"]
        
        # Calculate how much the player would need to add to meet the current bet
        to_call = max(0, current_bet - player_contribution)
        
        # Available stack after calling
        remaining = player_stack - to_call
        
        # Determine minimum raise amount
        min_raise_total = current_bet + env.last_raise_size
        
        # Calculate how much additional the player needs to contribute for min raise
        min_raise_additional = min_raise_total - player_contribution
        
        # Add raise actions if the player has enough chips
        if remaining > min_raise_additional:
            # Standard raise options (representing the BTN's total contribution)
            standard_options = [2, 2.5, 3, 4, 5, 6, 8, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            
            for option in standard_options:
                # Skip options below the minimum raise or that exceed stack
                if option >= min_raise_total and option - player_contribution <= remaining:
                    available_actions.append(PokerAction(ActionType.RAISE, raise_amount=option))
            
            # Add all-in option if different from standard options
            all_in_amount = player_contribution + remaining
            if all_in_amount not in [a.raise_amount for a in available_actions if a.action_type == ActionType.RAISE]:
                available_actions.append(PokerAction(ActionType.RAISE, raise_amount=all_in_amount))
        
        return available_actions
    
    def get_bb_actions_after_btn_call(env, players):
        """Get available actions for BB after BTN calls"""
        available_actions = [PokerAction(ActionType.CHECK)]
        
        # Add raise options
        player_stack = players["BB"]["stack"]
        
        # Minimum raise is to 2BB total
        min_raise_total = 2.0
        
        # Calculate how much additional the player needs to contribute for min raise
        min_raise_additional = min_raise_total - env.contributions["BB"]
        
        # Available stack for raising
        remaining = player_stack
        
        # Add raise actions if BB has enough chips
        if remaining >= min_raise_additional:
            # Standard raise options (representing the BB's total contribution)
            standard_options = [2, 2.5, 3, 4, 5, 6, 8, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            
            for option in standard_options:
                # Skip options that exceed the player's stack
                if option - 1 <= remaining:  # BB already contributed 1
                    available_actions.append(PokerAction(ActionType.RAISE, raise_amount=option))
            
            # Add all-in option if different from standard options
            all_in_amount = env.contributions["BB"] + remaining
            if all_in_amount not in [a.raise_amount for a in available_actions if a.action_type == ActionType.RAISE]:
                available_actions.append(PokerAction(ActionType.RAISE, raise_amount=all_in_amount))
        
        return available_actions
    
    # Ask the user which position they want to play
    print("\nWelcome to Heads-Up Pre-Flop Poker!")
    print("You can play as either the Button (BTN) or the Big Blind (BB).")
    
    player_position = None
    while player_position not in ["BTN", "BB"]:
        choice = input("Enter your position (BTN/BB): ").strip().upper()
        if choice in ["BTN", "BB"]:
            player_position = choice
        else:
            print("Invalid choice. Please enter 'BTN' or 'BB'.")
    
    ai_position = "BB" if player_position == "BTN" else "BTN"
    print(f"\nYou are playing as {player_position} against an AI opponent ({ai_position}).")
    print("Type 'quit' at any action prompt to exit the game.")
    
    try:
        while True:
            # Reset the environment (new hand)
            players, hands = env.reset()
            
            # Main game loop
            done = False
            
            while not done:
                if env.current_turn == player_position:
                    # Print player's state
                    print_player_state(players, hands, env.betting_history, player_position)
                    
                    # Determine available actions based on context
                    is_first_action = len(env.betting_history) == 0
                    
                    # Handle special case for BB when BTN has just called
                    if player_position == "BB" and (len(env.betting_history) == 1 and 
                        env.betting_history[0]['player'] == "BTN" and 
                        env.betting_history[0]['action'] == "call"):
                        available_actions = get_bb_actions_after_btn_call(env, players)
                    # Handle special case for BTN when BB has just called a raise
                    elif player_position == "BTN" and env.betting_history and env.betting_history[-1]['player'] == "BB" and env.betting_history[-1]['action'] == "call":
                        available_actions = get_btn_actions_after_bb_call(env, players)
                    else:
                        # Normal action determination
                        available_actions = get_available_actions(
                            current_bet=env.current_bet, 
                            player_stack=players[player_position]["stack"],
                            is_dealer=(player_position == "BTN"),
                            last_raise_size=env.last_raise_size,
                            is_first_action=is_first_action
                        )
                    
                    # Get player's action
                    action = get_player_action(available_actions)
                    
                    # Take the action
                    rewards, info, done = env.step(action)
                    
                    if done:
                        print_hand_result(rewards, info, hands, player_position)
                
                else:  # AI's turn
                    print(f"\n{ai_position} is thinking...")
                    
                    # Determine available actions based on context
                    is_first_action = len(env.betting_history) == 0
                    
                    # Handle special case for BB (AI) when BTN has just called
                    if ai_position == "BB" and (len(env.betting_history) == 1 and 
                        env.betting_history[0]['player'] == "BTN" and 
                        env.betting_history[0]['action'] == "call"):
                        available_actions = get_bb_actions_after_btn_call(env, players)
                    # Handle special case for BTN (AI) when BB has just called a raise
                    elif ai_position == "BTN" and env.betting_history and env.betting_history[-1]['player'] == "BB" and env.betting_history[-1]['action'] == "call":
                        available_actions = get_btn_actions_after_bb_call(env, players)
                    else:
                        # Normal action determination
                        available_actions = get_available_actions(
                            current_bet=env.current_bet, 
                            player_stack=players[ai_position]["stack"],
                            is_dealer=(ai_position == "BTN"),
                            last_raise_size=env.last_raise_size,
                            is_first_action=is_first_action
                        )
                    
                    # Get AI's action
                    ai_hand_idx = 0 if ai_position == "BTN" else 1
                    action = get_ai_action(available_actions, hands[ai_hand_idx])
                    
                    # Print AI's action
                    action_str = action.action_type.value.upper()
                    if action.action_type == ActionType.RAISE:
                        action_str += f" to {action.raise_amount}"
                    print(f"{ai_position} decides to {action_str}")
                    
                    # Take the action
                    rewards, info, done = env.step(action)
                    
                    if done:
                        print_hand_result(rewards, info, hands, player_position)
    
    except KeyboardInterrupt:
        print("\nThanks for playing!")
    except Exception as e:
        print(f"An error occurred: {e}")