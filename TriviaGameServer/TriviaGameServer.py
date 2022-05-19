import socket
import time
import threading
import random
import tkinter
from PIL import Image,ImageTk

HEADER = 64

FORMAT = "utf-8"
DISCONNECT_MESSAGE = "Disconnect"
GAMESTARTED_MESSAGE = "Game Already Started"
ImageSend_Message = "Incoming Image"
ASKFORDISCONNECT_MESSAGE = "Exit Game"
PLAYERNAME_MESSAGE = "Player Name:"
QUESTION_MESSAGE = "Question: "
DIVIDER_MESSAGE ="!!!"
QUESTIONHASIMAGE_MESSAGE = "!IMAGE "
ANSWERTOQUESTION_MESSAGE = "!ANSWER: "
ISANSWERCORRECT_MESSAGE = "!ISCORRECT: "
GAMESTATS_MESSAGE = "!STATS: "
PUBLIC_MESSAGE = "!PUBLICMESSAGE: "
questionPath = r"dist\questions.txt"
gameStarted = False

def addToNetworkInfo(text):
      networkInfo.config(state=tkinter.NORMAL)
      networkInfo.insert(tkinter.END, text)
      networkInfo.config(state=tkinter.DISABLED)

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
            if line.startswith(QUESTIONHASIMAGE_MESSAGE):
                newQ.append(line[len(QUESTIONHASIMAGE_MESSAGE):].strip())
                newQhasImage = True
                newQImagePath = qfile.readline()
            else:
                newQ.append(line.strip())
                newQhasImage = False
                newQImagePath = ""
            
            for i in range(4):
                line = qfile.readline()
                newQ.append(line.strip())
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

    def getAnswersInRandom(self):
        shuffledAnswers = random.sample(self.Answers, len(self.Answers))
        return shuffledAnswers

class PlayerList:

    def __init__(self):
        self.PList = []
    
    def sendAllPlayers(self, msg):
        for player in self.PList:
            player.sendMessage(msg)
    
    def sendAllPlayersQuestion(self, question):
        for player in self.PList:
            player.sendQuestion(question)

    def sendAllPlayersIfCorrect(self):
        for player in self.PList:
            player.sendIfCorrect()

    def disconnectAllPlayers(self):
        for player in self.PList:
            player.disconnect()

    def add(self, player):
        self.PList.append(player)

    def sortByScores(self):
        for i in range(len(self.PList)):
            for j in range(len(self.PList)-i-1):
                if self.PList[j].score < self.PList[j+1].score:
                    self.PList[j], self.PList[j+1] = self.PList[j+1], self.PList[j]
    
    def sendPlayerScores(self):
        self.sortByScores()
        i = 1
        #DO SOMETHING ABOUT TIES!!!
        for player in self.PList:
            player.sendMessage(GAMESTATS_MESSAGE + str(i) + DIVIDER_MESSAGE +  str(len(self.PList)) + DIVIDER_MESSAGE + str(player.score))
            i = i + 1
    
    def clear(self):
        self.PList = []

class Player:

    def __init__(self, Connection, Address, Name):
        self.playerConnection = Connection
        self.playerAddress = Address
        self.playerName = Name
        self.playerID = f"{self.playerName}[{self.playerAddress[0]}{self.playerAddress[1]}]"
        self.playerColor = "#%06x" % random.randint(0, 0xFFFFFF)
        self.currentQuestion = ""
        self.isAnswerCorrect = False
        self.score = 0
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
                    addToNetworkInfo(f"{self.playerID} Disconnected From Server \n")
                    time.sleep(2)
                    break

                if receivedMessage.startswith(ANSWERTOQUESTION_MESSAGE):
                    if isinstance(self.currentQuestion, Question):
                        Answer = receivedMessage[len(ANSWERTOQUESTION_MESSAGE):]
                        addToNetworkInfo(f"{self.playerID} answered {Answer} \n")
                        if Answer == self.currentQuestion.Answers[0]:
                            self.score = self.score + 1
                            isAnswerCorrect = True
                        else:
                            isAnswerCorrect = False
                    continue

                if receivedMessage.startswith(PUBLIC_MESSAGE):
                    receivedPublicMessage = receivedMessage[len(PUBLIC_MESSAGE):]
                    playerList.sendAllPlayers(PUBLIC_MESSAGE+self.playerColor+DIVIDER_MESSAGE+self.playerID+": "+receivedPublicMessage)


    def disconnect(self):
        self.sendMessage(ASKFORDISCONNECT_MESSAGE)

    def sendIfCorrect(self):
        if self.isAnswerCorrect:
            self.sendMessage(ISANSWERCORRECT_MESSAGE + "YES")
        else: 
            self.sendMessage(ISANSWERCORRECT_MESSAGE + "NO")

    def sendMessage(self, msg):
        if self.connected:
            addToNetworkInfo(f"Sent {msg} to {self.playerID} \n")
            sendConnectionMessage(msg, self.playerConnection)

    def sendImage(self, image):
        if self.connected:
            sendConnectionImage(image, self.playerConnection)

    def sendQuestion(self, question):

        shuffledAnswers = question.getAnswersInRandom()

        self.currentQuestion = question
        self.isAnswerCorrect = False

        if question.hasImage:
            self.sendMessage(QUESTION_MESSAGE + QUESTIONHASIMAGE_MESSAGE + question.Question + DIVIDER_MESSAGE + shuffledAnswers[0] + DIVIDER_MESSAGE + shuffledAnswers[1] + DIVIDER_MESSAGE + shuffledAnswers[2] + DIVIDER_MESSAGE + shuffledAnswers[3])
        else:
            self.sendMessage(QUESTION_MESSAGE + question.Question + DIVIDER_MESSAGE + shuffledAnswers[0] + DIVIDER_MESSAGE + shuffledAnswers[1] + DIVIDER_MESSAGE + shuffledAnswers[2] + DIVIDER_MESSAGE + shuffledAnswers[3])

