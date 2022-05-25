import socket
import time
import threading
import random
import tkinter
from PIL import Image, ImageTk
import timeit

HEADER = 64
imageBuffer = 2048
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "Disconnect"
GAMESTARTED_MESSAGE = "Game Already Started"
ASKFORDISCONNECT_MESSAGE = "Exit Game"
PLAYERNAME_MESSAGE = "Player Name:"
QUESTION_MESSAGE = "Question: "
DIVIDER_MESSAGE = "!!!"
QUESTIONHASIMAGE_MESSAGE = "!IMAGE "
ANSWERTOQUESTION_MESSAGE = "!ANSWER: "
ISANSWERCORRECT_MESSAGE = "!ISCORRECT: "
GAMESTATS_MESSAGE = "!STATS: "
PUBLIC_MESSAGE = "!PUBLICMESSAGE: "
configPath = "dist\config.txt"
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


def sendImage(imagepath):
    addToNetworkInfo("Sending Image... \n")
    f=open(imagepath,"rb")
    data = f.read(imageBuffer)
    while (data):
        if(udpServer.sendto(data,SERVERADDR)):
            data = f.read(imageBuffer)
            time.sleep(0.0001)
    f.close()
    addToNetworkInfo("Image Sent \n")

def recieveMessageFromConnection(connection):
    msg_lenght = connection.recv(HEADER).decode(FORMAT)
    if msg_lenght:
        msg_lenght = int(msg_lenght)
        receivedMessage = connection.recv(msg_lenght).decode(FORMAT)
        return receivedMessage


def readFile(path):

    FileData = []
    ConfigData = []
    QuestionData = []

    file = open(path, "r")

    line = file.readline()
    if line == "Config:\n":
        line = file.readline()
        line = file.readline()
        while line != "\n":
            ConfigData.append(line.strip())
            line = file.readline()

    FileData.append(ConfigData)

    line = file.readline()
    if line == "Questions:\n":
        line = file.readline()
        while line.strip() != "QuestionsEND":
            newQ = []
            newQnAList = []

            line = file.readline()

            if line.startswith(QUESTIONHASIMAGE_MESSAGE):
                newQnAList.append(line[len(QUESTIONHASIMAGE_MESSAGE):].strip())
                newQhasImage = True
                newQImagePath = file.readline().strip()
            else:
                newQnAList.append(line.strip())
                newQhasImage = False
                newQImagePath = ""

            for i in range(4):
                line = file.readline()
                newQnAList.append(line.strip())

            newQ.append(newQnAList)
            newQ.append(newQhasImage)
            newQ.append(newQImagePath)
            QuestionData.append(newQ)

            line = file.readline()

        FileData.append(QuestionData)
    return FileData


def getConfig(configList):
    configurations = []

    defaultQuestionTime = 20
    defaultTimeBetweenQuestions = 5

    configurations.append(defaultQuestionTime)
    configurations.append(defaultTimeBetweenQuestions)

    for config in configList:
        config = config.split("=")
        config[0] = config[0].strip()
        config[1] = config[1].strip()
        if config[0] == "Question time":
            configurations[0] = int(config[1])
        if config[0] == "Time between questions":
            configurations[1] = int(config[1])

    return configurations


class QuestionList:

    def __init__(self, QuestionDataList):
        self.qList = []
        for QuestionData in QuestionDataList:
            self.qList.append(
                Question(QuestionData[0], QuestionData[1], QuestionData[2]))


class Question:

    def __init__(self, qnaList, hasImage, imagepath):
        self.Question = qnaList[0]
        self.Answers = []
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

    def removeDisconnected(self):
        for i in range(len(self.PList)):
            if not self.PList[i].connected:
                del self.PList[i]
                i = i-1

    def sortByScores(self):
        for i in range(len(self.PList)):
            for j in range(len(self.PList)-i-1):
                if self.PList[j].score < self.PList[j+1].score:
                    self.PList[j], self.PList[j +
                                              1] = self.PList[j+1], self.PList[j]

    def sendPlayerScores(self):
        self.sortByScores()

        self.PList[0].sendMessage(GAMESTATS_MESSAGE + "1" + DIVIDER_MESSAGE + str(
            len(self.PList)) + DIVIDER_MESSAGE + str(self.PList[0].score))

        placement = 1

        for i in range(1, len(self.PList)):
            if self.PList[i].score == self.PList[i-1].score:
                self.PList[i].sendMessage(GAMESTATS_MESSAGE + str(placement) + DIVIDER_MESSAGE + str(
                    len(self.PList)) + DIVIDER_MESSAGE + str(self.PList[i].score))
            else:
                placement = i+1
                self.PList[i].sendMessage(GAMESTATS_MESSAGE + str(placement) + DIVIDER_MESSAGE + str(
                    len(self.PList)) + DIVIDER_MESSAGE + str(self.PList[i].score))

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
                receivedMessage = self.playerConnection.recv(
                    msg_lenght).decode(FORMAT)

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
                            self.isAnswerCorrect = True
                        else:
                            self.isAnswerCorrect = False
                    continue

                if receivedMessage.startswith(PUBLIC_MESSAGE):
                    receivedPublicMessage = receivedMessage[len(
                        PUBLIC_MESSAGE):]
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

    def sendQuestion(self, question):

        shuffledAnswers = question.getAnswersInRandom()

        self.currentQuestion = question
        self.isAnswerCorrect = False

        if question.hasImage:
            self.sendMessage(QUESTION_MESSAGE + QUESTIONHASIMAGE_MESSAGE + str(timeForQuestions) + DIVIDER_MESSAGE + question.Question + DIVIDER_MESSAGE +
                             shuffledAnswers[0] + DIVIDER_MESSAGE + shuffledAnswers[1] + DIVIDER_MESSAGE + shuffledAnswers[2] + DIVIDER_MESSAGE + shuffledAnswers[3])

            sendImage(question.imagepath)

        else:
            self.sendMessage(QUESTION_MESSAGE + str(timeForQuestions) + DIVIDER_MESSAGE + question.Question + DIVIDER_MESSAGE +
                             shuffledAnswers[0] + DIVIDER_MESSAGE + shuffledAnswers[1] + DIVIDER_MESSAGE + shuffledAnswers[2] + DIVIDER_MESSAGE + shuffledAnswers[3])


