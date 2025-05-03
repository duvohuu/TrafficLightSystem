import sys
import time
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QApplication, QWidget, QGraphicsScene, QGraphicsDropShadowEffect, QPushButton, QGraphicsTextItem, QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QIcon, QPen, QPixmap
import serial
import serial.tools.list_ports
from traffic_light_ui import Ui_Traffic_Light
from serial_handler import SerialThread
import icons_rc

class TrafficLightGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Traffic_Light()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(':/icons/github.png'))
        self.status = "Disconnected"
        self.serial_port = None
        self.old_pos = None
        self.current_mode = -1
        self.is_paused = False

        # Load stylesheet
        self.load_stylesheet('styles.css')
        # Set initial size
        self.resize(1000, 700)
        # Remove title bar
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        # Set up blinking for lb_status
        self.blink_status_label()

        # SET UP SHADOW EFFECT
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(50)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QtCore.Qt.GlobalColor.black)
        self.setGraphicsEffect(self.shadow)

        # SET UP BUTTONS
        self.set_cursor_hand_for_buttons()
        self.ui.pbtn_minimize.clicked.connect(lambda: self.showMinimized())
        self.ui.pbtn_restore.clicked.connect(lambda: self.restore_or_maximize_window())
        self.ui.pbtn_close.clicked.connect(lambda: self.close())
        self.ui.pbtn_connect.clicked.connect(lambda: self.connect_serial())
        self.ui.pbtn_disconnect.clicked.connect(lambda: self.disconnect_serial())
        self.ui.pbtn_pause.clicked.connect(self.toggle_pause_resume)  
        self.ui.pbtn_mode.clicked.connect(self.send_change_mode)
        self.ui.pbtn_road1.clicked.connect(self.send_road1_green)
        self.ui.pbtn_road2.clicked.connect(self.send_road2_green)

        # Set up QGraphicsScene for the intersection
        self.scene = QGraphicsScene(self)
        self.ui.trafficIntersectionView.setScene(self.scene)

        # Initialize traffic light states
        self.lights = {
            "north": {"red": None, "yellow": None, "green": None},
            "south": {"red": None, "yellow": None, "green": None},
            "east": {"red": None, "yellow": None, "green": None},
            "west": {"red": None, "yellow": None, "green": None},
        }

        # Dictionary to store timer labels
        self.timer_labels = {
            "north": None,
            "south": None,
            "east": None,
            "west": None,
        }

        # Dictionary to store cars and their initial positions
        self.cars = {
            "north": None,
            "south": None,
            "east": None,
            "west": None,
        }
        self.initial_positions = {
            "north": None,
            "south": None,
            "east": None,
            "west": None,
        }
        self.is_green = {
            "north_south": False,  # GREEN1 cho North/South
            "east_west": False     # GREEN2 cho East/West
        }

        # Delay drawing the intersection until the window is fully ready
        QTimer.singleShot(0, self.draw_intersection)

        # Populate COM ports
        self.populate_com_ports()
        # Populate baud rates
        self.populate_baud_rates()

        # Timer for COM port updates
        self.com_port_timer = QTimer(self)
        self.com_port_timer.timeout.connect(self.populate_com_ports)
        self.com_port_timer.start(1000)  

        # Timer for moving cars
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.move_cars)
        self.move_timer.start(50)

    def load_stylesheet(self, path):
        # Load the stylesheet from the given path
        with open(path, 'r') as file:
            stylesheet = file.read()
        self.setStyleSheet(stylesheet)
    
    def blink_status_label(self):
        self.blink_state = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_status_label)
        self.timer.start(500)
    
    # Toggle status label
    def toggle_status_label(self):
        if self.blink_state:
            if self.status == "Connected":
                self.ui.lb_status.setText("CONNECTED")
                self.ui.lb_status.setStyleSheet("color: rgb(0, 255, 0); qproperty-alignment: AlignCenter;")
                self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-success-48-green.png"))
            elif self.status == "Pause":
                self.ui.lb_status.setText("PAUSE")
                self.ui.lb_status.setStyleSheet("color: rgb(255, 255, 0); qproperty-alignment: AlignCenter;")
                self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-pause-50-yellow.png"))  
            else:
                self.ui.lb_status.setText("DISCONNECTED")
                self.ui.lb_status.setStyleSheet("color: rgb(255, 0, 0); qproperty-alignment: AlignCenter;")
                self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-warning-50-red.png"))
        else:
            if self.status == "Connected":
                self.ui.lb_status.setText("CONNECTED")
                self.ui.lb_status.setStyleSheet("color: rgb(255, 255, 255); qproperty-alignment: AlignCenter;")
                self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-success-48-white.png"))
            elif self.status == "Pause":
                self.ui.lb_status.setText("PAUSE")
                self.ui.lb_status.setStyleSheet("color: rgb(255, 255, 255); qproperty-alignment: AlignCenter;")
                self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-pause-50-white.png"))  
            else:
                self.ui.lb_status.setText("DISCONNECTED")
                self.ui.lb_status.setStyleSheet("color: rgb(255, 255, 255); qproperty-alignment: AlignCenter;")
                self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-warning-50-white.png"))
        self.blink_state = not self.blink_state

    def set_cursor_hand_for_buttons(self):
        # Set cursor to pointing hand for all buttons
        for widget in self.findChildren(QPushButton):
            widget.setCursor(Qt.CursorShape.PointingHandCursor)

    def restore_or_maximize_window(self):
        # Toggle between maximized and normal window state
        if self.isMaximized():
            self.showNormal()
            self.ui.pbtn_restore.setIcon(QIcon(":/icons/icons8-maximize-window-50.png"))
        else:
            self.showMaximized()
            self.ui.pbtn_restore.setIcon(QIcon(":/icons/icons8-restore-down-52.png"))
        # Redraw the intersection after resizing
        self.draw_intersection()

    def mousePressEvent(self, event):
        # Handle mouse press for window dragging
        if self.isMaximized():
            return
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        # Handle mouse movement for window dragging
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        # Handle mouse release for window dragging
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.old_pos = None

    def resizeEvent(self, event):
        # Redraw the intersection when the window is resized
        self.draw_intersection()
        super().resizeEvent(event)

    def draw_intersection(self):
        ## Clear the scene to redraw
        self.scene.clear()

        ## Update scene dimensions based on QGraphicsView size
        scene_width = self.ui.trafficIntersectionView.width()
        scene_height = self.ui.trafficIntersectionView.height()
        self.scene.setSceneRect(0, 0, scene_width, scene_height)

        ## Variables for the intersection
        road_width = 130  
        lane_width = 30
        light_size = 30 
        light_spacing = 5
        timer_width = 40
        timer_height = 20
        wheel_size = 10
        center_x = scene_width // 2
        center_y = scene_height // 2
        pole_width = light_size + 20
        pole_height = 3 * (light_size + light_spacing) + timer_height + 20

        ## INTERSECTION 
        ### East-West 
        self.scene.addRect(0, center_y - road_width // 2, scene_width, road_width, brush=QBrush(QColor("#333333")))
        ### North-South 
        self.scene.addRect(center_x - road_width // 2, 0, road_width, scene_height, brush=QBrush(QColor("#333333")))
        ### Central square 
        self.scene.addRect(center_x - road_width // 2, center_y - road_width // 2, road_width, road_width, brush=QBrush(QColor("#222222")))
        ### Add traffic police
        traffic_police = self.scene.addPixmap(QPixmap(":/icons/pikachu.png"))
        traffic_police.setPos(center_x - 40, center_y - 40)
        traffic_police.setScale(0.15)
        
        ## DASHED LINES
        dash_length = 20
        dash_spacing = 40
        ### Vertical dashed lines 
        ### Top part 
        for i in range(0, int(center_y - road_width // 2 - dash_length), dash_spacing):
            self.scene.addLine(
                center_x, i, center_x, i + dash_length,
                QPen(QColor("#FFFF00"), 4, Qt.PenStyle.DashLine)
            )
        ### Bottom part 
        for i in range(int(center_y + road_width // 2), int(scene_height - dash_length), dash_spacing):
            self.scene.addLine(
                center_x, i, center_x, i + dash_length,
                QPen(QColor("#FFFF00"), 4, Qt.PenStyle.DashLine)
            )

        ### Horizontal dashed lines 
        ### Left part 
        for i in range(0, int(center_x - road_width // 2 - dash_length), dash_spacing):
            self.scene.addLine(
                i, center_y, i + dash_length, center_y,
                QPen(QColor("#FFFF00"), 4, Qt.PenStyle.DashLine)
            )
        ### Right part 
        for i in range(int(center_x + road_width // 2), int(scene_width - dash_length), dash_spacing):
            self.scene.addLine(
                i, center_y, i + dash_length, center_y,
                QPen(QColor("#FFFF00"), 4, Qt.PenStyle.DashLine)
            )

        ## CARS
        ### North car 
        self.cars["north"] = self.scene.addPixmap(QPixmap(":/icons/north_car.png"))
        north_pos_x = center_x - road_width // 2 + lane_width - 15
        north_pos_y = center_y - road_width // 2 - 100
        self.cars["north"].setPos(north_pos_x, north_pos_y)
        self.cars["north"].setScale(0.11)
        self.initial_positions["north"] = (north_pos_x, north_pos_y)

        ### South car 
        self.cars["south"] = self.scene.addPixmap(QPixmap(":/icons/south_car.png"))
        south_pos_x = center_x - road_width // 2 + lane_width + 5
        south_pos_y = center_y + road_width // 2
        self.cars["south"].setPos(south_pos_x, south_pos_y)
        self.cars["south"].setScale(0.22)
        self.initial_positions["south"] = (south_pos_x, south_pos_y)

        ### West car 
        self.cars["west"] = self.scene.addPixmap(QPixmap(":/icons/west_car.png"))
        west_pos_x = center_x - road_width // 2 - 120
        west_pos_y = center_y - lane_width // 2
        self.cars["west"].setPos(west_pos_x, west_pos_y)
        self.cars["west"].setScale(0.2)
        self.initial_positions["west"] = (west_pos_x, west_pos_y)

        ### East car 
        self.cars["east"] = self.scene.addPixmap(QPixmap(":/icons/east_car.png"))
        east_pos_x = center_x + road_width // 2 + 10
        east_pos_y = center_y - 3*lane_width + 10
        self.cars["east"].setPos(east_pos_x, east_pos_y)
        self.cars["east"].setScale(0.17)
        self.initial_positions["east"] = (east_pos_x, east_pos_y)

        ## TRAFFIC LIGHT
        ### North 
        self.scene.addRect(center_x - road_width // 2 - pole_width - 10, center_y - road_width // 2 - pole_height - 10, pole_width, pole_height, brush=QBrush(QColor("#111111")))
        self.lights["north"]["red"] = self.scene.addEllipse(center_x - road_width // 2 - pole_width, center_y - road_width // 2 - pole_height, light_size, light_size, brush=QBrush(Qt.GlobalColor.red))
        self.lights["north"]["yellow"] = self.scene.addEllipse(center_x - road_width // 2 - pole_width - 10 + 10, center_y - road_width // 2 - pole_height + light_size + light_spacing, light_size, light_size, brush=QBrush(Qt.GlobalColor.gray))
        self.lights["north"]["green"] = self.scene.addEllipse(center_x - road_width // 2 - pole_width - 10 + 10, center_y - road_width // 2 - pole_height + 2 * (light_size + light_spacing), light_size, light_size, brush=QBrush(Qt.GlobalColor.gray))
        self.timer_labels["north"] = self.scene.addText("30", QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.timer_labels["north"].setDefaultTextColor(Qt.GlobalColor.red)
        self.timer_labels["north"].setPos(center_x - road_width // 2 - pole_width - 10 + 15, center_y - road_width // 2 - pole_height + 3 * (light_size + light_spacing))

        ### South 
        self.scene.addRect(center_x + road_width // 2 + 10, center_y + road_width // 2 + 10, pole_width, pole_height, brush=QBrush(QColor("#111111")))
        self.lights["south"]["red"] = self.scene.addEllipse(center_x + road_width // 2 + 20, center_y + road_width // 2 + 20, light_size, light_size, brush=QBrush(Qt.GlobalColor.red))
        self.lights["south"]["yellow"] = self.scene.addEllipse(center_x + road_width // 2 + 20, center_y + road_width // 2 + 20 + light_size + light_spacing, light_size, light_size, brush=QBrush(Qt.GlobalColor.gray))
        self.lights["south"]["green"] = self.scene.addEllipse(center_x + road_width // 2 + 20, center_y + road_width // 2 + 20 + 2 * (light_size + light_spacing), light_size, light_size, brush=QBrush(Qt.GlobalColor.gray))
        self.timer_labels["south"] = self.scene.addText("30", QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.timer_labels["south"].setDefaultTextColor(Qt.GlobalColor.red)
        self.timer_labels["south"].setPos(center_x + road_width // 2 + 25, center_y + road_width // 2 + 20 + 3 * (light_size + light_spacing))

        ### East 
        self.scene.addRect(center_x + road_width // 2 + 10, center_y - road_width // 2 - pole_width - 10, pole_height, pole_width, brush=QBrush(QColor("#111111")))
        self.lights["east"]["red"] = self.scene.addEllipse(center_x + road_width // 2 + 20, center_y - road_width // 2 - pole_width, light_size, light_size, brush=QBrush(Qt.GlobalColor.gray))
        self.lights["east"]["yellow"] = self.scene.addEllipse(center_x + road_width // 2 + 20 + light_size + light_spacing, center_y - road_width // 2 - pole_width, light_size, light_size, brush=QBrush(Qt.GlobalColor.gray))
        self.lights["east"]["green"] = self.scene.addEllipse(center_x + road_width // 2 + 20 + 2 * (light_size + light_spacing), center_y - road_width // 2 - pole_width, light_size, light_size, brush=QBrush(Qt.GlobalColor.green))
        self.timer_labels["east"] = self.scene.addText("30", QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.timer_labels["east"].setDefaultTextColor(Qt.GlobalColor.green)
        self.timer_labels["east"].setPos(center_x + road_width // 2 + 20 + 3 * (light_size + light_spacing), center_y - road_width // 2 - pole_width)

        ### West 
        self.scene.addRect(center_x - road_width // 2 - pole_height - 10, center_y + road_width // 2 + 10, pole_height, pole_width, brush=QBrush(QColor("#111111")))
        self.lights["west"]["red"] = self.scene.addEllipse(center_x - road_width // 2 - pole_height, center_y + road_width // 2 + 20, light_size, light_size, brush=QBrush(Qt.GlobalColor.gray))
        self.lights["west"]["yellow"] = self.scene.addEllipse(center_x - road_width // 2 - pole_height + light_size + light_spacing, center_y + road_width // 2 + 20, light_size, light_size, brush=QBrush(Qt.GlobalColor.gray))
        self.lights["west"]["green"] = self.scene.addEllipse(center_x - road_width // 2 - pole_height + 2 * (light_size + light_spacing), center_y + road_width // 2 + 20, light_size, light_size, brush=QBrush(Qt.GlobalColor.green))
        self.timer_labels["west"] = self.scene.addText("30", QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.timer_labels["west"].setDefaultTextColor(Qt.GlobalColor.green)
        self.timer_labels["west"].setPos(center_x - road_width // 2 - pole_height + 3 * (light_size + light_spacing) + 5, center_y + road_width // 2 + 20)

        ## LABELS FOR ROADS
        font = QFont("Arial")
        font.setPointSize(16)
        font.setWeight(QFont.Weight.Bold)

        # North label
        north_label = self.scene.addText("NORTH", font)
        north_label.setPos(center_x - 40, 10)
        north_label.setDefaultTextColor(Qt.GlobalColor.white)

        # South label
        south_label = self.scene.addText("SOUTH", font)
        south_label.setPos(center_x - 40, scene_height - 50)
        south_label.setDefaultTextColor(Qt.GlobalColor.white)

        # East label
        east_label = self.scene.addText("EAST", font)
        east_label.setPos(scene_width - 100, center_y - 20)
        east_label.setDefaultTextColor(Qt.GlobalColor.white)

        # West label
        west_label = self.scene.addText("WEST", font)
        west_label.setPos(10, center_y - 20)
        west_label.setDefaultTextColor(Qt.GlobalColor.white)
    
    def move_cars(self):
        # Lấy kích thước cảnh
        scene_width = self.ui.trafficIntersectionView.width()
        scene_height = self.ui.trafficIntersectionView.height()

        # North/South (GREEN1)
        if self.is_green["north_south"]:
            # North: di chuyển xuống
            north_pos = self.cars["north"].pos()
            north_y = north_pos.y() + 5  # Di chuyển 5 pixel xuống
            if north_y > scene_height:  # Nếu ra ngoài khung hình
                north_y = self.initial_positions["north"][1]  # Quay về vị trí ban đầu
            self.cars["north"].setPos(north_pos.x(), north_y)

            # South: di chuyển lên
            south_pos = self.cars["south"].pos()
            south_y = south_pos.y() - 5  # Di chuyển 5 pixel lên
            if south_y < -50:  # Nếu ra ngoài khung hình (bao gồm kích thước xe)
                south_y = self.initial_positions["south"][1]  # Quay về vị trí ban đầu
            self.cars["south"].setPos(south_pos.x(), south_y)
        else:
            # Đặt lại vị trí ban đầu khi không có đèn xanh
            self.cars["north"].setPos(*self.initial_positions["north"])
            self.cars["south"].setPos(*self.initial_positions["south"])

        # East/West (GREEN2)
        if self.is_green["east_west"]:
            # East: di chuyển sang trái
            east_pos = self.cars["east"].pos()
            east_x = east_pos.x() - 5  # Di chuyển 5 pixel sang trái
            if east_x < -50:  # Nếu ra ngoài khung hình
                east_x = self.initial_positions["east"][0]  # Quay về vị trí ban đầu
            self.cars["east"].setPos(east_x, east_pos.y())

            # West: di chuyển sang phải
            west_pos = self.cars["west"].pos()
            west_x = west_pos.x() + 5  # Di chuyển 5 pixel sang phải
            if west_x > scene_width:  # Nếu ra ngoài khung hình
                west_x = self.initial_positions["west"][0]  # Quay về vị trí ban đầu
            self.cars["west"].setPos(west_x, west_pos.y())
        else:
            # Đặt lại vị trí ban đầu khi không có đèn xanh
            self.cars["east"].setPos(*self.initial_positions["east"])
            self.cars["west"].setPos(*self.initial_positions["west"])
        
    def populate_com_ports(self):
        # Populate cbb_port with available COM ports
        self.ui.cbb_port.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.ui.cbb_port.addItem(port.device)   
        if ports:
            self.ui.cbb_port.setCurrentIndex(0) 

    def populate_baud_rates(self):
        # Populate cbb_baud with common baud rates
        baud_rates = ["9600", "19200", "38400", "57600", "115200"]
        self.ui.cbb_baud.clear()
        self.ui.cbb_baud.addItems(baud_rates)
        self.ui.cbb_baud.setCurrentText("9600")

    def connect_serial(self):
        if self.serial_port and self.serial_port.is_open:
            return
        selected_port = self.ui.cbb_port.currentText()
        selected_baud = int(self.ui.cbb_baud.currentText())
        if not selected_port:
            self.ui.lb_status.setText("NO PORT SELECTED")
            self.ui.lb_status.setStyleSheet("color: rgb(255, 0, 0);")
            return
        try:
            self.serial_port = serial.Serial(port=selected_port, baudrate=selected_baud, timeout=0.1)
            self.serial_port.reset_input_buffer()
            self.serial_thread = SerialThread(self.serial_port)
            self.serial_thread.data_received.connect(self.parse_serial_data)
            self.serial_thread.error_occurred.connect(self.handle_serial_error)
            self.serial_thread.start()
            self.status = "Connected"
            self.ui.lb_status.setText("CONNECTED")
            self.ui.lb_status.setStyleSheet("color: rgb(0, 255, 0);")
            self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-success-48-green.png"))
        except serial.SerialException:
            self.status = "Disconnected"
            self.ui.lb_status.setText("CONNECTION FAILED")
            self.ui.lb_status.setStyleSheet("color: rgb(255, 0, 0);")
            self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-warning-50-red.png"))

    def disconnect_serial(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.serial_port = None
        self.status = "Disconnected"
        self.ui.lb_status.setText("DISCONNECTED")
        self.ui.lb_status.setStyleSheet("color: rgb(255, 0, 0);")
        self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-warning-50-red.png"))

    def toggle_pause_resume(self):
        if not self.serial_thread:
            print("No serial thread to pause/resume")
            return
        if not self.is_paused:
            # Pause
            self.serial_thread.stop()
            self.serial_thread.wait()  # Đợi luồng dừng hoàn toàn
            self.status = "Pause"
            self.is_paused = True
            self.ui.lb_status.setText("PAUSE")
            self.ui.lb_status.setStyleSheet("color: rgb(255, 255, 0);")
            self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-pause-50-yellow.png"))
            print(f"[{time.time()}] Paused serial thread")
        else:
            # Resume
            self.serial_thread = SerialThread(self.serial_port)
            self.serial_thread.data_received.connect(self.parse_serial_data)
            self.serial_thread.error_occurred.connect(self.handle_serial_error)
            self.serial_thread.start()
            self.status = "Connected"
            self.is_paused = False
            self.ui.lb_status.setText("CONNECTED")
            self.ui.lb_status.setStyleSheet("color: rgb(0, 255, 0);")
            self.ui.lb_icon_status.setPixmap(QtGui.QPixmap(":/icons/icons8-success-48-green.png"))
            print(f"[{time.time()}] Resumed serial thread")

    def handle_serial_error(self, error_msg):
        self.disconnect_serial()
        self.ui.lb_status.setText("SERIAL ERROR")
        self.ui.lb_status.setStyleSheet("color: rgb(255, 0, 0);")
        print(error_msg)

    def parse_serial_data(self, data):
        print(f"[{time.time()}] Received: {data}")
        try:
            values = data.split(',')
            if len(values) == 9:
                mode = int(values[0])
                self.current_mode = mode  # Cập nhật current_mode
                self.status = "Connected"  # Đảm bảo status là Connected
                print(f"Updated mode: {self.current_mode}")
                self.update_mode_label(mode)
                self.update_traffic_lights("north", values[1:5], mode)
                self.update_traffic_lights("south", values[1:5], mode)
                self.update_traffic_lights("east", values[5:9], mode)
                self.update_traffic_lights("west", values[5:9], mode)
            else:
                print(f"Invalid data length: {len(values)}")
                self.ui.lb_status.setText("INVALID DATA")
                self.ui.lb_status.setStyleSheet("color: rgb(255, 165, 0);")
                QTimer.singleShot(1000, lambda: self.ui.lb_status.setText(self.status.upper()))
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.reset_input_buffer()
        except ValueError as e:
            print(f"Parse error: {e}")
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.reset_input_buffer()

    def update_traffic_lights(self, direction, states, mode):
        red, yellow, green, countdown = map(int, states)
        self.lights[direction]["red"].setBrush(QBrush(Qt.GlobalColor.red if red else Qt.GlobalColor.gray))
        self.lights[direction]["yellow"].setBrush(QBrush(Qt.GlobalColor.yellow if yellow else Qt.GlobalColor.gray))
        self.lights[direction]["green"].setBrush(QBrush(Qt.GlobalColor.green if green else Qt.GlobalColor.gray))
        self.timer_labels[direction].setPlainText(str(countdown) if mode == 0 and countdown >= 0 else "")
        if mode == 0 and countdown >= 0:
            self.timer_labels[direction].setDefaultTextColor(
                Qt.GlobalColor.red if red else Qt.GlobalColor.green if green else Qt.GlobalColor.yellow
            )
        # Theo dõi trạng thái đèn xanh
        if direction == "north":  # North/South dùng GREEN1
            self.is_green["north_south"] = (green == 1)
        elif direction == "east":  # East/West dùng GREEN2
            self.is_green["east_west"] = (green == 1)

    def update_mode_label(self, mode):
        mode_text = {0: "Auto", 1: "Manual", 2: "Midnight"}.get(mode, "Unknown Mode")
        self.ui.le_display_mode.setText(mode_text)
        self.current_mode = mode
        # Bật/tắt nút road1, road2 dựa trên mode
        if mode == 1:  # Manual Mode
            self.ui.pbtn_road1.setEnabled(True)
            self.ui.pbtn_road2.setEnabled(True)
        else:
            self.ui.pbtn_road1.setEnabled(False)
            self.ui.pbtn_road2.setEnabled(False)

    def send_change_mode(self):
        if self.serial_port and self.serial_port.is_open:
            for _ in range(3):
                try:
                    self.serial_port.reset_output_buffer()
                    self.serial_port.write(b'M\n')
                    self.serial_port.flush()
                    print(f"[{time.time()}] Sent: M\\n")
                    self.ui.pbtn_mode.setEnabled(False)
                    QTimer.singleShot(500, lambda: self.ui.pbtn_mode.setEnabled(True))
                    break
                except serial.SerialException as e:
                    print(f"Retry sending M: {str(e)}")
                    time.sleep(0.1)
            else:
                self.handle_serial_error("Failed to send mode change command after retries")
        else:
            print(f"Cannot send M: Serial port not open")

    def send_road1_green(self):
        if self.serial_port and self.serial_port.is_open:
            if self.current_mode == 1:
                for _ in range(3):
                    try:
                        self.serial_port.reset_output_buffer()
                        self.serial_port.write(b'R1\n')
                        self.serial_port.flush()
                        print(f"[{time.time()}] Sent: R1\\n")
                        self.ui.pbtn_road1.setEnabled(False)
                        QTimer.singleShot(1000, lambda: self.ui.pbtn_road1.setEnabled(True))
                        break
                    except serial.SerialException as e:
                        print(f"Retry sending R1: {str(e)}")
                        time.sleep(0.5)
                else:
                    self.handle_serial_error("Failed to send road1 green command after retries")
            else:
                self.ui.lb_status.setText("ONLY IN MANUAL MODE")
                self.ui.lb_status.setStyleSheet("color: rgb(255, 165, 0);")
                QTimer.singleShot(1000, lambda: self.ui.lb_status.setText(self.status.upper()))
        else:
            print(f"Cannot send R1: Serial port not open")

    def send_road2_green(self):
        if self.serial_port and self.serial_port.is_open:
            if self.current_mode == 1:
                for _ in range(3):
                    try:
                        self.serial_port.reset_output_buffer()
                        self.serial_port.write(b'R2\n')
                        self.serial_port.flush()
                        print(f"[{time.time()}] Sent: R2\\n")
                        self.ui.pbtn_road2.setEnabled(False)
                        QTimer.singleShot(1000, lambda: self.ui.pbtn_road2.setEnabled(True))
                        break
                    except serial.SerialException as e:
                        print(f"Retry sending R2: {str(e)}")
                        time.sleep(0.5)
                else:
                    self.handle_serial_error("Failed to send road2 green command after retries")
            else:
                self.ui.lb_status.setText("ONLY IN MANUAL MODE")
                self.ui.lb_status.setStyleSheet("color: rgb(255, 165, 0);")
                QTimer.singleShot(1000, lambda: self.ui.lb_status.setText(self.status.upper()))
        else:
            print(f"Cannot send R2: Serial port not open")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TrafficLightGUI()
    window.show()
    sys.exit(app.exec())