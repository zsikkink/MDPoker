#!/usr/bin/env python
# MDPoker Integration Example

from equity_client import EquityCalculator
import sys
import os

# Add the MDPoker source directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MDPoker components
from simulation.poker_engine import PokerEngine
from src.bot import GTOBot
from src.table import Table

class HybridEquityEstimator:
    """
    A hybrid equity estimator that uses the JavaScript equity calculator
    for accurate equity calculations while integrating with the Python MDPoker project.
    """
    
    def __init__(self):
        """Initialize the hybrid equity estimator with the JavaScript service client."""
        self.js_calculator = EquityCalculator()
        print("Hybrid equity estimator initialized with JavaScript service")
    
    def calculate_preflop_equity(self, hole_cards1, hole_cards2):
        """
        Calculate preflop equity between two hands.
        
        Args:
            hole_cards1 (list): First player's hole cards in MDPoker format
            hole_cards2 (list): Second player's hole cards in MDPoker format
            
        Returns:
            tuple: (player1_equity, player2_equity)
        """
        # Convert MDPoker card format to the format expected by the JS calculator
        js_hand1 = self._convert_cards_to_js_format(hole_cards1)
        js_hand2 = self._convert_cards_to_js_format(hole_cards2)
        
        # Calculate equity using the JavaScript service
        result = self.js_calculator.calculate_equity(js_hand1, js_hand2)
        
        if result:
            return (result['player1Equity'], result['player2Equity'])
        else:
            # Fallback to a simplified estimation if the service fails
            print("Warning: JavaScript equity calculation failed, using simplified estimate")
            return (0.5, 0.5)  # Equal equity as a fallback
    
    def calculate_postflop_equity(self, hole_cards1, hole_cards2, community_cards):
        """
        Calculate equity between two hands with community cards.
        
        Args:
            hole_cards1 (list): First player's hole cards in MDPoker format
            hole_cards2 (list): Second player's hole cards in MDPoker format
            community_cards (list): Community cards in MDPoker format
            
        Returns:
            tuple: (player1_equity, player2_equity)
        """
        # Convert card formats
        js_hand1 = self._convert_cards_to_js_format(hole_cards1)
        js_hand2 = self._convert_cards_to_js_format(hole_cards2)
        js_board = self._convert_cards_to_js_format(community_cards)
        
        # Calculate equity using the JavaScript service
        result = self.js_calculator.calculate_equity(js_hand1, js_hand2, js_board)
        
        if result:
            return (result['player1Equity'], result['player2Equity'])
        else:
            # Fallback to a simplified estimation if the service fails
            print("Warning: JavaScript equity calculation failed, using simplified estimate")
            return (0.5, 0.5)  # Equal equity as a fallback
    
    def _convert_cards_to_js_format(self, cards):
        """
        Convert cards from MDPoker format to the format expected by the JS calculator.
        
        Args:
            cards (list): Cards in MDPoker format [(rank, suit), ...]
            
        Returns:
            str: Cards in JS format (e.g., "AcKh")
        """
        # Convert ranks and suits to the format expected by the JS calculator
        rank_mapping = {
            '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9', '10': 'T',
            'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'
        }
        
        suit_mapping = {
            'Hearts': 'h', 'Diamonds': 'd', 'Clubs': 'c', 'Spades': 's',
            'h': 'h', 'd': 'd', 'c': 'c', 's': 's'  # Handle already shortened formats
        }
        
        js_cards = ""
        for card in cards:
            rank, suit = card
            js_rank = rank_mapping.get(rank, rank)  # Use original if not in mapping
            js_suit = suit_mapping.get(suit, suit.lower()[0])  # Use first char of lowercase if not in mapping
            js_cards += js_rank + js_suit
        
        return js_cards

# Example usage in MDPoker context
def demo_mdpoker_integration():
    """Demo the integration of the JavaScript equity calculator with MDPoker."""
    # Initialize the hybrid equity estimator
    equity_estimator = HybridEquityEstimator()
    
    # Define some example hole cards in MDPoker format
    player1_cards = [('A', 'Hearts'), ('K', 'Hearts')]
    player2_cards = [('Q', 'Spades'), ('J', 'Diamonds')]
    
    # Calculate preflop equity
    preflop_equity = equity_estimator.calculate_preflop_equity(player1_cards, player2_cards)
    print(f"\nPreflop equity calculation:")
    print(f"Player 1 ({player1_cards}): {preflop_equity[0]:.2%}")
    print(f"Player 2 ({player2_cards}): {preflop_equity[1]:.2%}")
    
    # Define some example community cards
    flop_cards = [('T', 'Hearts'), ('9', 'Diamonds'), ('2', 'Clubs')]
    
    # Calculate postflop equity
    postflop_equity = equity_estimator.calculate_postflop_equity(player1_cards, player2_cards, flop_cards)
    print(f"\nPostflop equity calculation with {flop_cards}:")
    print(f"Player 1 ({player1_cards}): {postflop_equity[0]:.2%}")
    print(f"Player 2 ({player2_cards}): {postflop_equity[1]:.2%}")
    
    # Example of how to use this in a reward function context
    pot_size = 10  # Example pot size
    player1_reward = pot_size * (2 * postflop_equity[0] - 1)
    player2_reward = pot_size * (2 * postflop_equity[1] - 1)
    
    print(f"\nReward calculation with pot size {pot_size}:")
    print(f"Player 1 reward: {player1_reward:.2f}")
    print(f"Player 2 reward: {player2_reward:.2f}")
    print(f"Sum of rewards (should be zero in zero-sum game): {player1_reward + player2_reward:.2f}")

if __name__ == "__main__":
    demo_mdpoker_integration()