DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS messages;

CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT,  -- For security reasons, we would need another more complex random id to identify the player in the cookiers
username TEXT UNIQUE NOT NULL,
password TEXT NOT NULL
);

CREATE TABLE rooms (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE NOT NULL,
max_players INTEGER NOT NULL,
small_blind DECIMAL NOT NULL,
big_blind DECIMAL NOT NULL
);

CREATE TABLE messages (
id INTEGER PRIMARY KEY AUTOINCREMENT,
room_id INTEGER NOT NULL,
user_id INTEGER NOT NULL,
message TEXT NOT NULL,
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY(room_id) REFERENCES rooms(id),
FOREIGN KEY(user_id) REFERENCES users(id)
);
