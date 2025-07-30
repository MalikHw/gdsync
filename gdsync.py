import sys
import os
import subprocess
import platform
import webbrowser
import shutil
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QRadioButton, QButtonGroup,
                            QLabel, QTextEdit, QFileDialog, QMessageBox, QProgressBar,
                            QDialog, QDialogButtonBox, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, QProcess, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QFont

class InstallationSetupDialog(QDialog):
    """Dialog for setting up GD installation path"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Geometry Dash Installation Setup")
        self.setFixedSize(500, 300)
        self.selected_path = ""
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Select your Geometry Dash installation type:")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Installation type selection
        self.installation_combo = QComboBox()
        self.installation_combo.addItems([
            "Wine (Default)",
            "Steam with Proton",
            "Manual/Custom Path"
        ])
        self.installation_combo.currentTextChanged.connect(self.on_installation_changed)
        layout.addWidget(self.installation_combo)
        
        # Path display and browse
        path_layout = QHBoxLayout()
        self.path_label = QLabel("Path:")
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_path)
        self.browse_btn.setEnabled(False)  # Initially disabled
        
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)
        
        # Info text
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        layout.addWidget(self.info_text)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Initialize with default selection
        self.on_installation_changed("Wine (Default)")
    
    def on_installation_changed(self, installation_type):
        """Handle installation type change"""
        home_dir = os.path.expanduser("~")
        username = os.environ.get("USER", "user")
        
        if installation_type == "Wine (Default)":
            self.selected_path = os.path.join(home_dir, ".wine", "drive_c", "users", username, "AppData", "Local", "GeometryDash")
            self.browse_btn.setEnabled(False)
            self.info_text.setText(
                "Default Wine installation path.\n"
                "This is used when GD is installed through Wine directly.\n"
                f"Path: {self.selected_path}"
            )
        elif installation_type == "Steam with Proton":
            self.selected_path = os.path.join(home_dir, ".local", "share", "Steam", "steamapps", "compatdata", "322170", "pfx", "drive_c", "users", "steamuser", "AppData", "Local", "GeometryDash")
            self.browse_btn.setEnabled(False)
            self.info_text.setText(
                "Steam with Proton installation path.\n"
                "This is used when GD is installed through Steam on Linux.\n"
                f"Path: {self.selected_path}\n\n"
                "Note: Steam App ID 322170 is for Geometry Dash"
            )
        else:  # Manual/Custom Path
            self.selected_path = ""
            self.browse_btn.setEnabled(True)
            self.info_text.setText(
                "Custom installation path.\n"
                "Use this if you have a custom Wine prefix or different installation.\n"
                "Click 'Browse...' to select your GeometryDash folder containing the .dat files."
            )
        
        self.path_edit.setText(self.selected_path)
    
    def browse_path(self):
        """Browse for custom path"""
        path = QFileDialog.getExistingDirectory(
            self, 
            "Select Geometry Dash Data Folder",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        if path:
            self.selected_path = path
            self.path_edit.setText(path)
    
    def get_selected_path(self):
        """Get the selected installation path"""
        return self.selected_path

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
        self.setWindowTitle("gdsync v4.0.0 by MalikHw47")
        self.setFixedSize(600, 500)
        self.process = None
        self.adb_path = ""
        self.gd_pc_path = ""
        self.sync_worker = None
        self.init_ui()
        self.detect_adb()
        self.setup_gd_installation()
        self.log("GDSync initialized. Ready for operation.")
        
    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Title section (replacing banner)
        title_layout = QVBoxLayout()
        self.title_label = QLabel("GDSync v4.0.0 by MalikHw47")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Style the title
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 10px;
            }
        """)
        
        title_layout.addWidget(self.title_label)
        main_layout.addLayout(title_layout)
        
        # Installation info section
        install_layout = QVBoxLayout()
        self.install_label = QLabel("GD Installation: Not configured")
        self.install_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        self.setup_btn = QPushButton("Setup GD Installation")
        self.setup_btn.clicked.connect(self.setup_gd_installation)
        
        install_layout.addWidget(self.install_label)
        install_layout.addWidget(self.setup_btn)
        main_layout.addLayout(install_layout)
        
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
        self.only_userdata = QRadioButton("Only userdata")
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
        
        self.sync_btn = QPushButton("Sync")
        self.sync_btn.setFixedSize(120, 40)
        self.sync_btn.clicked.connect(self.start_sync)
        
        right_buttons.addWidget(self.donate_btn)
        right_buttons.addStretch()
        right_buttons.addWidget(self.sync_btn)
        
        button_layout.addLayout(right_buttons)
        main_layout.addLayout(button_layout)
        
        self.setCentralWidget(central_widget)
    
    def setup_gd_installation(self):
        """Setup Geometry Dash installation path"""
        dialog = InstallationSetupDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            path = dialog.get_selected_path()
            if path and self.validate_gd_installation(path):
                self.gd_pc_path = path
                self.install_label.setText(f"GD Installation: {path}")
                self.log(f"GD installation path set to: {path}")
            elif path:
                self.log(f"Invalid GD installation path: {path}")
    
    def validate_gd_installation(self, path):
        """Validate GD installation and check for required files"""
        if not os.path.exists(path):
            self.log(f"Path does not exist: {path}")
            QMessageBox.critical(
                self,
                "Invalid Path",
                f"The selected path does not exist:\n{path}"
            )
            return False
        
        # Check for CCGameManager.dat file
        ccgamemanager_path = os.path.join(path, "CCGameManager.dat")
        
        if not os.path.exists(ccgamemanager_path):
            reply = QMessageBox.question(
                self,
                "GD Data Files Not Found",
                f"CCGameManager.dat was not found in:\n{path}\n\n"
                "This usually means Geometry Dash hasn't been run yet, or the path is incorrect.\n\n"
                "Would you like to:\n"
                "• Continue anyway (files will be created during sync)\n"
                "• Cancel and run GD first\n\n"
                "Note: It's recommended to run GD at least once to create the initial data files.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                QMessageBox.information(
                    self,
                    "Run Geometry Dash First",
                    "Please run Geometry Dash at least once and close it normally.\n"
                    "This will create the necessary data files for syncing.\n\n"
                    "After running GD, come back and setup the installation path again."
                )
                return False
            else:
                self.log("Warning: CCGameManager.dat not found. Continuing anyway...")
                return True
        else:
            self.log("CCGameManager.dat found. Installation path validated.")
            return True
    
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
        """Detect Linux distribution and return package manager"""
        try:
            # Try to read /etc/os-release
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release", "r") as f:
                    content = f.read().lower()
                    if "ubuntu" in content or "debian" in content or "mint" in content:
                        return "apt"
                    elif "fedora" in content or "rhel" in content or "centos" in content:
                        return "dnf"
                    elif "arch" in content or "manjaro" in content or "endeavouros" in content:
                        return "pacman"
                    elif "opensuse" in content or "suse" in content:
                        return "zypper"
            
            # Fallback checks for package managers
            if os.path.exists("/usr/bin/apt") or os.path.exists("/usr/bin/apt-get"):
                return "apt"
            elif os.path.exists("/usr/bin/dnf"):
                return "dnf"
            elif os.path.exists("/usr/bin/pacman"):
                return "pacman"
            elif os.path.exists("/usr/bin/zypper"):
                return "zypper"
            elif os.path.exists("/usr/bin/yum"):
                return "yum"
        except Exception as e:
            self.log(f"Error detecting Linux distro: {str(e)}")
        
        return None
    
    def show_windows_adb_tutorial(self):
        """Show ADB installation tutorial for Windows"""
        tutorial_text = """
ADB Installation Tutorial for Windows:

1. Download Android SDK Platform Tools:
   - Go to: https://developer.android.com/studio/releases/platform-tools
   - Download "SDK Platform-Tools for Windows"

2. Extract the downloaded ZIP file to a folder (e.g., C:\\platform-tools)

3. Add ADB to System Environment Variables:
   - Right-click "This PC" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System Variables", find and select "Path"
   - Click "Edit" → "New"
   - Add the path where you extracted platform-tools (e.g., C:\\platform-tools)
   - Click OK on all windows

4. Restart this application after installation

5. Enable USB Debugging on your Android device:
   - Go to Settings → About Phone
   - Tap "Build Number" 7 times to enable Developer Options
   - Go to Settings → Developer Options
   - Enable "USB Debugging"
        """
        
        QMessageBox.information(self, "ADB Installation Tutorial", tutorial_text)

    def install_adb_linux(self):
        """Install ADB on Linux based on detected distribution"""
        distro = self.detect_linux_distro()
        
        if not distro:
            self.log("Could not detect Linux distribution. Please install ADB manually.")
            QMessageBox.information(
                self,
                "Manual Installation Required",
                "Could not detect your Linux distribution.\n\n"
                "Please install ADB manually using your distribution's package manager:\n"
                "- Most distributions have 'android-tools-adb' or 'android-tools' package\n"
                "- After installation, restart this application"
            )
            return False
        
        commands = {
            "apt": "sudo apt update && sudo apt install -y android-tools-adb",
            "dnf": "sudo dnf install -y android-tools",
            "pacman": "sudo pacman -S --noconfirm android-tools",
            "zypper": "sudo zypper install -y android-tools",  # OpenSUSE
            "yum": "sudo yum install -y android-tools"
        }
        
        if distro in commands:
            distro_names = {
                "apt": "Ubuntu/Debian",
                "dnf": "Fedora",
                "pacman": "Arch Linux",
                "zypper": "OpenSUSE",
                "yum": "CentOS/RHEL"
            }
            
            self.log(f"Detected {distro_names.get(distro, distro)}-based system. Installing ADB...")
            try:
                subprocess.run(commands[distro], shell=True, check=True)
                
                self.log("ADB installation completed successfully!")
                QMessageBox.information(
                    self,
                    "Installation Complete",
                    "ADB has been installed successfully!\n\n"
                    "Please restart this application to use ADB functionality."
                )
                # Re-detect ADB after installation
                self.detect_adb()
                return True
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install ADB: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Installation Failed",
                    f"Failed to install ADB automatically.\n\n"
                    f"Error: {str(e)}\n\n"
                    "Please install ADB manually using:\n"
                    f"{commands[distro]}"
                )
                return False
        else:
            self.log(f"Unsupported package manager: {distro}")
            QMessageBox.information(
                self,
                "Manual Installation Required",
                f"Detected package manager: {distro}\n\n"
                "Please install ADB manually using your distribution's package manager.\n"
                "After installation, restart this application."
            )
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
                return
            
            # ADB not found, show installation options
            self.log("ADB not found on system.")
            self.show_adb_installation_dialog()
                    
        except Exception as e:
            self.log(f"Error detecting ADB: {str(e)}")
            self.show_adb_installation_dialog()
    
    def show_adb_installation_dialog(self):
        """Show ADB installation dialog based on OS"""
        if platform.system() == "Windows":
            reply = QMessageBox.question(
                self,
                "ADB Not Found",
                "ADB is not installed or not in system PATH.\n\n"
                "Would you like to see the installation tutorial?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.show_windows_adb_tutorial()
        else:  # Linux
            reply = QMessageBox.question(
                self,
                "ADB Not Found",
                "ADB is not installed on your system.\n\n"
                "Would you like to install it automatically?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.install_adb_linux()
    
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
        """Get paths for Geometry Dash data"""
        # Android path is always the same
        gd_android_path = "/storage/emulated/0/Android/media/com.geode.launcher/save"
        
        # Use the configured PC path
        return self.gd_pc_path, gd_android_path
    
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
        
        # Only get files from the root directory, exclude subfolders
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path) and not self.should_exclude_path(item_path):
                    files_to_sync.append((item_path, item))
        except Exception as e:
            self.log(f"Error reading directory {directory}: {str(e)}")
        
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
            "CCGameManager2.dat",
            "sfxlibrary.dat",
            "musiclibrary.dat"
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
            "CCGameManager2.dat",
            "sfxlibrary.dat",
            "musiclibrary.dat"
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
        """Sync all data from phone to PC, file by file"""
        self.log("Syncing all data from phone to PC...")
        
        # Get list of files only from the root directory (no subdirectories)
        result = subprocess.run(
            [self.adb_path, "shell", f"find {android_path} -maxdepth 1 -type f"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self.log(f"Error getting file list: {result.stderr}")
            return False
        
        all_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        # Filter out excluded paths
        files = [f for f in all_files if not self.should_exclude_path(f)]
        success = True
        
        self.log(f"Found {len(files)} files to sync from root directory")
        for i, file_path in enumerate(files):
            if self.sync_worker:
                self.sync_worker.progress_updated.emit(i, len(files))
            
            # Get just the filename for local storage
            filename = os.path.basename(file_path)
            local_file_path = os.path.join(pc_path, filename)
            
            self.log(f"Pulling file {i+1}/{len(files)}: {filename}")
            if not self.run_adb_command(["pull", file_path, local_file_path]):
                success = False
        
        if self.sync_worker:
            self.sync_worker.progress_updated.emit(len(files), len(files))
        return success
    
    def sync_pc_to_phone_all(self, pc_path, android_path):
        """Sync all data from PC to phone, file by file"""
        self.log("Syncing all data from PC to phone...")
        
        if not os.path.exists(pc_path):
            self.log(f"Error: PC path does not exist: {pc_path}")
            return False
        
        # Get files to sync (only from root directory, excluding subfolders)
        files_to_sync = self.get_files_to_sync(pc_path)
        
        if not files_to_sync:
            self.log("No files found to sync")
            return False
        
        self.log(f"Found {len(files_to_sync)} files to sync from root directory")
        success = True
        
        for i, (file_path, filename) in enumerate(files_to_sync):
            if self.sync_worker:
                self.sync_worker.progress_updated.emit(i, len(files_to_sync))
            
            # Push the file directly to the android path
            remote_file_path = f"{android_path}/{filename}"
            self.log(f"Pushing file {i+1}/{len(files_to_sync)}: {filename}")
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
            QMessageBox.critical(self, "Error", "ADB path not set. Please install ADB first.")
            return
        
        if not self.gd_pc_path:
            QMessageBox.critical(self, "Error", "GD installation path not set. Please setup GD installation first.")
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
