import sys
import os
import time
import board
import busio
import numpy as np

from scipy.signal import find_peaks
import matplotlib.pyplot as plt
from datetime import datetime
import xml.etree.ElementTree as ET
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from loguru import logger
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

# Import the ConfigLoader
from utils.config_loader import ConfigLoader

# Import local modules
from core.data_collection import DataCollectionThread
from gui.vsc_gui import CalibrationToolGUI

# Configure Loguru logger
logger.add("logs/voltage_sensor_calibrator.log", rotation="1 MB")

class ADS1115Wrapper:
    def __init__(self, i2c, address):
        self.ads = ADS.ADS1115(i2c, address=address)

    def get_reading(self, pin):
        chan = AnalogIn(self.ads, getattr(ADS, f'P{pin}'))
        return chan.voltage



class CalibrationTool:
    def __init__(self):
        logger.info("Initializing CalibrationTool")
        self.config_loader = ConfigLoader()
        logger.info("ConfigLoader created")
        self.initialize_i2c()
        self.boards = {}
        self.load_config()
        logger.info("CalibrationTool initialization complete")

    def initialize_i2c(self):
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            logger.info("I2C interface initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize I2C interface: {str(e)}")
            self.i2c = None

    def load_config(self):
        logger.info("Starting to load configuration")
        try:
            self.config_loader.reload_configs()
            logger.info("Configs reloaded")
            self.devices = self.config_loader.get_devices()
            logger.info(f"Devices loaded: {len(self.devices)}")
            self.board_configs = self.config_loader.get_boards()
            logger.info(f"Board configs loaded: {len(self.board_configs)}")
            
            # Create a mapping of board IDs to their configurations
            self.board_map = {board['id']: board for board in self.board_configs}
            
            logger.info("Configurations loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def get_board_config_for_device(self, device_id):
        device = next((d for d in self.devices if d['id'] == device_id), None)
        if not device:
            logger.error(f"No device found with ID: {device_id}")
            return None
        
        board_id = device['connection']['board']
        logger.debug(f"Device {device_id} is associated with board: {board_id}")
        
        board_config = self.board_map.get(board_id)
        if not board_config:
            logger.error(f"No board configuration found for board: {board_id}")
            logger.debug(f"Available board IDs: {list(self.board_map.keys())}")
            return None
        
        logger.debug(f"Found board config for {board_id}: {board_config}")
        return board_config

    def get_board(self, device_id):
        logger.info(f"Attempting to get board for device: {device_id}")
        board_config = self.get_board_config_for_device(device_id)
        if not board_config:
            logger.error(f"Failed to get board config for device: {device_id}")
            return None

        board_id = board_config['id']
        logger.debug(f"Board ID for device {device_id}: {board_id}")
        if board_id not in self.boards:
            logger.info(f"Board {board_id} not initialized. Initializing now.")
            if board_config['type'] == 'ADS1115':
                try:
                    if self.i2c is None:
                        raise ValueError("I2C interface is not initialized")
                    address = int(board_config['i2c_address'], 16)
                    self.boards[board_id] = ADS1115Wrapper(self.i2c, address)
                    logger.info(f"Board {board_id} initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize board {board_id}: {str(e)}")
                    return None
            else:
                logger.error(f"Unsupported board type: {board_config['type']}")
                return None
        return self.boards.get(board_id)

    def analyze_calibration_data(self, device, off_data, on_data):
        off_data = np.array(off_data)
        on_data = np.array(on_data)

        results = {
            'off_mean': np.mean(off_data),
            'off_std': np.std(off_data),
            'on_mean': np.mean(on_data),
            'on_std': np.std(on_data),
        }

        # Calculate optimal threshold
        results['optimal_threshold'] = self.calculate_optimal_threshold(off_data, on_data)

        # Calculate optimal window size
        results['optimal_window_size'] = self.calculate_optimal_window_size(off_data, on_data)

        # Calculate optimal percentage
        results['optimal_percentage'] = self.calculate_optimal_percentage(off_data, on_data, results['optimal_threshold'], results['optimal_window_size'])

        logger.info(f"Calibration results: {results}")

        # Save the calibration data
        (off_filename, on_filename), timestamp = self.save_calibration_data_xml(device, off_data, on_data)

        # Visualize the data
        analysis_filename = self.visualize_data(device, off_data, on_data, results, timestamp)

        return results, (off_filename, on_filename, analysis_filename)

    def calculate_optimal_threshold(self, off_data, on_data):
        combined_data = np.concatenate((off_data, on_data))
        hist, bin_edges = np.histogram(combined_data, bins='auto')
        peaks, _ = find_peaks(hist)
        if len(peaks) >= 2:
            valley = np.argmin(hist[peaks[0]:peaks[1]]) + peaks[0]
            return bin_edges[valley]
        else:
            return np.mean(off_data) + 3 * np.std(off_data)

    def calculate_optimal_window_size(self, off_data, on_data):
        max_window_size = min(len(off_data), len(on_data))
        window_sizes = range(10, max_window_size, 10)
        accuracies = []

        for window_size in window_sizes:
            accuracy = self.calculate_accuracy(off_data, on_data, window_size)
            accuracies.append(accuracy)

        return window_sizes[np.argmax(accuracies)]

    def calculate_optimal_percentage(self, off_data, on_data, threshold, window_size):
        percentages = range(10, 100, 5)
        accuracies = []

        for percentage in percentages:
            accuracy = self.calculate_accuracy(off_data, on_data, window_size, threshold, percentage)
            accuracies.append(accuracy)

        return percentages[np.argmax(accuracies)]

    def calculate_accuracy(self, off_data, on_data, window_size, threshold=None, percentage=50):
        if threshold is None:
            threshold = np.mean(off_data) + 3 * np.std(off_data)

        off_windows = [off_data[i:i+window_size] for i in range(0, len(off_data)-window_size+1, window_size)]
        on_windows = [on_data[i:i+window_size] for i in range(0, len(on_data)-window_size+1, window_size)]

        off_correct = sum(1 for window in off_windows if np.mean(np.abs(window - np.mean(off_data)) > threshold) * 100 < percentage)
        on_correct = sum(1 for window in on_windows if np.mean(np.abs(window - np.mean(off_data)) > threshold) * 100 >= percentage)

        return (off_correct + on_correct) / (len(off_windows) + len(on_windows))

    def visualize_data(self, device, off_data, on_data, results, timestamp):
        plt.figure(figsize=(15, 12))  # Increased figure height to accommodate the text

        # Histogram
        plt.subplot(2, 2, 1)
        plt.hist(off_data, bins=50, alpha=0.5, label='Off State')
        plt.hist(on_data, bins=50, alpha=0.5, label='On State')
        plt.axvline(results['optimal_threshold'], color='r', linestyle='dashed', linewidth=2, label='Optimal Threshold')
        plt.xlabel('Voltage')
        plt.ylabel('Frequency')
        plt.title('Voltage Distribution')
        plt.legend()

        # Time series
        plt.subplot(2, 2, 2)
        plt.plot(off_data, label='Off State', alpha=0.5)
        plt.plot(range(len(off_data), len(off_data) + len(on_data)), on_data, label='On State', alpha=0.5)
        plt.axhline(results['optimal_threshold'], color='r', linestyle='dashed', linewidth=2, label='Optimal Threshold')
        plt.xlabel('Sample')
        plt.ylabel('Voltage')
        plt.title('Time Series')
        plt.legend()

        # Window size vs Accuracy
        plt.subplot(2, 2, 3)
        window_sizes = range(10, min(len(off_data), len(on_data)), 10)
        accuracies = [self.calculate_accuracy(off_data, on_data, ws, results['optimal_threshold'], results['optimal_percentage']) for ws in window_sizes]
        plt.plot(window_sizes, accuracies)
        plt.axvline(results['optimal_window_size'], color='r', linestyle='dashed', linewidth=2, label='Optimal Window Size')
        plt.xlabel('Window Size')
        plt.ylabel('Accuracy')
        plt.title('Window Size vs Accuracy')
        plt.legend()

        # Percentage vs Accuracy
        plt.subplot(2, 2, 4)
        percentages = range(10, 100, 5)
        accuracies = [self.calculate_accuracy(off_data, on_data, results['optimal_window_size'], results['optimal_threshold'], p) for p in percentages]
        plt.plot(percentages, accuracies)
        plt.axvline(results['optimal_percentage'], color='r', linestyle='dashed', linewidth=2, label='Optimal Percentage')
        plt.xlabel('Percentage')
        plt.ylabel('Accuracy')
        plt.title('Percentage vs Accuracy')
        plt.legend()

        plt.tight_layout()

        # Add text box with results
        results_text = (
            f"Off Mean: {results['off_mean']:.6f}\n"
            f"Off Std: {results['off_std']:.6f}\n"
            f"On Mean: {results['on_mean']:.6f}\n"
            f"On Std: {results['on_std']:.6f}\n"
            f"Optimal Threshold: {results['optimal_threshold']:.6f}\n"
            f"Optimal Window Size: {results['optimal_window_size']}\n"
            f"Optimal Percentage: {results['optimal_percentage']}%"
        )
        plt.figtext(0.5, 0.01, results_text, ha="center", fontsize=10, bbox={"facecolor":"white", "alpha":0.8, "pad":5})

        # Generate filename with device name and timestamp
        device_name = device['id']
        filename = f"tools/test_data/{device_name}_{timestamp}_analysis.png"
        
        plt.savefig(filename, bbox_inches='tight', dpi=300)
        logger.info(f"Calibration analysis visualization saved as {filename}")
        plt.close()
        return filename

    def save_calibration_data_xml(self, device, off_data, on_data):
        # Create a directory for calibration data if it doesn't exist
        os.makedirs('tools/test_data', exist_ok=True)

        # Generate base filename with device name and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        device_name = device['id']
        base_filename = f"{device_name}_{timestamp}"

        # Function to create and save XML for a dataset
        def save_xml(data, state):
            filename = f"tools/test_data/{base_filename}_{state}.xml"
            root = ET.Element("CalibrationData")
            ET.SubElement(root, "DeviceID").text = device['id']
            ET.SubElement(root, "DeviceLabel").text = device['label']
            ET.SubElement(root, "Timestamp").text = timestamp
            ET.SubElement(root, "State").text = state
            ET.SubElement(root, "Readings").text = ",".join(map(str, data))

            tree = ET.ElementTree(root)
            try:
                tree.write(filename)
                logger.info(f"{state.capitalize()} calibration data saved to {filename}")
                return filename
            except Exception as e:
                logger.error(f"Error saving {state} calibration data: {str(e)}")
                return None

        # Save OFF and ON data separately
        off_filename = save_xml(off_data, "off")
        on_filename = save_xml(on_data, "on")

        return (off_filename, on_filename), timestamp

if __name__ == '__main__':
    from gui.vsc_gui import CalibrationToolGUI
    logger.info("Starting Voltage Sensor Calibrator application")
    app = QApplication(sys.argv)
    calibration_tool = CalibrationTool()
    ex = CalibrationToolGUI(calibration_tool)
    ex.show()
    logger.info("Application window shown")
    sys.exit(app.exec())
