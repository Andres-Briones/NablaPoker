from collections import defaultdict
import numpy as np
from datetime import datetime
from app.utils.poker_utils import cardsToClass, getCardSymbol, cardsListToString


def parse_hand_at_upload(ohh_obj):
    #Extract general info necessary for hand insertion in table
    ohh_data = ohh_obj["ohh"]
    hero_id = ohh_data.get("hero_player_id")
    game_number = ohh_data["game_number"]
    date_time = datetime.strptime(ohh_data["start_date_utc"], "%Y-%m-%dT%H:%M:%SZ")
    date_time = date_time.strftime("%Y-%m-%d %H:%M:%S")
    table_size = ohh_data["table_size"]
    flop = False # Stores if there is a flop in the hand or not

    # Set players_hands_data to None if anonymous game
    # If players_hands_data is None, the hand will be skipped
    if "Anonymous" in ohh_data.get("flags",[]):
        return {"game_number": game_number}, None 

    # Extract players and rounds
    players = ohh_data['players']
    rounds = ohh_data['rounds']
    pots = ohh_data['pots']

    # Map player IDs to names for easy reference
    id_to_name = {p['id']: p['name'] for p in players}

    hero_name = id_to_name.get(hero_id, None)
    observed = True if hero_name is None else False

    # Extract dealer seat
    dealer_seat = ohh_data["dealer_seat"]

    # Extraact players profits and seat 
    player_profit = {}
    player_seat = {}

    for player in players :
        win_amount = float(player.get("final_stack", 0)) - float(player["starting_stack"])
        name = player["name"]
        player_profit[name] = '%g' % win_amount
        player_seat[name] = player["seat"]




    # Generate dict to store statistical data for each player 
    # IMPORTANT : players_hands_dics need to have the same  keys as the row names in players_hands table
    players_hands_data = defaultdict(lambda:
                             {"cards": None,
                              "hand_class": None,
                              "position": 0,
                              "position_name": None,
                              "profit": 0,
                              "rake" : 0,
                              "participed" : 0,
                              "vpip": 0,
                              "pfr": 0,
                              "two_bet_possibility": 0,
                              "limp" : 0,
                              "two_bet": 0,
                              "three_bet_possibility": 0,
                              "three_bet": 0,
                              "aggressive" : 0,
                              "passive" : 0 
                              })
            
    # Track preflop participation and actions for each player in the hand
    game_participation = set()

    preflop_participation = set()
    preflop_raisers = set()

    player_cards = {}
    BB_player = None
    
    for round_data in rounds:
        street = round_data['street']
        actions = round_data['actions']

        raise_counter = 1 # We start after BB
        for action in actions:
            player_id = action.get("player_id")
            player_name = id_to_name.get(player_id)
            action_type = action.get("action")
            game_participation.add(player_name)

            if street == "Preflop":
                if action_type == "Post BB":
                    BB_player = player_name

                # VPIP: Any call or raise action before the flop
                if action_type in ["Call", "Raise"]:
                    preflop_participation.add(player_name)

                if action_type in ["Call", "Raise", "Fold", "Check"]:
                    if raise_counter == 1: # First bet round
                        players_hands_data[player_name]["two_bet_possibility"] = 1
                        if action_type == "Raise":
                            players_hands_data[player_name]["two_bet"] = 1
                        elif action_type == "Call":
                            players_hands_data[player_name]["limp"] = 1
                    elif raise_counter == 2: # Second bet round
                        players_hands_data[player_name]["three_bet_possibility"] = 1
                        if action_type == "Raise":
                            players_hands_data[player_name]["three_bet"] = 1

                #PFR : Preflop first raises or 3-bet, 4-bet, etc
                if action_type == "Raise":
                    raise_counter += 1
                    preflop_raisers.add(player_name) 

            else :
                flop = True
                if action_type in ["Bet", "Raise"]:
                    players_hands_data[player_name]["aggressive"] += 1
                elif  action_type == "Call" :
                    players_hands_data[player_name]["passive"] += 1


            if action.get("cards", 0) : # action containes cards an they are not empty
                player_cards[player_name] = cardsListToString(action.get("cards"))

    number_players = len(game_participation)

    # Generate seats_list for players that participated
    seats_list = []
    for name in game_participation:
        seats_list.append(player_seat[name])
    # We get a position from 0 to 6
    position_list = (np.array(seats_list) - dealer_seat -1)% table_size
    # We transform the position from 0 to 6 to 0 to number_players. 0 is SB and the highest is BU
    real_position_list = np.argsort(np.argsort(position_list))
    seat_to_position = {seat:int(real_position_list[i]) for i, seat in enumerate(seats_list) }

    position_to_name = {
        (0,2):"SB", (1,2):"BB",
        (0,3):"SB", (1,3):"BB", (2,3):"BU",
        (0,4):"SB", (1,4):"BB", (2,4):"CO", (3,4):"BU",
        (0,5):"SB", (1,5):"BB", (2,5):"HJ", (3,5):"CO", (4,5):"BU",
        (0,6):"SB", (1,6):"BB", (2,6):"MP", (3,6):"HJ", (4,6):"CO", (5,6):"BU"
    }


    for name in game_participation :
        # Generate input for player in players_hands_data if player is not observer 
        players_hands_data[name]["participed"] = 1 
        # positon =  (seat - dealer_seat - 1)% table_size 
        position = seat_to_position[player_seat[name]]
        players_hands_data[name]["position"] = position
        players_hands_data[name]["position_name"] = position_to_name[(position,number_players)]
        players_hands_data[name]["profit"] = player_profit[name]
        if name in player_cards :
            cards = player_cards[name]
            players_hands_data[name]["cards"] = cards
            players_hands_data[name]["hand_class"] = cardsToClass(cards)

    if preflop_participation:
        for name in preflop_participation : players_hands_data[name]["vpip"] = 1
    else :
        players_hands_data[BB_player]["participed"] = 0 # If everyone folds, BB wins but doesn't take any decision in the game
    for name in preflop_raisers : players_hands_data[name]["pfr"] = 1

    #Extract contributed rake
    for pot in pots :
        for pw in pot['player_wins']:
            name = id_to_name[pw['player_id']]
            new_rake = float(players_hands_data[name]["rake"]) + float(pw['contributed_rake'])
            players_hands_data[name]["rake"] = '%g' % new_rake 

    players_hands_data = dict(players_hands_data) #Use dict in order to transform the defaultdic object

    # Generate dic for hands data
    # IMPORTANT : this dic need to have exactly the same keys as the row names in hands table
    hands_data = {
        "game_number" : game_number,
        "date_time" : date_time,
        "table_size" : table_size,
        "number_players" : number_players,
        "hero_name" : hero_name,
        "hero_position" : None, 
        "hero_position" : None,
        "hero_profit" : None,
        "table_name" : ohh_data["table_name"],
        "small_blind_amount" : ohh_data["small_blind_amount"],
        "big_blind_amount" : ohh_data["big_blind_amount"],
        "site_name" : ohh_data["site_name"],
        "observed" : observed,
        "flop" : flop,
        "players" : ", ".join(game_participation)
        }
    if not observed: # Redundant data but it makes some queries faster
        hands_data["hero_position"] = players_hands_data[hero_name]["position_name"]
        hands_data["hero_cards"] = players_hands_data[hero_name]["cards"]
        hands_data["hero_hand_class"] = players_hands_data[hero_name]["hand_class"]
        hands_data["hero_profit"] = players_hands_data[hero_name]["profit"]

    return hands_data, players_hands_data

