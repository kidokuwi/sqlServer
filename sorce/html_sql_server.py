__author__ = 'Yossi'
import socket
import SQL_ORM

import Queue, threading,time, random
from  tcp_by_size import send_with_size ,recv_by_size
DEBUG = True
exit_all = False




def handl_client(sock , tid, db):
    global exit_all
    
    print "New Client num " + str(tid)
    
    while not exit_all:
        try:
            data = recv_by_size(sock)
            if data == "":
                print "Error: Seens Client DC"
                break


            to_send = do_action(data ,db)

            
            send_with_size(sock,to_send)

        except socket.error as  err:
            if err.errno == 10054:
                #'Connection reset by peer'
                print "Error %d Client is Gone. %s reset by peer." % (err.errno,str(sock))
                break
            else:
                print "%d General Sock Error Client %s disconnected" % (err.errno,str(sock))
                break

        except Exception as err:
            print "General Error:", err.message
            break
    sock.close()


def do_action(data ,db):
    """
    check what client ask and fill to send with the answer
    """
    to_send = "Not Set Yet"
    action = data[:6]
    data = data[7:]
    fields = data.split('|')

    if DEBUG:
        print "Got client request " + action + " -- " + str(fields) 

    if action == "UPDUSR":
        usr = SQL_ORM.User(fields[0], fields[1], fields[2], fields[3], fields[4], \
                                                fields[5],fields[6], fields[7], False)
        if db.update_user(usr):
            to_send = "UPDUSRR|"+ "Success"
        else:
            to_send = "UPDUSRR|"+ "Error"

    elif action == "BBBBBB":
        to_send = "BBBBBBR|"+ "b"

    elif action == "CCCCCC":
        to_send = "CCCCCCR|"+ "c"

    elif action == "RULIVE":
        to_send = "RULIVER|"+ "yes i am a live server"

    else:
        print "Got unknown action from client " +action
        to_send = "ERR___R|001|"+ "unknown action"

    return to_send




def q_manager(q,tid):
    global exit_all
    
    print "manager start:" + str(tid)
    while not exit_all:
        item = q.get()
        print "manager got somthing:" + str(item)
        # do some work with it(item)



        q.task_done()
        time.sleep(0.3)
    print "Manager say Bye"
    


def main ():
    global exit_all
    
    exit_all = False
    db= SQL_ORM.UserAccountORM()
    
    s = socket.socket()
    
    q = Queue.Queue()

    q.put("Hi for start")
    
    
    manager = threading.Thread(target=q_manager, args=(q, 0))
    
    s.bind(("0.0.0.0", 33445))

    s.listen(4)
    print "after listen"

    threads = []
    i = 1
    while True:
        cli_s , addr = s.accept()
        t = threading.Thread(target =handl_client, args=(cli_s, i,db))
        t.start()
        i+=1
        threads.append(t);



    exit_all = True
    for t in threads:
        t.join()
    manager.join()
    
    s.close()



main()
