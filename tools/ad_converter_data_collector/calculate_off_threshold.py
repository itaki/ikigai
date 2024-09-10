# tools/ad_converter_data_collector/calculate_off_threshold.py
import pandas as pd
import numpy as np
from loguru import logger
import os

def load_parquet_data(file_path):
    return pd.read_parquet(file_path)

def calculate_max_rolling_std(data, column, window_size=40):
    # Remove the first data point as it might be anomalous
    rolling_std = data[column].iloc[1:].rolling(window=window_size).std()
    max_std = rolling_std.max()
    return max_std

def process_file(file_path):
    try:
        data = load_parquet_data(file_path)
        results = {}
        for column in ['voltage_0', 'voltage_1', 'voltage_2', 'voltage_3']:
            max_std = calculate_max_rolling_std(data, column)
            results[column] = max_std
        return results
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

def main():
    data_dir = 'tools/ad_converter_data_collector/test_data'
    files = [
        'voltage_readings_island_ad_converter_20240909_195640.parquet',
        'voltage_readings_master_control_ad_converter_20240909_194407.parquet'
    ]

    for file in files:
        file_path = os.path.join(data_dir, file)
        logger.info(f"Processing file: {file}")
        results = process_file(file_path)
        if results:
            for column, max_std in results.items():
                logger.info(f"{column}: Maximum rolling standard deviation: {max_std}")
        logger.info("---")

if __name__ == "__main__":
    main()