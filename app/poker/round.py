from typing import List
from .action import Action

possible_streets = ["Preflop", "Flop", "Turn", "River", "Showdown"]

class Round:
    def __init__(self, round_id: int, street: str):
        if street not in possible_streets:
            raise ValueError("Incorrect street")

        self.round_id = round_id 
        self.street = street
        self.actions: List[Action] = []
        self.cards: List[str] = []

    def add_action(self, action: Action):
        """Add an Action object to the round."""
        self.actions.append(action)

    def set_community_cards(self, cards: List[str]):
        """Set community cards for the round."""
        self.cards = cards

    def to_json(self) -> dict:
        """Return a JSON-compatible dictionary for the round."""
        return {
            "id": self.round_id,
            "street": self.street,
            "actions": [action.to_json() for action in self.actions],
            "cards": self.cards
        }
