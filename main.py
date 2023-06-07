import sys

from PyQt5 import QtGui
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QMainWindow, QLineEdit, QLabel
from PyQt5.uic import loadUi


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = loadUi('untitled.ui', self)

        self.button_ok.clicked.connect(self._append_anchor)
        self.button_mode.clicked.connect(self._change_mode)

        self._image = QtGui.QPixmap(self.height(), self.width())
        self._image.fill(Qt.white)
        self.label.setPixmap(self._image)

        self.anchor_positions = []
        self.anchor_ids = []
        self.tag_positions = []

    def _append_anchor(self):
        x = int(self.box_x.text())
        y = int(self.box_y.text())
        ID = self.box_ID.text()

        invalid_vals = ""

        for val in (x, y, ID):
            if not isinstance(val, int):
                invalid_vals += f"{val}"

        if isinstance(x, int) and isinstance(y, int) and isinstance(ID, int):
            self.anchor_positions.append(QPoint(x, y))
            self.anchor_ids.append(ID)
            self.update()

            self.box_x.clear()
            self.box_y.clear()
            self.box_ID.clear()
            print(self.anchor_positions)
        else:
            invalid_val = "x" * (not isinstance(x, int)) \
                          + "y" * (not isinstance(y, int)) \
                          + "ID" * (not isinstance(ID, int))
            print('Invalid value:', invalid_val)

    def _change_mode(self):
        pass

    def on_mqtt_message(self, client, userdata, msg):
        try:
            data = msg.payload.decode()
            x, y = map(float, data.split(','))
            self.tag_positions.append(QPoint(x, y))
            self.update()
        except Exception as e:
            print(f"Error processing MQTT message: {e}")

    def paintEvent(self, paint_event):
        painter = QtGui.QPainter(self._image)
        pen = QtGui.QPen()
        pen.setWidth(10)

        # Vẽ anchor
        pen.setColor(Qt.red)
        painter.setPen(pen)
        for pos in self.anchor_positions:
            painter.drawPoint(pos)
            self.anchor_positions.pop()

        # Vẽ tag
        pen.setColor(Qt.green)
        painter.setPen(pen)
        for pos in self.tag_positions:
            painter.drawPoint(pos)
            self.tag_positions.pop()

        self.label.setPixmap(self._image)

    def mouseReleaseEvent(self, cursor_event):
        self.tag_positions.append(cursor_event.pos())
        self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
