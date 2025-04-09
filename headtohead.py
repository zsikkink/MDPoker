import itertools
from treys import Card, Evaluator, Deck

def main():
    # Set up the players' hole cards:
    # Player 1: Ace of Diamonds and King of Diamonds
    # Player 2: Queen of Diamonds and Jack of Diamonds
    p1_cards = [Card.new('Jh'), Card.new('Js')]
    p2_cards = [Card.new('Qd'), Card.new('Jd')]

    # Get a full deck from treys and remove the 4 hole cards.
    full_deck = Deck.GetFullDeck()
    cards_to_remove = set(p1_cards + p2_cards)
    remaining_deck = [card for card in full_deck if card not in cards_to_remove]

    print("Remaining deck count:", len(remaining_deck))
    # Confirm that we have 48 cards left.
    assert len(remaining_deck) == 48, "Unexpected deck size after removing hole cards."

    # Initialize evaluator
    evaluator = Evaluator()

    # Counters for win/tie tally
    win1 = 0
    win2 = 0
    tie = 0
    total = 0

    # Iterate over all 5-card combinations from the remaining deck
    for board in itertools.combinations(remaining_deck, 5):
        total += 1
        board_list = list(board)  # Convert tuple to list for the evaluator

        # Evaluate the hands.
        score1 = evaluator.evaluate(p1_cards, board_list)
        score2 = evaluator.evaluate(p2_cards, board_list)

        # Lower score is better.
        if score1 < score2:
            win1 += 1
        elif score2 < score1:
            win2 += 1
        else:
            tie += 1

    # Calculate percentages.
    win1_percent = win1 / total * 100
    win2_percent = win2 / total * 100
    tie_percent = tie / total * 100

    # Display the results.
    print("Total boards evaluated:", total)
    print("Player 1 wins: {} ({:.4f}%)".format(win1, win1_percent))
    print("Player 2 wins: {} ({:.4f}%)".format(win2, win2_percent))
    print("Ties: {} ({:.4f}%)".format(tie, tie_percent))

if __name__ == '__main__':
    main()