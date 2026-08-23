__author__ = "Ido Keysar"

import os
import sqlite3


class User:
    def __init__(self, username, password, email, phone, account_id, is_admin=False, friends=None, salt=""):
        self.username = username
        self.password = password
        self.email = email
        self.phone = phone
        self.account_id = account_id
        self.is_admin = is_admin
        self.friends = friends if friends is not None else []
        self.salt = salt

    def __str__(self):
        return f"user:{self.username}:{self.email}:{self.phone}:{self.account_id}:{self.is_admin}"


class PokemonAccount:
    def __init__(self, account_id, nickname, pokecoins=0, pokemons=None, level=1):
        self.account_id = account_id
        self.nickname = nickname
        self.pokecoins = pokecoins
        self.pokemons = pokemons if pokemons is not None else []
        self.level = level

    def __str__(self):
        return f"account:{self.account_id}:{self.nickname}:{self.pokecoins}:{self.level}"


class IdoKeysar:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def open_DB(self):
        self.conn = sqlite3.connect('PokemonAccount.db')
        db_path = os.path.abspath('PokemonAccount.db')
        print(f"Connecting to DB at: {db_path}")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def close_DB(self):
        self.conn.close()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                username TEXT PRIMARY KEY,
                password TEXT,
                email TEXT,
                phone TEXT,
                account_id INTEGER,
                is_admin TEXT,
                salt TEXT
            )
        ''')
        try:
            self.cursor.execute("ALTER TABLE Users ADD COLUMN salt TEXT DEFAULT ''")
        except Exception:
            pass
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Accounts (
                account_id INTEGER PRIMARY KEY,
                nickname TEXT,
                pokecoins INTEGER,
                pokemons TEXT,
                level INTEGER
            )
        ''')
        self.conn.commit()

    def commit(self):
        self.conn.commit()

    def get_user(self, username):
        self.open_DB()
        sql = "SELECT username, password, email, phone, account_id, is_admin, salt FROM Users WHERE username = ?"
        self.cursor.execute(sql, (username,))
        row = self.cursor.fetchone()
        self.close_DB()
        if row:
            salt_val = row[6] if len(row) > 6 and row[6] is not None else ""
            return User(row[0], row[1], row[2], row[3], row[4], bool(row[5]), salt=salt_val)
        return None

    def get_users(self):
        self.open_DB()
        sql = "SELECT username, password, email, phone, account_id, is_admin, salt FROM Users"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        self.close_DB()
        return [User(r[0], r[1], r[2], r[3], r[4], bool(r[5]), salt=r[6] if len(r) > 6 and r[6] is not None else "") for r in rows]

    def get_account(self, account_id):
        self.open_DB()
        sql = "SELECT account_id, nickname, pokecoins, pokemons, level FROM Accounts WHERE account_id = ?"
        self.cursor.execute(sql, (account_id,))
        row = self.cursor.fetchone()
        self.close_DB()
        if row:
            p_list = row[3].split(',') if row[3] else []
            return PokemonAccount(row[0], row[1], row[2], p_list, row[4])
        return None

    def get_accounts(self):
        self.open_DB()
        sql = "SELECT account_id, nickname, pokecoins, pokemons, level FROM Accounts"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        self.close_DB()
        return [PokemonAccount(r[0], r[1], r[2], r[3].split(',') if r[3] else [], r[4]) for r in rows]

    #  VULNERABLE
    def get_user_pokecoins(self, username):
        try:
            self.open_DB()
            coins = 0
            sql = "SELECT a.pokecoins FROM Accounts a, Users u WHERE a.account_id = u.account_id AND u.username = '" + username + "' "
            res = self.cursor.execute(sql)
            for ans in res:
                coins = ans[0]
            self.close_DB()
            return coins
        except Exception as err:
            try:
                self.close_DB()
            except Exception:
                pass
            return f"Error: {err}"

    def username_exists(self, username):
        self.open_DB()
        sql = "SELECT 1 FROM Users WHERE username = ?"
        self.cursor.execute(sql, (username,))
        row = self.cursor.fetchone()
        self.close_DB()
        return row is not None

    def email_exists(self, email):
        self.open_DB()
        sql = "SELECT 1 FROM Users WHERE email = ?"
        self.cursor.execute(sql, (email,))
        row = self.cursor.fetchone()
        self.close_DB()
        return row is not None

    def nickname_exists(self, nickname, exclude_account_id=None):
        self.open_DB()
        if exclude_account_id is not None:
            sql = "SELECT 1 FROM Accounts WHERE nickname = ? AND account_id != ?"
            self.cursor.execute(sql, (nickname, exclude_account_id))
        else:
            sql = "SELECT 1 FROM Accounts WHERE nickname = ?"
            self.cursor.execute(sql, (nickname,))
        row = self.cursor.fetchone()
        self.close_DB()
        return row is not None

    def insert_new_user(self, user):
        if self.username_exists(user.username):
            return False, "Username already exists"
        if self.email_exists(user.email):
            return False, "Email already exists"
        self.open_DB()
        sql = "INSERT INTO Users (username, password, email, phone, account_id, is_admin, salt) VALUES (?, ?, ?, ?, ?, ?, ?)"
        self.cursor.execute(sql, (user.username, user.password, user.email, user.phone, user.account_id, str(user.is_admin), user.salt))
        self.commit()
        self.close_DB()
        return True, "Success"

    def insert_new_account(self, account):
        if self.nickname_exists(account.nickname):
            return False, "Nickname already exists"
        self.open_DB()
        pokemons_str = ",".join(account.pokemons) if isinstance(account.pokemons, list) else str(account.pokemons)
        sql = "INSERT INTO Accounts (account_id, nickname, pokecoins, pokemons, level) VALUES (?, ?, ?, ?, ?)"
        self.cursor.execute(sql, (account.account_id, account.nickname, account.pokecoins, pokemons_str, account.level))
        self.commit()
        self.close_DB()
        return True, "Success"

    def update_account(self, account):
        if self.nickname_exists(account.nickname, exclude_account_id=account.account_id):
            return False, "Nickname already exists"
        self.open_DB()
        sql = "UPDATE Accounts SET nickname = ?, pokecoins = ?, level = ? WHERE account_id = ?"
        self.cursor.execute(sql, (account.nickname, account.pokecoins, account.level, account.account_id))
        self.commit()
        self.close_DB()
        return True, "Success"

    def delete_user(self, username):
        self.open_DB()
        sql = "DELETE FROM Users WHERE username = ?"
        self.cursor.execute(sql, (username,))
        self.commit()
        self.close_DB()

    def delete_account(self, account_id):
        self.open_DB()
        sql = "DELETE FROM Accounts WHERE account_id = ?"
        self.cursor.execute(sql, (account_id,))
        self.commit()
        self.close_DB()


def main():
    user1 = User("Ido", "123456", "ido@gmail.com", "0501234567", 1, False)
    acc1 = PokemonAccount(1, "pikachu123", 500, ["Pikachu", "Charizard"], 999)
    print(user1)
    print(acc1)


if __name__ == "__main__":
    main()