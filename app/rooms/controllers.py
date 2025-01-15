from flask import  request, render_template, session, flash
from decimal import Decimal
from app.ws import sock
from .models import create_room, get_all_rooms, get_room, delete_room_by_id
from app.utils.decorators import login_required, htmx_required
from app.utils.wrappers import render_template_flash, render_flash
from app.utils.scripts import open_window_script
import numpy as np
import random
from app.poker.table import Table
import json

from . import rooms_bp

# Track all active WebSocket connections to broadcast updates
connected_sockets = set()
tables_dict = {}

# Fixed global variab
# Index route for now
@rooms_bp.route("/", methods=["GET"])
def rooms():
    """
    Returns an HTML snippet listing all rooms (rooms_list.html).
    """
    redirect_message = session.pop('redirect_message', None)  # Get and remove the message
    login_popup = redirect_message == 'need_to_login' 

    rooms = get_all_rooms(tables_dict)
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
    table = tables_dict.get(room_id, None)

    if table is None:
        table = Table(table_id=room_id,
                      table_name=room_db["name"],
                      small_blind=Decimal(str(room_db["small_blind"])),
                      big_blind=Decimal(str(room_db["big_blind"])),
                      table_size=room_db["max_players"])
        tables_dict[room_id] = table

    # Check if player in already in the room dictionnary
    if table.players.get(player_id, None) is None: # If player is not in the room 
        try:
            player = table.new_player(id = player_id, name = session["username"], starting_stack = 100*table.big_blind)
        except Exception as e:
            print(e)
            return f"{e}"

    broadcast_room_update()
    broadcast_table_update(room_id)

    general_data, gamestate = table.get_display_data(player_id)

    return render_template("poker.html", general_data = general_data, gamestate = gamestate)


@rooms_bp.route('/start/<int:room_id>', methods=["GET", "POST"])
@login_required
def start_game(room_id):
    table = tables_dict.get(room_id)
    if not table:
        print("Room not found")
        return 'Game not found'

    try:
        table.start_new_game()
    except Exception as e:
        flash(f"{e}", "error")
        return render_template("flash_messages.html")
    
    broadcast_table_update(room_id)
    return  '', 204

@rooms_bp.route('/delete/<int:room_id>', methods=["GET"])
@login_required
def delete_room(room_id):
    try:
        delete_room_by_id(tables_dict, room_id)
        broadcast_room_update()
    except Exception as e:
        flash(f"{e}","error")
        return render_flash()

    # We need to return a signal to delete the current window
    return "<script> window.close() </script>"

# Quit room
@rooms_bp.route('/quit/<int:room_id>', methods=["GET"])
def quit_room(room_id):
    player_id = session["user_id"]
    table = tables_dict.get(room_id, None)
    if table is None:
        flash("Room not found", "error")
        return render_flash()
    player = table.players.get(player_id, None)
    if player is None:
        flash("Player not found", "error")
        return render_flash()
    active_players = table.active_players.to_list()
    for player in active_players:
        if player.id == player_id:
            flash(f"Finish the current game before leaving","error")
            return render_flash()

    table.remove_player(player_id)
    broadcast_room_update()
    broadcast_table_update(room_id)
    return "<script> window.close() </script>"


# Route for opening a new window for the given room_id
@rooms_bp.route('/load_room/<int:room_id>')                
@login_required
def load_room(room_id):
    return open_window_script(f"/room/{room_id}", 1000, 1000)


@rooms_bp.route('/action/<int:room_id>/<action>', methods=['POST'])
@login_required
def player_action(room_id, action):
    amount = Decimal(request.headers.get("HX-Prompt",0))
    table = tables_dict.get(room_id)
    if table.is_player_turn(session["user_id"]):
        try:
            table.action(action_type = action, amount=amount*table.big_blind)
        except Exception as e:
            print(f" {e}")
            flash(f"{e}", "error")
            return render_flash()
        broadcast_table_update(room_id)
    else:
        flash("You can't take action right now")
        return render_flash()
    return '', 204


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
    # Add socket to player in tables_dict
    print(session["username"],": Table WebSocket connected", ws) 

    # Check if room is in tables_dict
    table = tables_dict.get(room_id, None)
    if table is None:
        ws.close()
        return

    # Check if player is in the room
    player = table.players.get(session["user_id"], None)
    if player is None:
        ws.close()
        return 

    player.socket = ws
    player.status = "Active"

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
        player.status = "disconnected"

def broadcast_room_update():
    """
    Gets the updated rooms list and sends it to every connected WebSocket client.
    We'll leverage HTMX's WebSocket extension so no custom JS is needed.
    """
    print("Rooms updated. Broadcasting to all clients.")
    rooms = get_all_rooms(tables_dict)
    # Render a fresh snippet of the rooms list
    html = render_template("_rooms.html", rooms=rooms)

    for sock_conn in list(connected_sockets):
        try:
            sock_conn.send(html)
        except:
            connected_sockets.discard(sock_conn)

def broadcast_table_update(room_id):
    table = tables_dict[room_id]
    for pp_id, pp in table.players.items():
        if pp.socket is not None:
            general_data, gamestate = table.get_display_data(pp_id)
            html = render_template("poker_table_obb.html", general_data=general_data, gamestate = gamestate)
            try :
                pp.socket.send(html)
            except:
                print("The connection should have been deleted from the dict")
                tables_dict[room_id].players[session["user_id"]].socket = None



