from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from datetime import datetime
from PyQt6.QtGui import QColor

class HistoryWindow(QMainWindow):
    def __init__(self, history, highlight_results=None):
        super().__init__()
        self.setWindowTitle("Snap History")
        self.setMinimumSize(600, 400)
        
        # Set window style
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: none;
                border-right: 1px solid #d0d0d0;
                border-bottom: 1px solid #d0d0d0;
            }
        """)
        
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Time", "Duration", "Total Minutes", "Count", "Details"
        ])
        
        # Populate table
        self.populate_history(history, highlight_results)
        
        layout.addWidget(self.table)
        
    def populate_history(self, history, highlight_results=None):
        self.table.setRowCount(len(history))
        highlight_row = -1
        
        for i, entry in enumerate(history):
            results = entry["results"]
            time = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
            
            # Check if this is the entry to highlight
            if highlight_results and results == highlight_results:
                highlight_row = i
            
            self.table.setItem(i, 0, QTableWidgetItem(time))
            self.table.setItem(i, 1, QTableWidgetItem(results["total_formatted"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(results["total"])))
            self.table.setItem(i, 3, QTableWidgetItem(str(results["count"])))
            
            times = ", ".join(results["times_formatted"])
            self.table.setItem(i, 4, QTableWidgetItem(times))
            
        # Highlight the specified row
        if highlight_row >= 0:
            for col in range(self.table.columnCount()):
                item = self.table.item(highlight_row, col)
                if item:
                    item.setBackground(QColor("#e6f3ff"))  # Light blue highlight
                    item.setForeground(QColor("#000000"))  # Black text
            
            # Scroll to the highlighted row
            self.table.scrollToItem(self.table.item(highlight_row, 0)) 