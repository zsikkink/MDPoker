from treys import Evaluator, Card

# Create an evaluator
evaluator = Evaluator()

def evaluate_hand(hole_cards, community_cards):
    # Ensure the hole cards list has exactly 2 cards
    if len(hole_cards) != 2:
        raise ValueError("The hole cards list must contain exactly 2 cards.")
    
    # Ensure the community cards list has 3, 4, or 5 cards
    if len(community_cards) not in [3, 4, 5]:
        raise ValueError("The community cards list must contain 3, 4, or 5 cards.")

    # Convert hole cards and community cards to treys format
    hand_cards = [Card.new(card) for card in hole_cards]
    community_cards = [Card.new(card) for card in community_cards]

    # Evaluate hand strength
    hand_strength = evaluator.evaluate(community_cards, hand_cards)
    return hand_strength

def evaluate_range(community_cards, hand_range):
    # Ensure the community cards list has 3, 4, or 5 cards
    if len(community_cards) not in [3, 4, 5]:
        raise ValueError("The community cards list must contain 3, 4, or 5 cards.")
    
    hand_strengths = []

    for hand in hand_range:
        # Ensure each hand in the range has exactly 2 cards
        if len(hand) != 2:
            raise ValueError("Each hand in the range must contain exactly 2 cards.")
        
        # Evaluate the hand strength
        hand_strength = evaluate_hand(hand, community_cards)
        hand_strengths.append(hand_strength)
    
    return hand_strengths

def calculate_equity(community_cards, my_hand, opponent_range):
    # Calculate the strength of my hand
    my_hand_strength = evaluate_hand(my_hand, community_cards)

    # Calculate the strengths of each of the hands in my opponent's range
    opponent_hand_strengths = evaluate_range(community_cards, opponent_range)

    # Calculate the percentage of opponent's hands I'm beating
    hands_beaten = sum(1 for strength in opponent_hand_strengths if my_hand_strength < strength)
    equity_percentage = (hands_beaten / len(opponent_hand_strengths)) * 100

    return equity_percentage

def calculate_range_advantage(community_cards, my_range, opponent_range):
    # Calculate the strengths of each of the hands in my range
    my_hand_strengths = evaluate_range(community_cards, my_range)

    # Calculate the strengths of each of the hands in my opponent's range
    opponent_hand_strengths = evaluate_range(community_cards, opponent_range)

    # Calculate the percentage of combinations where my range is stronger than my opponent's range
    range_advantages = []

    for my_strength in my_hand_strengths:
        hands_beaten = sum(1 for strength in opponent_hand_strengths if my_strength < strength)
        range_advantage = (hands_beaten / len(opponent_hand_strengths)) * 100
        range_advantages.append(range_advantage)

    average_range_advantage = sum(range_advantages) / len(range_advantages)

    return average_range_advantage

if __name__ == "__main__":
    # Example lists of community cards, my hand, my range, and opponent's range
    community_cards = ['2c', '3d', '4d']
    my_hand = ['Qh', 'Jh']
    my_range = [['Ad', 'Kd'], ['Qh', 'Jh'], ['9c', '9d'], ['7s', '8s'], ['5d', '6d']]  # Adjust this list to test different ranges
    opponent_range = [['As', 'Ks'], ['Qc', 'Jc'], ['8h', '8d'], ['6s', '7s'], ['4d', '5d']]  # Adjust this list to test different ranges

    # Calculate the equity
    equity = calculate_equity(community_cards, my_hand, opponent_range)

    # Calculate the range advantage
    range_advantage = calculate_range_advantage(community_cards, my_range, opponent_range)

    # Print the equity percentage and range advantage
    print("Equity estimate", equity)
    print("Range advantage:", range_advantage)