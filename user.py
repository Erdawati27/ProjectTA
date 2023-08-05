from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
class User:
    def __init__(self, id_user,username, password, email, mysql):
        self.id_user = id_user
        self.username = username
        self.password = password
        self.email = email
        self.mysql = mysql

    def register(self):
        cur = self.mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", (self.username, self.password, self.email))
        self.mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_by_username(username, mysql):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user_data = cur.fetchone()
        cur.close()
        if user_data:
            return User(user_data[0],user_data[1], user_data[2], user_data[3], mysql)
        return None

    def check_password(self, password):
        return  check_password_hash(self.password, password)