def get_data_for_replayer(hand_data, amount_in_BB = True):
    if "ohh" not in hand_data:
        print("Error", "Invalid hand data format. Missing 'ohh' key")
        return {}

    ohh_data = hand_data["ohh"]
    
    # Map player IDs to names for easy reference

    players = {player["id"]: player for player in ohh_data["players"]}
    name_to_seat = {player["name"]:player["seat"] for player in ohh_data["players"]}
    hero_id = ohh_data.get("hero_player_id", None) 
    observed = True if hero_id is None else False
    hero_cards = ""

    hero_seat = players.get(hero_id, 0)["seat"]

    general_data = {
        "table_name": ohh_data["table_name"],
        "small_blind_amount": float(ohh_data["small_blind_amount"]),
        "big_blind_amount": float(ohh_data["big_blind_amount"]),
    }

    action_snapshot = {
        "players": [],
        "pot" : 0.00,
        "action": "",
        "board_cards": [],
        "street": "Preflop",
        "final_pots": None
        }

    id_to_index= {} # Dictionary to get the index of the player corresponding to the given id
    for index, player in enumerate(ohh_data["players"]):
        player_info = {
            "name": player["name"],
            "seat": player["seat"],
            "cards": [],
            "status": "Active",
            "chips": float(player["starting_stack"])/general_data["big_blind_amount"] if amount_in_BB else float(player["starting_stack"]),
            "bet" : 0.00,
            "dealer": player["seat"] == ohh_data["dealer_seat"],
            "angle": np.pi* (2*(player["seat"]-hero_seat)/len(ohh_data["players"]) + 1/2)
            }
        action_snapshot["players"].append(player_info)
        id_to_index[player['id']] = index 

    game_states = []
    need_to_deal_cards = False
    action_amount = 0

    states_to_pop = []

    for round_info in ohh_data["rounds"]:

        # If the street changes
        if action_snapshot["street"] != round_info["street"]:
            # Change the name of the street
            action_snapshot["street"] = round_info["street"]
            # For each player
            for player in action_snapshot["players"]:
                # Reset its bet to 0 
                player["bet"] = 0

            # Add cards to the board
            if "cards" in round_info:
                action_snapshot["board_cards"] += round_info["cards"] 
                action_snapshot["action"] = "New card(s)"

            if action_snapshot["street"] != "Showdown" :
                game_states.append(action_snapshot)

            #Copy action_snapshot for next action
            players = []
            for player in action_snapshot["players"]:
                players.append(player.copy())
            board_cards = action_snapshot["board_cards"].copy()
            action_snapshot = action_snapshot.copy()
            action_snapshot["players"] = players
            action_snapshot["board_cards"] = board_cards

        # For each action
        for action in round_info["actions"]:

            if action["action"] in ["Post BB", "Post SB", "Post Extra Blind"]:
                states_to_pop.append(len(game_states))

            player = action_snapshot["players"][id_to_index[action.get("player_id")]]
            action_amount = float(action.get('amount',0))
            if amount_in_BB : action_amount = action_amount / general_data["big_blind_amount"]

            # If need to dealt cards, give back cards to every player:
            if need_to_deal_cards:
                for pl in action_snapshot["players"]:
                    pl["cards"] = ['back', 'back']
                need_to_deal_cards = False

            # If big blind is posted, need to deal cards
            if action['action'] == "Post BB": need_to_deal_cards = True

            # If cards in action, add it to the player (given to Hero or showed)
            if action.get("cards"):
                player["cards"] = action["cards"]

            # If player folds, remove its cards
            if action['action'] == "Fold":
                player["cards"] = []

            # Generate a description for the action
            if action_amount == 0:
                action_snapshot["action"] = f"{player['name']}: {action['action']}"
            else :
                action_snapshot["action"] = f"{player['name']}: {action['action']} for {action_amount}"

            # Update bet, chip amount and pot
            player["bet"] += action_amount
            player["chips"] -= action_amount
            action_snapshot["pot"] += action_amount

            game_states.append(action_snapshot)

            #Copy action_snapshot for next action
            players = []
            for player in action_snapshot["players"]:
                players.append(player.copy())
            board_cards = action_snapshot["board_cards"].copy()
            action_snapshot = action_snapshot.copy()
            action_snapshot["players"] = players
            action_snapshot["board_cards"] = board_cards

            action_amount = 0
            action_snapshot["action"] = ""

    # Check the firsts actions and remove the undesired ones
    popped = 0
    for index in states_to_pop: 
        game_states.pop(index-popped)
        popped +=1

    
    # Include pot and winnings information at the last state
    game_states[-1]["final_pots"] = [
        {
            "rake": float(pot["rake"]),
            "amount": float(pot["amount"]),
            "player_wins": [
                {
                    "name": action_snapshot["players"][id_to_index[win.get("player_id")]]["name"],
                    "win_amount": float(win["win_amount"]),
                    "contributed_rake":float(win["contributed_rake"]),
                    "cashout_fee": float(win.get("cashout_fee", 0.00)),
                    "cashout_amount": float(win.get("cashout_amount", win["win_amount"]))
                }
                for win in pot["player_wins"]
            ]
        }
        for pot in ohh_data["pots"]
    ]

    return general_data, game_states
