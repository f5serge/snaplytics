from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QWidget, 
    QVBoxLayout, QHBoxLayout, QLabel, QDialog, QApplication,
    QPushButton, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QCursor, QColor
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QGuiApplication
from .screen_capture import ScreenCaptureWidget
from .processor import ImageProcessor
from .hotkey_manager import HotkeyManager
from .settings_dialog import SettingsDialog
from datetime import datetime
import json
import os
from plyer import notification
import sys
from pathlib import Path
from win10toast import ToastNotifier
import threading
from winotify import Notification, audio

class TrayAppWidget(QWidget):
    """Main widget to serve as parent for other widgets"""
    def __init__(self, tray_app):
        super().__init__()
        self.tray_app = tray_app
        self.hide()  # Keep it hidden

class ResultsPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(2)
        
        # Set a smaller fixed width
        self.setFixedWidth(220)  # Reduced width to ensure it fits
        
        # App name/title with icon
        title_layout = QHBoxLayout()
        title_layout.setSpacing(6)
        title_layout.setContentsMargins(0, 0, 0, 4)
        
        app_icon = QLabel()
        icon_pixmap = QPixmap(16, 16)  # Slightly larger icon
        icon_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(icon_pixmap)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawRect(2, 2, 12, 12)
        painter.end()
        app_icon.setPixmap(icon_pixmap)
        
        title = QLabel("Snaplytics")
        title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
        """)
        
        title_layout.addWidget(app_icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Results label
        self.label = QLabel()
        self.label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                padding: 4px 0;
            }
        """)
        self.label.setWordWrap(True)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)
        button_layout.setContentsMargins(0, 4, 0, 0)
        
        self.details_link = QPushButton("Show Details")
        self.details_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.details_link.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.06);
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
            }
        """)
        
        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dismiss_btn.setStyleSheet(self.details_link.styleSheet())
        dismiss_btn.clicked.connect(self.hide)
        
        button_layout.addWidget(self.details_link)
        button_layout.addWidget(dismiss_btn)
        
        # Add all layouts
        self.layout.addLayout(title_layout)
        self.layout.addWidget(self.label)
        self.layout.addLayout(button_layout)
        
        # Window style
        self.setStyleSheet("""
            QDialog {
                background-color: #202020;
                border: 1px solid #303030;
                border-radius: 6px;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        # Setup auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide)
        
    def set_tray_app(self, tray_app):
        self.tray_app = tray_app
        
    def show_results(self, results, pos):
        if results.get("times"):
            text = f"Total: {results['total_formatted']}\nCount: {results['count']}"
            self.label.setText(text)
            
            # Store results for details view
            self.current_results = results
            
            # Get primary screen
            primary = QGuiApplication.primaryScreen()
            available = primary.availableGeometry()
            
            # Get window size
            size = self.sizeHint()
            
            # Position like Windows 11 notifications (bottom-right)
            x = available.right() - size.width() - 12  # 12px from right edge
            y = available.bottom() - size.height() - 48  # 48px from bottom to account for taskbar
            
            # Ensure window stays on top
            self.setWindowFlags(
                Qt.WindowType.ToolTip | 
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
            
            # Move and show
            self.move(x, y)
            self.show()
            self.raise_()
            
            # Start auto-hide timer (5 seconds)
            self.hide_timer.start(5000)
            
    def show_details(self):
        # Stop auto-hide timer when showing details
        self.hide_timer.stop()
        self.hide()
        
        # Show history window with current results highlighted
        if hasattr(self, 'current_results') and self.tray_app:
            self.tray_app.show_history(highlight_results=self.current_results)
            
    def enterEvent(self, event):
        # Stop timer when mouse enters the popup
        self.hide_timer.stop()
        
    def leaveEvent(self, event):
        # Restart timer when mouse leaves the popup
        self.hide_timer.start(5000)

class TrayApp(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        
        # Create main widget with reference to self
        self.widget = TrayAppWidget(self)
        
        # Initialize components first
        self.screen_capture = None
        self.processor = ImageProcessor()
        self.results_popup = ResultsPopup()
        self.results_popup.set_tray_app(self)
        self.history = []
        
        # Load settings
        self.settings = self.load_settings()
        
        # Setup hotkey
        self.hotkey_manager = HotkeyManager()
        initial_hotkey = self.settings.get("hotkey", "Alt+Shift+S")
        print(f"Setting up initial hotkey: {initial_hotkey}")
        
        # Connect signal and register hotkey
        self.hotkey_manager.hotkey_triggered.connect(self.handle_hotkey)
        print("Signal connected")
        self.hotkey_manager.register(initial_hotkey)
        
        # Set icon - create a basic icon if resource not found
        icon_path = "resources/icon.png"
        if not os.path.exists(icon_path):
            from PyQt6.QtGui import QPixmap, QPainter
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawRect(0, 0, 63, 63)
            painter.drawText(10, 32, "Snap")
            painter.end()
            self.setIcon(QIcon(pixmap))
        else:
            self.setIcon(QIcon(icon_path))
            
        self.setVisible(True)
        
        # Create tray menu
        self.setup_menu()
        
        # Store the last capture position
        self.last_capture_pos = None
        
        # Get app path and icon path
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            self.app_path = Path(sys.executable).parent
        else:
            # Running from source
            self.app_path = Path(__file__).parent.parent.parent
            
        self.icon_path = str(self.app_path / "resources" / "icon.png")
        
        # Register app for notifications
        self.app_id = "Snaplytics.App"
        
        # Initialize Windows toast notifier
        self.toaster = ToastNotifier()
        
    def setup_menu(self):
        menu = QMenu()
        
        # Capture action
        capture_action = QAction("Capture Area", self)
        capture_action.triggered.connect(self.start_capture)
        menu.addAction(capture_action)
        
        menu.addSeparator()
        
        # Show history action
        history_action = QAction("Show History", self)
        history_action.triggered.connect(self.show_history)
        menu.addAction(history_action)
        
        # Settings action
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_app)
        menu.addAction(exit_action)
        
        self.setContextMenu(menu)
        
    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"hotkey": "Ctrl+Shift+S"}
            
    def save_settings(self):
        with open("settings.json", "w") as f:
            json.dump(self.settings, f)
            
    def handle_hotkey(self, combo):
        """Handle hotkey in the main thread"""
        print(f"TrayApp received hotkey signal: {combo}")
        self.start_capture()
        
    def start_capture(self):
        print("start_capture called")
        try:
            # Create screen capture widget if needed
            if not self.screen_capture:
                self.screen_capture = ScreenCaptureWidget(self.widget)
            else:
                self.screen_capture.hide()
            
            self.screen_capture.start_capture()
            print("Screen capture started")
            
        except Exception as e:
            print(f"Error starting capture: {e}")
            import traceback
            traceback.print_exc()
        
    def process_capture(self, pixmap, pos=None):
        if pixmap and not pixmap.isNull():
            results = self.processor.process_image(pixmap)
            
            # Save to history
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "results": results
            })
            
            try:
                # Format message with better spacing and alignment
                if results['count'] > 0:
                    message = (
                        f"✓ Found {results['count']} time{'s' if results['count'] > 1 else ''}\n"
                        f"Total duration: {results['total_formatted']}"
                    )
                else:
                    message = "No times found in the captured area"
                
                # Create Windows notification
                toast = Notification(
                    app_id=self.app_id,
                    title="Time Summary",
                    msg=message,
                    duration="long",
                    icon=self.icon_path if os.path.exists(self.icon_path) else None
                )
                
                # Add action button with protocol handler
                toast.add_actions(
                    label="Show Details",
                    launch="snaplytics://show_details"  # Custom protocol
                )
                
                # Set notification sound
                toast.set_audio(audio.Default, loop=False)
                
                # Show notification
                toast.show()
                
            except Exception as e:
                print(f"Error showing notification: {e}")
                # Fall back to custom popup if notification fails
                if pos is None:
                    pos = QCursor.pos()
                self.results_popup.show_results(results, pos)
        
    def show_history(self, highlight_results=None):
        from .history_window import HistoryWindow
        self.history_window = HistoryWindow(self.history, highlight_results)
        self.history_window.show()
        
    def quit_app(self):
        # Clean up
        self.hotkey_manager.unregister_all()
        self.save_settings()
        # Hide tray icon
        self.hide()
        # Quit application
        QApplication.quit()
        
    def show_settings(self):
        dialog = SettingsDialog(self.widget, self.settings.get("hotkey", "Alt+Shift+S"))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_hotkey = dialog.get_hotkey()
            if new_hotkey and new_hotkey != self.settings.get("hotkey"):
                # Update hotkey
                self.settings["hotkey"] = new_hotkey
                self.save_settings()
                
                # Update hotkey binding
                self.hotkey_manager.unregister_all()
                self.hotkey_manager.register(new_hotkey)
                
                # Show confirmation
                self.showMessage(
                    "Settings Updated",
                    f"New hotkey set to: {new_hotkey}",
                    QIcon(),
                    2000
                )
        
    def show_details(self):
        """Called when user clicks 'Show Details' in notification"""
        if self.history:
            self.show_history(highlight_results=self.history[-1]["results"])
        
    def handle_notification_action(self, action):
        """Handle notification action clicks"""
        if action == "show_details" and self.history:
            self.show_history(highlight_results=self.history[-1]["results"])