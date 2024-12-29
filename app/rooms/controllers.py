from flask import  request, render_template, session, flash
from app.ws import sock
from .models import create_room, get_all_rooms, get_room, delete_room_by_id, get_next_seat, get_used_seats
from app.utils.decorators import login_required, htmx_required
from app.utils.wrappers import render_template_flash
import numpy as np

import json

from . import rooms_bp

# Track all active WebSocket connections to broadcast updates
connected_sockets = set()
rooms_dict = {}


# Index route for now
@rooms_bp.route("/", methods=["GET"])
def rooms():
    """
    Returns an HTML snippet listing all rooms (rooms_list.html).
    """
    redirect_message = session.pop('redirect_message', None)  # Get and remove the message
    login_popup = redirect_message == 'need_to_login' 

    rooms = get_all_rooms(rooms_dict)
    return render_template("rooms.html", rooms=rooms, login_popup=login_popup)

@rooms_bp.route("/create", methods=["GET", "POST"])
@login_required
@htmx_required
def create():
    """
    Creates a new room, broadcasts the update to all WebSocket clients,
    and returns the updated rooms list for immediate HTMX swap.
    """
    if request.method == "POST":
        room_name = request.form.get("name", "").strip()
        max_players = int(request.form.get("max_players", "").strip())
        stakes = request.form.get("stakes", "").strip()
        if room_name and max_players and stakes:
            try:
                # Split stakes into small blind and big blind
                small_blind, big_blind = map(float, stakes.split('/'))
                room_id = create_room(room_name, max_players, small_blind, big_blind)
            except Exception as e:
                print(e)
                flash(f"Error creating room : {str(e)}", "error")
            else: # If there is no error
                broadcast_room_update()
                flash("Room created successfully.", "success")
                return render_template('flash_messages.html') 
        else:
            flash("All fields are required and max players must be a number.", "error")
            
        return render_template_flash('room_creation.html') # If there is an error

    return render_template_flash("room_creation.html") # If the request is a GET request


@rooms_bp.route('/room/<int:room_id>')
@login_required
def poker_room(room_id):
    player_id = session["user_id"]
    room_db = get_room(room_id)
    room = rooms_dict.get(room_id, None)

    if room is None:
        room = {
            "pot" : 0,
            "players" : {}, #Dic of players ids. Each player will be a dictionnary with the following keys: name, chips, bet, cards, status "dealer_seat" : 0, 
            "dealer_seat" : 0,
            "available_seats" : list(range(room_db["max_players"]))
        } # Initialize dictionnary
        rooms_dict[room_id] = room 

    # Check if player in already in the room dictionnary
    if room["players"].get(player_id, None) is None: # If player is not in the room 
        seat = get_next_seat(room)
        if seat is not None :  # If there is an available seat
            this_player = {
                "name": session["username"],
                "seat": seat,
                "socket": None,
                "chips": 100, # 100 BB
                "bet": 0,
                "cards": [],
                "status": "Active",
                "chips": 100, 
                "bet" : 0.00,
            }
            room["players"][player_id] = this_player
            broadcast_room_update()
        else: # No available seat
            return "The room is full" 

    broadcast_table_update(room_id)
    general_data, gamestate = get_game_data(room_id, player_id)

    return render_template("poker.html", general_data = general_data, gamestate = gamestate)

