from flask import  request, render_template, session, flash
from app.ws import sock
from .models import create_room, get_all_rooms
from app.utils.decorators import login_required, htmx_required
from app.utils.wrappers import render_template_flash

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
    if  request.method == "POST":
        room_name = request.form.get("name", "").strip()
        if room_name:
            create_room(room_name)
            broadcast_room_update()

            # Return the updated list to the client who just created the room
        rooms = get_all_rooms()
        return render_template("rooms.html", rooms=rooms)

    flash("Not yet implemented. Try the replayer and statistics")
    rooms = get_all_rooms()
    return render_template_flash("_rooms.html", rooms=rooms) 
    

@sock.route("/room_ws")
def rooms_ws(ws):
    """
    A pure WebSocket endpoint for broadcasting changes to all connected clients.
    We don't necessarily need to receive data from the client,
    but we keep this loop open so the connection remains alive.
    """
    connected_sockets.add(ws)
    try:
        while True:
            msg = ws.receive()
            if msg is None:
                # Client disconnected
                break
            # Optionally handle client-sent messages if needed
    finally:
        connected_sockets.discard(ws)

def broadcast_room_update():
    """
    Gets the updated rooms list and sends it to every connected WebSocket client.
    We'll leverage HTMX's WebSocket extension so no custom JS is needed.
    """
    rooms = get_all_rooms()
    # Render a fresh snippet of the rooms list
    html = render_template("_rooms.html", rooms=rooms)
    
    # HTMX default: we can send JSON with "event" and "data" 
    # so that "on:event swap:innerHTML" does the trick client-side
    payload = {
        "event": "roomsUpdated",
        "data": html
    }
    message_str = json.dumps(payload)

    for sock_conn in list(connected_sockets):
        try:
            sock_conn.send(message_str)
        except:
            # If it fails, remove that connection
            connected_sockets.discard(sock_conn)
