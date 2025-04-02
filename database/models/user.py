from flask_login import UserMixin
import sqlite3

class User(UserMixin):
    def __init__(self, id, username, password, is_admin):
        self.id = id
        self.username = username
        self.password = password  # This is the hashed password
        self.is_admin = is_admin

    @staticmethod
    def get_user_by_username(username):
        con = sqlite3.connect("database/database.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        con.close()
        return User(*row) if row else None
    
    @staticmethod
    def get_user_by_id(user_id):
        con = sqlite3.connect("database/database.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        con.close()
        return User(*row) if row else None


