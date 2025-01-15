from phevaluator import evaluate_cards
from typing import List, Dict, Tuple
from app.poker.card import Card
from app.poker.player import Player

def get_hand_name(score: int) -> str:
    if score > 6185:
        return "High Card"
    elif score > 3325:
        return "One Pair"
    elif score > 2467:
        return "Two Pair"
    elif score > 1609:
        return "Three of a Kind"
    elif score > 1599:
        return "Straight"
    elif score > 322:
        return "Flush"
    elif score > 166:
        return "Full House"
    elif score > 10:
        return "Four of a Kind"
    elif score > 1:
        return "Straight Flush"
    else:
        return "Royal Flush"


def evaluate_hand(hole_cards: List[Card], board_cards: List[Card]) -> Tuple[int, str]:
    all_cards = [str(card) for card in hole_cards + board_cards]
    hand_rank = evaluate_cards(*all_cards)
    hand_name = get_hand_name(hand_rank)
    return hand_rank, hand_name

def find_winners(players_cards: Dict[Player, List[Card]], board_cards: List[Card]) -> List[Tuple[Player, str]]:
    best_rank = 6185
    winners = []
    for player, hole_cards in players_cards.items():
        hand_rank, hand_rank_str = evaluate_hand(hole_cards, board_cards)
        if hand_rank < best_rank:
            best_rank = hand_rank
            winners = [(player, hand_rank_str)]
        elif hand_rank == best_rank:
            winners.append((player, hand_rank_str))
    return winners

def cardsListToString(cards):
    return " ".join([getCardSymbol(card) for card in cards])


RANK_ORDER = "23456789TJQKA" 
def cardsToClass(cards):
    cards = cards.split (' ')

    rank1 = cards[0][0]
    rank2 = cards[1][0]

    if RANK_ORDER.index(rank1) >= RANK_ORDER.index(rank2):
        handClass = rank1 + rank2
    else :
        handClass = rank2 + rank1

    if cards[0][1] == cards[1][1] :
        handClass += 's'
    elif cards[0][0] != cards[1][0] :
        handClass += 'o'

    return handClass

def getCardSymbol(card):
    suitSymbols = {
        'h': '♥', 
        's': '♠', 
        'd': '♦', 
        'c': '♣'  
    }
    return card[0]+ suitSymbols[card[1]]
