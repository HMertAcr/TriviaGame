import tkinter
from PIL import Image,ImageTk
import socket
import time
import threading

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

messagesReceived = []
connected = False

def addToNetworkInfo(text):
      networkInfo.config(state=tkinter.NORMAL)
      networkInfo.insert(tkinter.END, text)
      networkInfo.config(state=tkinter.DISABLED)
      clientWindow.update_idletasks()

def addToNetworkInfoWithColor(text, color):
      networkInfo.config(state=tkinter.NORMAL)
      networkInfo.tag_config("colored" + networkInfo.index('end'), foreground=color)
      networkInfo.insert(tkinter.END, text, "colored" + networkInfo.index('end'))
      networkInfo.config(state=tkinter.DISABLED)
      clientWindow.update_idletasks()

def changeQuestionTextBox(text):
      questionText.config(state=tkinter.NORMAL)
      questionText.delete("1.0", tkinter.END)
      questionText.insert(tkinter.END, text)
      questionText.config(state=tkinter.DISABLED)
      clientWindow.update_idletasks()

def answerChoosen(answer):

   if answer == 1:
      choosenAnswer = ans1button["text"]
   if answer == 2:
      choosenAnswer = ans2button["text"]
   if answer == 3:
      choosenAnswer = ans3button["text"]
   if answer == 4:
      choosenAnswer = ans4button["text"]

   sendMessageToServer(ANSWERTOQUESTION_MESSAGE+choosenAnswer)
   ans1button.config(text="", state="disabled")
   ans2button.config(text="", state="disabled")
   ans3button.config(text="", state="disabled")
   ans4button.config(text="", state="disabled")

   
def joinServer():
   global connected
   global PlayerName
   global SERVERIP
   global SERVERPORT
   global SERVERADDR
   global server
   global listenToServerThread

   PlayerName = EnterName.get()
   SERVERIP = EnterIP.get()
   SERVERPORT = EnterPort.get()

   try:
      if (PlayerName == "" or SERVERIP == "" or SERVERPORT == "" or (not SERVERPORT.isnumeric)):
         raise ValueError
      SERVERPORT = int(SERVERPORT)
      SERVERADDR = (SERVERIP, SERVERPORT)
      server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      server.connect(SERVERADDR)
   except ValueError:

      addToNetworkInfo("Inputs Invalid \n")

   except:

      addToNetworkInfo(f"Couldnt connect to {SERVERIP}:{SERVERPORT} \n")

   else:
      connected = True
      sendMessageToServer(PlayerName)
      addToNetworkInfo(f"Connected to {SERVERIP}:{SERVERPORT} \n")
      listenToServerThread = threading.Thread(target=listenToServer, daemon=True, args=())
      listenToServerThread.start()
      EnterInformationButton.config(state = tkinter.DISABLED)
      SendPublicMessageButton.config(state = tkinter.NORMAL)

def sendMessageToServer(msg):
   if(connected):
      encodedMsg = msg.encode(FORMAT)
      msg_length = len(encodedMsg)
      send_length = str(msg_length).encode(FORMAT)
      send_length += b' ' * (HEADER - len(send_length))
      server.send(send_length)
      server.send(encodedMsg)
      addToNetworkInfo(f"Message sent: {msg} \n")


def sendPublicMessage():
   if connected:
      sendMessageToServer(PUBLIC_MESSAGE+EnterPublicMessage.get())
   else:
      addToNetworkInfo("Not connected to server \n")


