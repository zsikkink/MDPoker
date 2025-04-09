"""
Client for the Node.js Equity Calculator service.
Communicates with the Express server to get accurate equity calculations.
"""

import requests
import json
import time
from typing import Tuple, List, Dict, Any, Optional


class EquityClient:
    """
    Client for the Express Equity Calculator service.
    Sends requests to calculate equity between poker hands.
    """
    
    def __init__(self, base_url="http://localhost:3000"):
        """
        Initialize the equity calculator client.
        
        Args:
            base_url (str): The base URL of the equity calculator service.
        """
        self.base_url = base_url
        self.health_endpoint = f"{base_url}/health"
        self.calculate_endpoint = f"{base_url}/calculate-equity"
        
        # Check if the service is running
        self._check_service()
    
    def _check_service(self):
        """Check if the equity calculator service is running."""
        try:
            response = requests.get(self.health_endpoint, timeout=2)
            if response.status_code != 200:
                print(f"Warning: Equity service returned status code: {response.status_code}")
                print("Will use fallback equity estimation")
                return False
            return True
        except requests.RequestException as e:
            print(f"Warning: Error connecting to equity calculator service: {e}")
            print("Make sure the Node.js service is running (node server.mjs)")
            print("Will use fallback equity estimation")
            return False
    
    def calculate_equity(self, 
                         player1_hand: List[Tuple[str, str]], 
                         player2_hand: List[Tuple[str, str]],
                         board: Optional[List[Tuple[str, str]]] = None) -> Tuple[float, float]:
        """
        Calculate equity between two poker hands.
        
        Args:
            player1_hand: The first player's hand as a list of (rank, suit) tuples
            player2_hand: The second player's hand as a list of (rank, suit) tuples
            board: Optional community cards as a list of (rank, suit) tuples
            
        Returns:
            Tuple of (player1_equity, player2_equity) as floats between 0 and 1
        """
        # Convert hands to string format expected by the API
        p1_hand_str = self._convert_hand_to_string(player1_hand)
        p2_hand_str = self._convert_hand_to_string(player2_hand)
        board_str = "" if board is None else self._convert_hand_to_string(board)
        
        payload = {
            "player1Hand": p1_hand_str,
            "player2Hand": p2_hand_str
        }
        
        if board_str:
            payload["board"] = board_str
        
        try:
            response = requests.post(
                self.calculate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Warning: Equity service returned status code {response.status_code}")
                return self._fallback_equity(player1_hand, player2_hand)
            
            result = response.json()
            return (result['player1Equity'], result['player2Equity'])
            
        except requests.RequestException as e:
            print(f"Warning: Error communicating with equity calculator service: {e}")
            return self._fallback_equity(player1_hand, player2_hand)
    
    def _convert_hand_to_string(self, cards: List[Tuple[str, str]]) -> str:
        """
        Convert a list of (rank, suit) tuples to a string format expected by the API.
        
        Args:
            cards: List of (rank, suit) tuples
            
        Returns:
            String in format like "AcKh" for ace of clubs and king of hearts
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
        
        result = ""
        for card in cards:
            rank, suit = card
            js_rank = rank_mapping.get(rank, rank)  # Use original if not in mapping
            js_suit = suit_mapping.get(suit, suit.lower()[0])  # Use first char if not in mapping
            result += js_rank + js_suit
        
        return result
    
    def _fallback_equity(self, 
                         player1_hand: List[Tuple[str, str]], 
                         player2_hand: List[Tuple[str, str]]) -> Tuple[float, float]:
        """
        Fallback method for equity calculation when the service is not available.
        This provides a very simplified estimate based on card ranks.
        
        Args:
            player1_hand: The first player's hand
            player2_hand: The second player's hand
            
        Returns:
            Tuple of (player1_equity, player2_equity)
        """
        print("Using fallback equity estimation - less accurate")
        # Simple rank-based estimation (not accurate)
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, 
                      '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        
        # Calculate simple hand strength based on ranks
        p1_strength = sum(rank_values.get(card[0], 0) for card in player1_hand)
        p2_strength = sum(rank_values.get(card[0], 0) for card in player2_hand)
        
        total_strength = p1_strength + p2_strength
        
        # Add some randomness to avoid deterministic results
        import random
        p1_equity = (p1_strength / total_strength) * 0.8 + 0.1 + random.uniform(-0.05, 0.05)
        p2_equity = 1 - p1_equity
        
        # Ensure equity is between 0 and 1
        p1_equity = max(0.01, min(0.99, p1_equity))
        p2_equity = max(0.01, min(0.99, p2_equity))
        
        return p1_equity, p2_equity


# Example usage
if __name__ == "__main__":
    client = EquityClient()
    
    # Example hand calculation
    player1_hand = [('A', 'Hearts'), ('K', 'Hearts')]
    player2_hand = [('Q', 'Spades'), ('J', 'Diamonds')]
    
    equity = client.calculate_equity(player1_hand, player2_hand)
    print(f"Player 1 equity: {equity[0]:.2%}")
    print(f"Player 2 equity: {equity[1]:.2%}")
    
    # Example with board
    board = [('T', 'Hearts'), ('9', 'Diamonds'), ('2', 'Clubs')]
    equity_with_board = client.calculate_equity(player1_hand, player2_hand, board)
    print(f"\nWith board {board}:")
    print(f"Player 1 equity: {equity_with_board[0]:.2%}")
    print(f"Player 2 equity: {equity_with_board[1]:.2%}")
