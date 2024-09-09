import os
import time
import numpy as np
from loguru import logger
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import pyarrow as pa
import pyarrow.parquet as pq
import psutil
import hashlib
import json
from collections import deque
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class DataCollector(QObject):
    progress_updated = pyqtSignal(int)
    error_count_updated = pyqtSignal(int)
    quality_updated = pyqtSignal(list)
    collection_finished = pyqtSignal(dict, dict)
    io_error_occurred = pyqtSignal(str)

    def __init__(self, board_config, pin_assignments, duration_minutes, sample_rate_hz):
        super().__init__()
        self.board_config = board_config
        self.pin_assignments = pin_assignments
        self.duration_minutes = duration_minutes
        self.sample_rate_hz = sample_rate_hz
        self.terminate_flag = False
        self.i2c = None
        self.ads = None

    def collect_voltage_readings(self):
        start_time = time.time()
        duration_seconds = int(self.duration_minutes * 60)
        logger.info(f"Starting voltage data collection for {self.board_config['label']} for {self.duration_minutes} minutes ({duration_seconds} seconds) at {self.sample_rate_hz} Hz")
        logger.info(f"Using {self.board_config['type']} at I2C address {self.board_config['i2c_address']}")
        
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.ads = ADS.ADS1115(self.i2c, address=int(self.board_config['i2c_address'], 16))
            self.ads.data_rate = min(self.sample_rate_hz, 860)
            self.ads.gain = 1

            channels = [AnalogIn(self.ads, getattr(ADS, f'P{i}')) for i in range(4)]
        except Exception as e:
            logger.error(f"Error initializing hardware: {e}")
            self.io_error_occurred.emit(f"Hardware initialization error: {str(e)}")
            return

        end_time = time.time() + duration_seconds
        interval = 1.0 / self.sample_rate_hz
        
        timestamps = deque()
        voltages = [deque() for _ in range(4)]
        
        sample_counts = [0, 0, 0, 0]
        error_count = 0
        expected_samples = 0
        next_sample_time = time.perf_counter()

        total_expected_samples = int(self.duration_minutes * 60 * self.sample_rate_hz)
        
        try:
            while time.time() < end_time and not self.terminate_flag:
                current_time = time.perf_counter()
                if current_time >= next_sample_time:
                    try:
                        timestamp = time.time()
                        timestamps.append(timestamp)
                        for i, chan in enumerate(channels):
                            voltage = chan.voltage
                            if not np.isfinite(voltage):
                                raise ValueError(f"Invalid voltage reading from channel {i}")
                            voltages[i].append(voltage)
                            sample_counts[i] += 1
                    except Exception as e:
                        error_count += 1
                        self.error_count_updated.emit(error_count)
                        logger.error(f"Error reading voltage: {e}")
                        if isinstance(e, OSError):
                            self.io_error_occurred.emit(f"I/O error during data collection: {str(e)}")
                            return
                    
                    next_sample_time += interval

                    expected_samples = int((time.time() - start_time) * self.sample_rate_hz)
                    qualities = [count / expected_samples if expected_samples > 0 else 1.0 for count in sample_counts]
                    self.quality_updated.emit(qualities)

                    self.progress_updated.emit(int((time.time() - start_time) / duration_seconds * 100))

                remaining_time = next_sample_time - time.perf_counter()
                if remaining_time > 0:
                    time.sleep(remaining_time)

        except Exception as e:
            logger.error(f"Error during data collection: {e}")
            self.io_error_occurred.emit(f"Error during data collection: {str(e)}")
            return

        actual_duration = time.time() - start_time
        actual_rate = sum(sample_counts) / actual_duration / 4

        data = {
            'timestamp': list(timestamps),
            'voltage_0': list(voltages[0]),
            'voltage_1': list(voltages[1]),
            'voltage_2': list(voltages[2]),
            'voltage_3': list(voltages[3])
        }

        checksum = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

        metadata = {
            'device_id': self.board_config['id'],
            'device_label': self.board_config['label'],
            'adc_address': self.board_config['i2c_address'],
            'voltage_range': '±4.096V',
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time)),
            'intended_duration': self.duration_minutes * 60,
            'actual_duration': actual_duration,
            'intended_sample_rate': self.sample_rate_hz,
            'actual_sample_rate': actual_rate,
            'errors': error_count,
            'checksum': checksum,
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'pin_assignments': self.pin_assignments
        }
        
        self.collection_finished.emit(data, metadata)

    def stop_collection(self):
        self.terminate_flag = True

    def cleanup_resources(self):
        if self.ads:
            # Perform any necessary cleanup for the ADS object
            pass
        if self.i2c:
            self.i2c.deinit()
        logger.info("Resources cleaned up")

def save_data(data, metadata, board_id):
    os.makedirs('test_data', exist_ok=True)
    
    table = pa.Table.from_pydict(data)
    parquet_filename = f"test_data/voltage_readings_{board_id}_{time.strftime('%Y%m%d_%H%M%S')}.parquet"
    
    # Convert all metadata values to strings and ensure keys are strings
    string_metadata = {str(k): str(v) for k, v in metadata.items()}
    
    # Write the table with metadata in a single operation
    pq.write_table(table, parquet_filename, compression='snappy', metadata=string_metadata)
    
    json_filename = parquet_filename.replace('.parquet', '_metadata.json')
    companion_metadata = {
        'board_id': board_id,
        'device_label': metadata['device_id'],
        'collection_start': time.strftime('%Y-%m-%d %H:%M:%S'),
        'intended_duration_minutes': metadata['intended_duration'] / 60,
        'actual_duration_minutes': round(metadata['actual_duration'] / 60, 2),
        'intended_sample_rate': metadata['intended_sample_rate'],
        'actual_sample_rate': round(metadata['actual_sample_rate'], 2),
        'total_samples': len(data['timestamp']),
        'errors': metadata['errors'],
        'cpu_usage_percent': metadata['cpu_usage'],
        'memory_usage_percent': metadata['memory_usage'],
        'pin_assignments': metadata['pin_assignments'],
        'parquet_file': os.path.basename(parquet_filename)
    }
    
    with open(json_filename, 'w') as f:
        json.dump(companion_metadata, f, indent=2)
    
    logger.info(f"Data saved to {parquet_filename}")
    logger.info(f"Metadata saved to {json_filename}")
