import pygame, sys, os, random
from PodSixNet.Connection import ConnectionListener, connection

# eliminations
# cancel search button
# add 'matchmaking' text

# Changelog
    # change 'ready' action to toggle

# add powers
    # Virtual Matter- Pixels of that player's color randomly spawn and despawn
        # in a radius around them; can only kill opponents if hit in the head.

pygame.init()
WHITE = (255,255,255)
BLACK = (0,0,0)
COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')
FONT = pygame.font.Font('Assets\\ror.ttf', 20)
checkmarkImg = pygame.image.load('Assets\\checkmark.png')

class Checkbox:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, 40, 40)
        self.color = (200,200,200)
        self.checkmark = False

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.checkmark = not self.checkmark
                if game.searching:
                    if self.checkmark:
                        game.buttons[0].color = (0,200,0)
                        game.Send({"action":"toggleReady", "ready": True})
                    else:
                        game.buttons[0].color = (200,0,0)
                        game.Send({"action":"toggleReady", "ready": False})
 
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, 40, 40))
        pygame.draw.rect(screen, (0,0,0), (self.x+2, self.y+2, 35, 35))
        if self.checkmark: screen.blit(checkmarkImg, (self.x-25, self.y-37))

class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    if game.connected:
                        game.username = self.text
                        game.Send({"action":"usernameEntered", "username":game.username})
                        self.text = ''
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = FONT.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        self.rect.w = max(200, self.txt_surface.get_width()+10)

    def draw(self, screen):
        game.screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pygame.draw.rect(game.screen, self.color, self.rect, 2)


