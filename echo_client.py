import socket
import struct
import wx
import datetime
import threading

MSG_EXIT = bytes([0x00])


class EchoClientFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, title='EchoClient', style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.MAXIMIZE_BOX | wx.CAPTION | wx.CLOSE_BOX)
        self.SetSize(620, 340)
        self.mainPanel = wx.Panel(self)

        self.initui()
        self.Show()
        self.SetFocus()
    
    def initui(self):
        self.IPStaticText = wx.StaticText(self.mainPanel, label='   Server IP :')
        self.IPInput = wx.TextCtrl(self.mainPanel, value='127.0.0.1')
        self.portStaticText = wx.StaticText(self.mainPanel, label='Server Port :')
        self.portInput = wx.TextCtrl(self.mainPanel, value='5452')
        self.messageInput = wx.TextCtrl(self.mainPanel, value='type message here')
        self.loopInput = wx.TextCtrl(self.mainPanel, size=wx.Size(30, 20), value='10000')
        self.sendBtn = wx.Button(self.mainPanel, label='Send')
        self.logStaticText = wx.StaticText(self.mainPanel, label='  - send/receive log')
        self.logListBox = wx.ListBox(self.mainPanel, size=wx.Size(400, 200), style=wx.LB_HSCROLL)
        self.progressGauge = wx.Gauge(self.mainPanel, range=100, size=wx.Size(480, 30))
        self.progressGauge.SetValue(0)

        inputSizer = wx.GridSizer(rows=2, cols=2, hgap=-30, vgap=5)
        inputSizer.Add(self.IPStaticText)
        inputSizer.Add(self.IPInput)
        inputSizer.Add(self.portStaticText)
        inputSizer.Add(self.portInput)

        logListSizer = wx.BoxSizer(wx.HORIZONTAL)
        logListSizer.Add(self.logListBox, 0, wx.EXPAND)
        logListSizer.Add(inputSizer, 0, wx.ALL, 5)

        subSizer1 = wx.BoxSizer(wx.VERTICAL)
        subSizer1.Add(self.logStaticText, 0, wx.EXPAND)
        subSizer1.Add(logListSizer, 0, wx.EXPAND | wx.ALL, 5)

        subSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        subSizer2.Add(self.messageInput, 4, wx.EXPAND | wx.ALL, 5)
        subSizer2.Add(self.loopInput, 1, wx.EXPAND | wx.ALL, 5)
        subSizer2.Add(self.sendBtn, 2, wx.EXPAND | wx.ALL, 5)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(subSizer1)
        mainSizer.Add(subSizer2, 0, wx.EXPAND)
        mainSizer.Add(self.progressGauge, 0, wx.EXPAND | wx.ALL, 5)
        self.mainPanel.SetSizer(mainSizer)

        self.sendBtn.Bind(wx.EVT_BUTTON, self.OnSendBtn)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnSendBtn(self, event):
        sendThread = threading.Thread(target=self.Handle, daemon=True)
        sendThread.start()

    def OnKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_NUMPAD_ENTER:
            sendThread = threading.Thread(target=self.Handle, daemon=True)
            sendThread.start()

    def Handle(self):
        serverIP = self.IPInput.GetValue()
        serverPort = int(self.portInput.GetValue())
        loops = int(self.loopInput.GetValue())
        message = self.messageInput.GetValue()

        self.progressGauge.SetRange(loops)

        try:
            for i in range(loops):
                # connect with server
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((serverIP, serverPort))
                self.WriteLog('connected : {}:{}'.format(serverIP, serverPort))

                # send & receive message
                self.Send(sock, message)
                self.WriteLog('sent message : {}'.format(message))

                received = self.Receive(sock)
                self.WriteLog('received message : {}'.format(received.decode('utf-8')))
                self.progressGauge.SetValue(i)
                    
                self.Send(sock, MSG_EXIT)
                received = self.Receive(sock)
                if received == MSG_EXIT:
                    self.WriteLog('connection is successfully closed.')
                else:
                    self.WriteLog('connection is not successfully closed.')
        except Exception as err:
            self.WriteLog('an error occurred : {}'.format(err))
            return
        finally:
            sock.close()
            self.progressGauge.SetValue(0)

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
        return rBody

    def WriteLog(self, data):
        message = self.GetNowTime() + data
        self.logListBox.Append(message)
        self.logListBox.SetFirstItem(self.logListBox.GetCount()-1)

    def GetNowTime(self):
        now = datetime.datetime.now()
        return '[{}/{}/{} {}:{}:{}.{}] '.format(now.year, now.month, now.day, now.hour, now.minute, now.second, now.microsecond)


if __name__ == '__main__':
    app = wx.App()
    frame = EchoClientFrame()
    app.MainLoop()