def listenForNewPlayers():
    try:
        server.listen()
        while True:
            (newPlayerConnection, PlayerAddress) = server.accept()
            if not gameStarted:
                newPlayerName = recieveMessageFromConnection(newPlayerConnection)
                playerList.add(Player(newPlayerConnection, PlayerAddress, newPlayerName))
                addToNetworkInfo(f"{playerList.PList[-1].playerID} Joined \n")
            else:
                rejectedPlayerName = recieveMessageFromConnection(newPlayerConnection)
                sendConnectionMessage(GAMESTARTED_MESSAGE, newPlayerConnection)
                newPlayerConnection.close()
    except:
        pass

questionList = QuestionList(questionPath)
playerList = PlayerList()

def startServer():
    global SERVERIP
    global SERVERPORT
    global SERVERADDR
    global server
    SERVERIP = EnterIP.get()
    SERVERPORT = EnterPort.get()

    try:
        if (SERVERIP == "" or SERVERPORT == "" or (not SERVERPORT.isnumeric)):
            raise ValueError
        SERVERPORT = int(SERVERPORT)
        SERVERADDR = (SERVERIP, SERVERPORT)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(SERVERADDR)
    except ValueError:
        addToNetworkInfo("Inputs Invalid \n")
    except:
        addToNetworkInfo("Couldn't start server \n")
    else:
        addToNetworkInfo(f"Server started {SERVERIP}:{SERVERPORT} \n")
        StartServerButton.config(state=tkinter.DISABLED)
        StartGameButton.config(state=tkinter.NORMAL)
        listenForNewPlayersThread = threading.Thread(target=listenForNewPlayers, daemon=True, args=())
        listenForNewPlayersThread.start()


def startGame():

    global gameStarted
    gameStarted = True

    if len(playerList.PList) > 0:

        for question in questionList.qList:
            playerList.sendAllPlayersQuestion(question)
            time.sleep(10)
            playerList.sendAllPlayersIfCorrect()
            time.sleep(5)

        playerList.sendPlayerScores()

        time.sleep(5)

        playerList.disconnectAllPlayers()
        playerList.clear()
        
        gameStarted = False
        StartServerButton.config(state=tkinter.NORMAL)
        StartGameButton.config(state=tkinter.DISABLED)

    else:
        addToNetworkInfo("No Current Players \n")
        StartServerButton.config(state=tkinter.NORMAL)
        StartGameButton.config(state=tkinter.DISABLED)
        server.close()
        gameStarted = False


windowWidth=345
windowHeight=640
ICONPATH = r"dist\TriviaGameIcon.ico"

serverWindow = tkinter.Tk()
serverWindow.geometry(f"{windowWidth}x{windowHeight}+40+40")
serverWindow.configure(bg="#404040")
serverWindow.attributes('-topmost', 1)
serverWindow.attributes('-topmost', 0)
serverWindow.title("TriviaGame Server")

iconphotoimage = ImageTk.PhotoImage(Image.open(ICONPATH))
serverWindow.iconphoto(False, iconphotoimage)
serverWindow.iconbitmap(default=ICONPATH)

networkInfo = tkinter.Text(serverWindow, width=40, height=35, bg = "black", fg = "white")
networkInfo.config(state=tkinter.DISABLED)
networkInfo.place(x=10,y=10)

IPLabel = tkinter.Label(serverWindow, text= "Ip Adress:", width=8, height=1, bg="#404040", fg="white", anchor=tkinter.W)
EnterIP = tkinter.Entry(serverWindow, width=16)
IPLabel.place(x=24, y=580)
EnterIP.place(x=24, y=603)
EnterIP.insert(tkinter.END, socket.gethostbyname(socket.gethostname()))

PortLabel = tkinter.Label(serverWindow, text="Port:", width=5, height=1, bg="#404040", fg="white", anchor=tkinter.W)
EnterPort = tkinter.Entry(serverWindow, width=8)
PortLabel.place(x=129, y=580)
EnterPort.place(x=129, y=603)

StartServerButton = tkinter.Button(serverWindow, text="start", command=startServer, width=8, height=0)
StartServerButton.place(x=186, y=600)

gameThread = threading.Thread(target=startGame, daemon=False, args=())

StartGameButton = tkinter.Button(serverWindow, text="play", command=gameThread.start, state="disabled" ,width=8, height=0)
StartGameButton.place(x=255, y=600)

def on_closing():
    playerList.disconnectAllPlayers()
    serverWindow.destroy()
    quit()

serverWindow.protocol("WM_DELETE_WINDOW", on_closing)

serverWindow.mainloop() 