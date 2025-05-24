import sys
import os
import subprocess
import platform
import webbrowser
import shutil
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QRadioButton, QButtonGroup,
                            QLabel, QTextEdit, QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QProcess, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap

class SyncWorker(QThread):
    """Worker thread for sync operations to prevent UI freezing"""
    progress_updated = pyqtSignal(int, int)
    log_message = pyqtSignal(str)
    sync_finished = pyqtSignal(bool)
    
    def __init__(self, sync_function, *args):
        super().__init__()
        self.sync_function = sync_function
        self.args = args
    
    def run(self):
        try:
            result = self.sync_function(*self.args)
            self.sync_finished.emit(result)
        except Exception as e:
            self.log_message.emit(f"Error in sync operation: {str(e)}")
            self.sync_finished.emit(False)

class GDSync(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("gdsync v3.0 by MalikHw47")
        self.setFixedSize(600, 450)
        self.process = None
        self.adb_path = ""
        self.sync_worker = None
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
    
    def detect_linux_distro(self):
        """Detect Linux distribution"""
        try:
            # Try to read /etc/os-release
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    content = f.read().lower()
                    if "ubuntu" in content or "debian" in content:
                        return "apt"
                    elif "fedora" in content or "rhel" in content or "centos" in content:
                        return "dnf"
                    elif "arch" in content or "manjaro" in content:
                        return "pacman"
            
            # Fallback checks
            if os.path.exists("/usr/bin/apt"):
                return "apt"
            elif os.path.exists("/usr/bin/dnf"):
                return "dnf"
            elif os.path.exists("/usr/bin/pacman"):
                return "pacman"
            elif os.path.exists("/usr/bin/yum"):
                return "yum"
        except Exception as e:
            self.log(f"Error detecting Linux distro: {str(e)}")
        
        return None
    
    def install_adb_linux(self):
        """Install ADB on Linux based on detected distribution"""
        distro = self.detect_linux_distro()
        
        if not distro:
            self.log("Could not detect Linux distribution. Please install ADB manually.")
            return False
        
        commands = {
            "apt": ["sudo", "apt", "update", "&&", "sudo", "apt", "install", "-y", "android-tools-adb"],
            "dnf": ["sudo", "dnf", "install", "-y", "android-tools"],
            "pacman": ["sudo", "pacman", "-S", "--noconfirm", "android-tools"],
            "yum": ["sudo", "yum", "install", "-y", "android-tools"]
        }
        
        if distro in commands:
            self.log(f"Detected {distro}-based system. Installing ADB...")
            try:
                # Use shell=True for commands with &&
                if distro == "apt":
                    subprocess.run("sudo apt update && sudo apt install -y android-tools-adb", 
                                 shell=True, check=True)
                else:
                    subprocess.run(commands[distro], check=True)
                
                self.log("ADB installation completed successfully!")
                # Re-detect ADB after installation
                self.detect_adb()
                return True
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install ADB: {str(e)}")
                return False
        else:
            self.log(f"Unsupported package manager: {distro}")
            return False
    
    def detect_adb(self):
        """Attempt to detect ADB on the system"""
        # First, try bundled ADB (for Windows PyInstaller builds)
        bundled_adb_path = os.path.join(self.get_resource_path(), "adb", "adb.exe" if platform.system() == "Windows" else "adb")
        if os.path.exists(bundled_adb_path):
            self.adb_path = bundled_adb_path
            self.log(f"Using bundled ADB: {self.adb_path}")
            return
        
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
                self.log(f"ADB found in PATH: {self.adb_path}")
            else:
                self.log("ADB not found in PATH.")
                if platform.system() == "Linux":
                    reply = QMessageBox.question(
                        self, 
                        "ADB Not Found", 
                        "ADB is not installed. Would you like to install it automatically?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        self.install_adb_linux()
                else:
                    self.log("On Windows, ADB should be bundled with the application.")
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
    
    def should_exclude_path(self, file_path):
        """Check if a file/folder should be excluded from sync"""
        excluded_patterns = [
            "geode/mods/tobyadd.gdh/Macros",
            "/geode/mods/tobyadd.gdh/Macros/",
            "\\geode\\mods\\tobyadd.gdh\\Macros\\",
            "geode\\mods\\tobyadd.gdh\\Macros"
        ]
        
        for pattern in excluded_patterns:
            if pattern in file_path:
                return True
        return False
    
    def get_files_to_sync(self, directory):
        """Get list of files to sync, excluding directories and unwanted paths"""
        files_to_sync = []
        
        if not os.path.exists(directory):
            return files_to_sync
        
        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            if self.should_exclude_path(root):
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                
                # Skip excluded files
                if not self.should_exclude_path(file_path):
                    files_to_sync.append((file_path, relative_path))
        
        return files_to_sync
    
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
            if self.sync_worker:
                self.sync_worker.progress_updated.emit(i, len(files))
            if not self.run_adb_command(["pull", f"{android_path}/{file}", pc_path]):
                success = False
        
        if self.sync_worker:
            self.sync_worker.progress_updated.emit(len(files), len(files))
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
            if self.sync_worker:
                self.sync_worker.progress_updated.emit(i, len(files))
            file_path = os.path.join(pc_path, file)
            if os.path.exists(file_path):
                if not self.run_adb_command(["push", file_path, android_path]):
                    success = False
            else:
                self.log(f"Warning: File not found: {file_path}")
                success = False
        
        if self.sync_worker:
            self.sync_worker.progress_updated.emit(len(files), len(files))
        return success
    
    def sync_phone_to_pc_all(self, pc_path, android_path):
        """Sync all data including songs and SFX from phone to PC"""
        self.log("Syncing all data from phone to PC...")
        
        # Get list of files (excluding directories)
        result = subprocess.run(
            [self.adb_path, "shell", f"find {android_path} -type f"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self.log(f"Error getting file list: {result.stderr}")
            return False
        
        all_files = result.stdout.strip().split('\n')
        # Filter out excluded paths
        files = [f for f in all_files if f.strip() and not self.should_exclude_path(f)]
        success = True
        
        self.log(f"Found {len(files)} files to sync")
        for i, file in enumerate(files):
            if self.sync_worker:
                self.sync_worker.progress_updated.emit(i, len(files))
            file = file.strip()
            if file:
                # Create relative path for local storage
                rel_path = file.replace(android_path, "").lstrip("/")
                local_dir = os.path.join(pc_path, os.path.dirname(rel_path))
                os.makedirs(local_dir, exist_ok=True)
                
                if not self.run_adb_command(["pull", file, os.path.join(pc_path, rel_path)]):
                    success = False
        
        if self.sync_worker:
            self.sync_worker.progress_updated.emit(len(files), len(files))
        return success
    
    def sync_pc_to_phone_all(self, pc_path, android_path):
        """Sync all data including songs and SFX from PC to phone"""
        self.log("Syncing all data from PC to phone...")
        
        if not os.path.exists(pc_path):
            self.log(f"Error: PC path does not exist: {pc_path}")
            return False
        
        # Get files to sync (excluding unwanted directories and files)
        files_to_sync = self.get_files_to_sync(pc_path)
        
        if not files_to_sync:
            self.log("No files found to sync")
            return False
        
        self.log(f"Found {len(files_to_sync)} files to sync")
        success = True
        
        for i, (file_path, relative_path) in enumerate(files_to_sync):
            if self.sync_worker:
                self.sync_worker.progress_updated.emit(i, len(files_to_sync))
            
            # Create remote directory structure
            remote_dir = os.path.dirname(os.path.join(android_path, relative_path).replace("\\", "/"))
            if remote_dir != android_path:
                self.run_adb_command(["shell", f"mkdir -p '{remote_dir}'"])
            
            # Push the file
            remote_file_path = os.path.join(android_path, relative_path).replace("\\", "/")
            if not self.run_adb_command(["push", file_path, remote_file_path]):
                success = False
        
        if self.sync_worker:
            self.sync_worker.progress_updated.emit(len(files_to_sync), len(files_to_sync))
        return success
    
    def on_sync_progress(self, current, total):
        """Handle progress updates from worker thread"""
        self.update_progress(current, total)
    
    def on_sync_log(self, message):
        """Handle log messages from worker thread"""
        self.log(message)
    
    def on_sync_finished(self, success):
        """Handle sync completion"""
        self.sync_btn.setEnabled(True)
        self.sync_worker = None
        
        if success:
            self.log("Sync completed successfully!")
            QMessageBox.information(self, "Success", "Geometry Dash data sync completed successfully!")
        else:
            self.log("Sync completed with errors. Check the logs for details.")
            QMessageBox.warning(self, "Warning", "Sync completed with errors. Check the logs for details.")
    
    def start_sync(self):
        """Start the sync process based on selected options"""
        if not self.adb_path:
            QMessageBox.critical(self, "Error", "ADB path not set. Please configure in Settings.")
            return
        
        if self.sync_worker and self.sync_worker.isRunning():
            QMessageBox.information(self, "Sync in Progress", "A sync operation is already running. Please wait for it to complete.")
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
        
        # Disable sync button during operation
        self.sync_btn.setEnabled(False)
        
        # Determine which sync operation to perform and start worker thread
        if self.phone_to_pc.isChecked():
            if self.only_userdata.isChecked():
                sync_func = self.sync_phone_to_pc_userdata
            else:
                sync_func = self.sync_phone_to_pc_all
        else:  # PC to Phone
            if self.only_userdata.isChecked():
                sync_func = self.sync_pc_to_phone_userdata
            else:
                sync_func = self.sync_pc_to_phone_all
        
        # Create and start worker thread
        self.sync_worker = SyncWorker(sync_func, pc_path, android_path)
        self.sync_worker.progress_updated.connect(self.on_sync_progress)
        self.sync_worker.log_message.connect(self.on_sync_log)
        self.sync_worker.sync_finished.connect(self.on_sync_finished)
        self.sync_worker.start()

def main():
    app = QApplication(sys.argv)
    window = GDSync()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
