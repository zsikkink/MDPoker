"""
Implements the core simulation environment for Texas Hold'em Poker, specifically focused on pre-flop play.
It defines the environment class that manages interactions, including state resets, action steps, and 
transitions in the pre-flop MDP. This module combines the general poker engine functionality with
pre-flop specific processing.
"""

import random
from typing import Dict, List, Tuple, Optional, Any, Set
from treys import Card, Deck

from .game_rules import GameState, GameRules, Action, Position, GameStage, calculate_reward
from .equity_client import EquityClient

class PreflopEnv:
    """
    A reinforcement learning environment for pre-flop Texas Hold'em poker.
    This environment manages the poker game state, handles player actions,
    and provides rewards according to the MDP formulation.
    """
    
    def __init__(self, equity_calculator=None, use_express_service=True):
        """
        Initialize the pre-flop poker environment.
        
        Args:
            equity_calculator: Optional function to calculate equity between hands.
                              Should take two hole card tuples and return a tuple of equities.
            use_express_service: Whether to use the Express service for equity calculations.
        """
        # Initialize equity client if using Express service
        self.use_express_service = use_express_service
        if use_express_service:
            self.equity_client = EquityClient()
            
        # Keep the custom equity calculator as fallback
        self.equity_calculator = equity_calculator
        
        self.state = None
        self.deck = None  # Will be initialized as a treys Deck in reset()
        self.community_cards = []
        self.game_rules = GameRules()
        
    def _treys_to_readable(self, card):
        """
        Convert a treys card integer to a readable (rank, suit) tuple format.
        
        Args:
            card: A treys card integer or a list of integers
            
        Returns:
            Tuple of (rank, suit) in the format used by the rest of the code
        """
        # Handle case where card might be a list
        if isinstance(card, list):
            if len(card) > 0:
                card = card[0]  # Take the first card if it's a list
            else:
                # Default to a placeholder card if list is empty
                return ('2', 'Clubs')  # Arbitrary default
                
        # Continue with normal processing for integer cards
        # Get string representation from treys
        card_str = Card.int_to_str(card)
        
        # Extract rank and suit
        rank = card_str[0]
        if rank == 'T':
            rank = '10'  # Convert 'T' to '10' for consistency
            
        suit_map = {'h': 'Hearts', 'd': 'Diamonds', 'c': 'Clubs', 's': 'Spades'}
        suit = suit_map[card_str[1]]
        
        return (rank, suit)
    
    def _readable_to_treys(self, card_tuple):
        """
        Convert a (rank, suit) tuple to a treys card integer.
        
        Args:
            card_tuple: A tuple of (rank, suit)
            
        Returns:
            A treys card integer
        """
        rank, suit = card_tuple
        
        # Convert '10' to 'T' for treys
        if rank == '10':
            rank = 'T'
            
        suit_map = {'Hearts': 'h', 'Diamonds': 'd', 'Clubs': 'c', 'Spades': 's'}
        suit_abbr = suit_map[suit]
        
        # Create the treys string and convert to integer
        return Card.new(rank + suit_abbr)
        
    def _calculate_preflop_reward(self, state, player_id, equity_client=None, equity_calculator=None):
        """
        Calculate the reward for a player based on the reward function:
        
        For any player i, the reward Ri is defined as follows:
        
        * If the hand ends pre-flop (fold or all-in):
            * Let P be the size of the pot at the moment the pre-flop action is ended.
            * If player i wins the hand: Ri = P
            * If player i loses the hand: Ri = –P
            
        * If the hand proceeds to the flop (both players remain):
            * Let ei be the equity of player i (with eA + eB = 1)
            * Then the reward is: Ri = (2*ei – 1) × P
            
        Args:
            state: The game state to calculate reward for
            player_id: ID of the player to calculate reward for
            equity_client: Optional EquityClient instance for using the Express service
            equity_calculator: Optional function to calculate equity between hands
            
        Returns:
            Reward value for the player
        """
        # If game is still in pre-flop or isn't done, no immediate reward
        if not state.is_terminal() and state.stage == GameStage.PREFLOP:
            return 0
        
        # Case 1: Hand ends pre-flop due to fold
        if state.is_terminal() and state.winner is not None and state.stage == GameStage.PREFLOP:
            # Determine if player won or lost
            if state.winner == player_id:
                return state.pot_size  # Player won, positive reward
            else:
                return -state.pot_size  # Player lost, negative reward
        
        # Case 2: Hand proceeds to the flop (both players remain)
        if state.stage == GameStage.FLOP or (state.stage == GameStage.TERMINAL and len(state.active_players) > 1):
            # Get player hands
            player_hand = state.hole_cards[player_id]
            opponent_id = next(pid for pid in state.positions if pid != player_id)
            opponent_hand = state.hole_cards[opponent_id]
            
            # Calculate equity using available methods
            if equity_client is not None:
                try:
                    player_equity, opponent_equity = equity_client.calculate_equity(
                        player_hand, opponent_hand, self.community_cards if self.community_cards else None
                    )
                except Exception as e:
                    print(f"Error using equity client: {e}")
                    # Fallback to provided equity calculator
                    if equity_calculator:
                        player_equity, opponent_equity = equity_calculator(player_hand, opponent_hand)
                    else:
                        # Fallback to simple estimation
                        player_equity = 0.5
                        opponent_equity = 0.5
            elif equity_calculator:
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
    
    def create_deck(self):
        """Create a standard 52-card deck using treys library."""
        return Deck()
    
    def shuffle_deck(self):
        """Shuffle the deck. (Not needed with treys as Deck() is already shuffled)"""
        # Treys Deck is already shuffled on creation
        pass
    
    def deal_cards(self, num_players=2):
        """
        Deal two cards to each player using treys library.
        
        Args:
            num_players: Number of players to deal cards to.
            
        Returns:
            Dictionary mapping player IDs to their hole cards.
        """
        hole_cards = {}
        for i in range(num_players):
            player_id = f"player_{i}"
            # Draw two cards from the treys deck and convert to readable format
            hole_cards[player_id] = [
                self._treys_to_readable(self.deck.draw()),
                self._treys_to_readable(self.deck.draw())
            ]
        return hole_cards
    
    def deal_community_cards(self, number):
        """
        Deal community cards from the deck using treys library.
        
        Args:
            number: Number of community cards to deal.
        """
        for _ in range(number):
            self.community_cards.append(self._treys_to_readable(self.deck.draw()))
    
    def reset(self, player_ids=None, stack_sizes=None, blinds=(0.5, 1.0)):
        """
        Reset the environment to a new game state.
        
        Args:
            player_ids: List of player IDs. If None, defaults to ["player_0", "player_1"].
            stack_sizes: Dictionary mapping player IDs to their starting stack sizes.
                        If None, defaults to 100 big blinds for each player.
            blinds: Tuple of (small blind, big blind) amounts.
            
        Returns:
            New GameState object.
        """
        # Default player IDs if none provided
        if player_ids is None:
            player_ids = ["player_0", "player_1"]
        
        # Default stack sizes if none provided
        if stack_sizes is None:
            stack_sizes = {pid: 100 * blinds[1] for pid in player_ids}
        
        # Create and shuffle the deck using treys library
        self.deck = self.create_deck()  # Treys Deck is already shuffled
        
        # Deal hole cards
        hole_cards = self.deal_cards(len(player_ids))
        
        # Initialize community cards
        self.community_cards = []
        
        # Create a new game state
        self.state = GameState(
            player_ids=player_ids,
            hole_cards=hole_cards,
            stack_sizes=stack_sizes,
            blinds=blinds
        )
        
        return self.state
    
    def step(self, action, raise_amount=None):
        """
        Take a step in the environment by applying an action.
        
        Args:
            action: The Action enum value representing the action to take.
            raise_amount: Amount to raise to (only used for RAISE action).
            
        Returns:
            Tuple of (next_state, reward, done, info):
                next_state: The new GameState after the action.
                reward: The reward for the current player.
                done: Boolean indicating if the episode is finished.
                info: Additional information dictionary.
        """
        if self.state is None:
            raise ValueError("Environment must be reset before calling step")
        
        # Get current player
        current_player = self.state.current_player
        
        # Apply the action to get the new state
        next_state = self.game_rules.apply_action(
            self.state, current_player, action, raise_amount
        )
        
        # Calculate reward for the current player based on the pre-flop reward function
        if self.use_express_service:
            reward = self._calculate_preflop_reward(next_state, current_player, self.equity_client)
        else:
            reward = self._calculate_preflop_reward(next_state, current_player, equity_calculator=self.equity_calculator)
        
        # Check if the game is done
        done = next_state.is_terminal() or next_state.stage != GameStage.PREFLOP
        
        # Additional info
        info = {
            "pot_size": next_state.pot_size,
            "stage": next_state.stage,
            "active_players": next_state.active_players,
        }
        
        # If transitioning to flop, deal community cards
        if next_state.stage == GameStage.FLOP and not self.community_cards:
            self.deal_community_cards(3)  # Deal the flop
            info["community_cards"] = self.community_cards
            
            # Set terminal state if we moved to flop since this is pre-flop only
            next_state.stage = GameStage.TERMINAL
            done = True
            
            # Include equity in info for transparency
            if self.use_express_service:
                try:
                    player_hand = next_state.hole_cards[current_player]
                    opponent_id = next(pid for pid in next_state.positions if pid != current_player)
                    opponent_hand = next_state.hole_cards[opponent_id]
                    player_equity, _ = self.equity_client.calculate_equity(player_hand, opponent_hand)
                    info["equity"] = player_equity
                except Exception as e:
                    print(f"Error calculating equity: {e}")
            elif self.equity_calculator:
                player_hand = next_state.hole_cards[current_player]
                opponent_id = next(pid for pid in next_state.positions if pid != current_player)
                opponent_hand = next_state.hole_cards[opponent_id]
                player_equity, _ = self.equity_calculator(player_hand, opponent_hand)
                info["equity"] = player_equity
        
        # Update current state
        self.state = next_state
        
        return next_state, reward, done, info
    
    def evaluate_winner(self, state=None):
        """
        Evaluate the winner of the current hand.
        
        Args:
            state: Optional GameState to evaluate. If None, uses self.state.
            
        Returns:
            ID of the winning player, or None if game isn't terminal.
        """
        if state is None:
            state = self.state
        
        if not state.is_terminal():
            return None
        
        # If someone folded, winner is already determined
        if state.winner is not None:
            return state.winner
        
        # If we reached showdown, evaluate hands using equity calculator
        if self.equity_calculator and len(state.active_players) > 1:
            player_ids = list(state.active_players)
            player1_hand = state.hole_cards[player_ids[0]]
            player2_hand = state.hole_cards[player_ids[1]]
            
            player1_equity, player2_equity = self.equity_calculator(
                player1_hand, player2_hand, self.community_cards
            )
            
            # Simulate the outcome based on equities
            # This is a simplification; in a real game you'd deal all community cards
            # and evaluate the actual winner
            rand_val = random.random()
            if rand_val < player1_equity:
                return player_ids[0]
            else:
                return player_ids[1]
        
        # Default fallback - equal chance for each player
        # This should rarely happen as we should have an equity calculator
        return random.choice(list(state.active_players))
    
    def get_legal_actions(self, player_id=None):
        """
        Get the legal actions for a player.
        
        Args:
            player_id: ID of the player. If None, uses current player.
            
        Returns:
            List of legal Action objects.
        """
        if self.state is None:
            raise ValueError("Environment must be reset before calling get_legal_actions")
        
        if player_id is None:
            player_id = self.state.current_player
        
        if player_id != self.state.current_player:
            return []  # No legal actions when it's not your turn
        
        return self.state.get_legal_actions()
    
    def play_round(self):
        """
        Automatically play a full round of poker with random actions.
        Useful for testing and simulation.
        
        Returns:
            Tuple of (final game state, winner ID, rewards).
        """
        if self.state is None:
            self.reset()
        
        done = False
        rewards = {}
        player_ids = list(self.state.positions.keys())
        
        while not done:
            current_player = self.state.current_player
            legal_actions = self.get_legal_actions()
            
            # Choose a random action
            action = random.choice(legal_actions)
            
            # If action is RAISE, choose a random raise amount
            raise_amount = None
            if action == Action.RAISE:
                min_raise = self.state.current_bet * 2
                max_raise = self.state.stack_sizes[current_player] + self.state.player_bets[current_player]
                raise_amount = random.uniform(min_raise, max_raise)
            
            # Apply action
            next_state, reward, done, info = self.step(action, raise_amount)
            
            # Record reward
            if done:
                # Calculate reward for both players when episode ends
                for pid in player_ids:
                    if self.use_express_service:
                        rewards[pid] = self._calculate_preflop_reward(next_state, pid, self.equity_client)
                    else:
                        rewards[pid] = self._calculate_preflop_reward(next_state, pid, equity_calculator=self.equity_calculator)
        
        # Determine winner if not already determined
        winner = self.evaluate_winner()
        
        # Print rewards for testing
        print(f"Final pot size: {self.state.pot_size}")
        for pid in player_ids:
            print(f"Player {pid} reward: {rewards[pid]:.2f}")
        
        return self.state, winner, rewards
    
    def render(self):
        """
        Render the current game state for human viewing.
        
        Returns:
            String representation of the game state.
        """
        if self.state is None:
            return "Environment not initialized"
        
        output = [
            "======== Texas Hold'em Poker - Pre-flop Environment ========",
            f"Stage: {self.state.stage.name}",
            f"Pot Size: {self.state.pot_size}",
            "\nPlayers:"
        ]
        
        for player_id, position in self.state.positions.items():
            cards_str = " ".join([f"{card[0]}{card[1][0]}" for card in self.state.hole_cards[player_id]])
            active = "Active" if player_id in self.state.active_players else "Folded"
            current = "<<< Current Player" if player_id == self.state.current_player else ""
            
            output.append(f"  {player_id} ({position.name}): {cards_str}, Stack: {self.state.stack_sizes[player_id]}, " +
                         f"Bet: {self.state.player_bets[player_id]}, {active} {current}")
        
        if self.community_cards:
            cards_str = " ".join([f"{card[0]}{card[1][0]}" for card in self.community_cards])
            output.append(f"\nCommunity Cards: {cards_str}")
        
        if self.state.betting_history:
            output.append("\nBetting History:")
            for action in self.state.betting_history:
                if len(action) == 2:
                    output.append(f"  {action[0]}: {action[1].name}")
                else:  # Raise or All-in with amount
                    output.append(f"  {action[0]}: {action[1].name} to {action[2]}")
        
        if self.state.is_terminal():
            output.append(f"\nGame Over - Winner: {self.state.winner}")
        
        return "\n".join(output)


