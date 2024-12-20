import winreg
import os
import sys

def register_protocol_handler():
    """Register the snaplytics:// protocol handler"""
    try:
        # Get the path to the executable
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
        else:
            app_path = os.path.abspath(sys.argv[0])
            
        # Register protocol handler
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "snaplytics") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "URL:Snaplytics Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, f'"{app_path}" "%1"')
                
        print("Protocol handler registered successfully")
        return True
        
    except Exception as e:
        print(f"Error registering protocol handler: {e}")
        return False

if __name__ == "__main__":
    register_protocol_handler() 