# Get gamestate and general_data of the room for the given player
def get_game_data(room_id, player_id):
    room_db = get_room(room_id)
    room = rooms_dict.get(room_id, None)
    if room is None:
        print("Error: room not found")
        return 

    this_player = room["players"][player_id]
    
    used_seats = get_used_seats(room)

    general_data = {
        "id" : room_db["id"],
        "table_name": room_db["name"],
        "small_blind_amount": float(room_db["small_blind"]),
        "big_blind_amount": float(room_db["big_blind"]),
    }

    gamestate = {
        "players": [],
        "pot" : 0.00,
        "action": "",
        "board_cards": [],
        "street": "Preflop",
        "final_pots": None
        }
    for player in room["players"].values(): 
        player_info = dict(player)
        player_info["dealer"] = player["seat"] == room["dealer_seat"]
        # To position of the player shouldn't be player["seat"] but the index of player in the list of used seats minus this player seat
        seat_index = used_seats.index(player["seat"])
        this_player_seat_index = used_seats.index(this_player["seat"])
        player_info["angle"] = np.pi * (2*(seat_index - this_player_seat_index)/len(room["players"]) + 1/2) # Angle in radians for the position of the player on the table
        gamestate["players"].append(player_info)

    return general_data, gamestate

@rooms_bp.route('/delete/<int:room_id>', methods=["GET"])
def delete_room(room_id):
    try:
        delete_room_by_id(room_id)
        broadcast_room_update()
    except Exception as e:
        print(f"Error deleting room: {str(e)}")
    finally:
        # We need to return a signal to delete the current window
        return "<script> window.close() </script>"

# Quit room
@rooms_bp.route('/quit/<int:room_id>', methods=["GET"])
def quit_room(room_id):
    player_id = session["user_id"]
    room = rooms_dict.get(room_id, None)
    if room is None:
        return "Room not found"
    player = room["players"].get(player_id, None)
    if player is None:
        return "Player not found"
    room["available_seats"].append(player["seat"])
    room["available_seats"].sort()
 
    # Disconnect the player socket
    rooms_dict[room_id]["players"][session["user_id"]]["socket"] = None
     
    # Delete player from the room
    del room["players"][player_id]

    broadcast_room_update()
    broadcast_table_update(room_id)
    return "<script> window.close() </script>"

@sock.route("/rooms_ws")
def rooms_ws(ws):
    """
    A pure WebSocket endpoint for broadcasting changes to all connected clients.
    We don't necessarily need to receive data from the client,
    but we keep this loop open so the connection remains alive.
    """
    connected_sockets.add(ws)
    print("Rooms WebSocket connected", ws) 
    try:
        while True:
            msg = ws.receive()
            if msg is None:
                # Client disconnected
                break
    finally:
        print("Rooms WebSocket disconnected", ws) 
        connected_sockets.discard(ws)

@sock.route("/table_ws/<int:room_id>")
def table_ws(ws, room_id):
    # Add socket to player in rooms_dict
    print(session["username"],": Table WebSocket connected", ws) 

    # Check if room is in rooms_dict
    room = rooms_dict.get(room_id, None)
    if room is None:
        ws.close()
        return

    # Check if player is in the room
    player = room["players"].get(session["user_id"], None)
    if player is None:
        ws.close()
        return 

    player["socket"] = ws

    try:
        while True:
            msg = ws.receive()
            if msg is None:
                # Client disconnected
                break
    except Exception as e:
        print(f" {e}")
    finally:
        print(session["username"],": Table WebSocket disconnected", ws) 

def broadcast_table_update(room_id):
    for player_id, player in rooms_dict[room_id]["players"].items():
        if player["socket"] is not None:
            general_data, gamestate = get_game_data(room_id, player_id)
            html = render_template("poker_table_obb.html", general_data=general_data, gamestate = gamestate)
            try :
                player["socket"].send(html)
            except:
                print("The connection should have been deleted from the dict")
                rooms_dict[room_id]["players"][session["user_id"]]["socket"] = None



def broadcast_room_update():
    """
    Gets the updated rooms list and sends it to every connected WebSocket client.
    We'll leverage HTMX's WebSocket extension so no custom JS is needed.
    """
    print("Rooms updated. Broadcasting to all clients.")
    rooms = get_all_rooms(rooms_dict)
    # Render a fresh snippet of the rooms list
    html = render_template("_rooms.html", rooms=rooms)

    for sock_conn in list(connected_sockets):
        try:
            sock_conn.send(html)
        except:
            connected_sockets.discard(sock_conn)