def listenToServer():
   global connected
   while connected:
      try:
         msg_lenght = server.recv(HEADER).decode(FORMAT)
      
         if msg_lenght:
            msg_lenght = int(msg_lenght)
            receivedMessage = server.recv(msg_lenght).decode(FORMAT)

            addToNetworkInfo(f"Message received: {receivedMessage} \n")

            messagesReceived.append(receivedMessage)

            if receivedMessage == ImageSend_Message:
               pass
               #more magic

            if receivedMessage == DISCONNECT_MESSAGE:
               server.close()
               connected = False
               addToNetworkInfo("Disconnected From Server \n")
               EnterInformationButton.config(state = tkinter.NORMAL)
               SendPublicMessageButton.config(state = tkinter.DISABLED)
               changeQuestionTextBox("")
               ans1button.config(text="", state="disabled")
               ans2button.config(text="", state="disabled")
               ans3button.config(text="", state="disabled")
               ans4button.config(text="", state="disabled")
               questionImage.config(image=pixelVirtual)
               break
            
            if receivedMessage == ASKFORDISCONNECT_MESSAGE:
               sendMessageToServer(DISCONNECT_MESSAGE)
               server.close()
               connected = False
               addToNetworkInfo("Disconnected From Server \n")
               EnterInformationButton.config(state = tkinter.NORMAL)
               SendPublicMessageButton.config(state = tkinter.DISABLED)
               changeQuestionTextBox("")
               ans1button.config(text="", state="disabled")
               ans2button.config(text="", state="disabled")
               ans3button.config(text="", state="disabled")
               ans4button.config(text="", state="disabled")
               questionImage.config(image=pixelVirtual)
               break

            if receivedMessage == GAMESTARTED_MESSAGE:
               server.close()
               connected = False
               addToNetworkInfo("Game Already Started \n")
               EnterInformationButton.config(state = tkinter.NORMAL)
               SendPublicMessageButton.config(state = tkinter.DISABLED)
               break

            if receivedMessage.startswith(QUESTION_MESSAGE):
               if receivedMessage.startswith(QUESTIONHASIMAGE_MESSAGE, len(QUESTION_MESSAGE)):
                  qnaString = receivedMessage[len(QUESTION_MESSAGE) + len(QUESTIONHASIMAGE_MESSAGE):]
                  hasImage = True
                  #somehow get image maybe
                  questionImage.config(image=pixelVirtual)

               else:
                  qnaString = receivedMessage[len(QUESTION_MESSAGE):]
                  questionImage.config(image=pixelVirtual)

               qnaList = qnaString.split(DIVIDER_MESSAGE)

               changeQuestionTextBox(qnaList[0])

               ans1button.config(text=qnaList[1], state="normal")
               ans2button.config(text=qnaList[2], state="normal")
               ans3button.config(text=qnaList[3], state="normal")
               ans4button.config(text=qnaList[4], state="normal")
               continue

            if receivedMessage.startswith(ISANSWERCORRECT_MESSAGE):
               isAnswerCorrect = receivedMessage[len(ISANSWERCORRECT_MESSAGE):]
               if isAnswerCorrect == "YES":

                  changeQuestionTextBox("")

                  ans1button.config(text="", state="disabled")
                  ans2button.config(text="", state="disabled")
                  ans3button.config(text="", state="disabled")
                  ans4button.config(text="", state="disabled")

                  questionImage.config(image=checkmarkimage)

               if isAnswerCorrect == "NO":
                  
                  changeQuestionTextBox("")

                  ans1button.config(text="", state="disabled")
                  ans2button.config(text="", state="disabled")
                  ans3button.config(text="", state="disabled")
                  ans4button.config(text="", state="disabled")

                  questionImage.config(image=crossimage)
                  continue
         
            if receivedMessage.startswith(PUBLIC_MESSAGE):
               publicMessageColor , publicMessage = receivedMessage[len(PUBLIC_MESSAGE):].split(DIVIDER_MESSAGE)
               addToNetworkInfoWithColor(publicMessage+"\n",publicMessageColor)
               continue

            if receivedMessage.startswith(GAMESTATS_MESSAGE):
               gameStats = receivedMessage[len(GAMESTATS_MESSAGE):].split(DIVIDER_MESSAGE)

               changeQuestionTextBox(f"You came in {gameStats[0]}. out of {gameStats[1]} place with {gameStats[2]} correct answers")

               continue
               #ADD SOME FLAIR
      except Exception:
         server.close()
         connected = False
         addToNetworkInfo("Disconnected From Server \n")
         EnterInformationButton.config(state = tkinter.NORMAL)
         SendPublicMessageButton.config(state = tkinter.DISABLED)
         changeQuestionTextBox("")
         ans1button.config(text="", state="disabled")
         ans2button.config(text="", state="disabled")
         ans3button.config(text="", state="disabled")
         ans4button.config(text="", state="disabled")
         questionImage.config(image=pixelVirtual)
         break



windowWIDTH=1225
windowHEIGHT=700
ANSWERBUTTONHEIGHT = 6
ANSWERBUTTONWIDTH = 50
ICONPATH = r"dist\TriviaGameIcon.ico"
CHECKMARKPATH = r"dist\checkMark.png"
CROSSPATH = r"dist\cross.png"
clientWindow = tkinter.Tk()
clientWindow.geometry(f"{windowWIDTH}x{windowHEIGHT}+50+50")
clientWindow.configure(bg="#141414")
clientWindow.resizable(False, False)
clientWindow.attributes('-topmost', 1)
clientWindow.attributes('-topmost', 0)
clientWindow.title("TriviaGame Client")

