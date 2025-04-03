import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect("database.db")

with open("schema.sql") as f:
    connection.executescript(f.read())

cur = connection.cursor()
# cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
#             ('First Post', 'Content for the first post')
#             )
# cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
#             ('Second Post', 'Content for the second post')
#             )
cur.execute(
    "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
    ("ishwargautam", generate_password_hash("IGTechTeam@8085"), True),
)
connection.commit()
connection.close()
