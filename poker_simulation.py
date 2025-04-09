import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from treys import Card, Deck, Evaluator
import random
from tqdm import tqdm
from collections import defaultdict

class PokerSimulation:
    def __init__(self):
        self.deck = Deck()
        self.evaluator = Evaluator()
        self.hand_rankings = self._create_hand_rankings()
        
    def _create_hand_rankings(self):
        """Create a preflop hand strength ranking."""
        # Create all possible starting hands
        ranks = "AKQJT98765432"
        suits = "shdc"
        cards = []
        
        for r in ranks:
            for s in suits:
                cards.append(r + s)
        
        # Generate all possible hand combinations
        hand_combinations = []
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                card1, card2 = cards[i], cards[j]
                # Convert to treys format
                card1_treys = Card.new(card1)
                card2_treys = Card.new(card2)
                
                # Get the card ranks
                rank1, rank2 = card1[0], card2[0]
                suit1, suit2 = card1[1], card2[1]
                is_suited = suit1 == suit2
                
                # Create a standardized representation
                if ranks.index(rank1) <= ranks.index(rank2):
                    hand_name = rank1 + rank2 + ('s' if is_suited else 'o')
                else:
                    hand_name = rank2 + rank1 + ('s' if is_suited else 'o')
                
                hand_combinations.append({
                    'hand': [card1_treys, card2_treys],
                    'hand_name': hand_name,
                    'card1': card1,
                    'card2': card2
                })
        
        # Create a simplified ranking system based on hand types
        hand_types = {}
        for combo in hand_combinations:
            hand_name = combo['hand_name']
            if hand_name not in hand_types:
                hand_types[hand_name] = []
            hand_types[hand_name].append(combo)
        
        # Create a ranking of hand types based on general poker strategy
        # These rankings are approximate - optimally this would use actual equity calculation
        hand_ranks = {
            'AA': 1, 'KK': 2, 'QQ': 3, 'JJ': 4, 'TT': 5, 'AKs': 6, 'AQs': 7, 'AKo': 8,
            '99': 9, 'AJs': 10, 'AQo': 11, 'ATs': 12, 'AJo': 13, '88': 14, 'ATo': 15,
            'KQs': 16, '77': 17, 'KJs': 18, 'A9s': 19, 'KQo': 20, 'A8s': 21, 'KTs': 22,
            'KJo': 23, 'A7s': 24, 'A5s': 25, 'A6s': 26, 'A4s': 27, 'KTo': 28, 'A3s': 29,
            '66': 30, 'A2s': 31, 'QJs': 32, 'K9s': 33, 'QTs': 34, 'Q9s': 35, 'QJo': 36,
            'K8s': 37, 'K7s': 38, 'QTo': 39, '55': 40, 'K6s': 41, 'K5s': 42, 'K4s': 43,
            'K3s': 44, 'K2s': 45, 'JTs': 46, 'Q8s': 47, 'T9s': 48, 'Q7s': 49, 'J9s': 50,
            'A9o': 51, 'JTo': 52, 'Q6s': 53, 'Q5s': 54, '44': 55, 'Q4s': 56, 'Q3s': 57,
            'T8s': 58, 'K9o': 59, 'Q2s': 60, 'J8s': 61, 'A8o': 62, 'T9o': 63, 'A7o': 64,
            '98s': 65, 'A5o': 66, 'J7s': 67, 'A6o': 68, 'A4o': 69, '33': 70, 'J9o': 71,
            'A3o': 72, 'T7s': 73, 'A2o': 74, 'J6s': 75, 'Q9o': 76, 'J5s': 77, '97s': 78,
            'T6s': 79, 'K8o': 80, 'J4s': 81, '87s': 82, 'Q8o': 83, 'J3s': 84, 'T8o': 85,
            '22': 86, 'J2s': 87, 'K7o': 88, '96s': 89, 'T5s': 90, 'K6o': 91, 'T4s': 92,
            '86s': 93, '76s': 94, 'K5o': 95, 'T3s': 96, 'J8o': 97, 'T2s': 98, 'K4o': 99,
            '95s': 100, '85s': 101, 'K3o': 102, 'Q7o': 103, '75s': 104, 'K2o': 105, '65s': 106,
            'J7o': 107, '94s': 108, 'Q6o': 109, '84s': 110, 'T7o': 111, '54s': 112, 'Q5o': 113,
            '64s': 114, '74s': 115, 'Q4o': 116, '98o': 117, 'T6o': 118, 'Q3o': 119, '93s': 120,
            '83s': 121, '97o': 122, 'T5o': 123, '53s': 124, 'Q2o': 125, '92s': 126, '43s': 127,
            '73s': 128, '63s': 129, '87o': 130, 'J6o': 131, 'T4o': 132, '82s': 133, '96o': 134,
            'J5o': 135, '52s': 136, '62s': 137, '86o': 138, 'J4o': 139, '76o': 140, '42s': 141,
            'T3o': 142, 'J3o': 143, '32s': 144, '72s': 145, '95o': 146, 'T2o': 147, '85o': 148,
            'J2o': 149, '75o': 150, '65o': 151, '94o': 152, '54o': 153, '84o': 154, '64o': 155,
            '74o': 156, '93o': 157, '53o': 158, '43o': 159, '92o': 160, '83o': 161, '73o': 162,
            '63o': 163, '82o': 164, '52o': 165, '62o': 166, '42o': 167, '32o': 168, '72o': 169,
        }
        
        # Map to string representations for easier lookup
        self.hand_names_map = {}
        
        # Create a lookup table for hand classifications
        for hand_name, rank in hand_ranks.items():
            if hand_name in hand_types:
                for hand_combo in hand_types[hand_name]:
                    card1_str = Card.int_to_str(hand_combo['hand'][0])
                    card2_str = Card.int_to_str(hand_combo['hand'][1])
                    # Store with both orderings of the cards
                    key1 = (card1_str, card2_str)
                    key2 = (card2_str, card1_str)
                    self.hand_names_map[key1] = {
                        'rank': rank,
                        'hand_name': hand_name,
                        'percentile': 1 - (rank / 169)
                    }
                    self.hand_names_map[key2] = {
                        'rank': rank,
                        'hand_name': hand_name,
                        'percentile': 1 - (rank / 169)
                    }
        
        return self.hand_names_map

    def deal_hands(self):
        """Deal two hands for heads-up play."""
        self.deck.shuffle()
        hand1 = self.deck.draw(2)
        hand2 = self.deck.draw(2)
        return hand1, hand2
    
    def get_hand_strength(self, hand):
        """Get the pre-flop hand strength based on rankings."""
        # Convert hand to string representation
        card1_str = Card.int_to_str(hand[0])
        card2_str = Card.int_to_str(hand[1])
        
        # Look up in the hand names map
        key = (card1_str, card2_str)
        
        if key in self.hand_rankings:
            return self.hand_rankings[key]
        else:
            # Try the reverse order
            key = (card2_str, card1_str)
            if key in self.hand_rankings:
                return self.hand_rankings[key]
            
        # If not found (shouldn't happen), return a default low value
        return {'rank': 169, 'hand_name': 'unknown', 'percentile': 0}
    
    def simulate_preflop_equity(self, hand1, hand2, num_simulations=1000):
        """Simulate post-flop equity by running Monte Carlo simulations."""
        hand1_wins = 0
        hand2_wins = 0
        ties = 0
        
        for _ in range(num_simulations):
            # Create a new deck excluding the cards in both hands
            temp_deck = Deck()
            for card in hand1 + hand2:
                temp_deck.cards.remove(card)
            
            # Deal the board
            board = temp_deck.draw(5)
            
            # Evaluate both hands
            hand1_score = self.evaluator.evaluate(hand1, board)
            hand2_score = self.evaluator.evaluate(hand2, board)
            
            # Lower score is better in treys
            if hand1_score < hand2_score:
                hand1_wins += 1
            elif hand2_score < hand1_score:
                hand2_wins += 1
            else:
                ties += 1
        
        hand1_equity = (hand1_wins + ties/2) / num_simulations
        hand2_equity = (hand2_wins + ties/2) / num_simulations
        
        return {
            'hand1_equity': hand1_equity,
            'hand2_equity': hand2_equity,
            'hand1_wins': hand1_wins,
            'hand2_wins': hand2_wins,
            'ties': ties
        }
    
    def preflop_decision(self, hand, position, opponent_action=None, pot_size=1.5):
        """Make a simplified pre-flop decision based on hand strength and position."""
        strength = self.get_hand_strength(hand)
        percentile = strength['percentile']
        
        # Basic strategy based on hand strength and position
        if opponent_action is None:  # We are first to act (out of position)
            if percentile > 0.85:  # Top 15% of hands
                return 'raise', 3  # Raise 3 big blinds
            elif percentile > 0.5:  # Top 50% of hands
                return 'raise', 2.5  # Raise 2.5 big blinds
            elif percentile > 0.2:  # Top 80% of hands
                if random.random() < 0.3:  # Sometimes raise with medium hands
                    return 'raise', 2.5
                else:
                    return 'call', 1  # Call the big blind
            else:
                if random.random() < 0.1:  # Occasionally bluff with bad hands
                    return 'raise', 2.5
                else:
                    return 'fold', 0
        
        else:  # Responding to opponent's action
            if opponent_action[0] == 'raise':
                opponent_bet = opponent_action[1]
                if percentile > 0.9:  # Top 10% of hands
                    return 'raise', opponent_bet * 3  # 3-bet
                elif percentile > 0.7:  # Top 30% of hands
                    return 'call', opponent_bet  # Call the raise
                elif percentile > 0.4:  # Top 60% of hands
                    if position == 'button':  # In position
                        return 'call', opponent_bet  # Call with more hands in position
                    else:
                        if random.random() < 0.3:  # Sometimes call
                            return 'call', opponent_bet
                        else:
                            return 'fold', 0
                else:
                    if random.random() < 0.05:  # Occasionally bluff-raise
                        return 'raise', opponent_bet * 3
                    else:
                        return 'fold', 0
            
            elif opponent_action[0] == 'call':
                if percentile > 0.6:  # Top 40% of hands
                    return 'raise', 2  # Raise 2 big blinds
                else:
                    return 'check', 0  # Check and see the flop
        
        # Default action
        return 'fold', 0

    def print_hand(self, hand):
        """Print a readable representation of a hand."""
        return [Card.int_to_str(card) for card in hand]
    
    def hand_class(self, hand):
        """Return the hand class (e.g., 'AKs', 'TT', etc.)."""
        strength = self.get_hand_strength(hand)
        return strength['hand_name']
    
    def simulate_hand(self, verbose=False):
        """Simulate a single pre-flop hand between two players."""
        # Deal hands
        hand_bb, hand_btn = self.deal_hands()
        
        if verbose:
            print(f"Big Blind: {self.print_hand(hand_bb)} ({self.hand_class(hand_bb)})")
            print(f"Button: {self.print_hand(hand_btn)} ({self.hand_class(hand_btn)})")
        
        # Initial pot
        pot = 1.5  # Small blind (0.5) + big blind (1)
        
        # Pre-flop action
        # Button acts first in heads-up
        btn_action = self.preflop_decision(hand_btn, 'button')
        
        if verbose:
            print(f"Button: {btn_action[0]} {btn_action[1]}")
        
        if btn_action[0] == 'fold':
            # Big blind wins without showdown
            return {
                'winner': 'bb',
                'hand_bb': hand_bb,
                'hand_btn': hand_btn,
                'pot': pot,
                'showdown': False
            }
            
        elif btn_action[0] == 'raise':
            pot += btn_action[1]
            bb_action = self.preflop_decision(hand_bb, 'bb', btn_action, pot)
            
            if verbose:
                print(f"Big Blind: {bb_action[0]} {bb_action[1]}")
            
            if bb_action[0] == 'fold':
                # Button wins without showdown
                return {
                    'winner': 'btn',
                    'hand_bb': hand_bb,
                    'hand_btn': hand_btn,
                    'pot': pot,
                    'showdown': False
                }
                
            elif bb_action[0] == 'call':
                pot += bb_action[1]
                # Go to showdown - simulate equity
                equity = self.simulate_preflop_equity(hand_bb, hand_btn)
                
                if verbose:
                    print(f"Equity - BB: {equity['hand1_equity']:.2f}, BTN: {equity['hand2_equity']:.2f}")
                
                # Determine winner based on equity
                if random.random() < equity['hand1_equity']:
                    winner = 'bb'
                else:
                    winner = 'btn'
                
                return {
                    'winner': winner,
                    'hand_bb': hand_bb,
                    'hand_btn': hand_btn,
                    'pot': pot,
                    'showdown': True,
                    'equity': equity
                }
                
            elif bb_action[0] == 'raise':  # 3-bet
                pot += bb_action[1]
                btn_action2 = self.preflop_decision(hand_btn, 'button', bb_action, pot)
                
                if verbose:
                    print(f"Button (responding to 3-bet): {btn_action2[0]} {btn_action2[1]}")
                
                if btn_action2[0] == 'fold':
                    return {
                        'winner': 'bb',
                        'hand_bb': hand_bb,
                        'hand_btn': hand_btn,
                        'pot': pot,
                        'showdown': False
                    }
                else:  # Call or raise (assume call for simplicity)
                    pot += btn_action2[1]
                    equity = self.simulate_preflop_equity(hand_bb, hand_btn)
                    
                    if verbose:
                        print(f"Equity - BB: {equity['hand1_equity']:.2f}, BTN: {equity['hand2_equity']:.2f}")
                    
                    if random.random() < equity['hand1_equity']:
                        winner = 'bb'
                    else:
                        winner = 'btn'
                    
                    return {
                        'winner': winner,
                        'hand_bb': hand_bb,
                        'hand_btn': hand_btn,
                        'pot': pot,
                        'showdown': True,
                        'equity': equity
                    }
        
        elif btn_action[0] == 'call':
            # Button calls the big blind
            pot += btn_action[1]
            
            # Big blind can now check or raise
            bb_action = self.preflop_decision(hand_bb, 'bb', btn_action, pot)
            
            if verbose:
                print(f"Big Blind: {bb_action[0]} {bb_action[1]}")
            
            if bb_action[0] == 'check':
                # Go to showdown
                equity = self.simulate_preflop_equity(hand_bb, hand_btn)
                
                if verbose:
                    print(f"Equity - BB: {equity['hand1_equity']:.2f}, BTN: {equity['hand2_equity']:.2f}")
                
                if random.random() < equity['hand1_equity']:
                    winner = 'bb'
                else:
                    winner = 'btn'
                
                return {
                    'winner': winner,
                    'hand_bb': hand_bb,
                    'hand_btn': hand_btn,
                    'pot': pot,
                    'showdown': True,
                    'equity': equity
                }
                
            elif bb_action[0] == 'raise':
                pot += bb_action[1]
                
                # Button responds to the raise
                btn_action2 = self.preflop_decision(hand_btn, 'button', bb_action, pot)
                
                if verbose:
                    print(f"Button (responding to raise): {btn_action2[0]} {btn_action2[1]}")
                
                if btn_action2[0] == 'fold':
                    return {
                        'winner': 'bb',
                        'hand_bb': hand_bb,
                        'hand_btn': hand_btn,
                        'pot': pot,
                        'showdown': False
                    }
                else:  # Call or raise (assume call for simplicity)
                    pot += btn_action2[1]
                    equity = self.simulate_preflop_equity(hand_bb, hand_btn)
                    
                    if verbose:
                        print(f"Equity - BB: {equity['hand1_equity']:.2f}, BTN: {equity['hand2_equity']:.2f}")
                    
                    if random.random() < equity['hand1_equity']:
                        winner = 'bb'
                    else:
                        winner = 'btn'
                    
                    return {
                        'winner': winner,
                        'hand_bb': hand_bb,
                        'hand_btn': hand_btn,
                        'pot': pot,
                        'showdown': True,
                        'equity': equity
                    }
        
        # This should never happen, but just in case
        print(f"WARNING: Unhandled action scenario - btn_action: {btn_action}")
        return {
            'winner': 'bb',  # Default to BB winning
            'hand_bb': hand_bb,
            'hand_btn': hand_btn,
            'pot': pot,
            'showdown': False
        }

    def run_simulation(self, num_hands=1000):
        """Run a simulation of multiple hands and gather statistics."""
        results = []
        
        for _ in tqdm(range(num_hands)):
            try:
                result = self.simulate_hand()
                if result is not None:  # Make sure we only add valid results
                    results.append(result)
            except Exception as e:
                print(f"Error in hand simulation: {e}")
                continue
        
        # Analyze results
        total_hands = len(results)
        if total_hands == 0:
            return [], {
                'bb_win_rate': 0,
                'btn_win_rate': 0,
                'showdown_rate': 0,
                'avg_pot_size': 0
            }
            
        bb_wins = sum(1 for r in results if r['winner'] == 'bb')
        btn_wins = sum(1 for r in results if r['winner'] == 'btn')
        showdowns = sum(1 for r in results if r.get('showdown', False))
        
        stats = {
            'bb_win_rate': bb_wins / total_hands,
            'btn_win_rate': btn_wins / total_hands,
            'showdown_rate': showdowns / total_hands,
            'avg_pot_size': sum(r['pot'] for r in results) / total_hands
        }
        
        return results, stats
    
    def analyze_hand_performance(self, results):
        """Analyze how different hands performed in the simulation."""
        hand_performance = defaultdict(lambda: {'count': 0, 'wins': 0})
        
        for result in results:
            bb_hand_class = self.hand_class(result['hand_bb'])
            btn_hand_class = self.hand_class(result['hand_btn'])
            
            hand_performance[bb_hand_class]['count'] += 1
            hand_performance[btn_hand_class]['count'] += 1
            
            if result['winner'] == 'bb':
                hand_performance[bb_hand_class]['wins'] += 1
            else:
                hand_performance[btn_hand_class]['wins'] += 1
        
        # Calculate win rates
        for hand, stats in hand_performance.items():
            if stats['count'] > 0:
                stats['win_rate'] = stats['wins'] / stats['count']
            else:
                stats['win_rate'] = 0
        
        return hand_performance

