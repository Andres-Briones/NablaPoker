from decimal import Decimal

possible_actions = [
            "Dealt Cards", #Player is dealt cards.
            "Mucks Cards", #The player mucks/doesn't show their cards.
            "Shows Cards", #The player shows their cards. Should be included in a "Showdown" round.
            "Post Ante", #The player posts an ante.
            "Post SB", #The player posts the small blind.
            "Post BB", #The player posts the big blind.
            "Straddle", #The player posts a straddle to buy the button.
            "Post Dead", #The player posts a dead blind.
            "Post Extra Blind", #The player posts any other type of blind.
            "Fold", #The player folds their cards.
            "Check", #The player checks.
            "Bet", #The player bets in an un-bet/unraised pot.
            "Raise", #The player makes a raise.
            "Call", #The player calls a bet/raise.
            "Added Chips", #Player adds chips to his chip stack (cash game only).
            "Sits Down", #Player sits down at a seat.
            "Stands Up", #Player removes them self from the table.
            "Add to Pot",  #This can be a player or non-player action.  Can be used when the site adds money/chips to the pot to stimulate action, for example.
]

class Action:
    def __init__(self, action_id, player_id: int, action_type: str, amount: Decimal = 0, is_all_in: bool = False, cards : list = None):
        self.action_id = action_id# Starts at 0 for each new round
        self.player_id = player_id
        self.action_type = action_type
        self.amount = amount
        self.is_all_in = is_all_in
        self.cards = cards

        if action_type not in possible_actions:
            raise ValueError("Incorrect action_type")

    def add_cards(self, cards): # Used for Dealt Cards action_type
        if type(cards) == str: cards = cards_string_to_list(cards)
        self.cards = cards

    def to_json(self) -> dict:
        """Return a JSON-compatible dictionary for the action."""
        output = {"action_id": self.action_id,
                   "player_id": self.player_id,
                   "action": self.action_type}
        if float(self.amount) > 0 : output["amount"] = self.amount
        if self.is_all_in : output["is_allin"]: True
        if self.cards is not None: output["cards"] = self.cards

        return output

