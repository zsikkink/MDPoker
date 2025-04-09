import requests
import json
import time

class EquityCalculator:
    """
    Client for the Node.js Equity Calculator service.
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
                raise ConnectionError(f"Service returned status code: {response.status_code}")
            print("Successfully connected to equity calculator service")
        except requests.RequestException as e:
            print(f"Error connecting to equity calculator service: {e}")
            print("Make sure the Node.js service is running")
            raise
    
    def calculate_equity(self, player1_hand, player2_hand, board=None):
        """
        Calculate equity between two poker hands.
        
        Args:
            player1_hand (str): The first player's hand in string format (e.g. "AcKh")
            player2_hand (str): The second player's hand in string format (e.g. "QsJd")
            board (str, optional): The community cards in string format (e.g. "Th9d2c")
        
        Returns:
            dict: A dictionary containing the equity results
        """
        payload = {
            "player1Hand": player1_hand,
            "player2Hand": player2_hand
        }
        
        if board:
            payload["board"] = board
        
        try:
            start_time = time.time()
            response = requests.post(
                self.calculate_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code != 200:
                print(f"Error: Service returned status code {response.status_code}")
                print(f"Response: {response.text}")
                return None
            
            result = response.json()
            result['calculationTime'] = round((end_time - start_time) * 1000, 2)  # ms
            return result
            
        except requests.RequestException as e:
            print(f"Error communicating with equity calculator service: {e}")
            return None

# Example usage
if __name__ == "__main__":
    calculator = EquityCalculator()
    
    # Example 1: Calculate equity for two hands preflop
    result1 = calculator.calculate_equity("AcKh", "QsJd")
    if result1:
        print(f"\nPreflop equity calculation:")
        print(f"Hand 1 ({result1['player1Hand']}): {result1['player1Equity']:.2%}")
        print(f"Hand 2 ({result1['player2Hand']}): {result1['player2Equity']:.2%}")
        print(f"Calculation time: {result1['calculationTime']} ms")
    
    # Example 2: Calculate equity with a flop
    result2 = calculator.calculate_equity("AcKh", "QsJd", "Th9d2c")
    if result2:
        print(f"\nFlop equity calculation:")
        print(f"Board: {result2['board']}")
        print(f"Hand 1 ({result2['player1Hand']}): {result2['player1Equity']:.2%}")
        print(f"Hand 2 ({result2['player2Hand']}): {result2['player2Equity']:.2%}")
        print(f"Calculation time: {result2['calculationTime']} ms")