__author__ = 'Ido Keysar'

import socket
import protocol
from tcp_by_size import send_with_size, recv_by_size


def menu():
    print("1. Login")
    print("2. Register New User")
    print("3. Get User by Username")
    print("4. Delete User")
    print("5. Get All Users")
    print("6. Create pokemon Account")
    print("7. Get Account by ID")
    print("8. Update Account")
    print("9. Get All Accounts")
    print("10. Get pokecoins by Username - vulnerable")
    print("11. Exit")

    choice = input("enter num: ")

    if choice == "11":
        return "q"
    elif choice == "1":
        name = input("Enter username: ")
        password = input("Enter password: ")
        return "LOGUSR|" + name + "|" + password
    elif choice == "2":
        name = input("Enter Username: ")
        password = input("Enter Password: ")
        email = input("Enter Email: ")
        phone = input("Enter Phone: ")
        return "REGUSR|" + name + "|" + password + "|" + email + "|" + phone
    elif choice == "3":
        name = input("Enter Username: ")
        return "GETUSR|" + name
    elif choice == "4":
        name = input("Enter Username to delete: ")
        return "DELUSR|" + name
    elif choice == "5":
        return "ALLUSR|"
    elif choice == "6":
        acc_id = input("Enter Account ID: ")
        nickname = input("Enter Nickname: ")
        coins = input("Enter Pokecoins: ")
        level = input("Enter Level: ")
        return "ADDACC|" + acc_id + "|" + nickname + "|" + coins + "|" + level
    elif choice == "7":
        acc_id = input("Enter Account ID: ")
        return "GETACC|" + acc_id
    elif choice == "8":
        acc_id = input("Enter Account ID: ")
        nickname = input("Enter New Nickname: ")
        coins = input("Enter New Pokecoins: ")
        level = input("Enter New Level: ")
        return "UPDACC|" + acc_id + "|" + nickname + "|" + coins + "|" + level
    elif choice == "9":
        return "ALLACC|"
    elif choice == "10":
        name = input("Enter Username: ")
        return "SQLINJ|" + name
    else:
        return ""


if __name__ == '__main__':
    cli_s = socket.socket()
    cli_s.connect(("127.0.0.1", 3141))

    session = protocol.perform_handshake_client(cli_s)
    if not session:
        print("Handshake failed")
        cli_s.close()
        exit(1)

    print("Secure connection established successfully!")

    while True:
        data = menu()

        if data == "q":
            break

        enc_data = session.encrypt(data)
        send_with_size(cli_s, enc_data)

        enc_resp = recv_by_size(cli_s)
        if not enc_resp:
            print("Server disconnected")
            break

        resp = session.decrypt(enc_resp).decode('utf-8')
        print("Got: " + resp)

    cli_s.close()
