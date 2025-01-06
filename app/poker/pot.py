from decimal import Decimal
from typing import List
from .player import Player

class Pot:
    def __init__(self, pot_number: int, amount: Decimal, rake: Decimal = Decimal('0.00'), jackpot: Decimal = Decimal('0.00')):
        self.pot_number = pot_number
        self.amount = amount
        self.rake = rake
        self.jackpot = jackpot
        self.players: List[Player] = []

    def add_player(self, player: Player):
        self.players.append(player)

    def to_json(self) -> dict:
        """Return a JSON-compatible dictionary for the hand, using session info for context."""
        return {
            "pot_number": self.pot_number,
            "amount": str(self.amount),
            "rake": str(self.rake),
            "jackpot": str(self.jackpot),
            "players_wins": [player.winnings_to_json() for player in self.players]
        }
