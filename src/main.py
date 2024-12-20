import sys
from PyQt6.QtWidgets import QApplication
from app.tray_app import TrayApp

def main():
    app = QApplication(sys.argv)
    
    # Handle protocol actions
    if len(sys.argv) > 1 and sys.argv[1].startswith("snaplytics://"):
        action = sys.argv[1].split("://")[1]
        if hasattr(tray_app, "handle_notification_action"):
            tray_app.handle_notification_action(action)
    
    app.setQuitOnLastWindowClosed(False)  # Keep running when all windows are closed
    tray = TrayApp()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 