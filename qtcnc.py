from PyQt5 import QtWidgets, QtCore, uic
import sys 
import os
from mqtt_qobject import MqttClient



def distance_for_button(button):
    on = button.objectName()
    if on == 'distance_point1':
        return 0.1
    elif on == 'distance_1':
        return 1
    elif on == 'distance_10':
        return 10
    elif on == 'distance_100':
        return 100
    else:
        print("Unrecognized radio button", on)
        return 0

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        #Load the UI Page
        uic.loadUi('qtcnc.ui', self)
        self.down_button.clicked.connect(self.down_button_clicked)
        self.up_button.clicked.connect(self.up_button_clicked)
        self.right_button.clicked.connect(self.right_button_clicked)
        self.left_button.clicked.connect(self.left_button_clicked)
        
        # self.home_x_button.clicked.connect(self.home_x_button_clicked)
        # self.home_y_button.clicked.connect(self.home_y_button_clicked)
        # self.dwell_button.clicked.connect(self.dwell_button_clicked)
        self.ramps_input.returnPressed.connect(self.line_entered)


        self.client = MqttClient(self)
        self.client.hostname = "inspectionscope.local"
        self.client.connectToHost()
        self.client.stateChanged.connect(self.on_stateChanged)
        self.client.messageSignal.connect(self.on_messageSignal)

    def line_entered(self):
        line = self.ramps_input.text()
        self.client.publish("grblesp32/command", line)
        self.ramps_input.clear()


    @QtCore.pyqtSlot(int)
    def on_stateChanged(self, state):
        if state == MqttClient.Connected:
            self.client.subscribe("grblesp32/status")
            self.client.subscribe("grblesp32/output")
            self.client.subscribe("grblesp32/state")

    @QtCore.pyqtSlot(str, str)
    def on_messageSignal(self, topic, payload):
        print("Message: ", topic, payload)
        if topic == 'grblesp32/output':
            self.ramps_output.insertPlainText(payload)
            self.ramps_output.insertPlainText("\n")
            self.ramps_output.verticalScrollBar().setValue(self.ramps_output.verticalScrollBar().maximum())
        elif topic == 'grblesp32/status':
            self.grbl_status.setText(payload)
            """ if 'm_pos' in data:
                pos = data['m_pos']
                self.position_x.display(pos[0])

                self.position_y.display(pos[1])
            """
        elif topic == 'grblesp32/state':
            self.status.setText(payload)
       
    def relative_move_to(self, delta_x, delta_y):
        cmd = "G91 G21 G0 X%5.2f Y%5.2f" % (delta_x, delta_y)
        self.client.publish('grblesp32/command', cmd)
        
    def down_button_clicked(self):
        distance = distance_for_button(self.distance_radio_group.checkedButton())
        self.relative_move_to(0, distance)
    
    def up_button_clicked(self):
        distance = distance_for_button(self.distance_radio_group.checkedButton())
        self.relative_move_to(0, -distance)

    def right_button_clicked(self):
        distance = distance_for_button(self.distance_radio_group.checkedButton())
        self.relative_move_to(distance, 0)
    
    def left_button_clicked(self):
        distance = distance_for_button(self.distance_radio_group.checkedButton())
        self.relative_move_to(-distance, 0)
"""   
    def home_x_button_clicked(self):
        self.grblesp32.home(axis="x")
  
    def home_y_button_clicked(self):
        self.grblesp32.home(axis="y")
 

    def dwell_button_clicked(self):
        self.grblesp32.dwell()
 """
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':      
    main()