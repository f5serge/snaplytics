from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit
)
from PyQt6.QtCore import Qt
from .screen_capture import ScreenCaptureWidget
from .processor import ImageProcessor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spanlytics")
        self.setMinimumSize(800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Status label
        self.status_label = QLabel("Ready to capture")
        
        # Capture button
        self.capture_btn = QPushButton("Capture Screen Area")
        self.capture_btn.clicked.connect(self.start_capture)
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        
        # Add widgets to layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.capture_btn)
        layout.addWidget(self.results_text)
        
        # Initialize components
        self.screen_capture = ScreenCaptureWidget(self)
        self.processor = ImageProcessor()
        
    def start_capture(self):
        self.status_label.setText("Starting capture...")
        self.hide()  # Hide main window before showing capture overlay
        self.screen_capture.start_capture()
        
    def process_capture(self, pixmap):
        self.status_label.setText("Processing capture...")
        self.show()
        if pixmap and not pixmap.isNull():
            self.status_label.setText("Analyzing image...")
            results = self.processor.process_image(pixmap)
            self.display_results(results)
        else:
            self.status_label.setText("Capture failed or cancelled")
            
    def display_results(self, results):
        self.status_label.setText("Results ready")
        if "error" in results and results["error"]:
            self.results_text.setText(
                f"Error processing image:\n{results['error']}"
            )
        else:
            output = "Summary:\n\n"
            
            if results.get("times"):
                output += "Times found:\n"
                for time_fmt, mins in zip(results["times_formatted"], results["times"]):
                    output += f"{time_fmt} ({mins} minutes)\n"
                output += f"\nTotal time: {results['total_formatted']}"
                output += f"\nTotal minutes: {results['total']}"
                output += f"\nAverage minutes: {results['average']:.1f}"
                output += f"\nCount: {results['count']}"
            
            self.results_text.setText(output) 