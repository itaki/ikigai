# data_analysis.py
import pandas as pd
import matplotlib.pyplot as plt
from loguru import logger
import seaborn as sns
from pathlib import Path

def load_parquet_data(file_path):
    try:
        return pd.read_parquet(file_path)
    except Exception as e:
        logger.error(f'Error loading parquet file: {e}')
        raise

def plot_time_series(data, title):
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data.values)
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel('Voltage')
    plt.tight_layout()
    plt.show()

def main():
    data_dir = Path('tools/ad_converter_data_collector/test_data')
    
    # Load data for master control AD converter
    off_data = load_parquet_data(data_dir / 'voltage_readings_master_control_ad_converter_20240909_194407.parquet')
    on_data = load_parquet_data(data_dir / 'voltage_readings_master_control_ad_converter_20240909_215735.parquet')
    
    # Assuming the data is already in the correct format, with a datetime index
    # and columns for each pin's voltage readings
    
    # Plot time series for pin 1 (band saw)
    plot_time_series(off_data['pin1'], 'Band Saw Off - Pin 1')
    plot_time_series(on_data['pin1'], 'Band Saw On - Pin 1')
    
    # Plot histograms
    plt.figure(figsize=(12, 6))
    sns.histplot(off_data['pin1'], kde=True, label='Off')
    sns.histplot(on_data['pin1'], kde=True, label='On')
    plt.title('Distribution of Voltage Readings - Pin 1 (Band Saw)')
    plt.xlabel('Voltage')
    plt.ylabel('Frequency')
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