# Example usage
if __name__ == "__main__":
    print("Testing PreflopEnv with Express equity calculator service")
    print("With reward function: R_i = P if player wins, R_i = -P if player loses, R_i = (2*e_i - 1)*P if proceeding to flop")
    print("-"*80)
    
    # Create and test the environment with Express service
    env = PreflopEnv(use_express_service=True)
    state = env.reset()
    print(env.render())
    
    # Play a round with random actions
    final_state, winner, rewards = env.play_round()
    print("\nAfter playing round:")
    print(env.render())
    print("\nReward Summary:")
    print(f"Winner: {winner}")
    for player_id, reward in rewards.items():
        win_status = "Winner" if player_id == winner else "Loser"
        print(f"Player {player_id} ({win_status}): Reward = {reward:.2f}")
    
    print("\n" + "-"*80)
    print("Testing with fallback equity calculator")
    
    # Simple equity calculator for testing (not accurate)
    def simple_equity(hand1, hand2, board=None):
        # Higher card gets slightly better equity
        # This is just for demonstration
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                      '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        
        hand1_value = max(rank_values[hand1[0][0]], rank_values[hand1[1][0]])
        hand2_value = max(rank_values[hand2[0][0]], rank_values[hand2[1][0]])
        
        # Simple simulation - better hand gets 60% equity
        if hand1_value > hand2_value:
            return 0.6, 0.4
        elif hand2_value > hand1_value:
            return 0.4, 0.6
        else:
            return 0.5, 0.5
    
    # Test with fallback calculator
    env2 = PreflopEnv(equity_calculator=simple_equity, use_express_service=False)
    state = env2.reset()
    print(env2.render())
    
    # Play a round with random actions
    final_state, winner, rewards = env2.play_round()
    print("\nAfter playing round:")
    print(env2.render())
    print("\nReward Summary:")
    print(f"Winner: {winner}")
    for player_id, reward in rewards.items():
        win_status = "Winner" if player_id == winner else "Loser"
        print(f"Player {player_id} ({win_status}): Reward = {reward:.2f}")
    
    # Verify rewards sum to zero (zero-sum property)
    total_reward = sum(rewards.values())
    print(f"\nSum of all rewards: {total_reward:.6f} (should be approximately zero for zero-sum game)")
    
    # Show reward calculation examples
    print("\n" + "-"*80)
    print("Reward Function Examples:")
    print("1. Player folds pre-flop with pot size of 10:")
    print("   - Winner reward: +10")
    print("   - Loser reward: -10")
    print("\n2. Both players proceed to flop with pot size of 10:")
    print("   - Player with 70% equity: (2*0.7-1)*10 = +4.0")
    print("   - Player with 30% equity: (2*0.3-1)*10 = -4.0")
