import kivy
kivy.require('2.0.0')

import os
import json
import time
import subprocess
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import DictProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window

# --- Configuration and Constants ---

CONFIG_FILE = 'config.json'
DEFAULT_SETTINGS = {
    'width': 1280,
    'height': 720,
    'sharpness': 1.0,
    'contrast': 1.0,
    'brightness': 0.0,
    'saturation': 1.0,
    'ev': 0.0,
    'awb': 'auto',
    'hflip': False,
    'vflip': False,
    'rotation': 0,
}

# --- Global Variables ---
rpicam_process = None

# --- Utility Functions ---

def build_command(app_type, settings, output_file=None):
    """Builds the rpicam-hello or rpicam-still command list."""
    s = settings
    
    if app_type == 'hello':
        # Use --nopreview to prevent rpicam-hello from opening its own window
        # Use --display to control the position and size of the preview window
        command = ['rpicam-hello', '--timeout', '0']
        
        # Calculate preview window size: 1/6 of screen width
        # Assuming a standard 16:9 aspect ratio for the preview window
        screen_width = Window.width
        preview_width = int(screen_width / 6)
        preview_height = int(preview_width * 9 / 16) # 16:9 aspect ratio
        
        # Position the preview window (e.g., top-right corner of the screen)
        # Note: The exact positioning might vary based on the window manager
        command.extend(['--display', f'0,0,{preview_width},{preview_height}'])
        
    elif app_type == 'still':
        command = ['rpicam-still', '--timeout', '1000']
        if output_file:
            command.extend(['--output', output_file])
    else:
        raise ValueError("Invalid app_type")

    # Add common settings
    command.extend(['--width', str(s['width']), '--height', str(s['height'])])
    command.extend(['--sharpness', str(s['sharpness'])])
    command.extend(['--contrast', str(s['contrast'])])
    command.extend(['--brightness', str(s['brightness'])])
    command.extend(['--saturation', str(s['saturation'])])
    command.extend(['--ev', str(s['ev'])])
    command.extend(['--awb', s['awb']])
    
    if s['hflip']:
        command.append('--hflip')
    if s['vflip']:
        command.append('--vflip')
    if s['rotation'] in [0, 180]:
        command.extend(['--rotation', str(s['rotation'])])
        
    return command

# --- Main Kivy Widget ---

class CameraControlLayout(BoxLayout):
    """Main layout and logic for the camera control application."""
    
    settings = DictProperty(DEFAULT_SETTINGS)
    status_text = StringProperty("Ready")
    preview_running = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_config()
        # Bind settings changes to the preview update function
        self.bind(settings=self.on_settings_change)

    def on_settings_change(self, instance, value):
        """Called when the settings dictionary is updated."""
        if self.preview_running:
            self.start_preview() # Restart preview to apply new settings

    def load_config(self):
        """Loads settings from the JSON configuration file."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded_settings = json.load(f)
                # Merge loaded settings with defaults to ensure all keys exist
                self.settings = {**DEFAULT_SETTINGS, **loaded_settings}
                self.status_text = "Configuration loaded."
            except Exception as e:
                self.status_text = f"Error loading config: {e}"
                self.settings = DEFAULT_SETTINGS
        else:
            self.settings = DEFAULT_SETTINGS
            self.status_text = "Using default configuration."

    def save_config(self):
        """Saves current settings to the JSON configuration file."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            self.status_text = "Configuration saved successfully."
        except Exception as e:
            self.status_text = f"Error saving config: {e}"

    def stop_preview(self):
        """Stops the rpicam-hello process."""
        global rpicam_process
        if rpicam_process:
            rpicam_process.terminate()
            rpicam_process.wait()
            rpicam_process = None
            self.preview_running = False
            self.status_text = "Preview stopped."

    def start_preview(self):
        """Starts the rpicam-hello process with current settings."""
        self.stop_preview() # Stop any existing process first
        
        command = build_command('hello', self.settings)
        
        def run_rpicam():
            global rpicam_process
            try:
                self.status_text = f"Starting preview with: {' '.join(command)}"
                # Run rpicam-hello in the background
                rpicam_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.preview_running = True
                self.status_text = "Preview running."
                
                # Monitor the process (optional, but good practice)
                rpicam_process.wait()
                
                # If the process exits unexpectedly
                if rpicam_process and rpicam_process.returncode != 0:
                    stderr_output = rpicam_process.stderr.read().decode()
                    Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"rpicam-hello exited with error: {stderr_output}"), 0)
                
                rpicam_process = None
                self.preview_running = False
                Clock.schedule_once(lambda dt: setattr(self, 'status_text', "Preview stopped unexpectedly."), 0)
                
            except FileNotFoundError:
                Clock.schedule_once(lambda dt: setattr(self, 'status_text', "Error: rpicam-hello not found. Is it installed?"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"Error running rpicam-hello: {e}"), 0)

        # Run the rpicam process in a separate thread to prevent blocking the Kivy UI
        threading.Thread(target=run_rpicam).start()

    def capture_image(self):
        """Captures a still image with current settings."""
        
        # Stop preview temporarily to ensure the camera is free for rpicam-still
        was_running = self.preview_running
        if was_running:
            self.stop_preview()

        # Generate unique filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        
        command = build_command('still', self.settings, output_file=filename)
        
        def run_rpicam_still():
            try:
                self.status_text = f"Capturing image to {filename}..."
                
                # Run rpicam-still
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                
                # Update status on the main thread
                Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"Image saved to {os.path.abspath(filename)}"), 0)
                
            except subprocess.CalledProcessError as e:
                Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"Capture failed: {e.stderr}"), 0)
            except FileNotFoundError:
                Clock.schedule_once(lambda dt: setattr(self, 'status_text', "Error: rpicam-still not found. Is it installed?"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: setattr(self, 'status_text', f"Error during capture: {e}"), 0)
            finally:
                # Restart preview if it was running before capture
                if was_running:
                    Clock.schedule_once(lambda dt: self.start_preview(), 1) # Delay restart slightly

        # Run the rpicam-still process in a separate thread
        threading.Thread(target=run_rpicam_still).start()

    def on_stop(self):
        """Called when the application is closed."""
        self.stop_preview()

# --- Kivy App Class ---

class RPiCamControlApp(App):
    AWB_MODES = ['auto', 'incandescent', 'tungsten', 'fluorescent', 'indoor', 'daylight', 'cloudy']
    ROTATION_MODES = [0, 180]
    RESOLUTIONS = [
        (640, 480), (1280, 720), (1920, 1080), (2592, 1944), (3280, 2464)
    ]
    
    def build(self):
        return CameraControlLayout()

    def on_stop(self):
        # Ensure the camera process is stopped when the app exits
        if self.root:
            self.root.on_stop()

if __name__ == '__main__':
    RPiCamControlApp().run()
