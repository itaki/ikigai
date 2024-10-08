import threading
import time
from loguru import logger
from devices.voltage_sensor import VoltageSensor

class VoltageSensorManager:
    def __init__(self, device_config, boards, app_config):
        self.voltage_sensors = {}  # Changed from self.sensors
        self.boards = boards
        self.stop_event = threading.Event()
        
        for device in device_config:
            if device['type'].lower() == 'voltage_sensor':
                sensor = VoltageSensor(device, app_config)
                board = self.boards.get(sensor.board_id)
                
                if not board:
                    logger.error(f"Board {sensor.board_id} not found for voltage sensor {sensor.id}")
                    continue
                
                sensor.set_board(board)
                self.voltage_sensors[sensor.id] = sensor  # Changed from self.sensors
        
        logger.info(f"Initialized {len(self.voltage_sensors)} voltage sensors")  # Changed from self.sensors

    def update(self):
        state_changed = False
        for sensor in self.voltage_sensors.values():  # Changed from self.sensors
            if sensor.board.is_initialized:
                if sensor.update():
                    state_changed = True
        return state_changed

    def cleanup(self):
        logger.info("🧹 Cleaning up VoltageSensorManager")
        self.stop_event.set()
        for sensor in self.voltage_sensors.values():  # Changed from self.sensors
            sensor.cleanup()
        logger.info("✅ VoltageSensorManager cleanup completed")

    def start_monitoring(self):
        logger.info("🔍 Starting voltage sensor monitoring")
        while not self.stop_event.is_set():
            self.update()
            time.sleep(0.1)  # Adjust this delay as needed

    def stop_monitoring(self):
        logger.info("🛑 Stopping voltage sensor monitoring")
        self.stop_event.set()

    def get_sensor_status(self, sensor_id):
        sensor = self.voltage_sensors.get(sensor_id)  # Changed from self.sensors
        return sensor.get_status() if sensor else None

    def get_all_sensor_statuses(self):
        return {sensor_id: sensor.get_status() for sensor_id, sensor in self.voltage_sensors.items()}  # Changed from self.sensors

    def reset_sensor(self, sensor_id):
        sensor = self.voltage_sensors.get(sensor_id)
        if sensor:
            sensor.reset()
            logger.info(f"Reset sensor {sensor_id}")
        else:
            logger.error(f"Sensor {sensor_id} not found")

    def reset_all_sensors(self):
        for sensor in self.voltage_sensors.values():
            sensor.reset()
        logger.info("Reset all sensors")

    def update_sensor_threshold(self, sensor_id, new_threshold):
        sensor = self.voltage_sensors.get(sensor_id)
        if sensor:
            sensor.sd_threshold = new_threshold
            logger.info(f"Updated threshold for sensor {sensor_id} to {new_threshold}")
        else:
            logger.error(f"Sensor {sensor_id} not found")
