from src.table import Table

class PreflopGTOBot:
    def __init__(self, starting_stack, num_opponents, opponent_stacks, position, actions):
        self.starting_stack = starting_stack
        self.num_opponents = num_opponents
        self.opponent_stacks = opponent_stacks
        self.position = position
        self.actions = actions
        self.strategy = self.load_strategy()

    def load_strategy(self):
        # Define a basic preflop strategy
        strategy = {
            'UTG': {
                'AA': 'raise',
                'KK': 'raise',
                'QQ': 'raise',
                'JJ': 'raise',
                'AKs': 'raise',
                'AQs': 'raise',
                'AJs': 'call',
                'ATs': 'call',
                'KQs': 'call',
                'KJs': 'fold',
                'QJs': 'fold',
                'JTs': 'fold',
                'T9s': 'fold',
                '98s': 'fold',
                '87s': 'fold',
                '76s': 'fold',
                '65s': 'fold',
                '54s': 'fold'
            },
            'UTG+1': {
                'AA': 'raise',
                'KK': 'raise',
                'QQ': 'raise',
                'JJ': 'raise',
                'AKs': 'raise',
                'AQs': 'raise',
                'AJs': 'raise',
                'ATs': 'call',
                'KQs': 'call',
                'KJs': 'call',
                'QJs': 'call',
                'JTs': 'call',
                'T9s': 'fold',
                '98s': 'fold',
                '87s': 'fold',
                '76s': 'fold',
                '65s': 'fold',
                '54s': 'fold'
            },
            'UTG+2': {
                'AA': 'raise',
                'KK': 'raise',
                'QQ': 'raise',
                'JJ': 'raise',
                'AKs': 'raise',
                'AQs': 'raise',
                'AJs': 'raise',
                'ATs': 'raise',
                'KQs': 'call',
                'KJs': 'call',
                'QJs': 'call',
                'JTs': 'call',
                'T9s': 'call',
                '98s': 'fold',
                '87s': 'fold',
                '76s': 'fold',
                '65s': 'fold',
                '54s': 'fold'
            },
            'LJ': {
                'AA': 'raise',
                'KK': 'raise',
                'QQ': 'raise',
                'JJ': 'raise',
                'AKs': 'raise',
                'AQs': 'raise',
                'AJs': 'raise',
                'ATs': 'raise',
                'KQs': 'raise',
                'KJs': 'call',
                'QJs': 'call',
                'JTs': 'call',
                'T9s': 'call',
                '98s': 'call',
                '87s': 'fold',
                '76s': 'fold',
                '65s': 'fold',
                '54s': 'fold'
            },
            'HJ': {
                'AA': 'raise',
                'KK': 'raise',
                'QQ': 'raise',
                'JJ': 'raise',
                'AKs': 'raise',
                'AQs': 'raise',
                'AJs': 'raise',
                'ATs': 'raise',
                'KQs': 'raise',
                'KJs': 'raise',
                'QJs': 'call',
                'JTs': 'call',
                'T9s': 'call',
                '98s': 'call',
                '87s': 'call',
                '76s': 'fold',
                '65s': 'fold',
                '54s': 'fold'
            },
            'CO': {
                'AA': 'raise',
                'KK': 'raise',
                'QQ': 'raise',
                'JJ': 'raise',
                'AKs': 'raise',
                'AQs': 'raise',
                'AJs': 'raise',
                'ATs': 'raise',
                'KQs': 'raise',
                'KJs': 'raise',
                'QJs': 'raise',
                'JTs': 'call',
                'T9s': 'call',
                '98s': 'call',
                '87s': 'call',
                '76s': 'call',
                '65s': 'fold',
                '54s': 'fold'
            },
            'BTN': {
                'AA': 'raise',
                'KK': 'raise',
                'QQ': 'raise',
                'JJ': 'raise',
                'AKs': 'raise',
                'AQs': 'raise',
                'AJs': 'raise',
                'ATs': 'raise',
                'KQs': 'raise',
                'KJs': 'raise',
                'QJs': 'raise',
                'JTs': 'raise',
                'T9s': 'call',
                '98s': 'call',
                '87s': 'call',
                '76s': 'call',
                '65s': 'call',
                '54s': 'call'
            },
            'SB': {
                'AA': 'raise',
                'KK': 'raise',
                'QQ': 'raise',
                'JJ': 'raise',
                'AKs': 'raise',
                'AQs': 'raise',
                'AJs': 'raise',
                'ATs': 'raise',
                'KQs': 'raise',
                'KJs': 'raise',
                'QJs': 'raise',
                'JTs': 'raise',
                'T9s': 'call',
                '98s': 'call',
                '87s': 'call',
                '76s': 'call',
                '65s': 'call',
                '54s': 'call'
            },
            'BB': {
                'AA': 'raise',
                'KK': 'raise',
                'QQ': 'raise',
                'JJ': 'raise',
                'AKs': 'raise',
                'AQs': 'raise',
                'AJs': 'raise',
                'ATs': 'raise',
                'KQs': 'raise',
                'KJs': 'raise',
                'QJs': 'raise',
                'JTs': 'raise',
                'T9s': 'call',
                '98s': 'call',
                '87s': 'call',
                '76s': 'call',
                '65s': 'call',
                '54s': 'call'
            }
        }
        return strategy

    def get_action(self, hand):
        # Convert hand to a string representation
        hand_str = ''.join(sorted([hand[0][0], hand[1][0]])) + ('s' if hand[0][1] == hand[1][1] else 'o')
        
        # Determine action based on position and strategy
        action = self.strategy[self.position].get(hand_str, 'fold')
        
        # Adjust action based on stack sizes and actions of other players
        if self.starting_stack < 20:  # Example adjustment for short stack
            if action == 'raise':
                action = 'all-in'
        
        # Example adjustment based on actions of other players
        if 'raise' in self.actions:
            if action == 'call':
                action = 'fold'
        
        return action

# Example usage
if __name__ == "__main__":
    starting_stack = 100
    num_opponents = 6
    opponent_stacks = [100, 80, 120, 90, 110, 95]
    position = 'HJ'
    actions = ['fold', 'raise', 'call', 'fold', 'call', 'fold']
    
    bot = PreflopGTOBot(starting_stack, num_opponents, opponent_stacks, position, actions)
    hand = [('A', 's'), ('K', 's')]  # Example hand
    action = bot.get_action(hand)
    print(f"Action for hand {hand}: {action}")