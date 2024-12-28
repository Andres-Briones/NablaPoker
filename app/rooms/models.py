from app.utils.db import query_db, execute_db

def create_room(name, max_players, small_blind, big_blind):
    """
    Create a new room with the given parameters.
    """
    query = """
    INSERT INTO rooms (name, max_players, small_blind, big_blind)
    VALUES (?, ?, ?, ?)
    """
    execute_db(query, (name, max_players, small_blind, big_blind))

def get_all_rooms():
    """
    Returns a list of dicts, each with { 'id': ..., 'name': ... }
    from the 'rooms' table.
    """
    rooms = query_db("SELECT * FROM rooms ORDER BY id DESC")
    if not rooms:
        return []

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
