# tools/ad_converter_data_collector/data_analysis.py
import sys
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QComboBox, QPushButton, QWidget, QHBoxLayout, QFileDialog, QLabel, QSpinBox
from PyQt6.QtCore import pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from loguru import logger
from datetime import datetime
import numpy as np

def get_datasets(directory):
    datasets = []
    for file in os.listdir(directory):
        if file.endswith('.parquet'):
            datasets.append(file[:-8])  # Remove '.parquet'
    return datasets

def load_metadata(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def load_parquet_data(file_path):
    return pd.read_parquet(file_path)

class AnalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AD Converter Data Analysis")
        self.setGeometry(100, 100, 1200, 800)

        layout = QVBoxLayout()

        # File selection
        file_selection_layout = QHBoxLayout()
        self.file1_combo = QComboBox()
        self.file2_combo = QComboBox()
        self.file1_combo.addItems(get_datasets('tools/ad_converter_data_collector/test_data/'))
        self.file2_combo.addItems(get_datasets('tools/ad_converter_data_collector/test_data/'))
        file_selection_layout.addWidget(self.file1_combo)
        file_selection_layout.addWidget(self.file2_combo)
        layout.addLayout(file_selection_layout)

        # Pin selection
        self.pin_combo = QComboBox()
        self.pin_combo.addItems(['voltage_0', 'voltage_1', 'voltage_2', 'voltage_3'])
        layout.addWidget(self.pin_combo)

        # Window size for rolling standard deviation
        window_layout = QHBoxLayout()
        window_layout.addWidget(QLabel("Rolling Window Size:"))
        self.window_size_spin = QSpinBox()
        self.window_size_spin.setRange(2, 1000)
        self.window_size_spin.setValue(50)
        window_layout.addWidget(self.window_size_spin)
        layout.addLayout(window_layout)

        # Plot button
        self.plot_button = QPushButton("Plot Rolling Standard Deviation")
        self.plot_button.clicked.connect(self.plot_rolling_std)
        layout.addWidget(self.plot_button)

        # Save button
        self.save_button = QPushButton("Save Plot")
        self.save_button.clicked.connect(self.save_plot)
        self.save_button.setEnabled(False)
        layout.addWidget(self.save_button)

        # Matplotlib figure
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    @pyqtSlot()
    def plot_comparison(self):
        file1 = self.file1_combo.currentText()
        file2 = self.file2_combo.currentText()
        selected_pin = self.pin_combo.currentText()

        if file1 == file2:
            logger.warning("Please select different files for comparison")
            return

        data1 = load_parquet_data(f'tools/ad_converter_data_collector/test_data/{file1}.parquet')
        data2 = load_parquet_data(f'tools/ad_converter_data_collector/test_data/{file2}.parquet')
        metadata1 = load_metadata(f'tools/ad_converter_data_collector/test_data/{file1}_metadata.json')

        # Remove the first data point from both datasets
        data1 = data1.iloc[1:]
        data2 = data2.iloc[1:]

        pin_assignments = metadata1.get('pin_assignments', {})
        pin_number = selected_pin.split('_')[-1]
        pin_name = pin_assignments.get(pin_number, f"Pin {pin_number}")

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(data1[selected_pin], label=f'{pin_name} (File 1)')
        ax.plot(data2[selected_pin], label=f'{pin_name} (File 2)')
        ax.set_title(f'{pin_name} Comparison')
        ax.set_xlabel('Sample Number')
        ax.set_ylabel('Voltage')
        ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()

        logger.info(f"Generated comparison plot for {pin_name}")
        self.save_button.setEnabled(True)

    @pyqtSlot()
    def plot_rolling_std(self):
        file1 = self.file1_combo.currentText()
        file2 = self.file2_combo.currentText()
        selected_pin = self.pin_combo.currentText()
        window_size = self.window_size_spin.value()

        data1 = load_parquet_data(f'tools/ad_converter_data_collector/test_data/{file1}.parquet')
        data2 = load_parquet_data(f'tools/ad_converter_data_collector/test_data/{file2}.parquet')

        # Remove the first data point and calculate rolling standard deviation
        rolling_std1 = data1[selected_pin].iloc[1:].rolling(window=window_size).std()
        rolling_std2 = data2[selected_pin].iloc[1:].rolling(window=window_size).std()

        self.ax.clear()
        self.ax.plot(rolling_std1, label=f'{file1}')
        self.ax.plot(rolling_std2, label=f'{file2}')
        self.ax.set_title(f'Rolling Standard Deviation - {selected_pin}')
        self.ax.set_xlabel('Sample Number')
        self.ax.set_ylabel('Standard Deviation')
        self.ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()

        logger.info(f"Generated rolling standard deviation plot for {selected_pin}")
        self.save_button.setEnabled(True)

    @pyqtSlot()
    def save_plot(self):
        file1 = self.file1_combo.currentText()
        file2 = self.file2_combo.currentText()
        selected_pin = self.pin_combo.currentText()
        window_size = self.window_size_spin.value()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure the output_plots directory exists
        output_dir = 'tools/ad_converter_data_collector/output_plots'
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate the filename
        filename = f"comparison_{selected_pin}_{file1}_vs_{file2}_{timestamp}.png"
        file_path = os.path.join(output_dir, filename)
        
        # Save the plot
        self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved plot to {file_path}")

def main():
    app = QApplication(sys.argv)
    window = AnalysisWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