class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, text, color=(255,255,255), textColor=(0)):
        pygame.sprite.Sprite.__init__(self)
        self.rect = pygame.Rect((x,y,w,h))
        self.text = text
        self.color = color
        self.textColor = textColor
        self.soundFlag = False
        self.showBorder = False

    def update(self, event):
        # update flags for glow and mouseover
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos[0], pos[1]):
            if self.soundFlag:
                play_sound('Assets\\mouseover.wav')
            self.soundFlag = False
            self.showBorder = True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                #play_sound('Assets\\select.wav')
                if self.text == 'Quit':
                    pygame.quit()
                    sys.exit()
                elif self.text == 'Search':
                    if game.connected:
                        game.searching = True
                        game.Send({"action":"startSearch"})
                        game.buttons = [game.readybtn]
                elif self.text == 'Main menu':
                    game.waitingForInput = False
                elif self.text == 'Ready':
                    game.checkbox.checkmark = not game.checkbox.checkmark
                    if game.checkbox.checkmark:
                        game.buttons[0].color = (0,200,0)
                        game.Send({"action":"toggleReady", "ready": True})
                    else:
                        game.buttons[0].color = (200,0,0)
                        game.Send({"action":"toggleReady", "ready": False})
        else:
            self.showBorder = False
            self.soundFlag = True

    def draw(self):
        if self.showBorder:
            pygame.draw.rect(game.screen, (140,0,20), (self.rect.x-3, self.rect.y-3, self.rect.w+6, self.rect.h+6), 5)
        pygame.draw.rect(game.screen, self.color, self.rect)
        drawText(self.text, 20, self.rect.x+(self.rect.w//2), self.rect.y+(self.rect.h//2), self.textColor, True)

class Game(ConnectionListener):
    def __init__(self):
        # initialize pygame
        width, height = 1200, 700
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Pytron")
        self.clock = pygame.time.Clock()
        self.colors = [(255,0,0), (0,255,0), (0,0,255), (0,255,255)]
        self.username = None
            
    # Recieve data from server
    def Network(self, data):
        pass

    def Network_connected(self, data):
        self.timeout = 0
        self.connected = True

    def Network_playerConnected(self, data):
        self.playersConnected = data["playersconnected"]

    def Network_playerReady(self, data):
        self.playersReady = data["playersReady"]

    def Network_startgame(self, data):
        self.startgame = True

    def Network_updateTimer(self, data):
        self.timer = data["timer"]

    def Network_playerPositions(self, data):
        self.playerPositions[data["playernum"]] = (data["playerx"], data["playery"], data["playerdir"])

    def Network_endofgame(self, data):
        self.winner = data["winner"]
        self.winnerNum = data["playernum"]
        if isinstance(self.winner, int):
            self.winner = 'Player ' + str(self.winner+1)
        self.running = False
        self.timer = 3

    def Network_lobbyClosed(self, data):
        print('A player has disconnected.')
        

    def mainmenu(self):
        self.username = None
        self.startgame = False
        self.connected = False
        self.waitingToConnect = False
        self.framecount = 0
        self.timeout = 0
        self.playersConnected = []
        self.searching = False
        self.playersReady = 0
        self.playerPositions = {}
        self.startbtn = Button(500,700-100,150,50,'Search')
        self.readybtn = Button(500,700-100,150,50,'Ready',(200,0,0))
        self.buttons = [self.startbtn]
        path = []
        direction = 4
        color = random.choice(self.colors)
        x,y = (20,350)
        self.box = InputBox(130, 655, 300, 32)
        self.checkbox = Checkbox(675, 700-95)
        while not self.startgame:
            self.framecount += 1
            # Attempt connnection to server every 60 seconds
            if not self.waitingToConnect and not self.connected:
                self.Connect(('98.214.123.43', 8001))
                #self.Connect(('localhost', 8000))
                self.waitingToConnect = True

            # check connection
            if self.framecount % (60*5) == 0:
                self.waitingToConnect = False
                try:
                    self.Send({"action":"ruThere"})
                except Exception as e:
                    print(e)
                self.timeout += 1
                if self.timeout >= 2:
                    self.searching = False
                    self.connected = False
                    self.buttons = [self.startbtn]

            # process user input
            for event in pygame.event.get():
                if event.type == pygame.QUIT: # 'close' button
                    pygame.quit()
                    sys.exit()
                for button in self.buttons:
                    button.update(event)
                self.box.handle_event(event)
                self.checkbox.handleEvent(event)
            self.box.update()
            # update bot
            if y <= 0: y = 690
            elif y >= 700: y = 0
            if x <= 0: x = 1190
            elif x >= 1200: x = 10
            if direction == 1:
                y -= 5
            elif direction == 2:
                y += 5
            elif direction == 3:
                x -= 5
            elif direction == 4:
                x += 5
            path.append((x,y))
            if len(path) > 60*20: path.pop(0)

            # draw bg, buttons, and text
            self.screen.fill(0)
            for x,y in path:
                pygame.draw.rect(self.screen, color, (x, y, 5, 5))
            if random.random() < 0.02:
                if direction <= 2: direction = random.randint(3,4)
                elif direction > 2: direction = random.randint(1,2)
            for button in self.buttons:
                button.draw()
            drawText('Username:', 20, 15, 660)
            if self.username is not None:
                drawText(self.username, 20, 130, 660, (0,255,255))
            else:
                self.box.draw(self.screen)
            if self.connected:
                drawText('Connected to server', 20, 15, 15)
            else:
                drawText('Not connected to server', 20, 15, 15)
            if self.searching:
                self.checkbox.draw(self.screen)
                drawText('Players connected: ', 20, 15, 225)
                for i, player in enumerate(self.playersConnected):
                    drawText(f'{player}', 20, 15, 250+(i*25), self.colors[i])
                drawText(f'Players ready: {self.playersReady}', 20, 15, 625)

            # pump connection (if there is one)
            self.Pump()
            connection.Pump()
            # update the screen
            pygame.display.flip()
            self.clock.tick(60)

    def mainGameLoop(self):
        self.screen.fill(0)
        self.running = True
        lastKnownCoords = [0,0,0,0]
        while self.running:
            # process user input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            if self.timer is None:
                # update player on server
                keys = pygame.key.get_pressed()
                if keys[pygame.K_w]:
                    self.Send({"action":"changeDirection", "dir":"up"})
                elif keys[pygame.K_a]:
                    self.Send({"action":"changeDirection", "dir":"left"})
                elif keys[pygame.K_s]:
                    self.Send({"action":"changeDirection", "dir":"down"})
                elif keys[pygame.K_d]:
                    self.Send({"action":"changeDirection", "dir":"right"})
            else:
                self.screen.fill(0)
                drawText(str(self.timer), 75, 1200//2, 700//2, center=True)
                if self.timer == 0:
                    self.screen.fill(0)

            # draw players and trails
            for playernum in self.playerPositions:
                x,y,direction = self.playerPositions.get(playernum)
                # path extrapolation
                if lastKnownCoords[playernum] == (x,y):# and player not eliminated:
                    if direction == 'up':
                        y -= 5
                    elif direction == 'down':
                        y += 5
                    elif direction == 'left':
                        x -= 5
                    elif direction == 'right':
                        x += 5
                lastKnownCoords[playernum] = (x,y)
                pygame.draw.rect(self.screen, self.colors[playernum], (x, y, 5, 5))

            connection.Pump()
            self.Pump()
            pygame.display.flip()
            self.clock.tick(60)

    def gameOver(self):
        self.endgamebg = self.screen.copy()
        self.mmbtn = Button(500,700-100,150,50,'Main menu')
        self.buttons = [self.mmbtn]
        self.waitingForInput = True
        while self.waitingForInput:
            # process user input
            for event in pygame.event.get():
                if event.type == pygame.QUIT: # 'close' button
                    pygame.quit()
                    sys.exit()
                for button in self.buttons:
                    button.update(event)

            # draw players and trails
            self.screen.blit(self.endgamebg, (0,0))
            drawText('Game over! The winner is ', 50, 1200//2-100, 700//2, (0,200,200), True)
            drawText(str(self.winner), 50, 1200//2+240, 700//2-30, self.colors[self.winnerNum])
            for button in self.buttons:
                button.draw()
            # communicate with server
            connection.Pump()
            self.Pump()
            # update the screen
            pygame.display.flip()
            self.clock.tick(60)

_image_library = {}
def get_image(path):
    global _image_library
    image = _image_library.get(path)
    if image == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path).convert_alpha()
        _image_library[path] = image
    return image

_sound_library = {}
def play_sound(path):
    global _sound_library
    sound = _sound_library.get(path)
    if sound == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        sound = pygame.mixer.Sound(canonicalized_path)
        _sound_library[path] = sound
    sound.play()

def drawText(text, size, x, y, color=WHITE, center=False):
    font = pygame.font.Font("Assets\\ror.ttf", size)
    text = font.render(text, True, color)
    if center:
        game.screen.blit(text, (x - (text.get_width() // 2), y - (text.get_height() // 2)))
    else:
        game.screen.blit(text, (x, y))

if __name__ == "__main__":
    game = Game()
    while True:
        game.mainmenu()
        game.mainGameLoop()
        game.gameOver()
