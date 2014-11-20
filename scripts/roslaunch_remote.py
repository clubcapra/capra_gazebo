import websocket

 
def request(req):
    global ws
    ws.send(req)
    return ws.recv() 

def list_instances():
    global ws
    return request('list').split()

def menu(instances):
    while True:
        for i, name in enumerate(instances):
            print "%d : %s" % (i + 1, name)
        print "%d : Create new instance" % (len(instances) + 1)
        print "%d : Kill instance" % (len(instances) + 2)

        choice = raw_input("Enter id:")
        if choice.isdigit():
            choice = int(choice)
            if choice > 0 and choice <= len(instances):
                print "OK"
                return
            elif choice == len(instances) + 1:
                print "Create"
                return
            elif choice == len(instances) + 2:
                print "Kill"
                return


if __name__ == "__main__":
    ws = websocket.create_connection("ws://192.168.1.132:8888/ws")
    instances = list_instances()
    print request('get_ports test1')
    if len(instances) > 0:
        menu(instances)
    #print request(ws, 'kill test4')
    #print request(ws, 'create test2 capra')
    #print request(ws, 'kill test1')

    ws.close()