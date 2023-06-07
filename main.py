import numbers
import random
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QLabel, QLineEdit
from PyQt5.QtCore import QTimer, QSize
import pyqtgraph as pg
# from varname.helpers import Wrapper
from PyQt5.uic import loadUi
import paho.mqtt.client as mqtt

# Cấu hình MQTT Broker
mqtt_broker = "broker.hivemq.com"
mqtt_port = 1883


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = loadUi('untitled.ui', self)
        display_range = (0, 5)

        # Create the QGraphicsView and QGraphicsScene
        self.view = self.findChild(QGraphicsView, 'mygraphic')
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.view.setGeometry(0, 0, 940, 710)

        self.plot_all = pg.PlotWidget()
        self.plot_all.setBackground((255, 255, 255))
        self.plot_all.showGrid(x=True, y=True)
        self.plot_all.setXRange(*display_range)
        self.plot_all.setYRange(*display_range)

        self.plot_one = pg.PlotWidget()
        self.plot_one.setBackground((255, 255, 255))
        self.plot_one.showGrid(x=True, y=True)
        self.plot_one.setXRange(*display_range)
        self.plot_one.setYRange(*display_range)

        self.scene.addWidget(self.plot_all)
        self.scene.addWidget(self.plot_one)

        # Set visibility for graphs
        self.is_visible_all = True
        self.is_visible_one = False
        self.plot_all.setVisible(self.is_visible_all)
        self.plot_one.setVisible(self.is_visible_one)

        # Connect buttons
        self.button_ok.clicked.connect(self._plot_anchor)
        self.button_mode.clicked.connect(self._change_mode)

        # MQTT Connection
        self.client = mqtt.Client()
        # self.client.on_connect = self.on_mqtt_connect
        self.client.on_message = self.on_mqtt_message
        self.client.connect(mqtt_broker, mqtt_port, 60)

        # Set timer
        self.timer_one = QTimer()
        self.timer_one.timeout.connect(self._plot_one)
        self.timer_one.timeout.connect(self._plot_all)
        self.timer_one.start(1000)

        # self.timer_all = QTimer()
        # self.timer_all.timeout.connect(self._plot_all)
        # self.timer_all.start(1000)

    def _plot_anchor(self):
        try:
            x = float(self.box_x.text())
            y = float(self.box_y.text())
            ID = int(self.box_ID.text())

            color = (255, 0, 0)
            self.plot_all.plot([x], [y], pen=color, symbolBrush=color, symbol='o')
            self.plot_one.plot([x], [y], pen=color, symbolBrush=color, symbol='o')

        except ValueError:
            print(f'Invalid values: must be numbers!')

        self.box_x.clear()
        self.box_y.clear()
        self.box_ID.clear()

    def _plot_all(self):
        n_tag = 3
        x = [random.uniform(0, 5) for _ in range(n_tag)]
        y = [random.uniform(0, 5) for _ in range(n_tag)]
        color = (0, 255, 0)

        scatter = pg.ScatterPlotItem(x, y, size=10, pen=color, brush=pg.mkBrush(30, 255, 35, 255), symbol='o')
        try:
            self.plot_one.removeItem(self.prev_scatter)
        except AttributeError:
            pass

        self.plot_one.addItem(scatter)
        self.prev_scatter = scatter

    def _plot_one(self):
        x, y = [random.uniform(0, 5) for _ in range(2)]
        # print(point)
        color = (0, 0, 255)
        self.plot_all.plot([x], [y], pen=color, symbolBrush=color, symbol='o')

    def on_mqtt_message(self, client, userdata, msg):
        try:
            data = msg.payload.decode()
            x, y = map(float, data.split(','))

            color = (0, 0, 255)
            self.plot_all.plot([x], [y], pen=color, symbolBrush=color, symbol='o')

        except Exception as e:
            print(f"Error processing MQTT message: {e}")

    def _change_mode(self):
        self.is_visible_all = not self.is_visible_all
        self.is_visible_one = not self.is_visible_one

        self.plot_all.setVisible(self.is_visible_all)
        self.plot_one.setVisible(self.is_visible_one)

    def resizeEvent(self, *args, **kwargs):
        w, h = self.view.width(), self.view.height()
        self.plot_all.resize(QSize(int(w * .9), h))
        self.plot_one.resize(QSize(int(w * .9), h))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
