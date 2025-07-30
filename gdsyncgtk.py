import sys
import os
import subprocess
import platform
import webbrowser
import shutil
import threading
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, GObject, Gio, Adw, GLib
from threading import Thread
import time

class InstallationSetupDialog(Gtk.Window):
    """Dialog for setting up GD installation path"""
    
    def __init__(self, parent=None):
        super().__init__()
        self.set_title("Geometry Dash Installation Setup")
        self.set_default_size(500, 400)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.selected_path = ""
        self.response_callback = None
        self.init_ui()
        
    def init_ui(self):
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Title
        title_label = Gtk.Label(label="Select your Geometry Dash installation type:")
        title_label.add_css_class("title-2")
        main_box.append(title_label)
        
        # Installation type dropdown
        self.installation_combo = Gtk.ComboBoxText()
        self.installation_combo.append_text("Wine (Default)")
        self.installation_combo.append_text("Steam with Proton")
        self.installation_combo.append_text("Manual/Custom Path")
        self.installation_combo.set_active(0)
        self.installation_combo.connect("changed", self.on_installation_changed)
        main_box.append(self.installation_combo)
        
        # Path section
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        path_label = Gtk.Label(label="Path:")
        path_label.set_size_request(50, -1)
        self.path_entry = Gtk.Entry()
        self.path_entry.set_editable(False)
        self.browse_btn = Gtk.Button(label="Browse...")
        self.browse_btn.connect("clicked", self.browse_path)
        self.browse_btn.set_sensitive(False)
        
        path_box.append(path_label)
        path_box.append(self.path_entry)
        path_box.append(self.browse_btn)
        main_box.append(path_box)
        
        # Info text
        self.info_text = Gtk.TextView()
        self.info_text.set_editable(False)
        self.info_text.set_size_request(-1, 150)
        self.info_text.set_wrap_mode(Gtk.WrapMode.WORD)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(self.info_text)
        main_box.append(scrolled)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", self.on_cancel)
        ok_btn = Gtk.Button(label="OK")
        ok_btn.add_css_class("suggested-action")
        ok_btn.connect("clicked", self.on_ok)
        
        button_box.append(cancel_btn)
        button_box.append(ok_btn)
        main_box.append(button_box)
        
        self.set_child(main_box)
        
        # Initialize with default selection
        self.on_installation_changed(self.installation_combo)
    
    def on_installation_changed(self, combo):
        """Handle installation type change"""
        home_dir = os.path.expanduser("~")
        username = os.environ.get("USER", "user")
        selection = combo.get_active_text()
        
        if selection == "Wine (Default)":
            self.selected_path = os.path.join(home_dir, ".wine", "drive_c", "users", username, "AppData", "Local", "GeometryDash")
            self.browse_btn.set_sensitive(False)
            info_text = (
                "Default Wine installation path.\n"
                "This is used when GD is installed through Wine directly.\n"
                f"Path: {self.selected_path}"
            )
        elif selection == "Steam with Proton":
            self.selected_path = os.path.join(home_dir, ".local", "share", "Steam", "steamapps", "compatdata", "322170", "pfx", "drive_c", "users", "steamuser", "AppData", "Local", "GeometryDash")
            self.browse_btn.set_sensitive(False)
            info_text = (
                "Steam with Proton installation path.\n"
                "This is used when GD is installed through Steam on Linux.\n"
                f"Path: {self.selected_path}\n\n"
                "Note: Steam App ID 322170 is for Geometry Dash"
            )
        else:  # Manual/Custom Path
            self.selected_path = ""
            self.browse_btn.set_sensitive(True)
            info_text = (
                "Custom installation path.\n"
                "Use this if you have a custom Wine prefix or different installation.\n"
                "Click 'Browse...' to select your GeometryDash folder containing the .dat files."
            )
        
        self.path_entry.set_text(self.selected_path)
        buffer = self.info_text.get_buffer()
        buffer.set_text(info_text)
    
    def browse_path(self, button):
        """Browse for custom path"""
        dialog = Gtk.FileChooserDialog(
            title="Select Geometry Dash Data Folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Select", Gtk.ResponseType.ACCEPT
        )
        
        dialog.connect("response", self.on_folder_response)
        dialog.show()
    
    def on_folder_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                self.selected_path = file.get_path()
                self.path_entry.set_text(self.selected_path)
        dialog.destroy()
    
    def on_ok(self, button):
        if self.response_callback:
            self.response_callback(Gtk.ResponseType.ACCEPT, self.selected_path)
        self.destroy()
    
    def on_cancel(self, button):
        if self.response_callback:
            self.response_callback(Gtk.ResponseType.CANCEL, "")
        self.destroy()
    
    def run_async(self, callback):
        """Run dialog asynchronously with callback"""
        self.response_callback = callback
        self.show()

