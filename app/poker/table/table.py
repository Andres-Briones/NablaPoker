from typing import List, Dict, Optional, Tuple
from app.utils.poker_utils import find_winners
from datetime import datetime
from decimal import Decimal
from app.poker import  Deck, Card, Player, Action, Pot, Hand, Session, Round
from app.poker.round import  possible_streets
from .circularlinkedlist import CircularLinkedList
import numpy as np
import random

class Table:
    def __init__(self, table_id: int, table_name: str, small_blind: Decimal, big_blind: Decimal, table_size: int, verbose: bool = False):
        self.table_id: int = table_id
        self.table_name: str = table_name
        self.table_size = table_size
        self.small_blind: Decimal = small_blind
        self.big_blind: Decimal = big_blind
        self.players: Dict[int, Player] = {}
        self.available_seats: List[int] = list(range(table_size)) # This list should always be ordered
        self.active_players = CircularLinkedList()
        self.playing_players = None 
        self.board_cards: List[Card] = []
        self.pot: Decimal = Decimal('0.00')
        self.uncalled_amount: Decimal = Decimal('0.00')
        self.current_bet: Decimal = Decimal('0.00')
        self.current_turn: int = None
        self.current_round: Round = None
        self.current_hand: Hand = None
        self.logs: List[str] = []
        self.streets = ["Preflop", "Flop", "Turn", "River", "Showdown"]
        self.deck: Deck = None
        self.verbose = True
        self.dealer_seat =  None
        self.dealer = None
        self.bb_player = None
        self.agressor: int = None #Id of the agressor


    def new_player(self, id: int, name: str, starting_stack: Decimal = Decimal(100)) -> Player:
        try:
            seat = self.available_seats.pop(0)
        except IndexError:
            raise Exception(f"No available seats for player {id}")
        player = Player(id = id,
                        name = name,
                        starting_stack = starting_stack,
                        #starting_stack = Decimal(f"{round(random.random(),1)*2}"),
                        seat = seat)
        self.add_player(player)
        return player


    def add_player(self, player: Player) -> None:
        self.players[player.id] = player


    def remove_player(self, id: int) -> None:
        player = self.players.pop(id, None)
        if player:
            self.available_seats.append(player.seat)
            self.available_seats.sort()


    def get_active_seats(self) -> List: 
        return self.active_players.get_seats()


    def get_player_by_seat(self, seat): # Not only fo active players
        player = next((player for id, player in self.players.items() if player.seat == seat), None)
        if player == None : 
            raise ValueError("No player was found at that seat.")
        return player


    def get_next_player(self, player, skip: Optional[int] = 0) -> Player:
        return self.playing_players.get_next(player.seat, skip)

    def get_next_active_player(self, player, skip: Optional[int] = 0) -> Player:
        return self.active_players.get_next(player.seat, skip)
    
    def get_next_seat(self, seat, return_player = False) : 
        if return_player :
            return self.active_players.get_next(player)
        return self.active_players.get_next(player).seat


    def set_next_turn(self) -> None:
        current_player = self.players[self.current_turn]
        next_player = self.get_next_player(current_player)
        return next_player.id


    def get_current_player(self) -> Player:
        return self.players.get(self.current_turn, None)


    def is_player_turn(self, id: int) -> bool:
        return self.current_turn == id


    def set_bet(self, bet: Decimal) -> None:
        player = self.get_current_player() 
        player.bet(bet)
        self.pot += bet


    def deal_community_cards(self, number: int) -> List[Card]:
        cards = self.deck.draw(number)
        self.board_cards.extend(cards)
        self.current_round.set_community_cards([str(card) for card in cards])
        return cards


    def deal_hole_cards(self) -> List[Card]:
        ''' Deal two cards the the current player '''
        player = self.get_current_player()
        cards = self.deck.draw(2)
        player.cards = cards
        return cards


    def get_used_seats(self) -> List[int]:
        used_seats = []
        for player in self.players.values() :
            used_seats.append(player.seat)
        return used_seats


    def get_current_street(self) -> str:
        street = None
        if self.current_round is not None:
            street = self.current_round.street
        return street


    def start_new_game(self) -> None:

        if self.current_hand is not None:
            raise Exception("Finish the hand before starting a new one")

        self.logs = []
        # Reset the game state for all players (Not only the active ones)
        # Add active players to the players list
        self.active_players = CircularLinkedList()
        for player in self.players.values():
            player.reset()
            if player.status == 'Active':
                self.active_players.append(position = player.seat, data = player)

        if self.verbose:
            print("Players in game: ")
            print(self.active_players)
                
        # If there aren't enough players to start a game, raise an exception
        if len(self.active_players) < 2:
            raise Exception("Not enough players to start a game")

        self.deck = Deck()  # Reset and shuffle the deck
        self.board_cards = []
        self.pot = Decimal('0.00')
        self.current_bet = Decimal('0.00')
        self.streets = ["Preflop", "Flop", "Turn", "River", "Showdown"]
        self.current_round = Round(round_id = 0, street = self.streets.pop(0))
        self.playing_players = self.active_players.copy()

        #Reset the starting_stack of the players to their current stack
        for player in self.active_players:
            player.starting_stack = player.stack

        # If there isn't a dealer, set the dearler randomly
        if self.dealer_seat is None:
            self.dealer = random.choice(self.active_players.to_list())
            self.dealer_seat = self.dealer.seat
        else : # Set the next active player as the dealer
            self.dealer = self.get_next_player(self.dealer)
            self.dealer_seat = self.dealer.seat

        if self.verbose : print(f"{self.dealer.name} is the dealer")

        # Deal cards to all active players startin by the small_blind
        self.current_turn = self.get_next_player(self.dealer).id # Set the next turn to the SB 

        # Deal cards
        for _ in range(len(self.active_players)):
            self.action("Dealt Cards")

        if len(self.active_players) == 2:
            self.current_turn = self.dealer.id # Set the next turn to the Dealer
            self.bb_player = self.get_next_player(self.dealer)
        else:
            self.current_turn = self.get_next_player(self.dealer).id # Set the next turn to the SB 
            self.bb_player = self.get_next_player(self.dealer, skip = 1)

        # Post the blinds 
        self.action("Post SB")
        self.action("Post BB")

        self.current_hand = Hand(
            game_number = int(datetime.now().strftime('%Y%m%d%H%M%S')+ 6*'0') + self.table_id,
            table_name=self.table_name,
            table_size=len(self.players),
            dealer_seat=self.dealer_seat,
            small_blind_amount=self.small_blind,
            big_blind_amount=self.big_blind)


    def give_back_uncalled_amount(self) -> None:
        if self.uncalled_amount != Decimal('0.00') : 
            agressor = self.players[self.agressor]
            agressor.stack += self.uncalled_amount
            self.pot -= self.uncalled_amount
            self.logs.append(f"The uncalled amount of {self.uncalled_amount/self.big_blind} BB went back to {agressor.name}")
            self.uncalled_amount = Decimal('0.00')


    def next_round(self) -> None:
        # Add previous round to the current hand
        self.current_hand.add_round(self.current_round)

        # Reset bets 
        self.current_bet = Decimal('0.00')
        for player in self.active_players:
            player.bet_amount = Decimal('0.00')

        # Create new round
        street = self.streets.pop(0) 
        self.current_round = Round(round_id = len(self.current_hand.rounds), street = street)

        if street == "Showdown":
            self.end_game()
        else: 
            if len(self.playing_players) != 0 : 
                self.agressor = self.get_next_player(self.dealer).id
                self.current_turn = self.get_next_player(self.dealer).id

            if street == "Flop":
                num_cards = 3
            else :
                num_cards = 1
            self.deal_community_cards(num_cards)

        if self.verbose:
            print(f"---------- {street} ----------")
            print(f"Board : {self.board_cards}")
            print(f"Pot: {self.pot}")
            current_player = None if self.current_turn is None else self.players[self.current_turn].name
            print(f"Current turn: {current_player}")

        # Check if all players (or except one) are all-in, in that case go to next round and repeat until showdown
        if self.current_hand :
            if len(self.playing_players) <= 1 :
                self.next_round()


    def check_if_all_in(self, total_bet:Decimal) -> bool :
        player = self.get_current_player()
        max_bet = player.stack + player.bet_amount
        if total_bet >= max_bet:
            return True, max_bet
        return False, total_bet 


    def action(self, action_type:str, amount: Optional[Decimal] = Decimal('0.00')) -> None:
        player = self.get_current_player()

        all_in = False

        new_action = Action(
            action_id = len(self.current_round.actions),
            player_id = player.id, 
            action_type = action_type)

        match action_type:
            case "Dealt Cards" : #Player is dealt cards.
                cards = self.deal_hole_cards()
                new_action.cards = cards
            case "Mucks Cards" : #The player mucks/doesn't show their cards.
                player.mucks = True
            case "Shows Cards" : #The player shows their cards. Should be included in a "Showdown" round.
                player.mucks = False
            case "Post Ante" : #The player posts an ante.
                self.set_bet(amount)
            case "Post SB" : #The player posts the small blind.
                amount = self.small_blind
                all_in, amount = self.check_if_all_in(amount)
                self.set_bet(amount)
                self.current_bet = amount
            case "Post BB" : #The player posts the big blind.
                amount = self.big_blind
                all_in, amount = self.check_if_all_in(amount)
                self.set_bet(amount)
                self.current_bet = amount
                self.agressor = player.id
                self.uncalled_amount = amount
            case "Fold" : #The player folds their cards.
                self.active_players.remove(player.seat)
                self.playing_players.remove(player.seat)
            case "Check" : #The player checks.
                if self.current_bet != Decimal('0.00'):
                    if player.id != self.bb_player.id or self.current_bet != self.big_blind:
                        raise Exception("The player can't check because the current bet is not zero")
            case "Bet" : #The player bets in an un-bet/unraised pot.
                if self.current_bet != Decimal('0.00'):
                    raise Exception("The player can't bet because the current bet is not zero")
                all_in, amount = self.check_if_all_in(amount)
                self.set_bet(amount)
                self.current_bet = amount
                self.agressor = player.id
                self.uncalled_amount = amount
            case "Raise" : #The player makes a raise.
                if self.current_bet == Decimal('0.00'):
                    raise Exception("The player can't raise because the current bet is zero")
                total_raise = player.bet_amount + amount
                all_in, total_raise = self.check_if_all_in(total_raise)
                amount = total_raise - player.bet_amount
                if total_raise < self.current_bet + self.small_blind :
                    raise Exception("The total raised amount should be greater or equal to the previous raise plus the small blind")
                self.set_bet(amount)
                self.uncalled_amount = total_raise - self.current_bet
                self.current_bet = total_raise
                self.agressor = player.id
            case "Call" : #The player calls a bet/raise.
                if self.current_bet == Decimal('0.00'):
                    raise Exception("The player can't call because the current bet is zero")
                if self.current_bet == player.bet_amount: # Can happen when the player is BB and everyone fold or call preflop
                    raise Exception("Calling here is useless because the player bet is equal the the maximum bet")
                all_in, total_bet = self.check_if_all_in(self.current_bet)
                amount = total_bet - player.bet_amount # amount added for call
                self.set_bet(amount)
                if all_in :
                    if total_bet >= self.current_bet - self.uncalled_amount:
                        self.uncalled_amount = self.current_bet - total_bet
                else :
                    self.uncalled_amount = Decimal("0.00")

        if all_in :
            new_action.is_all_in = True
            player.is_all_in =  True
            self.playing_players.remove(player.seat)

        new_action.amount = amount
        self.current_round.add_action(new_action)

        agressor_player = self.players.get(self.agressor,None)

        if len(self.active_players) == 1:
            self.end_game()
            return

        if len(self.playing_players) == 0 :
            self.next_round()
            return

        next_player = self.get_next_player(player)
        next_active_player= self.get_next_active_player(player)

        if self.verbose:
            string = f"\n{player.name} : {action_type}"
            if amount > 0: string += f" {amount}"
            if action_type == "Dealt Cards":  string += f" {player.cards}"
            print(string)
            print("Current bet :", self.current_bet)
            print("Agressor :", agressor_player.name if agressor_player else None)
            print("Uncalled amount :", self.uncalled_amount)

        if action_type in ["Dealt Cards", "Post SB", "Post BB"]: 
            self.current_turn = next_player.id
            return
        
        if next_active_player.is_all_in and next_active_player.id == self.agressor:
            self.next_round()
            return

        if self.current_round.street == "Preflop":
            if next_player.id == self.agressor:
                if next_player.id == self.bb_player.id and self.current_bet == self.big_blind: 
                    self.current_turn= next_player.id
                else:
                    self.next_round()
            elif player.id == self.agressor and player.id == self.bb_player.id and action_type not in ["Raise"]:
                self.next_round()
            else : 
                self.current_turn = next_player.id
            return

        # For post flop actions
        if next_player.id == self.agressor:
            self.next_round()
        else : 
            self.current_turn = next_player.id

        return

    def set_winnings(self) -> None:
        # Calculate total bets for each player (starting_stack - current_stack)
        total_bets = {
            player: player.starting_stack - player.stack 
            for player in self.active_players
        }
        # Sort by bet amount in ascending order
        sorted_bets = dict(sorted(total_bets.items(), key=lambda x: x[1]))

        if self.verbose:
            print("\nTotal bets:")
            for player, amount in sorted_bets.items():
                print(f"{player.name}: {amount}")

        # Create pots based on bet levels
        current_pot_number = 1
        previous_bet_level = Decimal('0.00')
        
        for player, bet_amount in sorted_bets.items():
            if bet_amount > previous_bet_level:
                # Create new pot for this bet level
                pot_amount = Decimal('0.00')
                eligible_players = []
                
                # Calculate pot size and eligible players
                for p, total_bet in sorted_bets.items():
                    if total_bet >= bet_amount:
                        pot_amount += bet_amount - previous_bet_level
                        eligible_players.append(p)
                
                if pot_amount > Decimal('0.00'):
                    pot = Pot(
                        pot_number=current_pot_number,
                        amount=pot_amount
                    )
                    
                    if len(eligible_players) == 1:
                        # Only one eligible player, they win this pot
                        winner = eligible_players[0]
                        winner.mucks = False
                        winner.stack += pot_amount
                        winner.add_winnings(win_amount=pot_amount)
                        pot.add_player(winner)
                        self.logs.append(f"{winner.name} won {pot_amount/self.big_blind} BB")
                    else:
                        # Find winners among eligible players
                        eligible_hands = {
                            p: p.cards for p in eligible_players
                        }
                        winners_hands = find_winners(eligible_hands, self.board_cards)
                        portion = pot_amount / len(winners_hands)
                        
                        for winner, hand_name in winners_hands:
                            winner.mucks = False
                            winner.stack += portion
                            winner.add_winnings(win_amount=portion)
                            pot.add_player(winner)
                            self.logs.append(f"{winner.name} won {portion/self.big_blind} BB with {hand_name}")
                    
                    self.current_hand.add_pot(pot)
                    current_pot_number += 1
                
                previous_bet_level = bet_amount

    def end_game(self) -> None:
        # Give back the uncalled amount
        self.give_back_uncalled_amount()

        # Set winnings
        self.set_winnings()

        # Reset bets
        self.current_bet = Decimal('0.00')
        for player in self.active_players:
            player.bet_amount = Decimal('0.00')
        self.current_turn = None
        self.current_round = None

        # Reset the current_hand and active_players
        self.current_hand = None
        self.active_players = CircularLinkedList()
        self.playing_players = None 

        # Set to uncactive the players for which their stack is 0: 
        for player in self.players.values():
            if player.stack == 0 :
                player.status = "Unactive"


    def get_display_data(self, player_id:int):
        this_player = self.players[player_id]

        general_data = {
            "id" : self.table_id,
            "table_name": self.table_name,
            "small_blind_amount": self.small_blind,
            "big_blind_amount": self.big_blind 
        }

        current_player = self.get_current_player()
        gamestate = {
            "pot" : self.pot / self.big_blind,
            "board_cards": self.board_cards,
            "street": self.get_current_street(),
            "final_pots": None,
            "dealer_seat": self.dealer_seat,
            "player_turn": current_player.id == player_id if current_player else None,
            "current_turn_name": current_player.name if current_player else None,
            "can_bet": self.current_bet == Decimal('0.00'),
            "can_check": self.current_bet == Decimal('0.00') or self.agressor == current_player.id,
            "logs": self.logs,
        }

        used_seats = self.get_used_seats()

        players = []
        for player in self.players.values():
            player_info = {
                "name": player.name,
                "id": player.id,
                "status": player.status,
                "seat": player.seat,
                "chips": player.stack / self.big_blind,
                "bet": player.bet_amount / self.big_blind
            }
            player_info["dealer"] = player.seat == gamestate["dealer_seat"]
            # To position of the player shouldn't be player["seat"] but the index of player in the list of used seats minus this player seat
            seat_index = used_seats.index(player.seat)
            this_player_seat_index = used_seats.index(this_player.seat)
            player_info["angle"] = np.pi * (2*(seat_index - this_player_seat_index)/len(self.players) + 1/2) # Angle in radians for the position of the player on the table
            # Add cards
            if player.cards:
                if player_id == player.id or player.mucks == False:
                    player_info["cards"] = [str(card) for card in player.cards]
                else : 
                    player_info["cards"] = ['back', 'back']
            else: 
                player_info["cards"] = []

            players.append(player_info)

        gamestate["players"] = players

        return general_data, gamestate

