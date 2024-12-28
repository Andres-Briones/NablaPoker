import os
import sqlite3
from flask import g, current_app

def get_db():
    """
    Creates a SQLite connection if not already in Flask's 'g' context.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        #g.db.row_factory = sqlite3.Row  # Return rows like dictionaries
        g.db.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
    return g.db

def close_db(e=None):
    """
    Closes the SQLite connection if it exists.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def ensure_db():
    """
    1) Checks if the DB file exists (using os.path.exists).
    2) If not, creates the file (by connecting) and executes 'schema.sql'.
    3) Otherwise, does nothing.
    """
    db_path = current_app.config['DATABASE']
    is_new = not os.path.exists(db_path)

    db = get_db()  # Creates or opens the database file

    if is_new:
        with open(current_app.config['SCHEMA'], 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        db.executescript(schema_sql)  # Execute all SQL statements
        db.commit()
        print("New database created.")
    else:
        print("Database already exists. No setup needed.")

    close_db()  # Cleanly close the connection

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    last_id = cur.lastrowid
    cur.close()
    close_db()
    return last_id
