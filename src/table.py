class Table:
    def __init__(self, num_players, hero_seat, player_ids, starting_stacks):
        self.num_players = num_players
        self.hero_seat = hero_seat
        self.player_ids = player_ids
        self.starting_stacks = starting_stacks
        self.pot_size = 1.5  # Initial pot size
        self.seats = self.initialize_seats()

    def initialize_seats(self):
        # Define the seat names
        seat_names = ['UTG', 'UTG+1', 'UTG+2', 'LJ', 'HJ', 'CO', 'BTN', 'SB', 'BB']
        
        # Initialize all seats as occupied with player IDs and starting stacks
        seats = {seat: {'player_id': player_id, 'stack': stack} for seat, player_id, stack in zip(seat_names, self.player_ids, self.starting_stacks)}
        
        # Remove the lowest numbered seats if there are fewer than 9 players
        if self.num_players < 9:
            seats_to_remove = 9 - self.num_players
            for i in range(seats_to_remove):
                seat_to_remove = seat_names[i]
                seats[seat_to_remove] = None
        
        return seats

    def get_seats(self):
        return self.seats

    def player_folds(self, seat_name):
        if seat_name in self.seats:
            self.seats[seat_name] = None
        else:
            raise ValueError(f"Invalid seat name: {seat_name}")

    def get_hero_seat(self):
        return self.hero_seat

    def add_to_pot(self, amount):
        self.pot_size += amount

    def get_pot_size(self):
        return self.pot_size

# Example usage
if __name__ == "__main__":
    num_players = 6
    hero_seat = 'HJ'
    player_ids = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', None, None, None]
    starting_stacks = [100, 80, 120, 90, 110, 95, None, None, None]
    table = Table(num_players, hero_seat, player_ids, starting_stacks)
    seats = table.get_seats()
    print("Seats before fold:", seats)
    print("Hero is sitting at:", table.get_hero_seat())
    print("Initial pot size:", table.get_pot_size())
    
    # Simulate a player folding
    table.player_folds('HJ')
    seats = table.get_seats()
    print("Seats after fold:", seats)
    print("Hero is sitting at:", table.get_hero_seat())
    
    # Simulate adding to the pot
    table.add_to_pot(10)
    print("Pot size after adding:", table.get_pot_size())