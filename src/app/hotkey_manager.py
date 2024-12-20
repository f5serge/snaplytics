from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard
import threading

class HotkeyManager(QObject):
    hotkey_triggered = pyqtSignal(str)  # Signal to emit when hotkey is pressed
    
    def __init__(self):
        super().__init__()
        self.listener = None
        self.registered_hotkey = None  # Store the registered hotkey
        self.pressed_keys = set()
        self.start_listener()
        print("HotkeyManager initialized")
        
    def _normalize_key(self, key):
        """Normalize key representation"""
        try:
            # Handle special case when key is None
            if key is None:
                return None
                
            # Handle character keys
            if hasattr(key, 'char') and key.char:
                return key.char.upper()
                
            # Handle modifier keys
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                return 'CTRL'
            if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                return 'SHIFT'
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                return 'ALT'
                
            # Handle other special keys
            key_str = str(key).replace('Key.', '').upper()
            return key_str
        except:
            return None
        
    def register(self, hotkey_str, callback=None):
        """Register a hotkey combination"""
        combo = []
        for key in hotkey_str.split('+'):
            key = key.strip().upper()
            if key in ['ALT']:
                combo.append('ALT')
            elif key in ['SHIFT']:
                combo.append('SHIFT')
            else:
                combo.append(key)
        
        self.registered_hotkey = '+'.join(sorted(combo))
        print(f"Registered hotkey: {self.registered_hotkey}")
        
    def start_listener(self):
        def on_press(key):
            try:
                key_str = self._normalize_key(key)
                if not key_str:
                    return
                
                print(f"Key pressed: {key_str}")
                self.pressed_keys.add(key_str)
                print(f"Current pressed keys: {self.pressed_keys}")
                
                # Create current combination
                current = set()
                if any(k in self.pressed_keys for k in ['ALT', 'ALT_L', 'ALT_R']):
                    current.add('ALT')
                if any(k in self.pressed_keys for k in ['SHIFT', 'SHIFT_L', 'SHIFT_R']):
                    current.add('SHIFT')
                
                # Add other pressed keys
                others = {k for k in self.pressed_keys 
                         if k not in {'CTRL', 'CTRL_L', 'CTRL_R', 
                                    'SHIFT', 'SHIFT_L', 'SHIFT_R',
                                    'ALT', 'ALT_L', 'ALT_R'}}
                current.update(others)
                
                # Check if current combination matches registered hotkey
                combo = '+'.join(sorted(current))
                print(f"Current combo: {combo}")
                print(f"Looking for: {self.registered_hotkey}")
                
                if combo == self.registered_hotkey:
                    print(f"Hotkey match found! Emitting signal...")
                    self.hotkey_triggered.emit(combo)
                
            except Exception as e:
                print(f"Error in hotkey handler: {e}")
                import traceback
                traceback.print_exc()
                
        def on_release(key):
            try:
                key_str = self._normalize_key(key)
                if not key_str:
                    return
                
                print(f"Key released: {key_str}")
                self.pressed_keys.discard(key_str)
                # Also remove the L/R variants
                self.pressed_keys.discard(f"{key_str}_L")
                self.pressed_keys.discard(f"{key_str}_R")
                print(f"Remaining pressed keys: {self.pressed_keys}")
            except Exception as e:
                print(f"Error in release handler: {e}")
                import traceback
                traceback.print_exc()
        
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()
        print("Keyboard listener started")
        
    def unregister_all(self):
        if self.listener:
            self.listener.stop()
            self.listener.join()
        self.pressed_keys.clear()
        