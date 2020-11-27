import sys

from PyQt5 import QtCore, QtWebSockets, QtNetwork
from PyQt5.QtCore import QUrl, QCoreApplication, QTimer

HOSTNAME="dykstrabot.local"

STATE_INIT=0
STATE_HOMING_X=1
STATE_HOMING_Y=2
STATE_DWELL=3
STATE_READY=4
STATE_SENDING_COMMAND=5
STATE_ERROR=-1

def parseStatus(status):
    status = status.strip()
    if not status.startswith("<") or not status.endswith(">"):
        return None
    rest = status[1:-3].split('|')
    state = rest[0]
    results = { 'state': state }
    for item in rest:
        if item.startswith("MPos"):
            m_pos = [float(field) for field in item[5:].split(',')]
            results['m_pos'] = m_pos
        elif item.startswith("Pn"):
            pins = item[3:]
            results['pins'] = pins
    return results

class GRBLESP32Client(QtCore.QObject):
    messageSignal = QtCore.pyqtSignal(str)
    statusSignal = QtCore.pyqtSignal(dict)
    stateSignal = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.client =  QtWebSockets.QWebSocket("",QtWebSockets.QWebSocketProtocol.Version13,None)
        self.client.error.connect(self.error)
        self.client.connected.connect(self.connected)

        self.client.open(QUrl(f"ws://{HOSTNAME}:81"))
        self.client.textMessageReceived.connect(self.onText)
        self.client.binaryMessageReceived.connect(self.onBinary)

        self.manager = QtNetwork.QNetworkAccessManager()

        self.changeState(STATE_INIT)

    def connected(self):
        print("connected")
        self.changeState(STATE_READY)

        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.do_status)
        self.status_timer.start(1000)

    def home(self, axis='x'):
        if self.state != STATE_READY:
            print("Can only home when READY")
            return False
        if axis == 'x':
            self.send_line("$HX")
            self.changeState(STATE_HOMING_X)
        elif axis == 'y':
            self.send_line("$HY")
            self.changeState(STATE_HOMING_Y)
        else:
            print("Unknown axis:", axis)
            return False
        return True

    def dwell(self, axis='x'):
        if self.state not in (STATE_SENDING_COMMAND, STATE_HOMING_X, STATE_HOMING_Y, STATE_READY):
            print("Invalid state", self.state, "for dwell")
        else:
            self.send_line("G4 P0")
            self.changeState(STATE_DWELL)

    def onText(self, message):
        if message.startswith("CURRENT_ID"):
            self.current_id = message.split(':')[1]
            print("Current id is:", self.current_id)
        elif message.startswith("ACTIVE_ID"):
            active_id = message.split(':')[1]
            if self.current_id != active_id:
                print("Warning: different active id.")
        elif message.startswith("PING"):
            ping_id = message.split(":")[1]
            if ping_id != self.current_id:
                print("Warning: ping different active id.")

    def changeState(self, state):
        self.state = state
        self.stateSignal.emit(self.state)

    def onBinary(self, messages):
        messages = str(messages, 'ascii')
        for message in messages.split("\r\n"):
            if message == '':
                continue
            print("Got message: '%s'" % message)
            if self.state in (STATE_SENDING_COMMAND, STATE_HOMING_X, STATE_HOMING_Y, STATE_DWELL):
                print("waiting for an ok")
            if message == 'ok':
                print("Got ok in state", self.state)
                if self.state in (STATE_SENDING_COMMAND, STATE_HOMING_X, STATE_HOMING_Y, STATE_DWELL):
                    self.changeState(STATE_READY)
                else:
                    print("Got ok when didn't expect one!")
            else:
                results = parseStatus(message)
                if results:
                    self.statusSignal.emit(results)
                else:
                    self.messageSignal.emit(message)
        
    def do_status(self):
        if self.state in (STATE_READY, STATE_SENDING_COMMAND, STATE_HOMING_X, STATE_HOMING_Y, STATE_DWELL):        
            request = QtNetwork.QNetworkRequest(url=QtCore.QUrl(f"http://{HOSTNAME}/command?commandText=?"))
            self.replyObject = self.manager.get(request)
        else:
            print("Can't get state when not connected", self.state)

    def send_line(self, line):
        if self.state != STATE_READY:
            print("Cannot send line when not ready")
            return False
        request = QtNetwork.QNetworkRequest()
        url = QtCore.QUrl(f"http://{HOSTNAME}/command?commandText={line}")
        request.setUrl(url)
        self.manager.get(request)
        self.changeState(STATE_SENDING_COMMAND)
        return True

    def error(self, error_code):
        print("error code: {}".format(error_code))
        if error_code == 1:
            print(self.client.errorString())

    def close(self):
        self.client.close()


if __name__ == '__main__':
    app = QCoreApplication(sys.argv)

    client = GRBLESP32Client()

    app.exec_()