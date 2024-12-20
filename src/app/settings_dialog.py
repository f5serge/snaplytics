from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit
)
from PyQt6.QtCore import Qt
from pynput import keyboard

class HotkeyLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pressed_keys = set()
        self.current_hotkey = set()
        self.listener = None
        self.setReadOnly(True)
        
        # Initialize with current hotkey - extract just the letter
        if args and args[0]:
            keys = args[0].upper().split('+')
            letter = next((k for k in keys if k not in ['CTRL', 'ALT', 'SHIFT']), None)
            if letter:
                self.current_hotkey = {'ALT', 'SHIFT', letter}
            self.update_text()
            
        # Start the listener
        self.start_listener()
        
    def start_listener(self):
        def on_press(key):
            try:
                # Only interested in character keys
                if hasattr(key, 'char') and key.char:
                    key_str = key.char.upper()
                    # Only accept letters
                    if key_str.isalpha():
                        self.current_hotkey = {'ALT', 'SHIFT', key_str}
                        self.update_text()
            except:
                pass
                
        def on_release(key):
            pass  # No need to handle key release
        
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()
        
    def update_text(self):
        # Always show the current hotkey
        if self.current_hotkey:
            self.setText('+'.join(sorted(self.current_hotkey)))
        else:
            self.clear()
        
    def stop_listener(self):
        if self.listener:
            self.listener.stop()
            self.listener.join()

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_hotkey="Alt+Shift+S"):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(300)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Hotkey setting
        hotkey_layout = QHBoxLayout()
        hotkey_label = QLabel("Hotkey:")
        self.hotkey_input = HotkeyLineEdit(current_hotkey)
        hotkey_layout.addWidget(hotkey_label)
        hotkey_layout.addWidget(self.hotkey_input)
        
        # Instructions
        instructions = QLabel("Press any letter key.\nIt will be combined with Alt+Shift")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # Add all layouts to main layout
        layout.addLayout(hotkey_layout)
        layout.addWidget(instructions)
        layout.addLayout(button_layout)
        
    def get_hotkey(self):
        return self.hotkey_input.text()
        
    def closeEvent(self, event):
        self.hotkey_input.stop_listener()
        super().closeEvent(event)