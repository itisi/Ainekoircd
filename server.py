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
    def remove(self, nick):
        self.nicks.discard(nick)
    def message(self, client, message, excludeme=True):
        for nick in self.nicks:
            if nick != client or not excludeme:
                mess = ":%s PRIVMSG %s :%s" % (client.hostmask(), self.name, message)
                nick.send(mess)
    def raw(self, message, client=False, excludeme=True):
        for nick in self.nicks:
            if nick != client or not excludeme:
                nick.send(message)
class Server:
    def __init__(self):
        self.port = 6667
        self.host = "216.151.3.132"
        self.connections = []
        self.nicks = {}
        self.channels = {}
        self.servername = "lol.lol.lol"
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
    def pinger(self):
        while 1:
            curtime = time.time()
            time.sleep(30)
            for nick in self.connections:
                if (curtime - nick.lastcontact) > 90:
                    nick.quit("Ping Timeout")
                else:
                    nick.send("PING :%s" % (self.servername))
        
class Client:
    def __init__(self, parent, conn, addr):
        self.server = parent
        self.connection = conn
        self.address = addr
        self.initialized = False
        self.lastcontact = time.time()
        self.connected = self.lastcontact
        self.channels = set()
        self.nick = False
        self.realname = False
        self.user = False
        self.hasquit = False
    def servsend(self, message): #sends :servername <message>
        self.send(":%s %s " % (self.server.servername, message))
    def hostmask(self): #returns nick!user@host
        return "%s!%s@%s" % (self.nick, self.user, self.host)
    def contactweb(self, exclude=[]): #returns all of the users that can see you in at least one channel (used for quits and nicks)
        users = set()
        for channel in self.channels:
            for nick in channel.nicks:
                if not nick in exclude:
                    users.add(nick)
        return users
    def quit(self, message="Quitting"):
        self.hasquit = True
        for user in self.contactweb([self]):
            user.send(":%s QUIT :%s" % (self.hostmask(), message))
        for channel in self.channels:
            channel.remove(self)
        self.server.connections.remove(self)
        if self.nick and self.nick.lower() in self.server.nicks: #The only time this won't be true is if the user pings out before sending a valid NICK command.
            del(self.server.nicks[self.nick.lower()])
        try:
            self.connection.close()
        except:
            pass
    def send(self, message):
        try:
            self.connection.send(message + "\r\n")
        except: #should have exception values eventually to differentiate connection reset by peer from other issues.
            pass #quit the client
        print message        
    def run(self):
        try:
            self.host = socket.gethostbyaddr(self.address[0])[0] #this isn't in init to avoid hostname lookup latency preventing new connections.
            while 1:
                for line in self.getlines():
                    self.handle(line)
        except:
            traceback.print_exc()
    def getlines(self):
        message = ""
        runtime = 0
        while message.rfind("\n") == -1 or message.rfind("\n") != len(message) - 1:
            try:
                receive = self.connection.recv(1024)
            except: #this should be expanded on with proper except codes
                if not self.hasquit:
                    self.quit("Connection reset by peer")
            else:
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
        parts = line.split(" ",2)
        while len(parts) <= 3:
            parts.append("")
        if parts[0] == "PING":
            self.servsend("PONG " + "%s :%s" % (self.server.servername, parts[1]))
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
