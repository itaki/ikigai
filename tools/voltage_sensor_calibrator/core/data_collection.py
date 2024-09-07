from PyQt6.QtCore import QThread, pyqtSignal
import time


class DataCollectionThread(QThread):
    progress_update = pyqtSignal(int)
    collection_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, ads, pin, duration, sps):
        super().__init__()
        self.ads = ads
        self.pin = pin
        self.duration = duration
        self.sps = sps

    def run(self):
        data = []
        start_time = time.time()
        try:
            while time.time() - start_time < self.duration:
                reading = self.ads.get_reading(self.pin)
                data.append(reading)
                
                progress = int(((time.time() - start_time) / self.duration) * 100)
                self.progress_update.emit(progress)

                time.sleep(1 / self.sps)

            self.collection_complete.emit(data)
        except Exception as e:
            self.error_occurred.emit(str(e))