# Example usage
if __name__ == "__main__":
    sim = PokerSimulation()
    
    # Simulate a single hand with verbose output
    print("Simulating a single hand:")
    result = sim.simulate_hand(verbose=True)
    print(f"Winner: {result['winner']}")
    print(f"Final pot: {result['pot']}")
    print()
    
    # Run a larger simulation
    print("Running a simulation of 1,000 hands...")
    results, stats = sim.run_simulation(1000)
    
    print("\nSimulation Results:")
    print(f"Big Blind win rate: {stats['bb_win_rate']:.2f}")
    print(f"Button win rate: {stats['btn_win_rate']:.2f}")
    print(f"Showdown rate: {stats['showdown_rate']:.2f}")
    print(f"Average pot size: {stats['avg_pot_size']:.2f} big blinds")
    
    # Analyze hand performance
    hand_perf = sim.analyze_hand_performance(results)
    
    # Get the top performing hands
    top_hands = sorted(
        [(hand, stats['win_rate'], stats['count']) 
         for hand, stats in hand_perf.items() if stats['count'] >= 10],
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    print("\nTop Performing Hands:")
    for hand, win_rate, count in top_hands:
        print(f"{hand}: {win_rate:.2f} win rate ({count} occurrences)")
    
    # Plot results
    plt.figure(figsize=(10, 6))
    
    positions = ['Big Blind', 'Button']
    win_rates = [stats['bb_win_rate'], stats['btn_win_rate']]
    
    plt.bar(positions, win_rates, color=['blue', 'green'])
    plt.title('Win Rates by Position')
    plt.ylabel('Win Rate')
    plt.ylim(0, 1)
    
    for i, v in enumerate(win_rates):
        plt.text(i, v + 0.02, f'{v:.2f}', ha='center')
    
    plt.show() 