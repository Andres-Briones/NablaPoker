def cards_string_to_list(string): #When cards are given as "AcKs" for example
    if len(string)%2 == 1 :
        raise ValueError("Invalid length of string")
    return [string[i:i+2] for i in range(0, len(string), 2)]

class Card:
    def __init__(self, value, suit):
        self.value = value
        self.suit = suit

    def __repr__(self):
        return f"{self.value}{self.suit}"

