import traceback
import string
from server import Channel
allowedchars = string.letters + string.digits + "_"

def refresh(): #called when this module is reloaded. this should reload all modules it loads that are subject to change
    pass
def handle(server, client, message):
    if "cmd_" + message[0].lower() in globals():
        try:
            globals()["cmd_" + message[0].lower()](server, client, message)
        except:
            traceback.print_exc()
def cmd_nick(server, client, message):
    nick = message[1]
    if nick.lower() in server.nicks:
        client.servsend("433 * " + nick + " :Nickname is already in use")
        return 0
    if not len(nick):
        client.servsend("431 :No nickname given")
        return 0
    for char in nick:
        if not char in allowedchars:
            client.servsend("432 " + nick + " :Erroneous Nickname: Illegal characters")
            return 0
    client.nick = nick
    server.nicks[nick.lower()] = client
def cmd_user(server, client, message):
    if not client.initialized:
        client.initialized = True
    user = message[1]
    endparts = message[2].split(" ",2)
    if len(endparts) != 3:
        client.realname = ""
    else:
        if endparts[2][0] == ":":
            client.realname = endparts[2][1:]
        else:
            client.realname = endparts[2]
    for char in user:
        if not char in allowedchars:
            client.servsend("I PITY THE FOOL THAT TRIES TO USE A BAD USERNAME")
            client.connection.close()
            return 0
    client.user = user
    client.servsend("001 %s :Welcome to the AINEKO IRC Network %s!%s@%s" % (client.nick, client.nick, client.user, client.host))
    client.servsend("422 %s :MOTD File is missing" % (client.nick))
def cmd_join(server, client, message):
    for channel in message[1].split(","):
        good = False
        if channel.lower() in server.channels:
            good = True
            server.channels[channel.lower()].append(client)
        else:
            if channel[0] == "#":
                good = True
                chan = Channel(server,channel)
                chan.append(client)
                server.channels[channel.lower()] = chan
        if good:
            chan = server.channels[channel.lower()]
            nicks = []
            for nick in chan.nicks:
                nick.send(":%s JOIN :%s" % (client.hostmask(), channel))
                nicks.append(nick.nick)
            client.servsend("353 %s = %s :%s" % (client.nick, channel, " ".join(nicks)))
            client.servsend("366 %s %s :End of /NAMES list." % (client.nick, channel))
def cmd_privmsg(server, client, message):
    if message[1][0] == "#":
        if message[1].lower() in server.channels:
            channel = server.channels[message[1].lower()]
            for nick in channel.nicks:
                if nick != client:
                    nick.send(":%s PRIVMSG %s :%s" % (client.hostmask(), channel.name, message[2][1:]))
    else:
        if message[1].lower() in server.nicks:
            nick = server.nicks[message[1].lower()]
            nick.send(":%s PRIVMSG %s :%s" % (client.hostmask(), channel.name, message[2][1:]))
