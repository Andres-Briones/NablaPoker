from decimal import Decimal

class Player:
    def __init__(self, id : int, name: str, seat: int, starting_stack: Decimal = Decimal(100), final_stack: Decimal = None) :
        self.id = id
        self.name = name
        self.starting_stack = starting_stack
        self.final_stack = final_stack
        self.seat = seat

        # For real time game tracking
        self.cards = []
        self.status = 'Active'
        self.stack = starting_stack
        self.bet_amount = Decimal('0.00')
        self.socket = None
        self.mucks = True # By default, the player mucks its cards if possible 
        self.is_all_in = False
        
        # Winnings
        self.win_amount = None 

    def add_chips(self, amount: Decimal) -> None:
        self.stack += amount

    def bet(self, bet: Decimal) -> None: 
        '''Add the bet to bet_amount'''
        self.bet_amount += bet
        self.stack -= bet

    def add_winnings(self, win_amount, cashout_amount : Decimal = 0, cashout_fee : Decimal = 0, bonus_amount : Decimal = 0, contributed_rake : Decimal = 0):
        self.win_amount = win_amount
        self.cashout_amount = cashout_amount
        self.cashout_fee = cashout_fee
        self.bonus_amount = bonus_amount
        self.contributed_rake = contributed_rake

    def reset(self):
        self.cards = []
        self.bet_amount = Decimal('0.00')
        self.win_amount = None 
        self.cashout_amount = None 
        self.cashout_fee = None 
        self.bonus_amount = None 
        self.contributed_rake = None 
        self.is_all_in = False


    def winnings_to_json(self) -> dict:
        return {
	        "win_amount": self.win_amount,
	        "cashout_amount": self.cashout_amount,
	        "cashout_fee": self.cashout_fee,
            "bonus_amount" : self.bonus_amount,
	        "contributed_rake" : self.contributed_rake 
        }


    def to_json(self) -> dict:
        """Return a JSON-compatible dictionary for the player."""
        return {
            "id": self.id,
            "name": self.name,
            "starting_stack": self.starting_stack,
            "final_stack": self.final_stack,
            "seat": self.seat
        }

    def __str__(self):
        return (f"\nPlayer ID: {self.id}\n"
                f"Name: {self.name}\n"
                f"Seat: {self.seat}\n"
                f"Stack: {self.stack}\n"
                f"Status: {self.status}")

