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


messagesReceived = []
connected = False

def addToNetworkInfo(text):
      networkInfo.config(state=tkinter.NORMAL)
      networkInfo.insert(tkinter.END, text)
      networkInfo.config(state=tkinter.DISABLED)
      window.update_idletasks()

def addToNetworkInfoWithColor(text, color):
      networkInfo.config(state=tkinter.NORMAL)
      networkInfo.tag_config("colored", foreground=color)
      networkInfo.insert(tkinter.END, text, "colored")
      networkInfo.config(state=tkinter.DISABLED)
      window.update_idletasks()


def changeQuestionTextBox(text):
      questionText.config(state=tkinter.NORMAL)
      questionText.delete("1.0", tkinter.END)
      questionText.insert(tkinter.END, text)
      questionText.config(state=tkinter.DISABLED)
      window.update_idletasks()

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
   except ValueError as ve:

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

def sendMessageToServer(msg):
   if(connected):
      encodedMsg = msg.encode(FORMAT)
      msg_length = len(encodedMsg)
      send_length = str(msg_length).encode(FORMAT)
      send_length += b' ' * (HEADER - len(send_length))
      server.send(send_length)
      server.send(encodedMsg)
      addToNetworkInfo(f"Message sent: {msg} \n")
   else:
      addToNetworkInfo(f"Trying to send messages to a server not connected Something Is Wrong \n")


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
               break
            
            if receivedMessage == ASKFORDISCONNECT_MESSAGE:
               sendMessageToServer(DISCONNECT_MESSAGE)
               server.close()
               connected = False
               addToNetworkInfo("Disconnected From Server \n")
               EnterInformationButton.config(state = tkinter.NORMAL)
               break

            if receivedMessage == GAMESTARTED_MESSAGE:
               server.close()
               connected = False
               addToNetworkInfo("Game Already Started \n")
               EnterInformationButton.config(state = tkinter.NORMAL)
               break

            if receivedMessage.startswith(QUESTION_MESSAGE):
               if receivedMessage.startswith(QUESTIONHASIMAGE_MESSAGE, len(QUESTION_MESSAGE)):
                  qnaString = receivedMessage[len(QUESTION_MESSAGE) + len(QUESTIONHASIMAGE_MESSAGE):]
                  hasImage = True
                  imagepath = ""
                  #somehow get image maybe
               else:
                  qnaString = receivedMessage[len(QUESTION_MESSAGE):]
                  hasImage = False
                  imagepath = ""

               print("here1")
               qnaList = qnaString.split(DIVIDER_MESSAGE) 
               print("here2")              
               changeQuestionTextBox(qnaList[0])
               print("here3")
               ans1button.config(text=qnaList[1])
               ans2button.config(text=qnaList[2])
               ans3button.config(text=qnaList[3])
               ans4button.config(text=qnaList[4])




      except:
         pass


windowWIDTH=1225
windowHEIGHT=700
ANSWERBUTTONHEIGHT = 6
ANSWERBUTTONWIDTH = 45
ICONPATH = r"dist\TriviaGameIcon.ico"
window = tkinter.Tk()
window.geometry("{}x{}+50+50".format(windowWIDTH, windowHEIGHT))
window.configure(bg="#141414")
window.resizable(False, False)
window.attributes('-topmost', 1)
window.attributes('-topmost', 0)
window.title("Kahoot Client")

photo = ImageTk.PhotoImage(Image.open(ICONPATH))
window.iconphoto(False, photo)
window.iconbitmap(default=ICONPATH)


def on_closing():
      if(connected):
         try:
            sendMessageToServer(DISCONNECT_MESSAGE)
         except:
            pass
      window.destroy()
      exit

window.protocol("WM_DELETE_WINDOW", on_closing)


leftFrame = tkinter.Frame(window, bg="#141414", width=5*(windowWIDTH)/7, height=windowHEIGHT)

rightFrame = tkinter.Frame(window, bg="#141414", width=2*(windowWIDTH)/7, height=windowHEIGHT)

questionFrame = tkinter.Frame(window, bg="red", width=5*(windowWIDTH)/7, height=4*(windowHEIGHT)/7)
answerFrame =tkinter.Frame(window, bg="green", width=5*(windowWIDTH)/7, height=3*(windowHEIGHT)/7)
networkFrame = tkinter.Frame(window, bg="blue", width=2*(windowWIDTH)/7, height=9*(windowHEIGHT)/10)
informationFrame = tkinter.Frame(window, bg="purple", width=2*(windowWIDTH)/7, height=1*(windowHEIGHT)/10)


questionFrame.place(x=0, y=0)
answerFrame.place(x=0, y=4*(windowHEIGHT)/7)
informationFrame.place(x=5*(windowWIDTH)/7, y=9*(windowHEIGHT)/10)
networkFrame.place(x=5*(windowWIDTH)/7, y=0)


questionText = tkinter.Text(questionFrame, width=70, height=22)
questionText.config(state=tkinter.DISABLED)

pixelVirtual = tkinter.PhotoImage(width=1, height=1)
questionImage=tkinter.Label(questionFrame, image=pixelVirtual, width=280, height= 352)


questionText.place(x=10, y=15)
questionImage.place(x=580, y=15)


ans1button = tkinter.Button(answerFrame, bg="#e51537", text="", state="disabled", width=ANSWERBUTTONWIDTH, height=ANSWERBUTTONHEIGHT)
ans2button = tkinter.Button(answerFrame, bg="#0565d1", text="", state="disabled", width=ANSWERBUTTONWIDTH, height=ANSWERBUTTONHEIGHT)
ans3button = tkinter.Button(answerFrame, bg="#d99f00", text="", state="disabled", width=ANSWERBUTTONWIDTH, height=ANSWERBUTTONHEIGHT)
ans4button = tkinter.Button(answerFrame, bg="#229000", text="", state="disabled", width=ANSWERBUTTONWIDTH, height=ANSWERBUTTONHEIGHT)

ans1button.place(x=50, y=25)
ans2button.place(x=450, y=25)
ans3button.place(x=50, y=150)
ans4button.place(x=450, y=150)



networkInfo = tkinter.Text(networkFrame, width=40, height=37 )
networkInfo.config(state=tkinter.DISABLED)

networkInfo.place(x=10,y=15)



NameLabel = tkinter.Label(informationFrame, text="Name:", width=5, height=1, bg="purple" ,anchor=tkinter.W)
EnterName = tkinter.Entry(informationFrame, width=16)
NameLabel.place(x=10, y=10)
EnterName.place(x=10, y=33)

IPLabel = tkinter.Label(informationFrame, text= "Ip Adress:", width=8, height=1, bg="purple" ,anchor=tkinter.W)
EnterIP = tkinter.Entry(informationFrame, width=16)
IPLabel.place(x=112, y=10)
EnterIP.place(x=112, y=33)

PortLabel = tkinter.Label(informationFrame, text="Port:", width=5, height=1, bg="purple" ,anchor=tkinter.W)
EnterPort = tkinter.Entry(informationFrame, width=8)
PortLabel.place(x=214, y=10)
EnterPort.place(x=214, y=33)

EnterInformationButton = tkinter.Button(informationFrame, text="join" , command=joinServer, width=8, height=0)
EnterInformationButton.place(x=270, y=30)

def main():
   window.mainloop()
main()