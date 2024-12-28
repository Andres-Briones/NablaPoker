from flask import  request, render_template, session, flash
from app.ws import sock
from .models import create_room, get_all_rooms, get_room, delete_room_by_id
from app.utils.decorators import login_required, htmx_required
from app.utils.wrappers import render_template_flash
import numpy as np

import json

from . import rooms_bp

# Track all active WebSocket connections to broadcast updates
connected_sockets = set()

# Index route for now
@rooms_bp.route("/", methods=["GET"])
def rooms():
    """
    Returns an HTML snippet listing all rooms (rooms_list.html).
    """
    redirect_message = session.pop('redirect_message', None)  # Get and remove the message
    login_popup = redirect_message == 'need_to_login' 

    rooms = get_all_rooms()
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
        max_players = request.form.get("max_players", "").strip()
        stakes = request.form.get("stakes", "").strip()
        if room_name and max_players and stakes:
            try:
                # Split stakes into small blind and big blind
                small_blind, big_blind = map(float, stakes.split('/'))
                create_room(room_name, int(max_players), small_blind, big_blind)
                broadcast_room_update()
            except Exception as e:
                flash(f"Error creating room: {str(e)}", "error")

            finally:
                flash("Room created successfully.", "success")
                return render_template('flash_messages.html') 
        else:
            flash("All fields are required and max players must be a number.", "error")
            
            return render_template_flash('room_creation.html')

    return render_template_flash("room_creation.html")


@rooms_bp.route('/room/<int:room_id>')
@login_required
def poker_room(room_id):
    room = get_room(room_id)

    general_data = {
        "id" : room["id"],
        "table_name": room["name"],
        "small_blind_amount": float(room["small_blind"]),
        "big_blind_amount": float(room["big_blind"]),
    }

    gamestate = {
        "players": [],
        "pot" : 0.00,
        "action": "",
        "board_cards": [],
        "street": "Preflop",
        "final_pots": None
        }

    player_info = {
        "name": session["username"],
        "seat": 0,
        "cards": [],
        "status": "Active",
        "chips": 100, 
        "bet" : 0.00,
        "dealer": 1,
        "angle": np.pi* (0 + 1/2)
        }
    gamestate["players"].append(player_info)

    return render_template("poker.html", general_data = general_data, gamestate = gamestate)

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

@sock.route("/room_ws")
def rooms_ws(ws):
    """
    A pure WebSocket endpoint for broadcasting changes to all connected clients.
    We don't necessarily need to receive data from the client,
    but we keep this loop open so the connection remains alive.
    """
    connected_sockets.add(ws)
    print("WebSocket connected", ws) 
    try:
        while True:
            msg = ws.receive()
    finally:
        print("WebSocket disconnected", ws) 
        connected_sockets.discard(ws)



def broadcast_room_update():
    """
    Gets the updated rooms list and sends it to every connected WebSocket client.
    We'll leverage HTMX's WebSocket extension so no custom JS is needed.
    """
    rooms = get_all_rooms()
    # Render a fresh snippet of the rooms list
    html = render_template("_rooms.html", rooms=rooms)

    for sock_conn in list(connected_sockets):
        try:
            sock_conn.send(html)
        except:
            connected_sockets.discard(sock_conn)
