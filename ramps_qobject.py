import sys
from PyQt5.QtSerialPort import QSerialPort
from PyQt5 import QtCore


def parseStatus(status):
    status = status.strip()
    if not status.startswith("<") or not status.endswith(">"):
        return None
    rest = status[1:-3]

    state = rest.split(",")[0]
    results = { 'state': state }
    
    for item in rest:
        if item.startswith("MPos"):
            m_pos = [float(field) for field in item[5:].split(',')]
            results['m_pos'] = m_pos
        elif item.startswith("Pn"):
            pins = item[3:]
            results['pins'] = pins
    return results

class QRAMPSObject(QtCore.QObject):
    messageSignal = QtCore.pyqtSignal(str)
    statusSignal = QtCore.pyqtSignal(dict)
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
    def do_status(self):
        if self.state in (STATE_READY, STATE_SENDING_COMMAND, STATE_HOMING_X, STATE_HOMING_Y, STATE_DWELL):        
            request = QtNetwork.QNetworkRequest(url=QtCore.QUrl(f"http://{HOSTNAME}/command?commandText=?"))
            self.replyObject = self.manager.get(request)
        else:
            print("Can't get state when not connected", self.state)

    def send_line(self, line):
        b = bytearray(line + '\r', 'utf-8')
        self.serial.writeData(b)
        return True
    def on_serial_read(self, *args):
        data = self.serial.readAll()
        decoded = data.data().decode('US_ASCII')
        print(decoded)
        self.messageSignal.emit(decoded)

if __name__ == '__main__':
    app = QtCore.QCoreApplication(sys.argv)

    client = QRAMPSObject()

    app.exec_()