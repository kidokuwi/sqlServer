__author__ = 'Ido Keysar'

import socket
import tkinter as tk

import protocol
from tcp_by_size import send_with_size, recv_by_size


class SimpleGUI:
    def __init__(self, root):
        self.root = root

        self.sock = None
        self.session = None

        tk.Label(root, text=" USER ").pack()

        tk.Label(root, text="Username:").pack()
        self.username = tk.Entry(root)
        self.username.pack()

        tk.Label(root, text="Password:").pack()
        self.password = tk.Entry(root)
        self.password.pack()

        tk.Label(root, text="Email:").pack()
        self.email = tk.Entry(root)
        self.email.pack()

        tk.Label(root, text="Phone:").pack()
        self.phone = tk.Entry(root)
        self.phone.pack()

        tk.Button(root, text="Login (Username, Password)", command=self.login).pack()
        tk.Button(root, text="Register User (Username, Password, Email, Phone)", command=self.register).pack()
        tk.Button(root, text="Get User (Username)", command=self.get_user).pack()
        tk.Button(root, text="Delete User (Username)", command=self.delete_user).pack()
        tk.Button(root, text="Get All Users", command=self.get_all_users).pack()

        tk.Label(root, text=" POKEMON ACCOUNT ").pack()

        tk.Label(root, text="Account ID:").pack()
        self.account_id = tk.Entry(root)
        self.account_id.pack()

        tk.Label(root, text="Nickname:").pack()
        self.nickname = tk.Entry(root)
        self.nickname.pack()

        tk.Label(root, text="Pokecoins:").pack()
        self.pokecoins = tk.Entry(root)
        self.pokecoins.pack()

        tk.Label(root, text="Level:").pack()
        self.level = tk.Entry(root)
        self.level.pack()

        tk.Button(root, text="Add Account (Account ID, Nickname, Pokecoins, Level)", command=self.add_account).pack()
        tk.Button(root, text="Get Account (Account ID)", command=self.get_account).pack()
        tk.Button(root, text="Update Account (Account ID, Nickname, Pokecoins, Level)", command=self.update_account).pack()
        tk.Button(root, text="Get All Accounts", command=self.get_all_accounts).pack()

        # --- SECTION 3: VULNERABILITY DEMO ---
        tk.Label(root, text=" SECURITY DEMO ").pack()
        tk.Button(root, text="SQL Injection (Username)", command=self.sql_injection).pack()

        # --- OUTPUT BOX ---
        tk.Label(root, text="Output Response:").pack()
        self.output = tk.Text(root, height=5, width=60)
        self.output.pack()

        self.connect()

    def connect(self):
        try:
            self.sock = socket.socket()
            self.sock.connect(("127.0.0.1", 3141))
            self.session = protocol.perform_handshake_client(self.sock)
        except Exception as e:
            self.output.insert(tk.END, f"Connect error: {e}\n")

    def send(self, msg):
        if not self.session:
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, "Not connected to server\n")
            return
        try:
            enc = self.session.encrypt(msg)
            send_with_size(self.sock, enc)
            resp = self.session.decrypt(recv_by_size(self.sock)).decode('utf-8')
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, resp + "\n")
        except Exception as e:
            self.output.delete("1.0", tk.END)
            self.output.insert(tk.END, f"Error: {e}\n")

    def login(self):
        self.send(f"LOGUSR|{self.username.get()}|{self.password.get()}")

    def register(self):
        self.send(f"REGUSR|{self.username.get()}|{self.password.get()}|{self.email.get()}|{self.phone.get()}")

    def get_user(self):
        self.send(f"GETUSR|{self.username.get()}")

    def delete_user(self):
        self.send(f"DELUSR|{self.username.get()}")

    def get_all_users(self):
        self.send("ALLUSR|")

    def add_account(self):
        self.send(f"ADDACC|{self.account_id.get()}|{self.nickname.get()}|{self.pokecoins.get()}|{self.level.get()}")

    def get_account(self):
        self.send(f"GETACC|{self.account_id.get()}")

    def update_account(self):
        self.send(f"UPDACC|{self.account_id.get()}|{self.nickname.get()}|{self.pokecoins.get()}|{self.level.get()}")

    def get_all_accounts(self):
        self.send("ALLACC|")

    def sql_injection(self):
        self.send(f"SQLINJ|{self.username.get()}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleGUI(root)
    root.mainloop()
