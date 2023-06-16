import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from PyQt5.QtCore import QTimer, QSize, QThread, pyqtSignal
import pyqtgraph as pg
from PyQt5.uic import loadUi
import paho.mqtt.client as mqtt
from pyqtgraph import TextItem
import json
import numpy as np

# Cấu hình MQTT Broker
mqtt_broker = "broker.hivemq.com"
mqtt_port = 1883
tags = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]


class MQTTThread(QThread):
    mqtt_data = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.client = mqtt.Client()
        self.client.on_connect = self.on_mqtt_connect
        self.client.on_message = self.on_mqtt_message

    def run(self):
        self.client.connect(mqtt_broker, mqtt_port, 60)
        self.client.loop_forever()

    def on_mqtt_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT Broker")
        # Subscribe các topic cho từng Tag
        for tag in tags:
            topic = f"tag/{tag}/location"
            self.client.subscribe(topic)

    def on_mqtt_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.mqtt_data.emit(data)
        except Exception as e:
            # print(f"Error processing MQTT message: {e}")
            print('Hello')


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = loadUi('untitled.ui', self)
        display_range = (0, 5)
        self.tags = {}
        self.trajectory = np.array([
            (0, 0),
            (2, 0),
            (2, 2),
            (0, 2),
            (0, 4),
            (4, 4)
        ])

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
        self.button_delete.clicked.connect(self._delete)

        # Create MQTT thread
        self.mqtt_thread = MQTTThread()
        self.mqtt_thread.mqtt_data.connect(self.on_mqtt_data)
        self.mqtt_thread.start()

    def _plot_anchor(self):
        try:
            x = float(self.box_x.text())
            y = float(self.box_y.text())
            ID = int(self.box_ID.text())

            color = (255, 0, 0)
            self.plot_all.plot([x], [y], pen=color, symbolBrush=color, symbol='t', symbolSize=16)
            self.plot_one.plot([x], [y], pen=color, symbolBrush=color, symbol='t', symbolSize=16)

            text_item_one = TextItem(text=str(ID), anchor=(0.5, 0), color=(0, 0, 0))
            text_item_all = TextItem(text=str(ID), anchor=(0.5, 0), color=(0, 0, 0))
            self.plot_all.addItem(text_item_one)
            text_item_one.setPos(x, y)

            self.plot_one.addItem(text_item_all)
            text_item_all.setPos(x, y)

        except ValueError:
            print(f'Invalid values: must be numbers!')

        self.box_x.clear()
        self.box_y.clear()
        self.box_ID.clear()

    def on_mqtt_data(self, data):
        try:
            address = data.get('address')
            x = float(data.get('x'))
            y = float(data.get('y'))

            self.tags[address] = (x, y)

            self._plot_one()
            self._plot_all()
            self._plot_trajectory()

        except Exception as e:
            print(f"Error processing MQTT data: {e}")
            pass

    def _plot_one(self):
        x, y = self.tags[1]
        color = (0, 0, 255)
        self.plot_one.plot([x], [y], pen=color, symbolBrush=color, symbol='o', symbolSize=5)

    def _plot_all(self):
        xs = []
        ys = []
        ids = []
        for address in self.tags.keys():
            x, y = self.tags[address]
            xs.append(x)
            ys.append(y)
            ids.append(address)

        # Delete previous data
        self.plot_all.clear()

        # Add current data
        for (x, y, _id) in zip(xs, ys, ids):
            label = TextItem(text=str(_id), color=(0, 0, 0))
            label.setPos(x, y)
            self.plot_all.addItem(label)

        scatter = pg.ScatterPlotItem(xs, ys, size=10, brush=(0, 0, 0), symbol='o')
        self.plot_all.addItem(scatter)

    def _change_mode(self):
        self.is_visible_all = not self.is_visible_all
        self.is_visible_one = not self.is_visible_one

        self.plot_all.setVisible(self.is_visible_all)
        self.plot_one.setVisible(self.is_visible_one)

    def resizeEvent(self, *args, **kwargs):
        w, h = self.view.width(), self.view.height()
        self.plot_all.resize(QSize(int(w * .9), h))
        self.plot_one.resize(QSize(int(w * .9), h))

    def _delete(self):
        self.plot_one.clear()

    def _plot_trajectory(self):
        xs, ys = self.trajectory.transpose()
        pen = pg.mkPen(color='r', width=3)
        lines1 = pg.PlotCurveItem(xs, ys, pen=pen)
        lines2 = pg.PlotCurveItem(xs, ys, pen=pen)
        self.plot_all.addItem(lines1)
        self.plot_one.addItem(lines2)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())