def listenForNewPlayers():
    try:
        server.listen()
        while True:
            (newPlayerConnection, PlayerAddress) = server.accept()
            if not gameStarted:
                newPlayerName = recieveMessageFromConnection(
                    newPlayerConnection)
                playerList.add(Player(newPlayerConnection,
                               PlayerAddress, newPlayerName))
                addToNetworkInfo(f"{playerList.PList[-1].playerID} Joined \n")
            else:
                rejectedPlayerName = recieveMessageFromConnection(
                    newPlayerConnection)
                sendConnectionMessage(GAMESTARTED_MESSAGE, newPlayerConnection)
                newPlayerConnection.close()
    except:
        pass


FileData = readFile(configPath)
questionList = QuestionList(FileData[1])
playerList = PlayerList()
timeForQuestions, timeBetweenQuestions = getConfig(FileData[0])


def startServer():
    global SERVERIP
    global SERVERPORT
    global SERVERADDR
    global server
    global udpServer
    SERVERIP = EnterIP.get()
    SERVERPORT = EnterPort.get()

    try:
        if (SERVERIP == "" or SERVERPORT == "" or (not SERVERPORT.isnumeric)):
            raise ValueError
        SERVERPORT = int(SERVERPORT)
        SERVERADDR = (SERVERIP, SERVERPORT)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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

    playerList.removeDisconnected()

    if len(playerList.PList) > 0:

        for question in questionList.qList:
            playerList.sendAllPlayersQuestion(question)
            time.sleep(timeForQuestions+1)
            playerList.sendAllPlayersIfCorrect()
            time.sleep(timeBetweenQuestions)

        playerList.removeDisconnected()
        playerList.sendPlayerScores()

        time.sleep(5)

        playerList.removeDisconnected()
        playerList.disconnectAllPlayers()
        playerList.clear()
        server.close()
        gameStarted = False

        gameStarted = False
        StartServerButton.config(state=tkinter.NORMAL)
        StartGameButton.config(state=tkinter.DISABLED)

    else:
        addToNetworkInfo("No Current Players \n")
        gameStarted = False


windowWidth = 345
windowHeight = 640
ICONPATH = r"dist\TriviaGameIcon.ico"

serverWindow = tkinter.Tk()
serverWindow.geometry(f"{windowWidth}x{windowHeight}+40+40")
serverWindow.configure(bg="#404040")
# clientWindow.resizable(False, False)
serverWindow.title("TriviaGame Server")

iconphotoimage = ImageTk.PhotoImage(Image.open(ICONPATH))
serverWindow.iconphoto(False, iconphotoimage)
serverWindow.iconbitmap(default=ICONPATH)

networkInfo = tkinter.Text(serverWindow, width=40, height=35, bg="black", fg="white")
networkInfo.config(state=tkinter.DISABLED)
networkInfo.place(x=10, y=10)

IPLabel = tkinter.Label(serverWindow, text="Ip Adress:", width=8, height=1, bg="#404040", fg="white", anchor=tkinter.W)
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

StartGameButton = tkinter.Button(serverWindow, text="play", command=lambda: threading.Thread(target=startGame, daemon=True, args=()).start(), state="disabled", width=8, height=0)
StartGameButton.place(x=255, y=600)

def on_closing():
    try:
        playerList.disconnectAllPlayers()
    except:
        pass
    serverWindow.destroy()
    quit()

serverWindow.protocol("WM_DELETE_WINDOW", on_closing)

serverWindow.mainloop()
