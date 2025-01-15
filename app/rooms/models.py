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

def get_all_rooms(tables_dict):
    """
    Returns a list of dicts, each with { 'id': ..., 'name': ... }
    from the 'rooms' table.
    """
    rooms = query_db("SELECT * FROM rooms ORDER BY id DESC")
    if not rooms:
        return []

    for room in rooms:
        table = tables_dict.get(room["id"], None)
        if table is None:
            room["players"] = 0 # Room is empty
        else : 
            room["players"] = len(table.players) # Get number of players in the room

    return rooms

# Get room info by id
def get_room(room_id):
    room = query_db("SELECT * FROM rooms WHERE id = ?", (room_id,), one=True)
    return room

#Delete room 
def delete_room_by_id(tables_dict, room_id):
    table = tables_dict[room_id]
    if len(table.players) != 1:
        raise Exception("You can't delete a room with other players in it")
    try:
        query = "DELETE FROM rooms WHERE id = ?"
        execute_db(query, (room_id,))
    except Exception as e:
        raise Exception("Error deleting room: ", e)
    # remove the table from tables_dict
    tables_dict.pop(room_id)
    return

