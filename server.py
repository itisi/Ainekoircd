import socket
import thread
import time
import traceback
import irc
class Channel():
    def __init__(self, server, name):
        self.nicks = set()
        self.server = server
        self.name = name
    def append(self, nick):
        self.nicks.add(nick)
    def message(self, client, message):
        for nick in self.nicks:
            if nick != client:
                mess = ":%s PRIVMSG %s :%s" % (client.hostmask(), self.name, message)
                client.send(mess)
class Server:
    def __init__(self):
        self.port = 6666
        self.host = ""
        self.connections = []
        self.nicks = {}
        self.channels = {}
    def run(self):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.allow_reuse_address = True
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((self.host, self.port))
        self.listener.listen(1)
        while 1:
            conn, addr = self.listener.accept()
            client = Client(self, conn, addr)
            self.connections.append(client)
            thread.start_new_thread(client.run,())
            print 'Connected by', client.address
        
class Client:
    def __init__(self, parent, conn, addr):
        self.server = parent
        self.connection = conn
        self.address = addr
        self.initialized = False
        self.lastcontact = time.time()
        self.connected = self.lastcontact
    def servsend(self, message):
        self.connection.send(":lol.lol.lol " + message + "\r\n")
        print ":lol.lol.lol " + message
    def hostmask(self):
        return "%s!%s@%s" % (self.nick, self.user, self.host)
    def send(self, message):
        self.connection.send(message + "\r\n")
        print message        
    def run(self):
        self.host = socket.gethostbyaddr(self.address[0])[0] #this isn't in init to avoid hostname lookup latency preventing new connections.
        while 1:
            for line in self.getlines():
                self.handle(line)
    def getlines(self):
        message = ""
        runtime = 0
        while message.rfind("\n") == -1 or message.rfind("\n") != len(message) - 1:
            receive = self.connection.recv(1024)
            message += receive
            if not runtime:
                starttime = time.time()
            elif time() - starttime > 10:
                print "Client did something unexpected. Attempting to recover."
                break
        return message.splitlines()
    def handle(self,line):
        self.lastcontact = time.time()
        print line
        parts = line.split(" ",3)
        while len(parts) <= 3:
            parts.append("")
        if parts[0] == "PING":
            self.servsend("PONG " + "lol.lol.lol :" + parts[1])
        elif parts[0] == "PRIVMSG" and parts[2] == ":.reload":
            try:
                reload(irc)
                irc.refresh(self)
                reload(irc)
                self.speak(parts[2],"Reload Successful")    
            except:
                self.speak(parts[2],"Reload Failed")
                traceback.print_exc()
                
        else:
            try:
                irc.handle(self.server, self, parts) #passed on to parser
            except:
                traceback.print_exc()

if __name__ == '__main__':
    serv = Server()
    serv.run()
