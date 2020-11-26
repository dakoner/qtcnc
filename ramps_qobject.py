import sys
from PyQt5.QtSerialPort import QSerialPort
from PyQt5 import QtCore


STATE_INIT=0
STATE_HOMING_X=1
STATE_HOMING_Y=2
STATE_DWELL=3
STATE_READY=4
STATE_SENDING_COMMAND=5
STATE_ERROR=-1

def parseStatus(status):
    print("Got status line:", status)
    status = status.strip()
    if not status.startswith("<") or not status.endswith(">"):
        return None
    rest = status[1:-3]

    state = rest.split(",")[0]
    print(state)
    results = { 'state': state }
    # need to parse more carefully....
    # <Idle,MPos:-99.0000,-2.0000,0.0000,WPos:-99.0000,-2.0000,0.0000>
    rest = rest[len(state)+1:]
    assert rest.startswith('MPos')
    coords = [float(item) for item in rest[5:rest.find(',WPos')].split(",")]
    print(coords)
    results['m_pos'] = coords
    return results

class QRAMPSObject(QtCore.QObject):
    messageSignal = QtCore.pyqtSignal(str)
    statusSignal = QtCore.pyqtSignal(dict)
    stateSignal = QtCore.pyqtSignal(int)
    def __init__(self, *args, **kwargs):
        super(QtCore.QObject, self).__init__(*args, **kwargs)

        self.serial = QSerialPort()
        port = "COM19"
        self.serial.setPortName(port)
        if self.serial.open(QtCore.QIODevice.ReadWrite):
            self.serial.setDataTerminalReady(True)
            self.serial.setBaudRate(115200)
            self.serial.readyRead.connect(self.on_serial_read)
        else:
            print("Failed to open serial port")

        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.do_status)
        self.status_timer.start(1000)

        self.changeState(STATE_INIT)
        b = bytearray('\r', 'utf-8')
        self.serial.writeData(b)
        self.line = ""
        
    def changeState(self, state):
        self.state = state
        self.stateSignal.emit(self.state)

    def do_status(self):
        if self.state in (STATE_READY, STATE_SENDING_COMMAND, STATE_HOMING_X, STATE_HOMING_Y, STATE_DWELL):        
            line = "?"
            b = bytearray(line, 'utf-8')
            self.serial.writeData(b)
        else:
            print("Can't get state when not connected", self.state)

    def send_line(self, line):
        if self.state != STATE_READY:
            #print("Cannot send line when not ready")
            return False
        b = bytearray(line + '\r', 'utf-8')
        self.serial.writeData(b)
        self.changeState(STATE_SENDING_COMMAND)
        return True

    def on_serial_read(self, *args):
        if not self.serial.canReadLine():
            line = self.serial.readLine()
            print("incomplete line, adding", line)
            self.line += line.data().decode('US_ASCII')
            return
        message = self.line + self.serial.readLine().data().decode('US_ASCII').strip()
        self.line = ""
        print("Read message:", message)
        if message == '':
            return
        if message == 'Smoothie':
            self.changeState(STATE_READY)
        if message == 'ok':
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

if __name__ == '__main__':
    app = QtCore.QCoreApplication(sys.argv)

    client = QRAMPSObject()

    app.exec_()