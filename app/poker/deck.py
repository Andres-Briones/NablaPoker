import random
from .card import Card

class Deck:
    def __init__(self):
        suits = ['c', 'd', 'h', 's']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
        self.cards = [Card(value, suit) for suit in suits for value in values]
        random.shuffle(self.cards)

    def draw(self, num=1):
        return [self.cards.pop() for _ in range(num)]