class SyncWorker(GObject.Object):
    """Worker for sync operations to prevent UI freezing"""
    
    __gsignals__ = {
        'progress-updated': (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        'log-message': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'sync-finished': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }
    
    def __init__(self, sync_function, *args):
        super().__init__()
        self.sync_function = sync_function
        self.args = args
        self.thread = None
    
    def start(self):
        """Start the worker thread"""
        self.thread = Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
    
    def _run(self):
        """Run the sync operation in thread"""
        try:
            result = self.sync_function(*self.args)
            GLib.idle_add(lambda: self.emit('sync-finished', result))
        except Exception as e:
            GLib.idle_add(lambda: self.emit('log-message', f"Error in sync operation: {str(e)}"))
            GLib.idle_add(lambda: self.emit('sync-finished', False))

class GDSync(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("gdsync v3.1.0 by MalikHw47")
        self.set_default_size(600, 600)
        self.adb_path = ""
        self.gd_pc_path = ""
        self.sync_worker = None
        self.init_ui()
        self.detect_adb()
        self.setup_gd_installation_auto()
        self.log("GDSync initialized. Ready for operation.")
        
    def init_ui(self):
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Header/Title section
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        title_label = Gtk.Label(label="GDSync v3.1.0 by MalikHw47")
        title_label.add_css_class("title-1")
        title_label.set_halign(Gtk.Align.CENTER)
        
        # Create a frame for the title
        title_frame = Gtk.Frame()
        title_frame.set_child(title_label)
        title_frame.add_css_class("card")
        
        header_box.append(title_frame)
        main_box.append(header_box)
        
        # Installation info section
        install_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        self.install_label = Gtk.Label(label="GD Installation: Not configured")
        self.install_label.set_halign(Gtk.Align.START)
        
        install_frame = Gtk.Frame()
        install_frame.set_child(self.install_label)
        install_frame.add_css_class("card")
        
        self.setup_btn = Gtk.Button(label="Setup GD Installation")
        self.setup_btn.connect("clicked", self.setup_gd_installation)
        
        install_box.append(install_frame)
        install_box.append(self.setup_btn)
        main_box.append(install_box)
        
        # Logs section
        logs_label = Gtk.Label(label="Logs:")
        logs_label.set_halign(Gtk.Align.START)
        
        self.logs_text = Gtk.TextView()
        self.logs_text.set_editable(False)
        self.logs_text.set_wrap_mode(Gtk.WrapMode.WORD)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        scrolled.set_child(self.logs_text)
        scrolled.add_css_class("card")
        
        main_box.append(logs_label)
        main_box.append(scrolled)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        main_box.append(self.progress_bar)
        
        # Direction options
        direction_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        direction_label = Gtk.Label(label="Direction:")
        direction_label.set_size_request(80, -1)
        
        self.phone_to_pc = Gtk.CheckButton(label="Phone to PC")
        self.pc_to_phone = Gtk.CheckButton(label="PC to Phone")
        self.pc_to_phone.set_group(self.phone_to_pc)  # Radio button behavior
        self.pc_to_phone.set_active(True)
        
        direction_box.append(direction_label)
        direction_box.append(self.phone_to_pc)
        direction_box.append(self.pc_to_phone)
        main_box.append(direction_box)
        
        # Data options
        data_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        data_label = Gtk.Label(label="Data:")
        data_label.set_size_request(80, -1)
        
        self.only_userdata = Gtk.CheckButton(label="Only userdata")
        self.all_data = Gtk.CheckButton(label="All data with Songs and SFX")
        self.all_data.set_group(self.only_userdata)  # Radio button behavior
        self.only_userdata.set_active(True)
        
        data_box.append(data_label)
        data_box.append(self.only_userdata)
        data_box.append(self.all_data)
        main_box.append(data_box)
        
        # Buttons section
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        
        self.donate_btn = Gtk.Button(label="Donate")
        self.donate_btn.connect("clicked", self.open_donate)
        
        self.sync_btn = Gtk.Button(label="Sync")
        self.sync_btn.add_css_class("suggested-action")
        self.sync_btn.connect("clicked", self.start_sync)
        
        button_box.append(self.donate_btn)
        button_box.append(self.sync_btn)
        main_box.append(button_box)
        
        self.set_content(main_box)
    
    def setup_gd_installation_auto(self):
        """Auto-setup GD installation if possible"""
        home_dir = os.path.expanduser("~")
        username = os.environ.get("USER", "user")
        
        # Try Wine path first
        wine_path = os.path.join(home_dir, ".wine", "drive_c", "users", username, "AppData", "Local", "GeometryDash")
        if os.path.exists(wine_path):
            self.gd_pc_path = wine_path
            self.install_label.set_text(f"GD Installation: {wine_path}")
            self.log(f"Auto-detected Wine GD installation: {wine_path}")
            return
        
        # Try Steam with Proton path
        steam_path = os.path.join(home_dir, ".local", "share", "Steam", "steamapps", "compatdata", "322170", "pfx", "drive_c", "users", "steamuser", "AppData", "Local", "GeometryDash")
        if os.path.exists(steam_path):
            self.gd_pc_path = steam_path
            self.install_label.set_text(f"GD Installation: {steam_path}")
            self.log(f"Auto-detected Steam GD installation: {steam_path}")
            return
        
        self.log("No GD installation auto-detected. Please setup manually.")
    
    def setup_gd_installation(self, button):
        """Setup Geometry Dash installation path"""
        dialog = InstallationSetupDialog(self)
        dialog.run_async(self.on_setup_response)
    
    def on_setup_response(self, response, path):
        """Handle setup dialog response"""
        if response == Gtk.ResponseType.ACCEPT:
            if path and self.validate_gd_installation(path):
                self.gd_pc_path = path
                self.install_label.set_text(f"GD Installation: {path}")
                self.log(f"GD installation path set to: {path}")
            elif path:
                self.log(f"Invalid GD installation path: {path}")
    
    def validate_gd_installation(self, path):
        """Validate GD installation and check for required files"""
        if not os.path.exists(path):
            self.log(f"Path does not exist: {path}")
            self.show_error_dialog("Invalid Path", f"The selected path does not exist:\n{path}")
            return False
        
        # Check for CCGameManager.dat file
        ccgamemanager_path = os.path.join(path, "CCGameManager.dat")
        
        if not os.path.exists(ccgamemanager_path):
            dialog = Gtk.AlertDialog()
            dialog.set_message("GD Data Files Not Found")
            dialog.set_detail(
                f"CCGameManager.dat was not found in:\n{path}\n\n"
                "This usually means Geometry Dash hasn't been run yet, or the path is incorrect.\n\n"
                "Would you like to:\n"
                "• Continue anyway (files will be created during sync)\n"
                "• Cancel and run GD first\n\n"
                "Note: It's recommended to run GD at least once to create the initial data files."
            )
            dialog.set_buttons(["Cancel", "Continue Anyway"])
            dialog.set_cancel_button(0)
            dialog.set_default_button(0)
            
            dialog.choose(self, None, self.on_validation_response, path)
            return False  # Will be handled by callback
        else:
            self.log("CCGameManager.dat found. Installation path validated.")
            return True
    
    def on_validation_response(self, dialog, result, path):
        """Handle validation dialog response"""
        try:
            response = dialog.choose_finish(result)
            if response == 1:  # Continue Anyway
                self.log("Warning: CCGameManager.dat not found. Continuing anyway...")
                self.gd_pc_path = path
                self.install_label.set_text(f"GD Installation: {path}")
                self.log(f"GD installation path set to: {path}")
            else:
                info_dialog = Gtk.AlertDialog()
                info_dialog.set_message("Run Geometry Dash First")
                info_dialog.set_detail(
                    "Please run Geometry Dash at least once and close it normally.\n"
                    "This will create the necessary data files for syncing.\n\n"
                    "After running GD, come back and setup the installation path again."
                )
                info_dialog.show(self)
        except Exception as e:
            self.log(f"Error in validation response: {str(e)}")
    
    def show_error_dialog(self, title, message):
        """Show error dialog"""
        dialog = Gtk.AlertDialog()
        dialog.set_message(title)
        dialog.set_detail(message)
        dialog.show(self)
    
    def show_info_dialog(self, title, message):
        """Show info dialog"""
        dialog = Gtk.AlertDialog()
        dialog.set_message(title)
        dialog.set_detail(message)
        dialog.show(self)
    
    def show_question_dialog(self, title, message, callback):
        """Show question dialog"""
        dialog = Gtk.AlertDialog()
        dialog.set_message(title)
        dialog.set_detail(message)
        dialog.set_buttons(["No", "Yes"])
        dialog.set_cancel_button(0)
        dialog.set_default_button(1)
        dialog.choose(self, None, callback)
    
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
        buffer = self.logs_text.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, message + "\n")
        
        # Auto-scroll to bottom
        mark = buffer.get_insert()
        self.logs_text.scroll_mark_onscreen(mark)
    
    def update_progress(self, value, max_value=100):
        """Update progress bar"""
        if max_value > 0:
            fraction = value / max_value
            self.progress_bar.set_fraction(fraction)
            self.progress_bar.set_text(f"{value}/{max_value}")
        else:
            self.progress_bar.set_fraction(0)
            self.progress_bar.set_text("0/0")
    
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
        tutorial_text = """ADB Installation Tutorial for Windows:

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
   - Enable "USB Debugging\""""
        
        self.show_info_dialog("ADB Installation Tutorial", tutorial_text)

    def install_adb_linux(self):
        """Install ADB on Linux based on detected distribution"""
        distro = self.detect_linux_distro()
        
        if not distro:
            self.log("Could not detect Linux distribution. Please install ADB manually.")
            self.show_info_dialog(
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
                self.show_info_dialog(
                    "Installation Complete",
                    "ADB has been installed successfully!\n\n"
                    "Please restart this application to use ADB functionality."
                )
                # Re-detect ADB after installation
                self.detect_adb()
                return True
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install ADB: {str(e)}")
                self.show_error_dialog(
                    "Installation Failed",
                    f"Failed to install ADB automatically.\n\n"
                    f"Error: {str(e)}\n\n"
                    "Please install ADB manually using:\n"
                    f"{commands[distro]}"
                )
                return False
        else:
            self.log(f"Unsupported package manager: {distro}")
            self.show_info_dialog(
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
            self.show_question_dialog(
                "ADB Not Found",
                "ADB is not installed or not in system PATH.\n\n"
                "Would you like to see the installation tutorial?",
                self.on_windows_adb_response
            )
        else:  # Linux
            self.show_question_dialog(
                "ADB Not Found",
                "ADB is not installed on your system.\n\n"
                "Would you like to install it automatically?",
                self.on_linux_adb_response
            )
    
    def on_windows_adb_response(self, dialog, result):
        """Handle Windows ADB dialog response"""
        try:
            response = dialog.choose_finish(result)
            if response == 1:  # Yes
                self.show_windows_adb_tutorial()
        except Exception as e:
            self.log(f"Error in Windows ADB response: {str(e)}")
    
    def on_linux_adb_response(self, dialog, result):
        """Handle Linux ADB dialog response"""
        try:
            response = dialog.choose_finish(result)
            if response == 1:  # Yes
                self.install_adb_linux()
        except Exception as e:
            self.log(f"Error in Linux ADB response: {str(e)}")
    
    def open_donate(self, button):
        """Open donation page in web browser"""
        ko_fi_url = "https://ko-fi.com/MalikHw47"
        try:
            webbrowser.open(ko_fi_url)
            self.log(f"Opening donation page: {ko_fi_url}")
        except Exception as e:
            self.log(f"Error opening donation page: {str(e)}")
            self.show_info_dialog(
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
                GLib.idle_add(lambda i=i, total=len(files): self.sync_worker.emit('progress-updated', i, total))
            if not self.run_adb_command(["pull", f"{android_path}/{file}", pc_path]):
                success = False
        
        if self.sync_worker:
            GLib.idle_add(lambda: self.sync_worker.emit('progress-updated', len(files), len(files)))
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
                GLib.idle_add(lambda i=i, total=len(files): self.sync_worker.emit('progress-updated', i, total))
            file_path = os.path.join(pc_path, file)
            if os.path.exists(file_path):
                if not self.run_adb_command(["push", file_path, android_path]):
                    success = False
            else:
                self.log(f"Warning: File not found: {file_path}")
                success = False
        
        if self.sync_worker:
            GLib.idle_add(lambda: self.sync_worker.emit('progress-updated', len(files), len(files)))
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
                GLib.idle_add(lambda i=i, total=len(files): self.sync_worker.emit('progress-updated', i, total))
            
            # Get just the filename for local storage
            filename = os.path.basename(file_path)
            local_file_path = os.path.join(pc_path, filename)
            
            self.log(f"Pulling file {i+1}/{len(files)}: {filename}")
            if not self.run_adb_command(["pull", file_path, local_file_path]):
                success = False
        
        if self.sync_worker:
            GLib.idle_add(lambda: self.sync_worker.emit('progress-updated', len(files), len(files)))
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
                GLib.idle_add(lambda i=i, total=len(files_to_sync): self.sync_worker.emit('progress-updated', i, total))
            
            # Push the file directly to the android path
            remote_file_path = f"{android_path}/{filename}"
            self.log(f"Pushing file {i+1}/{len(files_to_sync)}: {filename}")
            if not self.run_adb_command(["push", file_path, remote_file_path]):
                success = False
        
        if self.sync_worker:
            GLib.idle_add(lambda: self.sync_worker.emit('progress-updated', len(files_to_sync), len(files_to_sync)))
        return success
    
    def on_sync_progress(self, worker, current, total):
        """Handle progress updates from worker thread"""
        self.update_progress(current, total)
    
    def on_sync_log(self, worker, message):
        """Handle log messages from worker thread"""
        self.log(message)
    
    def on_sync_finished(self, worker, success):
        """Handle sync completion"""
        self.sync_btn.set_sensitive(True)
        self.sync_worker = None
        
        if success:
            self.log("Sync completed successfully!")
            self.show_info_dialog("Success", "Geometry Dash data sync completed successfully!")
        else:
            self.log("Sync completed with errors. Check the logs for details.")
            self.show_error_dialog("Warning", "Sync completed with errors. Check the logs for details.")
    
    def start_sync(self, button):
        """Start the sync process based on selected options"""
        if not self.adb_path:
            self.show_error_dialog("Error", "ADB path not set. Please install ADB first.")
            return
        
        if not self.gd_pc_path:
            self.show_error_dialog("Error", "GD installation path not set. Please setup GD installation first.")
            return
        
        if self.sync_worker:
            self.show_info_dialog("Sync in Progress", "A sync operation is already running. Please wait for it to complete.")
            return
        
        # Reset progress bar
        self.progress_bar.set_fraction(0)
        self.progress_bar.set_text("0/0")
        
        # Check ADB device connection
        self.log("Checking device connection...")
        if not self.run_adb_command(["devices"]):
            self.show_error_dialog("Error", "Failed to connect to ADB device. Make sure your device is connected and USB debugging is enabled.")
            return
        
        pc_path, android_path = self.get_geometry_dash_paths()
        
        # Make sure PC path exists
        if not os.path.exists(pc_path):
            os.makedirs(pc_path, exist_ok=True)
            self.log(f"Created PC directory: {pc_path}")
        
        # Disable sync button during operation
        self.sync_btn.set_sensitive(False)
        
        # Determine which sync operation to perform and start worker thread
        if self.phone_to_pc.get_active():
            if self.only_userdata.get_active():
                sync_func = self.sync_phone_to_pc_userdata
            else:
                sync_func = self.sync_phone_to_pc_all
        else:  # PC to Phone
            if self.only_userdata.get_active():
                sync_func = self.sync_pc_to_phone_userdata
            else:
                sync_func = self.sync_pc_to_phone_all
        
        # Create and start worker thread
        self.sync_worker = SyncWorker(sync_func, pc_path, android_path)
        self.sync_worker.connect('progress-updated', self.on_sync_progress)
        self.sync_worker.connect('log-message', self.on_sync_log)
        self.sync_worker.connect('sync-finished', self.on_sync_finished)
        self.sync_worker.start()

class GDSyncApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.gdsync")
        self.connect("activate", self.on_activate)
    
    def on_activate(self, app):
        self.window = GDSync(self)
        self.window.present()

def main():
    app = GDSyncApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
