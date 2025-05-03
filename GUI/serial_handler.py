import serial
from PyQt6.QtCore import QThread, pyqtSignal

class SerialThread(QThread):
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.is_running = True

    def run(self):
        while self.is_running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_data = self.serial_port.readline()
                    try:
                        data = raw_data.decode('utf-8').strip()
                        if data:
                            self.data_received.emit(data)
                    except UnicodeDecodeError as e:
                        print(f"Decode error: {e}, Raw data: {raw_data.hex()}")
                        # Bỏ qua gói dữ liệu không hợp lệ
                        continue
            except serial.SerialException as e:
                self.error_occurred.emit(f"Serial error: {str(e)}")
                self.is_running = False
                break
            self.msleep(30)  

    def stop(self):
        self.is_running = False
        self.wait()