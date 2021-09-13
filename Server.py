import PodSixNet, time, pygame
from time import sleep
from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
import urllib.request
import socket

# Recieve data from client
class ClientChannel(Channel):

    def Network(self, data):
        pass

    def Network_ruThere(self, data):
        self.Send({"action":"connected"})

    def Network_usernameEntered(self, data):
        if myserver.queue is not None:
            if self in myserver.queue.players:
                myserver.clientsConnected[myserver.clientsConnected.index(self.username)] = data["username"]
                self.username = data["username"]
                for player in myserver.queue.players:
                    player.Send({"action":"playerConnected", "playersconnected":myserver.clientsConnected})
        self.username = data["username"]


    def Network_startSearch(self, data):
        self._server.matchmaking(self)

    def Network_toggleReady(self, data):
        self._server.toggle_ready(self, data["ready"])

    def Network_changeDirection(self, data):
        self._server.changeDirection(self.num, self.gameid, data["dir"])
    
    def Close(self):
        # if user in game, disconnect everyone else and close the lobby
        if self.gameid != None:
            try:
                game = [a for a in myserver.games if a.gameid == self.gameid][0]
                game.players.remove(self)
                game.remainingPlayers.remove(self.num)
            except: pass
        # if user in queue, decrement connected/readied players
        if myserver.queue is not None:
            if self in myserver.queue.players:
                if self in myserver.clientsReady: # if player is readied
                    myserver.clientsReady.remove(self) # remove from ready list
                myserver.clientsConnected.remove(self.username)
                myserver.queue.players.remove(self)
                for player in myserver.queue.players: # refresh other clients' vars
                    player.Send({"action":"playerConnected", "playersconnected":myserver.clientsConnected})
                    player.Send({"action":"playerReady", "playersReady":len(myserver.clientsReady)})
                if not myserver.clientsConnected: # if player was the only one in queue
                    print('Queue has been reset.')
                    myserver.queue = None


class MyServer(Server):
    def __init__(self, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.currentIndex=0
        self.games = []
        self.queue = None
    channelClass = ClientChannel

    def Connected(self, channel, addr):
        channel.gameid = None
        channel.num = None
        channel.x = None
        channel.y = None
        channel.direction = None
        channel.hitTrail = False
        channel.username = None
        channel.Send({"action":"connected"})

    def matchmaking(self, client):
        if self.queue == None: # if no one is searching for a match
            self.currentIndex += 1
            self.queue = Game(self.currentIndex, [client]) # add new game instance to queue
            if client.username is None:
                client.username = "Player 1"
            client.num = 1
            self.clientsConnected = [client.username]
            self.clientsReady = []
            client.Send({"action":"playerConnected", "playersconnected":self.clientsConnected})
            print(f'Game instance with game ID # {self.queue.gameid} has been initialized.')
        else: # if someone is in queue
            client.num = len(self.clientsConnected)+1
            if client.username is None:
                client.username = f"Player {client.num}"
            self.clientsConnected.append(client.username)
            self.queue.players.append(client) # put client in players list
            for player in self.queue.players:
                player.Send({"action":"playerConnected", "playersconnected":self.clientsConnected})
                player.Send({"action":"playerReady", "playersReady":len(self.clientsReady)})

    def toggle_ready(self, client, ready):
        if ready and client not in self.clientsReady:
            self.clientsReady.append(client)
        elif not ready and client in self.clientsReady:
            self.clientsReady.remove(client)
        for player in self.queue.players:
            player.Send({"action":"playerReady", "playersReady":len(self.clientsReady)})
        if (len(self.clientsReady) == len(self.queue.players) and len(self.clientsReady) > 1):
            self.startGame()

    def startGame(self):
        # start if everyone (>1 person) is ready
            i = 0
            for player in self.queue.players:
                player.Send({"action":"startgame"})
                player.num = i
                i += 1
            self.queue.initGame()
            self.games.append(self.queue)
            print(f'Game # {self.queue.gameid} has started with {len(self.queue.players)} players.')
            self.queue = None

    def changeDirection(self, num, gameid, direction):
        game = [a for a in self.games if a.gameid == gameid]
        try: game[0].changeDirection(num, direction)
        except: pass

        
class Game:
    def __init__(self, gameid, player):
        self.players = player # list of references to the client objects
        self.gameid = gameid
        self.paths = []
        self.remainingPlayers = []
        self.framecount = 0
        self.match_timer = 0

    def initGame(self):
        for player in self.players:
            self.remainingPlayers.append(player)
            player.gameid = self.gameid
            if player.num == 0: player.x, player.y, player.direction = (600, 680, 'up')
            elif player.num == 1: player.x, player.y, player.direction = (600, 20, 'down')
            elif player.num == 2: player.x, player.y, player.direction = (1180, 350, 'left')
            elif player.num == 3: player.x, player.y, player.direction = (20, 350, 'right')

    def changeDirection(self, num, direction):
        # player input has been recieved and is being passed to the main game loop vars
        player = [a for a in self.players if a.num == num][0]
        player.direction = direction

    def mainLoop(self):
        # Update all players, send out data, repeat
        for player in self.players:
            if not player.hitTrail:
                # border collision
                if player.y <= 0: player.y = 690
                elif player.y >= 700: player.y = 0
                if player.x <= 0: player.x = 1190
                elif player.x >= 1200: player.x = 10

                if self.framecount > 180:
                    # move
                    self.paths.append((player.x,player.y))
                    if player.direction == 'up':
                        player.y -= 5
                    elif player.direction == 'down':
                        player.y += 5
                    elif player.direction == 'left':
                        player.x -= 5
                    elif player.direction == 'right':
                        player.x += 5

                    # elimination/end of game
                    if (player.x,player.y) in self.paths:
                        player.hitTrail = True
                        self.remainingPlayers.remove(player)
                if self.framecount % 60 == 0 and self.framecount // 60 < 4:
                    player.Send({"action":"updateTimer", "timer":3-self.framecount // 60})
                else:
                    player.Send({"action":"updateTimer", "timer":None})

                    # send clients elimination data 
                if len(self.remainingPlayers) == 1:
                    self.winner = self.remainingPlayers[0]
                    self.winner_num = self.winner.num
                    if self.winner.username is not None:
                        self.winner = self.winner.username
                    else:
                        self.winner = self.winner.num
                    for player in self.players:
                        player.Send({"action":"endofgame", "winner":self.winner, "playernum":self.winner_num})
                    myserver.games.remove(self) # dereference game instance
                    print(f'Game # {self.gameid} has ended.')
                    break

        for user in self.players: # for each user in game
            for player in self.players: # send every players info
                user.Send({"action":"playerPositions", "playernum":player.num, "playerx":player.x, "playery":player.y, "playerdir":player.direction})
        self.framecount += 1

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == "__main__":
    external_ip = urllib.request.urlopen('https://ipv4bot.whatismyipaddress.com').read().decode('utf8')
    print(f'Server address: {external_ip}')
    print(f'Port 8001 must be forwarded to {get_ip()} in order to recieve connections.\n')
    myserver = MyServer(localaddr=(get_ip(), 8001))
    print('Server established. Listening for connections...')
    pygame.init()
    clock = pygame.time.Clock()
    while True:
        for game in myserver.games:
            game.mainLoop()
        myserver.Pump()
        clock.tick(60)
