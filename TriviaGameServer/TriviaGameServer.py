import socket
import time
import threading

HEADER = 64
SERVERIP = socket.gethostbyname(socket.gethostname())
SERVERPORT =  6666
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "Disconnect"
GAMESTARTED_MESSAGE = "Game Already Started"
ImageSend_Message = "Incoming Image"
ASKFORDISCONNECT_MESSAGE = "Exit Game"
PLAYERNAME_MESSAGE = "Player Name:"
SERVERADDR = (SERVERIP, SERVERPORT)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
questionPath = r"dist\questions.txt"
server.bind(SERVERADDR)

global start
start = False


def sendConnectionMessage(msg, connection):
    encodedMsg = msg.encode(FORMAT)
    msg_length = len(encodedMsg)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    connection.send(send_length)
    connection.send(encodedMsg)


def sendConnectionImage(image, connection):
    sendConnectionMessage(ImageSend_Message)
    
    #do magic

def recieveMessageFromConnection(connection):
    msg_lenght = connection.recv(HEADER).decode(FORMAT)
    if msg_lenght:
        msg_lenght = int(msg_lenght)
        receivedMessage = connection.recv(msg_lenght).decode(FORMAT)
        return receivedMessage

class QuestionList:
    def __init__(self, qpath):
        self.qList=[]
        qfile=open(qpath, "r")
        line = True
        while line:
            newQ=[]
            line = qfile.readline()
            if line.startswith("!image "):
                newQ.append(line[7:])
                newQhasImage = True
                newQImagePath = qfile.readline()
            else:
                newQ.append(line)
                newQhasImage = False
                newQImagePath = ""
            
            for i in range(4):
                line = qfile.readline()
                newQ.append(line)
            self.qList.append(Question(newQ, newQhasImage, newQImagePath))
            line = qfile.readline()
        qfile.close()


class Question:
    def __init__(self, qnaList, hasImage, imagepath):
        self.Question = qnaList[0]
        self.Answers=[]
        for i in range(4):
            self.Answers.append(qnaList[i+1])
        self.hasImage = hasImage
        self.imagepath = imagepath

class PlayerList:

    def __init__(self):
        self.PList = []
    
    def sendAllPlayers(self, msg):
        for player in self.PList:
            player.sendMessage(msg)
    
    def disconnectAllPlayers(self):
        for player in self.PList:
            player.disconnect()

    def add(self, player):
        self.PList.append(player)

class Player:

    def __init__(self, Connection, Address, Name):
        self.playerConnection = Connection
        self.playerAddress = Address
        self.playerName = Name
        self.playerID = f"{self.playerName}[{self.playerAddress[0]}{self.playerAddress[1]}]"
        self.listeningThread = threading.Thread(target=self.Listen, daemon=True, args=())
        self.connected = True
        self.startListening()
        self.messageList = []


    def startListening(self):
        self.listeningThread.start()

    def Listen(self):
        while self.connected:
            msg_lenght = self.playerConnection.recv(HEADER).decode(FORMAT)
            if msg_lenght:
                msg_lenght = int(msg_lenght)
                receivedMessage = self.playerConnection.recv(msg_lenght).decode(FORMAT)

                self.messageList.append(receivedMessage)

                if receivedMessage == DISCONNECT_MESSAGE:
                    self.playerConnection.close()
                    self.connected = False
                    print(f"{self.playerID} Disconnected From Server")
                    time.sleep(2)
                    break
            


    def disconnect(self):
        self.sendMessage(ASKFORDISCONNECT_MESSAGE)

    def sendMessage(self, msg):
        if self.connected:
            print(f"Sent {msg} to {self.playerID}")
            sendConnectionMessage(msg, self.playerConnection)

    def sendImage(self, image):
        if self.connected:
            sendConnectionImage(image, self.playerConnection)



def listenForNewPlayers():
    server.listen()
    while True:
        try:
            (newPlayerConnection, PlayerAddress) = server.accept()
            if not start:
                newPlayerName = recieveMessageFromConnection(newPlayerConnection)
                playerList.add(Player(newPlayerConnection, PlayerAddress, newPlayerName))
                print(f"{playerList.PList[-1].playerID} Joined")
            else:
                rejectedPlayerName = recieveMessageFromConnection(newPlayerConnection)
                sendConnectionMessage(GAMESTARTED_MESSAGE, newPlayerConnection)
                newPlayerConnection.close()
        except:
            pass #there is no war in ba sing se


questionList = QuestionList(questionPath)
playerList = PlayerList()

print(f"Server started {socket.gethostbyname(socket.gethostname())}:{SERVERPORT}")

listenForNewPlayersThread = threading.Thread(target=listenForNewPlayers, daemon=True, args=())
listenForNewPlayersThread.start()

while not start:
    startInput = input("---Start Game? Y/N--- \n")
    if startInput == "Y":
        start = True
    else:
        if startInput == "N":
            start = False
        else:
            print("Enter only Y/N")

time.sleep(5)

playerList.sendAllPlayers("Hewwo")

time.sleep(5)

playerList.disconnectAllPlayers()

time.sleep(150)
server.close()