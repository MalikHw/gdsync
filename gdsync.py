import sys
import os
import subprocess
import platform
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QRadioButton, QButtonGroup,
                            QLabel, QTextEdit, QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QIcon, QPixmap

class GDSync(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("gdsync v3.0 by MalikHw47")
        self.setFixedSize(600, 450)
        self.process = None
        self.adb_path = ""
        self.init_ui()
        self.detect_adb()
        self.log("GDSync initialized. Ready for operation.")
        
    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Banner section
        banner_layout = QVBoxLayout()
        self.banner_label = QLabel()
        
        # Try to load banner image
        banner_path = os.path.join(self.get_resource_path(), "resources", "banner.png")
        if os.path.exists(banner_path):
            pixmap = QPixmap(banner_path)
            self.banner_label.setPixmap(pixmap.scaledToWidth(580))
            self.banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.banner_label.setText("Banner Image Not Found")
            self.banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.banner_label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        
        banner_layout.addWidget(self.banner_label)
        main_layout.addLayout(banner_layout)
        
        # Logs section
        logs_layout = QVBoxLayout()
        logs_label = QLabel("Logs:")
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        
        logs_layout.addWidget(logs_label)
        logs_layout.addWidget(self.logs_text)
        main_layout.addLayout(logs_layout)
        
        # Progress bar
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_layout)
        
        # Direction options
        direction_layout = QHBoxLayout()
        self.phone_to_pc = QRadioButton("Phone to PC")
        self.pc_to_phone = QRadioButton("PC to Phone")
        self.pc_to_phone.setChecked(True)
        
        direction_group = QButtonGroup(self)
        direction_group.addButton(self.phone_to_pc)
        direction_group.addButton(self.pc_to_phone)
        
        direction_layout.addWidget(self.phone_to_pc)
        direction_layout.addWidget(self.pc_to_phone)
        direction_layout.addStretch()
        main_layout.addLayout(direction_layout)
        
        # Data options
        data_layout = QHBoxLayout()
        self.only_userdata = QRadioButton("Only userdat")
        self.all_data = QRadioButton("All data with Songs and SFX")
        self.only_userdata.setChecked(True)
        
        data_group = QButtonGroup(self)
        data_group.addButton(self.only_userdata)
        data_group.addButton(self.all_data)
        
        data_layout.addWidget(self.only_userdata)
        data_layout.addWidget(self.all_data)
        data_layout.addStretch()
        main_layout.addLayout(data_layout)
        
        # Buttons row
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Right column buttons
        right_buttons = QVBoxLayout()
        
        self.donate_btn = QPushButton("Donate")
        self.donate_btn.setFixedSize(120, 40)
        self.donate_btn.clicked.connect(self.open_donate)
        
        self.sync_btn = QPushButton("sync")
        self.sync_btn.setFixedSize(120, 40)
        self.sync_btn.clicked.connect(self.start_sync)
        
        right_buttons.addWidget(self.donate_btn)
        right_buttons.addStretch()
        right_buttons.addWidget(self.sync_btn)
        
        button_layout.addLayout(right_buttons)
        main_layout.addLayout(button_layout)
        
        self.setCentralWidget(central_widget)
    
    def get_resource_path(self):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return base_path
    
    def log(self, message):
        """Add message to the logs panel"""
        self.logs_text.append(message)
    
    def update_progress(self, value, max_value=100):
        """Update progress bar"""
        percentage = int((value / max_value) * 100)
        self.progress_bar.setValue(percentage)
        QApplication.processEvents()  # Process UI events to update progress bar immediately
    
    def detect_adb(self):
        """Attempt to detect ADB on the system"""
        # Try to find ADB in PATH
        try:
            if platform.system() == "Windows":
                process = subprocess.run(["where", "adb"], capture_output=True, text=True)
                if process.returncode == 0:
                    self.adb_path = process.stdout.strip().split("\n")[0]
            else:  # Linux/Unix
                process = subprocess.run(["which", "adb"], capture_output=True, text=True)
                if process.returncode == 0:
                    self.adb_path = process.stdout.strip()
            
            if self.adb_path:
                self.log(f"ADB path: {self.adb_path}")
            else:
                self.log("ADB not found in PATH. Please set ADB path in Settings.")
        except Exception as e:
            self.log(f"Error detecting ADB: {str(e)}")
    
    def open_donate(self):
        """Open donation page in web browser"""
        ko_fi_url = "https://ko-fi.com/MalikHw47"
        try:
            webbrowser.open(ko_fi_url)
            self.log(f"Opening donation page: {ko_fi_url}")
        except Exception as e:
            self.log(f"Error opening donation page: {str(e)}")
            QMessageBox.information(
                self,
                "Donate",
                f"Please visit {ko_fi_url} to support the development of this tool."
            )
    
    def get_geometry_dash_paths(self):
        """Get platform-specific paths for Geometry Dash data"""
        system = platform.system()
        home_dir = os.path.expanduser("~")
        
        if system == "Windows":
            # Windows path
            gd_pc_path = os.path.join("C:", "users", os.environ.get("USER", ""), "AppData", "Local", "GeometryDash")
        else:
            # Linux path (assuming using Wine)
            gd_pc_path = os.path.join(home_dir, ".wine", "drive_c", "users", os.environ.get("USER", ""), "AppData", "Local", "GeometryDash")
        
        # Android path is the same in both OS
        gd_android_path = "/storage/emulated/0/Android/media/com.geode.launcher/save"
        
        return gd_pc_path, gd_android_path
    
    def run_adb_command(self, command):
        """Run an ADB command and log the output"""
        if not self.adb_path:
            self.log("Error: ADB path not set. Please configure in Settings.")
            return False
        
        try:
            full_command = [self.adb_path] + command
            self.log(f"Running: {' '.join(full_command)}")
            
            process = subprocess.run(
                full_command, 
                capture_output=True,
                text=True
            )
            
            if process.stdout:
                self.log(process.stdout)
            
            if process.returncode != 0:
                if process.stderr:
                    self.log(f"Error: {process.stderr}")
                return False
            
            return True
        except Exception as e:
            self.log(f"Error executing command: {str(e)}")
            return False
    
    def sync_phone_to_pc_userdata(self, pc_path, android_path):
        """Sync only user data from phone to PC"""
        self.log("Syncing user data from phone to PC...")
        
        files = [
            "CCLocalLevels.dat", 
            "CCLocalLevels2.dat", 
            "CCGameManager.dat",
            "CCGameManager2.dat"
        ]
        
        success = True
        for i, file in enumerate(files):
            self.update_progress(i, len(files))
            if not self.run_adb_command(["pull", f"{android_path}/{file}", pc_path]):
                success = False
        
        self.update_progress(len(files), len(files))
        return success
    
    def sync_pc_to_phone_userdata(self, pc_path, android_path):
        """Sync only user data from PC to phone"""
        self.log("Syncing user data from PC to phone...")
        
        files = [
            "CCLocalLevels.dat", 
            "CCLocalLevels2.dat", 
            "CCGameManager.dat",
            "CCGameManager2.dat"
        ]
        
        success = True
        for i, file in enumerate(files):
            self.update_progress(i, len(files))
            file_path = os.path.join(pc_path, file)
            if os.path.exists(file_path):
                if not self.run_adb_command(["push", file_path, android_path]):
                    success = False
            else:
                self.log(f"Warning: File not found: {file_path}")
                success = False
        
        self.update_progress(len(files), len(files))
        return success
    
    def sync_phone_to_pc_all(self, pc_path, android_path):
        """Sync all data including songs and SFX from phone to PC"""
        self.log("Syncing all data from phone to PC...")
        
        # Get list of files (excluding directories)
        result = subprocess.run(
            [self.adb_path, "shell", f"ls -p {android_path} | grep -v /"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self.log(f"Error getting file list: {result.stderr}")
            return False
        
        files = result.stdout.strip().split('\n')
        success = True
        
        self.log(f"Found {len(files)} files to sync")
        for i, file in enumerate(files):
            self.update_progress(i, len(files))
            file = file.strip()
            if file:
                if not self.run_adb_command(["pull", f"{android_path}/{file}", pc_path]):
                    success = False
        
        self.update_progress(len(files), len(files))
        return success
    
    def sync_pc_to_phone_all(self, pc_path, android_path):
        """Sync all data including songs and SFX from PC to phone"""
        self.log("Syncing all data from PC to phone...")
        
        if not os.path.exists(pc_path):
            self.log(f"Error: PC path does not exist: {pc_path}")
            return False
        
        self.update_progress(0, 2)
        # Push all files in the directory
        result = self.run_adb_command(["push", f"{pc_path}/.", android_path])
        self.update_progress(2, 2)
        return result
    
    def start_sync(self):
        """Start the sync process based on selected options"""
        if not self.adb_path:
            QMessageBox.critical(self, "Error", "ADB path not set. Please configure in Settings.")
            return
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        # Check ADB device connection
        self.log("Checking device connection...")
        if not self.run_adb_command(["devices"]):
            QMessageBox.critical(self, "Error", "Failed to connect to ADB device. Make sure your device is connected and USB debugging is enabled.")
            return
        
        pc_path, android_path = self.get_geometry_dash_paths()
        
        # Make sure PC path exists
        if not os.path.exists(pc_path):
            os.makedirs(pc_path, exist_ok=True)
            self.log(f"Created PC directory: {pc_path}")
        
        success = False
        
        # Determine which sync operation to perform
        if self.phone_to_pc.isChecked():
            if self.only_userdata.isChecked():
                success = self.sync_phone_to_pc_userdata(pc_path, android_path)
            else:
                success = self.sync_phone_to_pc_all(pc_path, android_path)
        else:  # PC to Phone
            if self.only_userdata.isChecked():
                success = self.sync_pc_to_phone_userdata(pc_path, android_path)
            else:
                success = self.sync_pc_to_phone_all(pc_path, android_path)
        
        if success:
            self.log("Sync completed successfully!")
            QMessageBox.information(self, "Success", "Geometry Dash data sync completed successfully!")
        else:
            self.log("Sync completed with errors. Check the logs for details.")
            QMessageBox.warning(self, "Warning", "Sync completed with errors. Check the logs for details.")

def main():
    app = QApplication(sys.argv)
    window = GDSync()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