iconphotoimage = ImageTk.PhotoImage(Image.open(ICONPATH))
checkmarkimage = ImageTk.PhotoImage(Image.open(CHECKMARKPATH))
crossimage = ImageTk.PhotoImage(Image.open(CROSSPATH))
pixelVirtual = tkinter.PhotoImage(width=1, height=1)
clientWindow.iconphoto(False, iconphotoimage)
clientWindow.iconbitmap(default=ICONPATH)


def on_closing():
      if(connected):
         try:
            sendMessageToServer(DISCONNECT_MESSAGE)
         except:
            pass
      clientWindow.destroy()
      quit()

clientWindow.protocol("WM_DELETE_WINDOW", on_closing)


questionFrame = tkinter.Frame(clientWindow, bg="#404040", width=5*(windowWIDTH)/7, height=4*(windowHEIGHT)/7)
answerFrame =tkinter.Frame(clientWindow, bg="#171717", width=5*(windowWIDTH)/7, height=3*(windowHEIGHT)/7)
networkFrame = tkinter.Frame(clientWindow, bg="#404040", width=2*(windowWIDTH)/7, height=17*(windowHEIGHT)/20)
informationFrame = tkinter.Frame(clientWindow, bg="#404040", width=2*(windowWIDTH)/7, height=3*(windowHEIGHT)/20)


questionFrame.place(x=0, y=0)
answerFrame.place(x=0, y=4*(windowHEIGHT)/7)
networkFrame.place(x=5*(windowWIDTH)/7, y=0)
informationFrame.place(x=5*(windowWIDTH)/7, y=17*(windowHEIGHT)/20)


questionText = tkinter.Text(questionFrame, width=70, height=22, state="disabled", bg="black",fg="white")

questionImage=tkinter.Label(questionFrame, image=pixelVirtual, width=280, height= 352,bg="black",fg="white")


questionText.place(x=10, y=15)
questionImage.place(x=580, y=15)


ans1button = tkinter.Button(answerFrame, command=lambda: answerChoosen(1), bg="#e51537", text="", state="disabled", width=ANSWERBUTTONWIDTH, height=ANSWERBUTTONHEIGHT)
ans2button = tkinter.Button(answerFrame, command=lambda: answerChoosen(2), bg="#0565d1", text="", state="disabled", width=ANSWERBUTTONWIDTH, height=ANSWERBUTTONHEIGHT)
ans3button = tkinter.Button(answerFrame, command=lambda: answerChoosen(3), bg="#d99f00", text="", state="disabled", width=ANSWERBUTTONWIDTH, height=ANSWERBUTTONHEIGHT)
ans4button = tkinter.Button(answerFrame, command=lambda: answerChoosen(4), bg="#229000", text="", state="disabled", width=ANSWERBUTTONWIDTH, height=ANSWERBUTTONHEIGHT)

ans1button.place(x=50, y=25)
ans2button.place(x=450, y=25)
ans3button.place(x=50, y=150)
ans4button.place(x=450, y=150)



networkInfo = tkinter.Text(networkFrame, width=40, height=35, state="disabled", fg="white", bg="black" )

networkInfo.place(x=10,y=15)

PublicMessageLabel = tkinter.Label(informationFrame, text="Public Message:", width=20, height=1, bg="#404040", anchor=tkinter.W, fg="white")
EnterPublicMessage = tkinter.Entry(informationFrame, width=42)
PublicMessageLabel.place(x=10, y=2)
EnterPublicMessage.place(x=10, y=25)

SendPublicMessageButton = tkinter.Button(informationFrame, text="send", command=sendPublicMessage, state="disabled", width=8, height=0)
SendPublicMessageButton.place(x=270, y=22)

NameLabel = tkinter.Label(informationFrame, text="Name:", width=5, height=1, bg="#404040",anchor=tkinter.W, fg="white")
EnterName = tkinter.Entry(informationFrame, width=16)
NameLabel.place(x=10, y=47)
EnterName.place(x=10, y=70)

IPLabel = tkinter.Label(informationFrame, text= "Ip Adress:", width=8, height=1, bg="#404040",anchor=tkinter.W, fg="white")
EnterIP = tkinter.Entry(informationFrame, width=16)
IPLabel.place(x=112, y=47)
EnterIP.place(x=112, y=70)

PortLabel = tkinter.Label(informationFrame, text="Port:", width=5, height=1, bg="#404040",anchor=tkinter.W, fg="white")
EnterPort = tkinter.Entry(informationFrame, width=8)
PortLabel.place(x=214, y=47)
EnterPort.place(x=214, y=70)

EnterInformationButton = tkinter.Button(informationFrame, text="join", command=joinServer, width=8, height=0)
EnterInformationButton.place(x=270, y=67)

def main():
   clientWindow.mainloop()

main()