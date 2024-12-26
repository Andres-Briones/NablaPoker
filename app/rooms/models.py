from app.utils.db import query_db, execute_db

def create_room(name):
    """
    Inserts a new row into the 'rooms' table and returns its ID.
    """
    return execute_db("INSERT INTO rooms (name) VALUES (?)", (name,))

def get_all_rooms():
    """
    Returns a list of dicts, each with { 'id': ..., 'name': ... }
    from the 'rooms' table.
    """
    rows = query_db("SELECT id, name FROM rooms")
    if not rows:
        return []

    # Each row is a tuple like (id, name)
    rooms = []
    for row in rows:
        rooms.append({"id": row[0], "name": row[1]})
    return rooms
