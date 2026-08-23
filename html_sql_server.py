__author__ = 'Ido Keysar'

import os
import random
import socket
import threading
import queue as Queue
import time

import SQL_ORM
import protocol
from tcp_by_size import send_with_size, recv_by_size

DEBUG = True
exit_all = False

server_private_key, server_public_key = protocol.load_rsa_keys()


def handle_client(sock, tid, db):
    global exit_all

    print("New Client num " + str(tid))

    session = protocol.perform_handshake_server(sock, server_private_key, server_public_key)
    if not session:
        print("Handshake failed for client " + str(tid))
        sock.close()
        return

    print("handshake succsses  for " + str(tid))

    while not exit_all:
        try:
            enc_data = recv_by_size(sock)
            if not enc_data:
                print("client dc " + str(tid))
                break

            data = session.decrypt(enc_data).decode('utf-8')
            to_send = do_action(data, db)

            enc_response = session.encrypt(to_send)
            send_with_size(sock, enc_response)

        except Exception as err:
            print("Error handling client " + str(tid) + ": " + str(err))
            break

    sock.close()


def do_action(data, db):
    try:
        if len(data) < 6:
            return "ERRORR|002|invalid format"

        action = data[:6]
        rest = data[7:] if len(data) > 6 else ""
        fields = rest.split('|') if rest else []

        if DEBUG:
            print("Got client request " + action + " : " + str(fields))

        if action == "LOGUSR":
            if len(fields) < 2:
                return "LOGUSRR|Failed: Missing fields"
            usr = db.get_user(fields[0])
            if usr:
                hashed_input = protocol.hash_password(fields[1], usr.salt)
                if usr.password == hashed_input:
                    return "LOGUSRR|Success"
            return "LOGUSRR|Failed"

        elif action == "REGUSR":
            if len(fields) < 4:
                return "REGUSRR|Failed: Missing fields"
            exist = [u.account_id for u in db.get_users()]
            id = random.randrange(0, 100000)
            while id in exist:
                id = random.randrange(0, 100000)
            salt = os.urandom(8).hex()
            hashed_pw = protocol.hash_password(fields[1], salt)
            new_usr = SQL_ORM.User(fields[0], hashed_pw, fields[2], fields[3], id, salt=salt)
            success, msg = db.insert_new_user(new_usr)
            if success:
                return "REGUSRR|Success"
            return "REGUSRR|Failed: " + msg

        elif action == "GETUSR":
            if not fields or not fields[0]:
                return "GETUSRR|Failed: Missing username"
            usr = db.get_user(fields[0])
            return "GETUSRR|" + str(usr)

        elif action == "DELUSR":
            if not fields or not fields[0]:
                return "DELUSRR|Failed: Missing username"
            db.delete_user(fields[0])
            return "DELUSRR|Success"

        elif action == "ALLUSR":
            users = db.get_users()
            return "ALLUSRR|" + str([str(u) for u in users])

        elif action == "ADDACC":
            if len(fields) < 4:
                return "ADDACCR|Failed: Missing fields"
            new_acc = SQL_ORM.PokemonAccount(int(fields[0]), fields[1], int(fields[2]), [], int(fields[3]))
            success, msg = db.insert_new_account(new_acc)
            if success:
                return "ADDACCR|Success"
            return "ADDACCR|Failed: " + msg

        elif action == "GETACC":
            if not fields or not fields[0]:
                return "GETACCR|Failed: Missing account ID"
            acc = db.get_account(int(fields[0]))
            return "GETACCR|" + str(acc)

        elif action == "UPDACC":
            if len(fields) < 4:
                return "UPDACCR|Failed: Missing fields"
            acc = SQL_ORM.PokemonAccount(int(fields[0]), fields[1], int(fields[2]), [], int(fields[3]))
            success, msg = db.update_account(acc)
            if success:
                return "UPDACCR|Success"
            return "UPDACCR|Failed: " + msg

        elif action == "ALLACC":
            accs = db.get_accounts()
            return "ALLACCR|" + str([str(a) for a in accs])

        elif action == "SQLINJ":
            if not fields or not fields[0]:
                return "SQLINJR|Failed: Missing payload"
            coins = db.get_user_pokecoins(fields[0])
            return "SQLINJR|" + str(coins)

        else:
            return "ERRORR|001|unknown action"

    except Exception as err:
        print("Error processing action: " + str(err))
        return "ERRORR|003|Action error: " + str(err)


def q_manager(q, tid):
    global exit_all
    print("manager start:" + str(tid))
    while not exit_all:
        item = q.get()
        # 
        q.task_done()
        time.sleep(0.3)


def main():
    global exit_all
    exit_all = False
    db = SQL_ORM.IdoKeysar()

    s = socket.socket()
    s.bind(("0.0.0.0", 3141))
    s.listen(4)
    print("server up")

    threads = []
    i = 1
    try:
        while True:
            cli_s, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(cli_s, i, db))
            t.start()
            i += 1
            threads.append(t)
    except KeyboardInterrupt:
        pass

    exit_all = True
    s.close()


if __name__ == '__main__':
    main()
