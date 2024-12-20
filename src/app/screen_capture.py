from PyQt6.QtWidgets import QWidget, QRubberBand, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QScreen, QGuiApplication, QColor, QPainter, QBrush, QCursor

class ScreenCaptureWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.Popup  # Add Popup flag
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)  # Prevent auto-deletion
        self.rubberband = None
        self.origin = QPoint()
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.selection = QRect()
        
    def start_capture(self):
        print("ScreenCaptureWidget.start_capture called")  # Debug print
        try:
            # Get all screens
            geometry = QRect()
            for screen in QGuiApplication.screens():
                geometry = geometry.united(screen.geometry())
            
            # Show the widget covering all screens
            self.setGeometry(geometry)
            self.showFullScreen()
            self.activateWindow()
            self.raise_()
            
            # Force the window to be active and on top
            self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
            
            print(f"Screen capture widget shown at geometry: {geometry}")  # Debug print
            print(f"Widget is visible: {self.isVisible()}")  # Debug print
            print(f"Widget is active: {self.isActiveWindow()}")  # Debug print
            
        except Exception as e:
            print(f"Error in start_capture: {e}")  # Debug print
            import traceback
            traceback.print_exc()
            
    def hideEvent(self, event):
        print("ScreenCaptureWidget hidden")  # Debug print
        if self.rubberband:
            self.rubberband.hide()
        super().hideEvent(event)
        
    def showEvent(self, event):
        print("ScreenCaptureWidget shown")  # Debug print
        super().showEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw semi-transparent overlay
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))  # 40% opacity black
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Draw the darkened area
        if self.rubberband and self.rubberband.isVisible():
            selection = self.rubberband.geometry()
            # Draw the outside areas
            painter.drawRect(0, 0, self.width(), selection.top())  # Top
            painter.drawRect(0, selection.bottom(), self.width(), self.height() - selection.bottom())  # Bottom
            painter.drawRect(0, selection.top(), selection.left(), selection.height())  # Left
            painter.drawRect(selection.right(), selection.top(), self.width() - selection.right(), selection.height())  # Right
            
            # Draw selection border
            painter.setPen(Qt.GlobalColor.green)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(selection)
        else:
            painter.drawRect(0, 0, self.width(), self.height())
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            if not self.rubberband:
                self.rubberband = QRubberBand(QRubberBand.Shape.Rectangle, self)
            self.rubberband.setGeometry(QRect(self.origin, QPoint()))
            self.rubberband.show()
        
    def mouseMoveEvent(self, event):
        if self.rubberband and event.buttons() & Qt.MouseButton.LeftButton:
            self.rubberband.setGeometry(
                QRect(self.origin, event.pos()).normalized()
            )
            self.update()  # Force a repaint
            
    def mouseReleaseEvent(self, event):
        if self.rubberband and event.button() == Qt.MouseButton.LeftButton:
            geometry = self.rubberband.geometry()
            if geometry.width() > 10 and geometry.height() > 10:
                self.rubberband.hide()
                
                # Find the screen that contains the selection
                screen = None
                for s in QGuiApplication.screens():
                    if s.geometry().contains(geometry.center() + self.pos()):
                        screen = s
                        break
                        
                if screen:
                    screen_geometry = screen.geometry()
                    adjusted_geometry = QRect(
                        geometry.x() + self.pos().x() - screen_geometry.x(),
                        geometry.y() + self.pos().y() - screen_geometry.y(),
                        geometry.width(),
                        geometry.height()
                    )
                    
                    pixmap = screen.grabWindow(
                        0,
                        adjusted_geometry.x(),
                        adjusted_geometry.y(),
                        adjusted_geometry.width(),
                        adjusted_geometry.height()
                    )
                    
                    self.hide()
                    # Get the current mouse position using globalPosition()
                    mouse_pos = event.globalPosition().toPoint()
                    # Pass to parent's tray_app if available
                    if hasattr(self.parent, 'tray_app'):
                        self.parent.tray_app.process_capture(pixmap, mouse_pos)
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            if hasattr(self.parent, 'tray_app'):
                self.parent.show()
            event.accept()