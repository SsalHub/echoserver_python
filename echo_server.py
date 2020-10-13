import os
import sys
import struct
import socket
import wx
import datetime
import threading

MSG_EXIT = bytes([0x00])

class EchoServerFrame(wx.Frame):
    clientList = {}

    def __init__(self, frameTitle):
        wx.Frame.__init__(self, parent=None, title=frameTitle, style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.MAXIMIZE_BOX | wx.CAPTION | wx.CLOSE_BOX)
        self.SetSize(600, 400)
        self.mainPanel = wx.Panel(self)
        self.isServerListening = False

        self.initui()
        self.SetFocus()

    def initui(self):
        # serverip input
        self.IPStaticText = wx.StaticText(self.mainPanel, label='ServerIP :')
        self.IPInput = wx.TextCtrl(self.mainPanel, value='127.0.0.1')
        # serverport input 
        self.portStaticText = wx.StaticText(self.mainPanel, label='     Port :')
        self.portInput = wx.TextCtrl(self.mainPanel, value='5452')
        # server open btn
        self.serverOpenBtn = wx.Button(self.mainPanel, label='Listen')
        # server close btn
        self.serverCloseBtn = wx.Button(self.mainPanel, label='Close')
        # connection log list
        self.logListBox = wx.ListBox(self.mainPanel, size=wx.Size(400, 250), style=wx.LB_HSCROLL)
        # client list
        self.clientListBox = wx.ListBox(self.mainPanel, size=wx.Size(200, 250))
        
        # define sizers on mainPanel
        inputSizer = wx.GridSizer(rows=2, cols=2, hgap=-50, vgap=5)
        inputSizer.Add(self.IPStaticText)
        inputSizer.Add(self.IPInput)
        inputSizer.Add(self.portStaticText)
        inputSizer.Add(self.portInput)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(inputSizer, 0, wx.EXPAND | wx.ALL, 5)
        btnSizer.Add(self.serverOpenBtn, 0, wx.EXPAND | wx.ALL, 5)
        btnSizer.Add(self.serverCloseBtn, 0, wx.EXPAND | wx.ALL, 5)

        listSizer = wx.BoxSizer(wx.HORIZONTAL)
        listSizer.Add(self.logListBox, 0, wx.ALL, 5)
        listSizer.Add(self.clientListBox, 0, wx.ALL, 5)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(btnSizer, 0, wx.EXPAND | wx.ALL, 5)
        mainSizer.Add(listSizer, 0, wx.ALL, 5)
        self.mainPanel.SetSizer(mainSizer)

        # bind events
        self.serverOpenBtn.Bind(wx.EVT_BUTTON, self.OnServerListenBtn)
        self.serverCloseBtn.Bind(wx.EVT_BUTTON, self.OnServerCloseBtn)

    def OnServerListenBtn(self, event):
        if self.isServerListening == True:
            wx.MessageBox('Server is already listening.', 'Info')
            return
        try:
            serverIP = self.IPInput.GetValue()
            serverPort = int(self.portInput.GetValue())
        except Exception as err:
            wx.MessageBox('input error : {}'.format(err), 'Error')
            return

        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serverSocket.bind((serverIP, serverPort))
            self.serverSocket.listen(10)    # maximum client = 10

            # server listen
            self.WriteLog('Server is listening.')
            self.isServerListening = True
            listenThread = threading.Thread(target=self.ListenServer, daemon=True)
            listenThread.start()

        except Exception as err:
            wx.MessageBox('error occurred : {}'.format(err), 'Error')

    def OnServerCloseBtn(self, event):
        self.CloseServer()

    def ListenServer(self):
        while 1:
            try:
                clientSocket, clientAddr = self.serverSocket.accept()   # accept()에서 클라이언트 소켓과 IP주소를 반환함
            except OSError:
                break
            handleThread = threading.Thread(target=self.Handle, args=(clientSocket, clientAddr), daemon=True)
            handleThread.start()

    def CloseServer(self):
        if self.isServerListening == True:
            self.isServerListening = False
            for client in self.clientList.items():
                self.Send(client[1], MSG_EXIT)
                client[1].close()
            self.clientList.clear()
            self.clientListBox.Clear()
            self.serverSocket.close()
            self.WriteLog('Server Closed.')
        else:
            wx.MessageBox('Server is not listening.', 'Close failed')

    def Handle(self, clientSocket, clientAddr):
        clientID = datetime.datetime.now().microsecond
        self.clientList[clientID] = clientSocket
        self.clientListBox.Append(str(clientID))
        err = Exception()
        
        while self.isServerListening == True:
            received = self.Receive(clientSocket)
            # if received exit msg
            if received[1] == MSG_EXIT:
                self.Send(clientSocket, received[1])
                break
            self.WriteLog('{} : {}'.format(clientID, received[1].decode('utf-8')))
            self.Send(clientSocket, received[1].decode('utf-8'))

        clientSocket.close()
        del(self.clientList[clientID])
        threading.Thread(target=self.RefreshClientListBox, daemon=True).start()
            

    def Send(self, sock, data):
        try:
            if data == MSG_EXIT:
                sBody = MSG_EXIT
                sHeader = struct.pack('=i', len(sBody))
            else:
                sBody = data.encode('utf-8')
                sHeader = struct.pack('=i', len(sBody))
            sock.send(sHeader)
            sock.send(sBody)
        except:
            return False
        else:
            return True

    def Receive(self, sock):
        sizeToRead = 4      # size of header

        rHeader = sock.recv(sizeToRead)
        if rHeader == None:
            return None
        rBodyLen = struct.unpack('=i', rHeader)[0]
        rBody = sock.recv(rBodyLen)
        return (rHeader, rBody)

    def RefreshClientListBox(self):
        self.clientListBox.Clear()
        self.clientListBox.Set(self.clientList.keys())


    def WriteLog(self, data):
        message = self.GetNowTime() + data
        self.logListBox.Append(message)
        self.logListBox.SetFirstItem(self.logListBox.GetCount()-1)
        with open('.\\log.txt', 'at') as file:
            file.write(message + '\n')

    def GetNowTime(self):
        now = datetime.datetime.now()
        return '[{}/{}/{} {}:{}:{}.{}] '.format(now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)


if __name__ == '__main__':
    app = wx.App()
    frame = EchoServerFrame('EchoServer')
    frame.Show()
    app.MainLoop()
    # print(socket.gethostbyname(socket.getfqdn())) 내 ip 알아내는 코드