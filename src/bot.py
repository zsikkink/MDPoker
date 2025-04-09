from src.gto_strategy import GTOStrategy

class GTOBot:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.strategy = GTOStrategy()

    def decide_action(self, community_cards, pot, current_bets):
        return self.strategy.decide_action(self.hand, community_cards, pot, current_bets)