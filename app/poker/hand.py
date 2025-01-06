from decimal import Decimal
from typing import List, Optional
from .round import Round
from .pot import Pot

class Hand:
    def __init__(self,
                 game_number : Optional[int] = None,
                 table_name: Optional[str] = None,
                 table_size: Optional[int] = None,
                 dealer_seat: Optional[int] = None, 
                 small_blind_amount: Optional[Decimal] = None,
                 big_blind_amount: Optional[Decimal] = None,
                 ante_amount: Optional[Decimal] = None,
                 start_date_utc: Optional[str] = None,
                 hero_player_id: Optional[int] = None):

        self.table_name = table_name
        self.table_size = table_size
        self.tournament = False # Not supported yet
        self.game_type ="Holdem" # Only game_type supported for now
        self.bet_limit: {"bet_type": "NL", "bet_cap": 0} # Only supported limits for now
        self.game_number = game_number
        self.start_date_utc = start_date_utc
        self.dealer_seat = dealer_seat
        self.hero_player_id = None
        self.small_blind_amount = small_blind_amount
        self.big_blind_amount = big_blind_amount
        self.ante_amount = ante_amount
        self.flags = []
        self.players = []
        self.rounds: List[Round] = []
        self.pots: List[Pot] = []

    def add_round(self, round_: Round):
        """Add a Round object to the hand."""
        self.rounds.append(round_)

    def add_player(self, player_data: dict):
        """Add player information to the hand."""
        self.players.append(player_data)

    def add_pot(self, pot_: Pot):
        """Set pot information for the hand."""
        self.pots.append(pot_)

    def to_json(self, session) -> dict:
        """Return a JSON-compatible dictionary for the hand, using session info for context."""
        if self.small_blind_amount % 1 == 0 :
            Decimal = lambda x: str(int(x)) 
        return { "ohh" :
                {
                    "spec_version": session.spec_version,
                    "site_name": session.site_name,
                    "network_name": session.network_name,
                    "internal_version": session.internal_version,
                    "tournament": self.tournament, # Not supported yet
                    "game_number": self.game_number,
                    "start_date_utc": self.start_date_utc,
                    "table_name": self.table_name,
                    "table_size": self.table_size,
                    "game_type" : self.game_type,
                    "hero_player_id": self.hero_player_id,
                    "small_blind_amount" : self.small_blind_amount,
                    "big_blind_amount" : self.big_blind_amount,
                    "ante_amount" : self.ante_amount,
                    "flags": self.flags,
                    "players": [player_.to_json() for player_ in self.players],
                    "rounds": [round_.to_json() for round_ in self.rounds],
                    "pots" : [pot_.to_json() for pot_ in self.pots]
                 }
                }
