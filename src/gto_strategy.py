from treys import Evaluator, Card

class GTOStrategy:
    def __init__(self):
        self.evaluator = Evaluator()

    def decide_action(self, hand, community_cards, pot, current_bets):
        # Convert hand and community cards to treys format
        hand_cards = [Card.new(card) for card in hand]
        community_cards = [Card.new(card) for card in community_cards]

        # Evaluate hand strength
        hand_strength = self.evaluator.evaluate(community_cards, hand_cards)

        # Placeholder for GTO decision logic based on hand strength
        if hand_strength < 1000:
            return 'raise'
        elif hand_strength < 5000:
            return 'call'
        else:
            return 'fold'