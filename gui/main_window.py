# gui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from loguru import logger

class MainWindow(QMainWindow):
    def __init__(self, board_manager):
        super().__init__()

        self.board_manager = board_manager

        # Set up the GUI layout
        self.setWindowTitle("Shop Management GUI")
        self.setGeometry(100, 100, 800, 600)

        # Example label showing board status
        layout = QVBoxLayout()

        self.status_label = QLabel("Board Status: Loading...")
        layout.addWidget(self.status_label)

        # Set up the central widget and layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Load and display the status of the boards
        self.load_board_status()

    def load_board_status(self):
        try:
            # Retrieve board statuses and update the label
            board_status = "All boards initialized" if self.board_manager else "No boards initialized"
            self.status_label.setText(f"Board Status: {board_status}")

        except Exception as e:
            logger.error(f"Error updating board status: {str(e)}")
