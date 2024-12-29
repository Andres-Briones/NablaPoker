from app.utils.db import query_db, execute_db
from flask import flash

def create_room(name, max_players, small_blind, big_blind):
    """
    Create a new room with the given parameters.
    """
    # Check if room exists
    query = f"""SELECT id FROM rooms where name == '{name}' """
    if query_db(query, one=True) is not None :
        raise Exception("There is already a room with this name")
        return 

    # Insert room into the database
    query = """
    INSERT INTO rooms (name, max_players, small_blind, big_blind)
    VALUES (?, ?, ?, ?)
    """
    id = execute_db(query, (name, max_players, small_blind, big_blind))

    return id

def get_all_rooms(rooms_dict):
    """
    Returns a list of dicts, each with { 'id': ..., 'name': ... }
    from the 'rooms' table.
    """
    rooms = query_db("SELECT * FROM rooms ORDER BY id DESC")
    if not rooms:
        return []

    for room in rooms:
        room_values = rooms_dict.get(room["id"], None)
        if room_values is None:
            room["players"] = 0 # Room is empty
        else : 
            room["players"] = len(room_values["players"]) # Get number of players in the room

    return rooms

# Get room info by id
def get_room(room_id):
    room = query_db("SELECT * FROM rooms WHERE id = ?", (room_id,), one=True)
    return room

#Delete room 
def delete_room_by_id(room_id):
    try:
        query = "DELETE FROM rooms WHERE id = ?"
        execute_db(query, (room_id,))
    except Exception as e:
        print("Error deleting room: ", e)

    return

# Get next available seat from the available_seats list and updates the available_seats list
def get_next_seat(room):
    available_seats = room["available_seats"]
    if available_seats: # If the list is not empty
        seat = available_seats.pop(0)
        return seat
    return None # If the list is empty

# Get list of used seats in the room
def get_used_seats(room):
    used_seats = []
    for player in room["players"].values():
        used_seats.append(player["seat"])
    return used_seats
