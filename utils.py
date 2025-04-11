#utils.py

import random
import requests

def shuffle_deck():
    """
    Create a standard 52-card deck and shuffle it.
    
    Each card is represented as a 2-character string:
      - Ranks: '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'
      - Suits: 'h' (hearts), 'd' (diamonds), 'c' (clubs), 's' (spades)
      
    Returns:
        list: A list of 52 shuffled card strings.
    """
    ranks = "23456789TJQKA"
    suits = "hdcs"
    deck = [rank + suit for rank in ranks for suit in suits]
    random.shuffle(deck)
    return deck

def deal(deck):
    """
    Deal four cards from the deck and return a four-character string for each player.
    
    The first and third cards form player 1's hand, and the second and fourth cards
    form player 2's hand.
    
    Args:
        deck (list): A list of card strings representing a shuffled deck.
        
    Returns:
        tuple: Two strings, each four characters long, representing the hands
               for player 1 and player 2.
    """
    if len(deck) < 4:
        raise ValueError("Deck must have at least 4 cards to deal.")
    
    # Concatenate card strings: each card is 2 characters,
    # so two cards will form a 4-character string.
    player1_hand = deck[0] + deck[2]
    player2_hand = deck[1] + deck[3]
    return player1_hand, player2_hand

def calculate_equity(player1_hand, player2_hand):
    """
    Calls the Node.js equity calculator service via HTTP POST to calculate
    pre-flop equities for two hands. The returned equity percentages are divided by 100
    to convert them to decimals. If the sum of the decimals is less than 1, the missing
    equity is split equally between the two players to ensure the equities sum to 1.
    
    Parameters:
      player1_hand (str): Player 1's hand, e.g., "AcKh"
      player2_hand (str): Player 2's hand, e.g., "QsJd"
      
    Returns:
      tuple: (player1_equity, player2_equity) as floats in decimal form summing to 1.
    
    Raises:
      Exception: When the request fails or the service returns an error.
    """
    url = "http://localhost:3000/calculate-equity"
    payload = {
        "player1Hand": player1_hand,
        "player2Hand": player2_hand
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        # Raise an error if the response contains an HTTP error status
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Error calling the equity calculator service: {e}")
    
    # Parse the JSON response
    data = response.json()
    if "error" in data:
        # Optionally, inspect data['message'] for more details if available
        raise Exception(f"Service returned an error: {data['error']}")

    # Get and convert the returned equity values to floats
    equity1 = float(data["player1Equity"])
    equity2 = float(data["player2Equity"])
    
    # Convert percentage equities into decimals
    equity1 /= 100
    equity2 /= 100
    
    # If the sum is less than 1, add the missing portion equally to both equities.
    total = equity1 + equity2
    if total < 1:
        missing = 1 - total
        equity1 += missing / 2
        equity2 += missing / 2

    # Round the equities to 3 decimal places
    equity1 = round(equity1, 3)
    equity2 = round(equity2, 3)
    
    return equity1, equity2


# Dictionary of 169 Texas Hold’em starting hands mapped to their estimated equity vs. a random hand.
hand_vs_random = {
    # Pocket Pairs (13 hands)
    "AA": 0.85, "KK": 0.82, "QQ": 0.80, "JJ": 0.77, "TT": 0.75,
    "99": 0.72, "88": 0.69, "77": 0.67, "66": 0.64, "55": 0.61,
    "44": 0.58, "33": 0.55, "22": 0.52,

    # Suited Non-Pairs (78 hands)
    # Ace–High Suited (12 hands)
    "AKs": 0.67, "AQs": 0.66, "AJs": 0.64, "ATs": 0.63, "A9s": 0.62,
    "A8s": 0.61, "A7s": 0.60, "A6s": 0.59, "A5s": 0.58, "A4s": 0.57,
    "A3s": 0.56, "A2s": 0.55,
    # King–High Suited (11 hands)
    "KQs": 0.63, "KJs": 0.61, "KTs": 0.60, "K9s": 0.59, "K8s": 0.58,
    "K7s": 0.57, "K6s": 0.56, "K5s": 0.55, "K4s": 0.54, "K3s": 0.53,
    "K2s": 0.52,
    # Queen–High Suited (10 hands)
    "QJs": 0.60, "QTs": 0.59, "Q9s": 0.58, "Q8s": 0.57, "Q7s": 0.56,
    "Q6s": 0.55, "Q5s": 0.54, "Q4s": 0.53, "Q3s": 0.52, "Q2s": 0.51,
    # Jack–High Suited (9 hands)
    "JTs": 0.58, "J9s": 0.57, "J8s": 0.56, "J7s": 0.55, "J6s": 0.54,
    "J5s": 0.53, "J4s": 0.52, "J3s": 0.51, "J2s": 0.50,
    # Ten–High Suited (8 hands)
    "T9s": 0.56, "T8s": 0.55, "T7s": 0.54, "T6s": 0.53, "T5s": 0.52,
    "T4s": 0.51, "T3s": 0.50, "T2s": 0.49,
    # 9–High Suited (7 hands)
    "98s": 0.55, "97s": 0.54, "96s": 0.53, "95s": 0.52, "94s": 0.51,
    "93s": 0.50, "92s": 0.49,
    # 8–High Suited (6 hands)
    "87s": 0.54, "86s": 0.53, "85s": 0.52, "84s": 0.51, "83s": 0.50,
    "82s": 0.49,
    # 7–High Suited (5 hands)
    "76s": 0.52, "75s": 0.51, "74s": 0.50, "73s": 0.49, "72s": 0.48,
    # 6–High Suited (4 hands)
    "65s": 0.50, "64s": 0.49, "63s": 0.48, "62s": 0.47,
    # 5–High Suited (3 hands)
    "54s": 0.48, "53s": 0.47, "52s": 0.46,
    # 4–High Suited (2 hands)
    "43s": 0.46, "42s": 0.45,
    # 3–High Suited (1 hand)
    "32s": 0.44,

    # Offsuit Non-Pairs (78 hands)
    # Ace–High Offsuit (12 hands)
    "AKo": 0.65, "AQo": 0.64, "AJo": 0.62, "ATo": 0.61, "A9o": 0.60,
    "A8o": 0.59, "A7o": 0.58, "A6o": 0.57, "A5o": 0.56, "A4o": 0.55,
    "A3o": 0.54, "A2o": 0.53,
    # King–High Offsuit (11 hands)
    "KQo": 0.61, "KJo": 0.59, "KTo": 0.58, "K9o": 0.57, "K8o": 0.56,
    "K7o": 0.55, "K6o": 0.54, "K5o": 0.53, "K4o": 0.52, "K3o": 0.51,
    "K2o": 0.50,
    # Queen–High Offsuit (10 hands)
    "QJo": 0.59, "QTo": 0.58, "Q9o": 0.57, "Q8o": 0.56, "Q7o": 0.55,
    "Q6o": 0.54, "Q5o": 0.53, "Q4o": 0.52, "Q3o": 0.51, "Q2o": 0.50,
    # Jack–High Offsuit (9 hands)
    "JTo": 0.57, "J9o": 0.56, "J8o": 0.55, "J7o": 0.54, "J6o": 0.53,
    "J5o": 0.52, "J4o": 0.51, "J3o": 0.50, "J2o": 0.49,
    # Ten–High Offsuit (8 hands)
    "T9o": 0.55, "T8o": 0.54, "T7o": 0.53, "T6o": 0.52, "T5o": 0.51,
    "T4o": 0.50, "T3o": 0.49, "T2o": 0.48,
    # 9–High Offsuit (7 hands)
    "98o": 0.54, "97o": 0.53, "96o": 0.52, "95o": 0.51, "94o": 0.50,
    "93o": 0.49, "92o": 0.48,
    # 8–High Offsuit (6 hands)
    "87o": 0.53, "86o": 0.52, "85o": 0.51, "84o": 0.50, "83o": 0.49,
    "82o": 0.48,
    # 7–High Offsuit (5 hands)
    "76o": 0.51, "75o": 0.50, "74o": 0.49, "73o": 0.48, "72o": 0.47,
    # 6–High Offsuit (4 hands)
    "65o": 0.49, "64o": 0.48, "63o": 0.47, "62o": 0.46,
    # 5–High Offsuit (3 hands)
    "54o": 0.47, "53o": 0.46, "52o": 0.45,
    # 4–High Offsuit (2 hands)
    "43o": 0.45, "42o": 0.44,
    # 3–High Offsuit (1 hand)
    "32o": 0.43,
}

def estimate_equity(hand: str) -> float:
    """
    Given a classified Texas Hold'em starting hand (e.g., 'AA', 'AKs', 'AKo'),
    return the approximate equity (as a float) of that hand versus a random hand 
    (all-in, heads-up situation).

    Parameters:
        hand (str): The hand in standard notation; must be one of the keys in the lookup table.

    Returns:
        float: The estimated winning equity (between 0 and 1).

    Raises:
        ValueError: If the hand is not found in the lookup table.
    """
    try:
        return hand_vs_random[hand]
    except KeyError:
        raise ValueError(f"Hand '{hand}' not found in the equity lookup table.")




def classify_hand(hand):
    """
    Classifies a poker hand based on the input string and returns an equity estimate.

    Args:
        hand (str): A string of exactly four characters representing a poker hand,
                    e.g. "AsAd", "AsKs", "Ad2s", "5c8h".

    Returns:
        tuple: (classified: str, suited: bool, pair: bool, connected: bool, estimated_equity: float)
               - classified: The hand notation (e.g., "AA", "AKs", "A2o", "85o").
               - suited: True if both cards have the same suit.
               - pair: True if both cards share the same rank.
               - connected: For non-pair hands, True if the two card ranks are consecutive 
                            in "A23456789TJQKA" (with Ace and King considered consecutive),
                            False otherwise; for pairs, connected is always False.
               - estimated_equity: The estimated winning equity (a float between 0 and 1) versus a random hand.
    
    Raises:
        ValueError: If the hand is not exactly 4 characters.
    """
    if len(hand) != 4:
        raise ValueError("Hand must be a string of exactly four characters.")

    # Extract card ranks and suits.
    rank1, suit1, rank2, suit2 = hand[0], hand[1], hand[2], hand[3]

    # If it's a pair, return immediately.
    if rank1 == rank2:
        classified = rank1 + rank2
        suited = False
        pair = True
        connected = False
        # Lookup the equity from hand_vs_random (which must contain pairs such as "AA", "KK", etc.)
        estimated_equity = estimate_equity(classified)
        return classified, suited, pair, connected, estimated_equity

    # For non-pair hands, order the ranks by "greatness".
    greatness_order = "23456789TJQKA"
    if greatness_order.index(rank1) > greatness_order.index(rank2):
        ordered_ranks = rank1 + rank2
    else:
        ordered_ranks = rank2 + rank1

    # Determine if the hand is suited.
    suited = (suit1 == suit2)
    pair = False

    # Determine if the two ranks are connected.
    connected_pairs = set()
    connectivity_string = "23456789TJQK"  # Exclude Ace for now.
    for i in range(len(connectivity_string) - 1):
        pair_tuple = (connectivity_string[i], connectivity_string[i+1])
        connected_pairs.add(pair_tuple)
        connected_pairs.add((connectivity_string[i+1], connectivity_string[i]))
    # Add wheel connectivity: Ace and 2.
    connected_pairs.add(("A", "2"))
    connected_pairs.add(("2", "A"))
    # Add Ace-King connectivity.
    connected_pairs.add(("A", "K"))
    connected_pairs.add(("K", "A"))
    
    if (rank1, rank2) in connected_pairs or (rank2, rank1) in connected_pairs:
        connected = True
    else:
        connected = False

    # Determine the suffix ("s" for suited, "o" for offsuit).
    suffix = "s" if suited else "o"
    classified = ordered_ranks + suffix

    # Look up the estimated equity from the hand_vs_random dictionary via the estimate_equity function.
    estimated_equity = estimate_equity(classified)

    return classified, suited, pair, connected, estimated_equity


def calculate_reward_no_fold(equity1: float, equity2: float, contributions: dict) -> tuple:
    """
    Calculate the reward for two players when neither player folds,
    based on their equity and the contributions made to the pot.
    
    The pot is computed as the sum of the contributions from both players.

    Parameters:
        equity1 (float): The equity (between 0 and 1) for player 1.
        equity2 (float): The equity (between 0 and 1) for player 2.
        contributions (dict): A dictionary with keys "BTN" and "BB" representing the
                              chips each player has contributed to the pot.
    
    Returns:
        tuple: (reward1, reward2) where:
            reward1 = (2 * equity1 - 1) * (contributions["BTN"] + contributions["BB"])
            reward2 = (2 * equity2 - 1) * (contributions["BTN"] + contributions["BB"])
    """
    pot = contributions.get("BTN", 0) + contributions.get("BB", 0)
    reward1 = (2 * equity1 - 1) * pot
    reward2 = (2 * equity2 - 1) * pot
    return reward1, reward2


def calculate_reward_fold(folding_player: str, contributions: dict) -> tuple:
    """
    Calculate the rewards for the fold case.
    
    When a player folds, the reward is based solely on the amount that player committed to the pot.
    The folding player's reward is negative that amount, and their opponent's reward is positive
    that amount.
    
    Parameters:
        folding_player (str): The identifier of the folding player ("BTN" or "BB").
        contributions (dict): A dictionary with keys "BTN" and "BB" mapping to the chips they
                              contributed to the pot.
    
    Returns:
        tuple: (reward_BTN, reward_BB) where:
           - If BTN folds: reward_BTN = -contributions["BTN"] and reward_BB = +contributions["BTN"]
           - If BB folds:  reward_BTN = +contributions["BB"] and reward_BB = -contributions["BB"]
    
    Example:
        - If contributions = {"BTN": 0.5, "BB": 1} and BTN folds,
            then the function returns (-0.5, +0.5).
        - If contributions = {"BTN": 3, "BB": 1} and BB folds,
            then the function returns (+1, -1).
        - If contributions = {"BTN": 3, "BB": 9} and BTN folds,
            then the function returns (-3, +3).
    """
    
    if folding_player not in contributions:
        raise ValueError("Folding player must be 'BTN' or 'BB' with a valid contribution.")
    
    folded_amount = contributions[folding_player]
    
    if folding_player == "BTN":
        reward_BTN = -folded_amount
        reward_BB = folded_amount
    elif folding_player == "BB":
        reward_BTN = folded_amount
        reward_BB = -folded_amount
    else:
        raise ValueError("Invalid folding player; expected 'BTN' or 'BB'.")
        
    return reward_BTN, reward_BB


def update_contributions(contributions, player, amount):
    """
    Update a player's contribution to the pot.
    
    Args:
        contributions (dict): A dictionary mapping player positions ('BTN', 'BB') to their contributions.
        player (str): The player position ('BTN' or 'BB').
        amount (float): The additional amount the player is contributing.
        
    Returns:
        dict: The updated contributions dictionary.
    """
    if player not in contributions:
        contributions[player] = 0
    contributions[player] += amount
    return contributions


def calculate_pot(contributions):
    """
    Calculate the total pot size based on all players' contributions.
    
    Args:
        contributions (dict): A dictionary mapping player positions ('BTN', 'BB') to their contributions.
        
    Returns:
        float: The total pot size.
    """
    return sum(contributions.values())


def calculate_implied_probability(contributions):
    """
    Calculate the implied probability based on player contributions.
    
    The implied probability represents the minimum probability of winning 
    needed to make a call profitable, calculated as 1/(pot_odds_ratio + 1).
    
    Args:
        contributions (dict): A dictionary mapping player positions ('BTN', 'BB') to their contributions.
        
    Returns:
        float: The implied probability (1/(pot_odds_ratio + 1)).
               Returns 0 if there is nothing to call (equal contributions).
    
    Example:
        If contributions = {'BTN': 0.5, 'BB': 1}, then:
        - Pot size is 1.5 (sum of all contributions)
        - Bet to call is 0.5 (difference between contributions)
        - Pot odds ratio is 3 (1.5/0.5)
        - Implied probability is 0.25 (1/(3+1))
    """
    if 'BTN' not in contributions or 'BB' not in contributions:
        raise ValueError("Contributions must include both 'BTN' and 'BB' players")
    
    # Calculate total pot size
    pot_size = contributions['BTN'] + contributions['BB']
    
    # Calculate the bet to call as the absolute difference between contributions
    bet_to_call = abs(contributions['BTN'] - contributions['BB'])
    
    # Handle division by zero (when contributions are equal)
    if bet_to_call == 0:
        return 0  # No call required, implied probability is 0
    
    # Calculate pot odds ratio
    pot_odds_ratio = pot_size / bet_to_call
    
    # Calculate implied probability
    implied_probability = 1 / (pot_odds_ratio + 1)
    
    return implied_probability





def main():
    # Shuffle the deck.
    deck = shuffle_deck()
    
    # Deal four cards to produce two players' hands.
    BTN_hand_basic, BB_hand_basic = deal(deck)
    
    # Print the players' raw hands.
    print("BTN Hand:", BTN_hand_basic)
    print("BB Hand:", BB_hand_basic)
    
    # Classify the hands.
    BTN_classified, BTN_suited, BTN_pair, BTN_connected, BTN_equity_estimate = classify_hand(BTN_hand_basic)
    BB_classified, BB_suited, BB_pair, BB_connected, BB_equity_estimate = classify_hand(BB_hand_basic)
    
    # Print the classified hands.
    print("\nClassified Hands:")
    
    print("BTN Hand:")
    print(f"  Classified: {BTN_classified}")
    print(f"  Suited: {BTN_suited}")
    print(f"  Pair: {BTN_pair}")
    print(f"  Connected: {BTN_connected}")
    print(f"  Equity Estimate (lookup): {BTN_equity_estimate}")
    
    print("BB Hand:")
    print(f"  Classified: {BB_classified}")
    print(f"  Suited: {BB_suited}")
    print(f"  Pair: {BB_pair}")
    print(f"  Connected: {BB_connected}")
    print(f"  Equity Estimate (lookup): {BB_equity_estimate}")
    
    # Calculate the equity using the Node.js equity calculator service.
    try:
        BTN_equity_service, BB_equity_service = calculate_equity(BTN_hand_basic, BB_hand_basic)
    except Exception as e:
        print("Failed to calculate equity:", e)
        return
    
    # Print the service-based equity results.
    print("\nEquity Results (Service):")
    print("BTN Equity:", BTN_equity_service)
    print("BB Equity:", BB_equity_service)

if __name__ == '__main__':
    main()