__author__ = 'Yossi'


import socket

import threading
from  tcp_by_size import send_with_size ,recv_by_size


def manu():
    print "1. Update User\n" + \
          "2. Insert User\n" + \
          "3. Delete User\n" + \
          "4. Get All Users\n>" +\
          "9. exit\n\n>"

    data = raw_input("Enter Num> ")

    if data == "9":
        return "q"
    elif data == "1":
        name = raw_input("Enter name > ")
        password = raw_input("Enter name > ")
        #
        #
        #
        return "UPDUSR|" + name + "|" + password + "|yossi|zahav|kefar saba|123123123|a@net.il|0"
    else:
        return "RULIVE"


cli_s = socket.socket()


cli_s.connect(("127.0.0.1",33445))


while True:
    data = manu()


    if data == "q":
        break
    send_with_size(cli_s,data)

    data = recv_by_size(cli_s)
    if data =="":
        print "seems server DC"
        break
    print "Got>>" + data


