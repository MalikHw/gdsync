#include <windows.h>
#include <shlobj.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <process.h>
#include <direct.h>
#include <string.h>
#include <tlhelp32.h>
#include <time.h>
#include <sys/stat.h> // Required for stat to get local file time easily

#define ID_LOGS_EDIT 1001
#define ID_PHONE_TO_PC_RADIO 1002
#define ID_PC_TO_PHONE_RADIO 1003
#define ID_ONLY_USERDATA_RADIO 1004
#define ID_ALL_DATA_RADIO 1005
#define ID_SYNC_BUTTON 1006
#define ID_SETTINGS_BUTTON 1007
#define ID_DONATE_BUTTON 1008
#define ID_ACTIVATE_PRO_BUTTON 1009
#define ID_SYNC_GEODE_CHECKBOX 1010
#define ID_SYNC_GDH_CHECKBOX 1011
#define ID_PRO_ONLY_LABEL 1012

#define ID_SETTINGS_PC_GD_EDIT 2001
#define ID_SETTINGS_PHONE_GD_EDIT 2002
#define ID_SETTINGS_PC_GEODE_EDIT 2003
#define ID_SETTINGS_PHONE_GEODE_EDIT 2004
#define ID_SETTINGS_PC_GDH_EDIT 2005
#define ID_SETTINGS_PHONE_GDH_EDIT 2006
#define ID_SETTINGS_SAVE_BUTTON 2007

#define ID_ACTIVATE_KEY_EDIT 3001
#define ID_ACTIVATE_OK_BUTTON 3002
#define ID_ACTIVATE_GET_CODE_BUTTON 3003

HWND hwndMain;
HWND hwndLogs;
HWND hwndSettings;
HWND hwndActivatePro;
HWND hwndPhoneToPC;
HWND hwndPCToPhone;
HWND hwndOnlyUserdata;
HWND hwndAllData;
HWND hwndSyncButton;
HWND hwndDonateButton;
HWND hwndSettingsButton;
HWND hwndActivateProButton;
HWND hwndSyncGeodeCheckbox;
HWND hwndSyncGDHCheckbox;
HWND hwndProOnlyLabel;

char PC_GD_PATH[MAX_PATH];
char PHONE_GD_PATH[MAX_PATH];
char PC_GEODE_PATH[MAX_PATH];
char PHONE_GEODE_PATH[MAX_PATH];
char PC_GDH_PATH[MAX_PATH];
char PHONE_GDH_PATH[MAX_PATH];
char CONFIG_FILE[MAX_PATH];
char LICENSE_FILE[MAX_PATH];
char ADB_PATH[MAX_PATH];
char LICENSE_KEY[100] = "";

bool PRO_ENABLED = false;

const char* VALID_KEYS[] = {
    "YOUBIIITCHHHHHHHHHHHHHH",
};
const int NUM_VALID_KEYS = sizeof(VALID_KEYS) / sizeof(VALID_KEYS[0]);

#define DEFAULT_PC_GD_PATH_FORMAT "%s\\AppData\\Local\\GeometryDash"
#define DEFAULT_PHONE_GD_PATH "/storage/emulated/0/Android/media/com.geode.launcher/save"
#define DEFAULT_PC_GEODE_PATH_FORMAT "%s\\geode\\mods" // Assuming GD is in Steam path relative to LocalAppData
#define DEFAULT_PHONE_GEODE_PATH "/storage/emulated/0/Android/media/com.geode.launcher/game/geode/mods"
#define DEFAULT_PC_GDH_PATH_FORMAT "%s\\geode\\mods\\tobyadd.gdh\\Macros" // Relative to GD Path
#define DEFAULT_PHONE_GDH_PATH "/storage/emulated/0/Android/media/com.geode.launcher/save/geode/mods/tobyadd.gdh/Macros"


const char* USERDATA_FILES[] = {
    "CCLocalLevels.dat", "CCLocalLevels2.dat",
    "CCGameManager.dat", "CCGameManager2.dat"
};
const int NUM_USERDATA_FILES = sizeof(USERDATA_FILES) / sizeof(USERDATA_FILES[0]);

const char* CRITICAL_USERDATA_FILES[] = {
    "CCLocalLevels.dat", "CCLocalLevels2.dat",
    "CCGameManager.dat", "CCGameManager2.dat"
};
const int NUM_CRITICAL_FILES = sizeof(CRITICAL_USERDATA_FILES) / sizeof(CRITICAL_USERDATA_FILES[0]);


void InitializeUI(HWND hwnd);
void LoadConfiguration();
void SaveConfiguration();
void LoadLicense();
void SaveLicense();
bool ExecuteADBCommand(const char* command, char* output, int outputSize);
void AppendToLogs(const char* message);
bool IsGameRunning();
void BackupFile(const char* filepath);
void SyncData();
void PushData(bool userDataOnly, bool smartSync);
void PullData(bool userDataOnly, bool smartSync);
void SyncGeodeMods(bool push, bool smartSync);
void SyncGDHReplays(bool push, bool smartSync);
bool CheckGeodeInstalled();
time_t GetLocalFileTime(const char* filepath);
time_t GetRemoteFileTime(const char* filepath);
bool IsCriticalFile(const char* filename);
void ShowSettingsDialog();
void ShowActivationDialog();
void OpenDonationPage();
void OpenActivationCodePage();
void UpdateUIForProStatus();
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam);
LRESULT CALLBACK SettingsProc(HWND hwndDlg, UINT msg, WPARAM wParam, LPARAM lParam);
LRESULT CALLBACK ActivationProc(HWND hwndDlg, UINT msg, WPARAM wParam, LPARAM lParam);


int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    WNDCLASSEX wc = {0};
    WNDCLASSEX wcSettings = {0};
    WNDCLASSEX wcActivate = {0};
    MSG msg;

    wc.cbSize = sizeof(WNDCLASSEX);
    wc.style = 0;
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wc.lpszClassName = "GDSyncClass";

    wcSettings.cbSize = sizeof(WNDCLASSEX);
    wcSettings.style = 0;
    wcSettings.lpfnWndProc = SettingsProc;
    wcSettings.hInstance = hInstance;
    wcSettings.hCursor = LoadCursor(NULL, IDC_ARROW);
    wcSettings.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wcSettings.lpszClassName = "GDSyncSettingsClass";

    wcActivate.cbSize = sizeof(WNDCLASSEX);
    wcActivate.style = 0;
    wcActivate.lpfnWndProc = ActivationProc;
    wcActivate.hInstance = hInstance;
    wcActivate.hCursor = LoadCursor(NULL, IDC_ARROW);
    wcActivate.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    wcActivate.lpszClassName = "GDSyncActivationClass";

    if (!RegisterClassEx(&wc) || !RegisterClassEx(&wcSettings) || !RegisterClassEx(&wcActivate)) {
        MessageBox(NULL, "Window Registration Failed!", "Error", MB_ICONERROR | MB_OK);
        return 0;
    }

    GetModuleFileName(NULL, ADB_PATH, MAX_PATH);
    char* lastSlash = strrchr(ADB_PATH, '\\');
    if (lastSlash != NULL) {
        *(lastSlash + 1) = '\0';
    }
    strcat(ADB_PATH, "adb.exe");

    char appDataPath[MAX_PATH];
    SHGetFolderPath(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, appDataPath);
    sprintf(CONFIG_FILE, "%s\\gdsync\\gdsync.conf", appDataPath);
    sprintf(LICENSE_FILE, "%s\\gdsync\\gdsync.license", appDataPath);

    LoadConfiguration();
    LoadLicense();

    hwndMain = CreateWindowEx(
        0,
        "GDSyncClass",
        "gdsync v2.0 by MalikHw47",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 600, 400,
        NULL, NULL, hInstance, NULL
    );

    if (hwndMain == NULL) {
        MessageBox(NULL, "Window Creation Failed!", "Error", MB_ICONERROR | MB_OK);
        return 0;
    }

    InitializeUI(hwndMain);
    UpdateUIForProStatus();

    ShowWindow(hwndMain, nCmdShow);
    UpdateWindow(hwndMain);

    if (!PRO_ENABLED) {
         if (MessageBox(hwndMain, "Welcome to GDSync!\n\nActivate Pro features for enhanced sync capabilities?\n\n- Sync Geode mods\n- Smart sync (only new files)\n- Sync GDH replays",
                        "GDSync Pro", MB_YESNO | MB_ICONQUESTION) == IDYES) {
             ShowActivationDialog();
         }
    }


    while (GetMessage(&msg, NULL, 0, 0) > 0) {
         if (!IsDialogMessage(hwndSettings, &msg) && !IsDialogMessage(hwndActivatePro, &msg)) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    return (int)msg.wParam;
}

void InitializeUI(HWND hwnd) {
    CreateWindow("STATIC", "Logs:", WS_VISIBLE | WS_CHILD,
                10, 10, 80, 20, hwnd, NULL, NULL, NULL);

    hwndLogs = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "",
                WS_VISIBLE | WS_CHILD | WS_VSCROLL | ES_MULTILINE | ES_AUTOVSCROLL | ES_READONLY,
                10, 35, 400, 250, hwnd, (HMENU)ID_LOGS_EDIT, NULL, NULL);

    hwndPhoneToPC = CreateWindow("BUTTON", "Phone to PC",
                WS_VISIBLE | WS_CHILD | BS_AUTORADIOBUTTON | WS_GROUP,
                10, 300, 110, 20, hwnd, (HMENU)ID_PHONE_TO_PC_RADIO, NULL, NULL);
    hwndPCToPhone = CreateWindow("BUTTON", "PC to Phone",
                WS_VISIBLE | WS_CHILD | BS_AUTORADIOBUTTON,
                130, 300, 110, 20, hwnd, (HMENU)ID_PC_TO_PHONE_RADIO, NULL, NULL);

    hwndOnlyUserdata = CreateWindow("BUTTON", "Only userdata",
                WS_VISIBLE | WS_CHILD | BS_AUTORADIOBUTTON | WS_GROUP,
                10, 330, 110, 20, hwnd, (HMENU)ID_ONLY_USERDATA_RADIO, NULL, NULL);
    hwndAllData = CreateWindow("BUTTON", "All data with Songs and SFX",
                WS_VISIBLE | WS_CHILD | BS_AUTORADIOBUTTON,
                130, 330, 200, 20, hwnd, (HMENU)ID_ALL_DATA_RADIO, NULL, NULL);

    SendMessage(hwndPCToPhone, BM_SETCHECK, BST_CHECKED, 0);
    SendMessage(hwndOnlyUserdata, BM_SETCHECK, BST_CHECKED, 0);


    hwndActivateProButton = CreateWindow("BUTTON", "Activate Pro",
                WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
                430, 35, 140, 30, hwnd, (HMENU)ID_ACTIVATE_PRO_BUTTON, NULL, NULL);
    hwndSettingsButton = CreateWindow("BUTTON", "Settings",
                WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
                430, 75, 140, 30, hwnd, (HMENU)ID_SETTINGS_BUTTON, NULL, NULL);
    hwndDonateButton = CreateWindow("BUTTON", "Donate",
                WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
                430, 115, 140, 30, hwnd, (HMENU)ID_DONATE_BUTTON, NULL, NULL);

    hwndSyncGeodeCheckbox = CreateWindow("BUTTON", "Sync Geode Mods",
                WS_VISIBLE | WS_CHILD | BS_AUTOCHECKBOX,
                430, 160, 140, 20, hwnd, (HMENU)ID_SYNC_GEODE_CHECKBOX, NULL, NULL);
    hwndSyncGDHCheckbox = CreateWindow("BUTTON", "Sync GDH replays",
                WS_VISIBLE | WS_CHILD | BS_AUTOCHECKBOX,
                430, 185, 140, 20, hwnd, (HMENU)ID_SYNC_GDH_CHECKBOX, NULL, NULL);
    hwndProOnlyLabel = CreateWindow("STATIC", "PRO ONLY!", WS_VISIBLE | WS_CHILD | SS_CENTER,
                430, 210, 140, 20, hwnd, (HMENU)ID_PRO_ONLY_LABEL, NULL, NULL);


    hwndSyncButton = CreateWindow("BUTTON", "sync",
                WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON,
                430, 300, 140, 50, hwnd, (HMENU)ID_SYNC_BUTTON, NULL, NULL);

    AppendToLogs("GDSync initialized. Ready for operation.");
    AppendToLogs("ADB path:");
    AppendToLogs(ADB_PATH);
}

void UpdateUIForProStatus() {
    EnableWindow(hwndSyncGeodeCheckbox, PRO_ENABLED);
    EnableWindow(hwndSyncGDHCheckbox, PRO_ENABLED);
    ShowWindow(hwndProOnlyLabel, PRO_ENABLED ? SW_HIDE : SW_SHOW);

    if (PRO_ENABLED) {
        SetWindowText(hwndActivateProButton, "Pro: Active ✓");
        EnableWindow(hwndActivateProButton, FALSE); // Disable after activation
    } else {
         SetWindowText(hwndActivateProButton, "Activate Pro");
         EnableWindow(hwndActivateProButton, TRUE);
    }
}


void LoadConfiguration() {
    char userProfile[MAX_PATH];
    SHGetFolderPath(NULL, CSIDL_PROFILE, NULL, 0, userProfile);
    sprintf(PC_GD_PATH, DEFAULT_PC_GD_PATH_FORMAT, userProfile);
    strcpy(PHONE_GD_PATH, DEFAULT_PHONE_GD_PATH);

    char steamPath[MAX_PATH] = ""; // Placeholder, ideally find Steam GD install path
    SHGetFolderPath(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, steamPath); // Default to AppData if Steam path logic is missing
    sprintf(PC_GEODE_PATH, DEFAULT_PC_GEODE_PATH_FORMAT, PC_GD_PATH); // Default relative to GD path for simplicity
    strcpy(PHONE_GEODE_PATH, DEFAULT_PHONE_GEODE_PATH);
    sprintf(PC_GDH_PATH, DEFAULT_PC_GDH_PATH_FORMAT, PC_GD_PATH); // Default relative to GD path
    strcpy(PHONE_GDH_PATH, DEFAULT_PHONE_GDH_PATH);


    FILE* file = fopen(CONFIG_FILE, "r");
    if (file != NULL) {
        char line[MAX_PATH * 2];
        while (fgets(line, sizeof(line), file)) {
            char* equals = strchr(line, '=');
            if (equals) {
                *equals = '\0';
                char* value = equals + 1;

                char* newline = strchr(value, '\n');
                if (newline) *newline = '\0';

                if (value[0] == '"') {
                    value++;
                    char* endQuote = strrchr(value, '"'); // Use strrchr for last quote
                    if (endQuote) *endQuote = '\0';
                }

                if (strcmp(line, "PC_GD_PATH") == 0) strcpy(PC_GD_PATH, value);
                else if (strcmp(line, "PHONE_GD_PATH") == 0) strcpy(PHONE_GD_PATH, value);
                else if (strcmp(line, "PC_GEODE_PATH") == 0) strcpy(PC_GEODE_PATH, value);
                else if (strcmp(line, "PHONE_GEODE_PATH") == 0) strcpy(PHONE_GEODE_PATH, value);
                else if (strcmp(line, "PC_GDH_PATH") == 0) strcpy(PC_GDH_PATH, value);
                else if (strcmp(line, "PHONE_GDH_PATH") == 0) strcpy(PHONE_GDH_PATH, value);
            }
        }
        fclose(file);
    }
}

void SaveConfiguration() {
    char configDir[MAX_PATH];
    strcpy(configDir, CONFIG_FILE);
    char* lastSlash = strrchr(configDir, '\\');
    if (lastSlash) {
        *lastSlash = '\0';
        _mkdir(configDir);
    }

    FILE* file = fopen(CONFIG_FILE, "w");
    if (file != NULL) {
        fprintf(file, "PC_GD_PATH=\"%s\"\n", PC_GD_PATH);
        fprintf(file, "PHONE_GD_PATH=\"%s\"\n", PHONE_GD_PATH);
        fprintf(file, "PC_GEODE_PATH=\"%s\"\n", PC_GEODE_PATH);
        fprintf(file, "PHONE_GEODE_PATH=\"%s\"\n", PHONE_GEODE_PATH);
        fprintf(file, "PC_GDH_PATH=\"%s\"\n", PC_GDH_PATH);
        fprintf(file, "PHONE_GDH_PATH=\"%s\"\n", PHONE_GDH_PATH);
        fclose(file);
        AppendToLogs("Configuration saved.");
    } else {
        AppendToLogs("Failed to save configuration!");
    }
}

void LoadLicense() {
    FILE* file = fopen(LICENSE_FILE, "r");
    if (file != NULL) {
        char line[MAX_PATH];
        while (fgets(line, sizeof(line), file)) {
            char* equals = strchr(line, '=');
            if (equals) {
                *equals = '\0';
                char* value = equals + 1;
                char* newline = strchr(value, '\n');
                if (newline) *newline = '\0';
                 if (value[0] == '"') {
                    value++;
                    char* endQuote = strrchr(value, '"');
                    if (endQuote) *endQuote = '\0';
                }
                if (strcmp(line, "LICENSE_KEY") == 0) {
                    strncpy(LICENSE_KEY, value, sizeof(LICENSE_KEY) - 1);
                    LICENSE_KEY[sizeof(LICENSE_KEY) - 1] = '\0';
                    break;
                }
            }
        }
        fclose(file);
    }

    PRO_ENABLED = false;
    if (strlen(LICENSE_KEY) > 0) {
        for (int i = 0; i < NUM_VALID_KEYS; i++) {
            if (strcmp(LICENSE_KEY, VALID_KEYS[i]) == 0) {
                PRO_ENABLED = true;
                break;
            }
        }
    }
     if (PRO_ENABLED) {
        AppendToLogs("Pro version activated.");
    } else {
         AppendToLogs("Running in Free mode.");
         strcpy(LICENSE_KEY, ""); // Clear invalid key
    }
}


void SaveLicense() {
     char licenseDir[MAX_PATH];
    strcpy(licenseDir, LICENSE_FILE);
    char* lastSlash = strrchr(licenseDir, '\\');
    if (lastSlash) {
        *lastSlash = '\0';
        _mkdir(licenseDir);
    }

    FILE* file = fopen(LICENSE_FILE, "w");
    if (file != NULL) {
        fprintf(file, "LICENSE_KEY=\"%s\"\n", LICENSE_KEY);
        fclose(file);
        AppendToLogs("License key saved.");
    } else {
        AppendToLogs("Failed to save license key!");
    }
}

bool ExecuteADBCommand(const char* adbArgs, char* output, int outputSize) {
    char fullCommand[MAX_PATH + 1024];
    sprintf(fullCommand, "\"%s\" %s", ADB_PATH, adbArgs);

    AppendToLogs("Executing:");
    AppendToLogs(fullCommand);

    SECURITY_ATTRIBUTES sa;
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.lpSecurityDescriptor = NULL;
    sa.bInheritHandle = TRUE;

    HANDLE hReadPipe, hWritePipe;
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
        AppendToLogs("Error creating pipe!");
        return false;
    }

    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(STARTUPINFO));
    si.cb = sizeof(STARTUPINFO);
    si.dwFlags |= STARTF_USESTDHANDLES;
    si.hStdOutput = hWritePipe;
    si.hStdError = hWritePipe; // Capture errors too
    si.hStdInput = NULL;
    ZeroMemory(&pi, sizeof(PROCESS_INFORMATION));

    bool success = CreateProcess(NULL, fullCommand, NULL, NULL, TRUE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi);

    if (!success) {
        AppendToLogs("Error creating ADB process!");
        CloseHandle(hReadPipe);
        CloseHandle(hWritePipe);
        return false;
    }

     CloseHandle(hWritePipe); // Close our handle to the write end

    DWORD bytesRead;
    char buffer[1024];
    if (output != NULL) output[0] = '\0';
    int totalBytes = 0;

    while (ReadFile(hReadPipe, buffer, sizeof(buffer) - 1, &bytesRead, NULL) && bytesRead > 0) {
         buffer[bytesRead] = '\0'; // Null-terminate the read buffer
         if (output != NULL) {
              if (totalBytes + bytesRead < outputSize) {
                  strcat(output, buffer);
                  totalBytes += bytesRead;
              } else {
                   // Buffer overflow, maybe log truncation
                   strncat(output, buffer, outputSize - totalBytes -1 );
                   break; // Stop reading
              }
         }
         // Optionally log chunks for debugging long commands
         // AppendToLogs(buffer);
    }


    WaitForSingleObject(pi.hProcess, INFINITE);

    DWORD exitCode;
    GetExitCodeProcess(pi.hProcess, &exitCode);

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    CloseHandle(hReadPipe);


    char exitMsg[100];
    sprintf(exitMsg, "ADB command finished with exit code: %lu", exitCode);
    AppendToLogs(exitMsg);

    return (exitCode == 0);
}


void AppendToLogs(const char* message) {
    if (!message) return;
    int length = GetWindowTextLength(hwndLogs);
    SendMessage(hwndLogs, EM_SETSEL, (WPARAM)length, (LPARAM)length);
    SendMessage(hwndLogs, EM_REPLACESEL, 0, (LPARAM)message);
    SendMessage(hwndLogs, EM_REPLACESEL, 0, (LPARAM)"\r\n");
    SendMessage(hwndLogs, WM_VSCROLL, SB_BOTTOM, 0); // Scroll to bottom
}

bool IsGameRunning() {
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) return false;

    PROCESSENTRY32 pe32;
    pe32.dwSize = sizeof(PROCESSENTRY32);

    if (!Process32First(hSnapshot, &pe32)) {
        CloseHandle(hSnapshot);
        return false;
    }

    bool isRunning = false;
    do {
        if (_stricmp(pe32.szExeFile, "GeometryDash.exe") == 0) {
            isRunning = true;
            break;
        }
    } while (Process32Next(hSnapshot, &pe32));

    CloseHandle(hSnapshot);
    return isRunning;
}

void BackupFile(const char* filepath) {
    char backupPath[MAX_PATH];
    sprintf(backupPath, "%s.bak", filepath);

    if (!CopyFile(filepath, backupPath, FALSE)) {
         DWORD error = GetLastError();
         if (error != ERROR_FILE_NOT_FOUND) {
             char msg[MAX_PATH + 100];
             sprintf(msg, "Warning: Could not back up %s (Error %lu)", filepath, error);
             AppendToLogs(msg);
         }
    } else {
         char msg[MAX_PATH + 50];
         sprintf(msg, "Backed up: %s", filepath);
         AppendToLogs(msg);
    }
}


bool CheckADBDevice() {
     char output[512] = {0};
    if (!ExecuteADBCommand("devices", output, sizeof(output))) {
        MessageBox(hwndMain, "Failed to execute ADB devices command. Ensure ADB is working.",
                   "ADB Error", MB_ICONERROR | MB_OK);
        AppendToLogs("ADB 'devices' command failed!");
        return false;
    }

     // Check output for "device" state, avoiding "offline", "unauthorized" etc.
     char *deviceLine = strstr(output, "\n"); // Find first newline to skip header
     if (deviceLine) {
         deviceLine++; // Move past newline
         if (strstr(deviceLine, "\tdevice")) { // Look for tab followed by "device"
              AppendToLogs("ADB device found.");
              return true;
         }
     }

     MessageBox(hwndMain, "No authorized Android device detected.\n\n- Ensure USB debugging is enabled on your phone.\n- Check your phone screen for an authorization prompt.\n- Make sure correct drivers are installed.",
               "No Device", MB_ICONWARNING | MB_OK);
    AppendToLogs("No authorized ADB device detected!");
    return false;
}


bool IsCriticalFile(const char* filename) {
    if (!filename) return false;
    for (int i = 0; i < NUM_CRITICAL_FILES; i++) {
        if (strcmp(filename, CRITICAL_USERDATA_FILES[i]) == 0) {
            return true;
        }
    }
    return false;
}

time_t GetLocalFileTime(const char* filepath) {
    struct stat fileInfo;
    if (stat(filepath, &fileInfo) == 0) {
        return fileInfo.st_mtime;
    }
    return 0; // Return 0 on error
}

time_t GetRemoteFileTime(const char* filepath) {
     if (!filepath || strlen(filepath) == 0) return 0;

    char command[MAX_PATH + 100];
    // Quote the path properly for the shell
    sprintf(command, "shell stat -c %%Y \"%s\"", filepath);
    char output[128] = {0};

    if (ExecuteADBCommand(command, output, sizeof(output))) {
        // Trim leading/trailing whitespace/newlines
        char* ptr = output;
        while (*ptr && isspace((unsigned char)*ptr)) ptr++;
        char* end = ptr + strlen(ptr) - 1;
        while (end > ptr && isspace((unsigned char)*end)) end--;
        *(end + 1) = '\0';

        // Check if output contains only digits
        bool all_digits = true;
        if (strlen(ptr) == 0) {
             all_digits = false; // Empty string is not a valid time
        } else {
            for(char* c = ptr; *c; ++c) {
                if (!isdigit((unsigned char)*c)) {
                    all_digits = false;
                    break;
                }
            }
        }


        if (all_digits) {
            return (time_t)strtol(ptr, NULL, 10);
        } else {
            // Handle cases where stat might output an error message instead of time
            char logMsg[MAX_PATH + 100];
            sprintf(logMsg, "Could not parse time for remote file: %s (Output: %s)", filepath, output);
            AppendToLogs(logMsg);
            return 0; // Indicate error or file not found
        }
    }
    // Log that the command itself failed
    // AppendToLogs("Failed to get remote file time command.");
    return 0; // Indicate error or file not found
}


void SyncData() {
    EnableWindow(hwndSyncButton, FALSE); // Disable button during sync
    AppendToLogs("====================");
    AppendToLogs("Starting sync operation...");

    if (IsGameRunning()) {
        MessageBox(hwndMain, "Geometry Dash is running. Please close it before syncing.",
                   "Game Running", MB_ICONWARNING | MB_OK);
        AppendToLogs("Sync aborted: Geometry Dash is running.");
        EnableWindow(hwndSyncButton, TRUE);
        return;
    }

    char output[256] = {0};
    if (!ExecuteADBCommand("version", output, sizeof(output))) {
        MessageBox(hwndMain, "ADB not found or not working. Make sure adb.exe is in the same directory as this application or in your system PATH.",
                   "ADB Error", MB_ICONERROR | MB_OK);
        AppendToLogs("ADB not found or not working!");
         EnableWindow(hwndSyncButton, TRUE);
        return;
    }
    AppendToLogs(output); // Log ADB version

    if (!CheckADBDevice()) {
        EnableWindow(hwndSyncButton, TRUE);
        return;
    }

    bool pcToPhone = (SendMessage(hwndPCToPhone, BM_GETCHECK, 0, 0) == BST_CHECKED);
    bool userDataOnly = (SendMessage(hwndOnlyUserdata, BM_GETCHECK, 0, 0) == BST_CHECKED);
    bool syncGeode = PRO_ENABLED && (SendMessage(hwndSyncGeodeCheckbox, BM_GETCHECK, 0, 0) == BST_CHECKED);
    bool syncGDH = PRO_ENABLED && (SendMessage(hwndSyncGDHCheckbox, BM_GETCHECK, 0, 0) == BST_CHECKED);
    bool smartSync = PRO_ENABLED; // Smart sync is always attempted if Pro is enabled

    if (pcToPhone) {
        AppendToLogs("Direction: PC -> Phone");
        PushData(userDataOnly, smartSync);
        if (syncGeode) SyncGeodeMods(true, smartSync);
        if (syncGDH) SyncGDHReplays(true, smartSync);
        AppendToLogs("Push operation finished.");
         MessageBox(hwndMain, "Files pushed to phone!", "Success", MB_ICONINFORMATION | MB_OK);
    } else {
        AppendToLogs("Direction: Phone -> PC");
        PullData(userDataOnly, smartSync);
        if (syncGeode) SyncGeodeMods(false, smartSync);
        if (syncGDH) SyncGDHReplays(false, smartSync);
        AppendToLogs("Pull operation finished.");
         MessageBox(hwndMain, "Files pulled from phone!", "Success", MB_ICONINFORMATION | MB_OK);
    }

    AppendToLogs("Sync operation complete.");
    AppendToLogs("====================");
    EnableWindow(hwndSyncButton, TRUE); // Re-enable button

    // Donation prompt after successful sync
    if (MessageBox(hwndMain, "Like GDSync?\n\nConsider donating to MalikHw47!",
                   "Support the Developer", MB_YESNO | MB_ICONQUESTION) == IDYES) {
        OpenDonationPage();
    }
}


void PushData(bool userDataOnly, bool smartSync) {
    AppendToLogs("--- Syncing Game Data (Push) ---");
    char command[MAX_PATH * 3];
    sprintf(command, "shell mkdir -p \"%s\"", PHONE_GD_PATH);
    ExecuteADBCommand(command, NULL, 0);

    int successCount = 0;
    int skipCount = 0;

    if (userDataOnly) {
        AppendToLogs("Mode: User data only");
        for (int i = 0; i < NUM_USERDATA_FILES; i++) {
            char sourcePath[MAX_PATH];
            sprintf(sourcePath, "%s\\%s", PC_GD_PATH, USERDATA_FILES[i]);
            char remotePath[MAX_PATH];
            sprintf(remotePath, "%s/%s", PHONE_GD_PATH, USERDATA_FILES[i]);
            const char* filename = USERDATA_FILES[i];

             FILE* file = fopen(sourcePath, "rb");
             if (file == NULL) continue; // Skip if local file doesn't exist
             fclose(file);

             bool pushFile = true;
             if (smartSync && !IsCriticalFile(filename)) {
                 time_t pcTime = GetLocalFileTime(sourcePath);
                 time_t phoneTime = GetRemoteFileTime(remotePath);
                 if (pcTime > 0 && phoneTime > 0 && pcTime <= phoneTime) {
                     pushFile = false;
                 }
             }

             if (pushFile) {
                 sprintf(command, "push \"%s\" \"%s/\"", sourcePath, PHONE_GD_PATH);
                 if (ExecuteADBCommand(command, NULL, 0)) {
                     AppendToLogs("Pushed:"); AppendToLogs(filename);
                     successCount++;
                 } else {
                     AppendToLogs("Failed to push:"); AppendToLogs(filename);
                 }
             } else {
                   AppendToLogs("Skipped (up-to-date):"); AppendToLogs(filename);
                   skipCount++;
             }
        }
    } else {
        AppendToLogs("Mode: All files");
        WIN32_FIND_DATA findData;
        char searchPath[MAX_PATH];
        sprintf(searchPath, "%s\\*", PC_GD_PATH);

        HANDLE hFind = FindFirstFile(searchPath, &findData);
        if (hFind != INVALID_HANDLE_VALUE) {
            do {
                if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                    char sourcePath[MAX_PATH];
                    sprintf(sourcePath, "%s\\%s", PC_GD_PATH, findData.cFileName);
                    char remotePath[MAX_PATH];
                    sprintf(remotePath, "%s/%s", PHONE_GD_PATH, findData.cFileName);
                    const char* filename = findData.cFileName;

                    bool pushFile = true;
                     if (smartSync && !IsCriticalFile(filename)) {
                         time_t pcTime = GetLocalFileTime(sourcePath);
                         time_t phoneTime = GetRemoteFileTime(remotePath);
                         if (pcTime > 0 && phoneTime > 0 && pcTime <= phoneTime) {
                             pushFile = false;
                         }
                     }

                    if (pushFile) {
                         sprintf(command, "push \"%s\" \"%s/\"", sourcePath, PHONE_GD_PATH);
                        if (ExecuteADBCommand(command, NULL, 0)) {
                            AppendToLogs("Pushed:"); AppendToLogs(filename);
                            successCount++;
                        } else {
                            AppendToLogs("Failed to push:"); AppendToLogs(filename);
                        }
                    } else {
                         AppendToLogs("Skipped (up-to-date):"); AppendToLogs(filename);
                         skipCount++;
                    }
                }
            } while (FindNextFile(hFind, &findData));
            FindClose(hFind);
        }
    }
    char summary[100];
    sprintf(summary, "Game Data Push Summary: %d pushed, %d skipped.", successCount, skipCount);
    AppendToLogs(summary);
}

void PullData(bool userDataOnly, bool smartSync) {
    AppendToLogs("--- Syncing Game Data (Pull) ---");
    _mkdir(PC_GD_PATH);

    int successCount = 0;
    int skipCount = 0;
    char command[MAX_PATH * 3];
    char output[MAX_PATH * 2] = {0}; // Buffer for file lists

    if (userDataOnly) {
        AppendToLogs("Mode: User data only");
        for (int i = 0; i < NUM_USERDATA_FILES; i++) {
            char destPath[MAX_PATH];
            sprintf(destPath, "%s\\%s", PC_GD_PATH, USERDATA_FILES[i]);
            char remotePath[MAX_PATH];
            sprintf(remotePath, "%s/%s", PHONE_GD_PATH, USERDATA_FILES[i]);
             const char* filename = USERDATA_FILES[i];

             sprintf(command, "shell \"[ -f \\\"%s\\\" ] && echo EXISTS\"", remotePath);
             if (!ExecuteADBCommand(command, output, sizeof(output)) || strstr(output, "EXISTS") == NULL) {
                 AppendToLogs("Remote file not found:"); AppendToLogs(filename);
                 continue; // Skip if remote file doesn't exist
             }

             bool pullFile = true;
             if (smartSync && !IsCriticalFile(filename)) {
                  time_t pcTime = GetLocalFileTime(destPath);
                  time_t phoneTime = GetRemoteFileTime(remotePath);
                  if (phoneTime > 0 && pcTime > 0 && phoneTime <= pcTime) {
                       pullFile = false;
                  }
             }

            if (pullFile) {
                BackupFile(destPath);
                sprintf(command, "pull \"%s\" \"%s\\\"", remotePath, PC_GD_PATH);
                if (ExecuteADBCommand(command, NULL, 0)) {
                    AppendToLogs("Pulled:"); AppendToLogs(filename);
                    successCount++;
                } else {
                    AppendToLogs("Failed to pull:"); AppendToLogs(filename);
                }
            } else {
                 AppendToLogs("Skipped (up-to-date):"); AppendToLogs(filename);
                 skipCount++;
            }
        }
    } else {
        AppendToLogs("Mode: All files");
        sprintf(command, "shell find \"%s\" -maxdepth 1 -type f -printf '%%f\\n'", PHONE_GD_PATH);

        if (ExecuteADBCommand(command, output, sizeof(output))) {
             char* token = strtok(output, "\n");
             while (token != NULL) {
                 // Clean up token (remove potential \r)
                 char* cr = strchr(token, '\r');
                 if (cr) *cr = '\0';

                 if (strlen(token) > 0) {
                     char destPath[MAX_PATH];
                     sprintf(destPath, "%s\\%s", PC_GD_PATH, token);
                     char remotePath[MAX_PATH];
                     sprintf(remotePath, "%s/%s", PHONE_GD_PATH, token);
                     const char* filename = token;

                     bool pullFile = true;
                      if (smartSync && !IsCriticalFile(filename)) {
                          time_t pcTime = GetLocalFileTime(destPath);
                          time_t phoneTime = GetRemoteFileTime(remotePath);
                           if (phoneTime > 0 && pcTime > 0 && phoneTime <= pcTime) {
                                pullFile = false;
                           }
                      }

                     if (pullFile) {
                        BackupFile(destPath);
                         sprintf(command, "pull \"%s\" \"%s\\\"", remotePath, PC_GD_PATH);
                         if (ExecuteADBCommand(command, NULL, 0)) {
                             AppendToLogs("Pulled:"); AppendToLogs(filename);
                             successCount++;
                         } else {
                             AppendToLogs("Failed to pull:"); AppendToLogs(filename);
                         }
                     } else {
                         AppendToLogs("Skipped (up-to-date):"); AppendToLogs(filename);
                         skipCount++;
                     }
                 }
                 token = strtok(NULL, "\n");
             }
        } else {
             AppendToLogs("Failed to list remote files in game data directory.");
        }
    }
     char summary[100];
    sprintf(summary, "Game Data Pull Summary: %d pulled, %d skipped.", successCount, skipCount);
    AppendToLogs(summary);
}

bool CheckGeodeInstalled() {
    AppendToLogs("Checking for Geode installation on phone...");
    char command[MAX_PATH + 50];
     // Check for base game/geode/mods dir OR the separate save/geode/mods dir
    sprintf(command, "shell \"[ -d \\\"%s\\\" ] || [ -d \\\"$(dirname \\\"%s\\\")\\\" ] && echo EXISTS\"", PHONE_GEODE_PATH, PHONE_GEODE_PATH);
    char output[128] = {0};

    if (ExecuteADBCommand(command, output, sizeof(output)) && strstr(output, "EXISTS") != NULL) {
         AppendToLogs("Geode directory found on phone.");
         return true;
    } else {
        AppendToLogs("Geode directory not found on phone.");
         MessageBox(hwndMain, "Geode does not appear to be installed on your phone (could not find Geode mods directory).\nGeode sync might fail.",
                    "Geode Not Found", MB_ICONWARNING | MB_OK);
        return false;
    }
}


void SyncGeodeMods(bool push, bool smartSync) {
    AppendToLogs("--- Syncing Geode Mods ---");
    if (!CheckGeodeInstalled() && push) { // Only strictly needed for push? Pull might still work.
        AppendToLogs("Skipping Geode sync due to installation check failure.");
        return;
    }

    char command[MAX_PATH * 3];
    char output[32 * 1024] = {0}; // Larger buffer for potentially many mods
    int successCount = 0;
    int skipCount = 0;

    if (push) {
         AppendToLogs("Direction: PC -> Phone");
         sprintf(command, "shell mkdir -p \"%s\"", PHONE_GEODE_PATH);
         ExecuteADBCommand(command, NULL, 0);

        WIN32_FIND_DATA findData;
        char searchPath[MAX_PATH];
        sprintf(searchPath, "%s\\*.geode", PC_GEODE_PATH);

        HANDLE hFind = FindFirstFile(searchPath, &findData);
        if (hFind != INVALID_HANDLE_VALUE) {
            do {
                if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                    char sourcePath[MAX_PATH];
                    sprintf(sourcePath, "%s\\%s", PC_GEODE_PATH, findData.cFileName);
                    char remotePath[MAX_PATH];
                    sprintf(remotePath, "%s/%s", PHONE_GEODE_PATH, findData.cFileName);
                    const char* filename = findData.cFileName;

                    bool pushFile = true;
                    if (smartSync) {
                        time_t pcTime = GetLocalFileTime(sourcePath);
                        time_t phoneTime = GetRemoteFileTime(remotePath);
                        if (pcTime > 0 && phoneTime > 0 && pcTime <= phoneTime) {
                            pushFile = false;
                        }
                    }

                    if (pushFile) {
                        sprintf(command, "push \"%s\" \"%s/\"", sourcePath, PHONE_GEODE_PATH);
                        if (ExecuteADBCommand(command, NULL, 0)) {
                            AppendToLogs("Pushed mod:"); AppendToLogs(filename);
                            successCount++;
                        } else {
                            AppendToLogs("Failed to push mod:"); AppendToLogs(filename);
                        }
                    } else {
                        AppendToLogs("Skipped mod (up-to-date):"); AppendToLogs(filename);
                        skipCount++;
                    }
                }
            } while (FindNextFile(hFind, &findData));
            FindClose(hFind);
        } else {
             AppendToLogs("No local Geode mods found to push.");
        }
    } else { // Pull
        AppendToLogs("Direction: Phone -> PC");
        _mkdir(PC_GEODE_PATH);
        sprintf(command, "shell find \"%s\" -maxdepth 1 -name '*.geode' -type f -printf '%%f\\n'", PHONE_GEODE_PATH);

        if (ExecuteADBCommand(command, output, sizeof(output))) {
             char* token = strtok(output, "\n");
             while (token != NULL) {
                 char* cr = strchr(token, '\r'); if (cr) *cr = '\0';
                 if (strlen(token) > 0) {
                    char destPath[MAX_PATH];
                    sprintf(destPath, "%s\\%s", PC_GEODE_PATH, token);
                    char remotePath[MAX_PATH];
                    sprintf(remotePath, "%s/%s", PHONE_GEODE_PATH, token);
                    const char* filename = token;

                    bool pullFile = true;
                    if (smartSync) {
                        time_t pcTime = GetLocalFileTime(destPath);
                        time_t phoneTime = GetRemoteFileTime(remotePath);
                        if (phoneTime > 0 && pcTime > 0 && phoneTime <= pcTime) {
                             pullFile = false;
                        }
                    }

                     if (pullFile) {
                        // BackupFile(destPath); // Optional: Backup mods?
                         sprintf(command, "pull \"%s\" \"%s\\\"", remotePath, PC_GEODE_PATH);
                         if (ExecuteADBCommand(command, NULL, 0)) {
                             AppendToLogs("Pulled mod:"); AppendToLogs(filename);
                             successCount++;
                         } else {
                             AppendToLogs("Failed to pull mod:"); AppendToLogs(filename);
                         }
                     } else {
                          AppendToLogs("Skipped mod (up-to-date):"); AppendToLogs(filename);
                          skipCount++;
                     }
                 }
                 token = strtok(NULL, "\n");
             }
        } else {
             AppendToLogs("Failed to list remote Geode mods.");
        }
    }
     char summary[100];
    sprintf(summary, "Geode Mods Sync Summary: %d synced, %d skipped.", successCount, skipCount);
    AppendToLogs(summary);
}

void SyncGDHReplays(bool push, bool smartSync) {
     AppendToLogs("--- Syncing GDH Replays ---");
    // Note: No check_gdh_installed equivalent for now

    char command[MAX_PATH * 3];
    char output[16 * 1024] = {0}; // Buffer for replays
    int successCount = 0;
    int skipCount = 0;

    if (push) {
         AppendToLogs("Direction: PC -> Phone");
         sprintf(command, "shell mkdir -p \"%s\"", PHONE_GDH_PATH);
         ExecuteADBCommand(command, NULL, 0);

        WIN32_FIND_DATA findData;
        char searchPath[MAX_PATH];
        sprintf(searchPath, "%s\\*.macro", PC_GDH_PATH); // Find .macro files

        HANDLE hFind = FindFirstFile(searchPath, &findData);
        if (hFind != INVALID_HANDLE_VALUE) {
            do {
                if (!(findData.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                    char sourcePath[MAX_PATH];
                    sprintf(sourcePath, "%s\\%s", PC_GDH_PATH, findData.cFileName);
                    char remotePath[MAX_PATH];
                    sprintf(remotePath, "%s/%s", PHONE_GDH_PATH, findData.cFileName);
                    const char* filename = findData.cFileName;

                    bool pushFile = true;
                    if (smartSync) {
                        time_t pcTime = GetLocalFileTime(sourcePath);
                        time_t phoneTime = GetRemoteFileTime(remotePath);
                        if (pcTime > 0 && phoneTime > 0 && pcTime <= phoneTime) {
                             pushFile = false;
                        }
                    }

                    if (pushFile) {
                        sprintf(command, "push \"%s\" \"%s/\"", sourcePath, PHONE_GDH_PATH);
                        if (ExecuteADBCommand(command, NULL, 0)) {
                            AppendToLogs("Pushed replay:"); AppendToLogs(filename);
                            successCount++;
                        } else {
                            AppendToLogs("Failed to push replay:"); AppendToLogs(filename);
                        }
                    } else {
                        AppendToLogs("Skipped replay (up-to-date):"); AppendToLogs(filename);
                        skipCount++;
                    }
                }
            } while (FindNextFile(hFind, &findData));
            FindClose(hFind);
        } else {
             AppendToLogs("No local GDH replays found to push.");
        }

    } else { // Pull
         AppendToLogs("Direction: Phone -> PC");
        _mkdir(PC_GDH_PATH);
        sprintf(command, "shell find \"%s\" -maxdepth 1 -name '*.macro' -type f -printf '%%f\\n'", PHONE_GDH_PATH);

         if (ExecuteADBCommand(command, output, sizeof(output))) {
             char* token = strtok(output, "\n");
             while (token != NULL) {
                 char* cr = strchr(token, '\r'); if (cr) *cr = '\0';
                  if (strlen(token) > 0) {
                    char destPath[MAX_PATH];
                    sprintf(destPath, "%s\\%s", PC_GDH_PATH, token);
                     char remotePath[MAX_PATH];
                    sprintf(remotePath, "%s/%s", PHONE_GDH_PATH, token);
                    const char* filename = token;

                    bool pullFile = true;
                    if (smartSync) {
                         time_t pcTime = GetLocalFileTime(destPath);
                         time_t phoneTime = GetRemoteFileTime(remotePath);
                          if (phoneTime > 0 && pcTime > 0 && phoneTime <= pcTime) {
                                pullFile = false;
                          }
                     }

                     if (pullFile) {
                         // BackupFile(destPath); // Optional: Backup replays?
                         sprintf(command, "pull \"%s\" \"%s\\\"", remotePath, PC_GDH_PATH);
                         if (ExecuteADBCommand(command, NULL, 0)) {
                             AppendToLogs("Pulled replay:"); AppendToLogs(filename);
                             successCount++;
                         } else {
                             AppendToLogs("Failed to pull replay:"); AppendToLogs(filename);
                         }
                     } else {
                          AppendToLogs("Skipped replay (up-to-date):"); AppendToLogs(filename);
                          skipCount++;
                     }
                 }
                 token = strtok(NULL, "\n");
             }
        } else {
             AppendToLogs("Failed to list remote GDH replays.");
        }
    }
    char summary[100];
    sprintf(summary, "GDH Replays Sync Summary: %d synced, %d skipped.", successCount, skipCount);
    AppendToLogs(summary);
}


void ShowSettingsDialog() {
    if (hwndSettings && IsWindow(hwndSettings)) {
         SetForegroundWindow(hwndSettings);
         return;
    }

    hwndSettings = CreateWindowEx(
        WS_EX_DLGMODALFRAME,
        "GDSyncSettingsClass",
        "GDSync Settings",
        WS_POPUP | WS_CAPTION | WS_SYSMENU | WS_VISIBLE,
         (GetSystemMetrics(SM_CXSCREEN) - 500) / 2,
         (GetSystemMetrics(SM_CYSCREEN) - 400) / 2, // Centered
        500, 400,
        hwndMain, NULL, GetModuleHandle(NULL), NULL);

    if (hwndSettings == NULL) {
        MessageBox(NULL, "Settings dialog creation failed!", "Error", MB_ICONERROR | MB_OK);
        return;
    }

    int yPos = 10;
    CreateWindow("STATIC", "PC Geometry Dash Path:", WS_VISIBLE | WS_CHILD, 10, yPos + 5, 180, 20, hwndSettings, NULL, NULL, NULL);
    CreateWindowEx(WS_EX_CLIENTEDGE,"EDIT", PC_GD_PATH, WS_VISIBLE | WS_CHILD | WS_BORDER | ES_AUTOHSCROLL, 10, yPos + 25, 460, 25, hwndSettings, (HMENU)ID_SETTINGS_PC_GD_EDIT, NULL, NULL);
    yPos += 50;

    CreateWindow("STATIC", "Phone Geometry Dash Path:", WS_VISIBLE | WS_CHILD, 10, yPos + 5, 180, 20, hwndSettings, NULL, NULL, NULL);
    CreateWindowEx(WS_EX_CLIENTEDGE,"EDIT", PHONE_GD_PATH, WS_VISIBLE | WS_CHILD | WS_BORDER | ES_AUTOHSCROLL, 10, yPos + 25, 460, 25, hwndSettings, (HMENU)ID_SETTINGS_PHONE_GD_EDIT, NULL, NULL);
    yPos += 50;

     CreateWindow("STATIC", "--- Pro Settings ---", WS_VISIBLE | WS_CHILD | SS_CENTER, 10, yPos, 460, 20, hwndSettings, NULL, NULL, NULL);
     yPos += 30;

     HWND hwndPCGeodeLabel = CreateWindow("STATIC", "PC Geode Mods Path:", WS_VISIBLE | WS_CHILD, 10, yPos+5, 180, 20, hwndSettings, NULL, NULL, NULL);
     HWND hwndPCGeodeEdit = CreateWindowEx(WS_EX_CLIENTEDGE,"EDIT", PC_GEODE_PATH, WS_VISIBLE | WS_CHILD | WS_BORDER | ES_AUTOHSCROLL, 10, yPos+25, 460, 25, hwndSettings, (HMENU)ID_SETTINGS_PC_GEODE_EDIT, NULL, NULL);
     yPos += 50;

     HWND hwndPhoneGeodeLabel = CreateWindow("STATIC", "Phone Geode Mods Path:", WS_VISIBLE | WS_CHILD, 10, yPos+5, 180, 20, hwndSettings, NULL, NULL, NULL);
     HWND hwndPhoneGeodeEdit = CreateWindowEx(WS_EX_CLIENTEDGE,"EDIT", PHONE_GEODE_PATH, WS_VISIBLE | WS_CHILD | WS_BORDER | ES_AUTOHSCROLL, 10, yPos+25, 460, 25, hwndSettings, (HMENU)ID_SETTINGS_PHONE_GEODE_EDIT, NULL, NULL);
     yPos += 50;

     HWND hwndPCGDHLabel = CreateWindow("STATIC", "PC GDH Replays Path:", WS_VISIBLE | WS_CHILD, 10, yPos+5, 180, 20, hwndSettings, NULL, NULL, NULL);
     HWND hwndPCGDHEdit = CreateWindowEx(WS_EX_CLIENTEDGE,"EDIT", PC_GDH_PATH, WS_VISIBLE | WS_CHILD | WS_BORDER | ES_AUTOHSCROLL, 10, yPos+25, 460, 25, hwndSettings, (HMENU)ID_SETTINGS_PC_GDH_EDIT, NULL, NULL);
     yPos += 50;

     HWND hwndPhoneGDHLabel = CreateWindow("STATIC", "Phone GDH Replays Path:", WS_VISIBLE | WS_CHILD, 10, yPos+5, 180, 20, hwndSettings, NULL, NULL, NULL);
     HWND hwndPhoneGDHEdit = CreateWindowEx(WS_EX_CLIENTEDGE,"EDIT", PHONE_GDH_PATH, WS_VISIBLE | WS_CHILD | WS_BORDER | ES_AUTOHSCROLL, 10, yPos+25, 460, 25, hwndSettings, (HMENU)ID_SETTINGS_PHONE_GDH_EDIT, NULL, NULL);
     yPos += 50;

     EnableWindow(hwndPCGeodeLabel, PRO_ENABLED);
     EnableWindow(hwndPCGeodeEdit, PRO_ENABLED);
     EnableWindow(hwndPhoneGeodeLabel, PRO_ENABLED);
     EnableWindow(hwndPhoneGeodeEdit, PRO_ENABLED);
     EnableWindow(hwndPCGDHLabel, PRO_ENABLED);
     EnableWindow(hwndPCGDHEdit, PRO_ENABLED);
     EnableWindow(hwndPhoneGDHLabel, PRO_ENABLED);
     EnableWindow(hwndPhoneGDHEdit, PRO_ENABLED);


    CreateWindow("BUTTON", "Save", WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON, 190, yPos + 10, 120, 30, hwndSettings, (HMENU)ID_SETTINGS_SAVE_BUTTON, NULL, NULL);

    ShowWindow(hwndSettings, SW_SHOW);
    EnableWindow(hwndMain, FALSE); // Disable main window while settings are open
}

LRESULT CALLBACK SettingsProc(HWND hwndDlg, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_COMMAND:
            if (LOWORD(wParam) == ID_SETTINGS_SAVE_BUTTON) {
                char tempPath[MAX_PATH];

                GetDlgItemText(hwndDlg, ID_SETTINGS_PC_GD_EDIT, tempPath, MAX_PATH); strcpy(PC_GD_PATH, tempPath);
                GetDlgItemText(hwndDlg, ID_SETTINGS_PHONE_GD_EDIT, tempPath, MAX_PATH); strcpy(PHONE_GD_PATH, tempPath);

                if (PRO_ENABLED) {
                     GetDlgItemText(hwndDlg, ID_SETTINGS_PC_GEODE_EDIT, tempPath, MAX_PATH); strcpy(PC_GEODE_PATH, tempPath);
                     GetDlgItemText(hwndDlg, ID_SETTINGS_PHONE_GEODE_EDIT, tempPath, MAX_PATH); strcpy(PHONE_GEODE_PATH, tempPath);
                     GetDlgItemText(hwndDlg, ID_SETTINGS_PC_GDH_EDIT, tempPath, MAX_PATH); strcpy(PC_GDH_PATH, tempPath);
                     GetDlgItemText(hwndDlg, ID_SETTINGS_PHONE_GDH_EDIT, tempPath, MAX_PATH); strcpy(PHONE_GDH_PATH, tempPath);
                }

                SaveConfiguration();
                DestroyWindow(hwndDlg);
            }
            break;
        case WM_CLOSE:
            DestroyWindow(hwndDlg);
            break;
        case WM_DESTROY:
             EnableWindow(hwndMain, TRUE);
             SetForegroundWindow(hwndMain);
             hwndSettings = NULL; // Reset handle
            break;
        default:
            return DefWindowProc(hwndDlg, msg, wParam, lParam);
    }
    return 0;
}


void ShowActivationDialog() {
     if (PRO_ENABLED) {
         MessageBox(hwndMain, "Pro version is already activated!", "Pro Status", MB_ICONINFORMATION | MB_OK);
         return;
     }
     if (hwndActivatePro && IsWindow(hwndActivatePro)) {
          SetForegroundWindow(hwndActivatePro);
          return;
     }

    hwndActivatePro = CreateWindowEx(
        WS_EX_DLGMODALFRAME,
        "GDSyncActivationClass",
        "Activate GDSync Pro",
        WS_POPUP | WS_CAPTION | WS_SYSMENU | WS_VISIBLE,
         (GetSystemMetrics(SM_CXSCREEN) - 350) / 2,
         (GetSystemMetrics(SM_CYSCREEN) - 180) / 2,
        350, 180,
        hwndMain, NULL, GetModuleHandle(NULL), NULL);

     if (hwndActivatePro == NULL) {
        MessageBox(NULL, "Activation dialog creation failed!", "Error", MB_ICONERROR | MB_OK);
        return;
    }

     CreateWindow("STATIC", "Enter License Key:", WS_VISIBLE | WS_CHILD, 10, 20, 150, 20, hwndActivatePro, NULL, NULL, NULL);
     CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_VISIBLE | WS_CHILD | WS_BORDER, 10, 45, 310, 25, hwndActivatePro, (HMENU)ID_ACTIVATE_KEY_EDIT, NULL, NULL);

     CreateWindow("BUTTON", "Activate", WS_VISIBLE | WS_CHILD | BS_DEFPUSHBUTTON, 30, 90, 120, 30, hwndActivatePro, (HMENU)ID_ACTIVATE_OK_BUTTON, NULL, NULL);
     CreateWindow("BUTTON", "Get Activation Code", WS_VISIBLE | WS_CHILD | BS_PUSHBUTTON, 180, 90, 140, 30, hwndActivatePro, (HMENU)ID_ACTIVATE_GET_CODE_BUTTON, NULL, NULL);


     ShowWindow(hwndActivatePro, SW_SHOW);
     EnableWindow(hwndMain, FALSE);
}


LRESULT CALLBACK ActivationProc(HWND hwndDlg, UINT msg, WPARAM wParam, LPARAM lParam) {
     switch (msg) {
        case WM_COMMAND:
             switch(LOWORD(wParam)) {
                 case ID_ACTIVATE_OK_BUTTON:
                     {
                         char enteredKey[100];
                         GetDlgItemText(hwndDlg, ID_ACTIVATE_KEY_EDIT, enteredKey, sizeof(enteredKey));

                         if (strlen(enteredKey) == 0) {
                              MessageBox(hwndDlg, "Please enter a license key.", "Input Required", MB_ICONWARNING | MB_OK);
                              break;
                         }

                         bool valid = false;
                         for (int i = 0; i < NUM_VALID_KEYS; i++) {
                             if (strcmp(enteredKey, VALID_KEYS[i]) == 0) {
                                 valid = true;
                                 break;
                             }
                         }

                         if (valid) {
                             strcpy(LICENSE_KEY, enteredKey);
                             PRO_ENABLED = true;
                             SaveLicense();
                             UpdateUIForProStatus();
                             MessageBox(hwndDlg, "Activation Successful! Pro features are now active.", "Success", MB_ICONINFORMATION | MB_OK);
                             DestroyWindow(hwndDlg);
                         } else {
                              MessageBox(hwndDlg, "Invalid license key. Please check the key and try again.", "Invalid Key", MB_ICONERROR | MB_OK);
                         }
                     }
                     break;
                 case ID_ACTIVATE_GET_CODE_BUTTON:
                     OpenActivationCodePage();
                     break;
             }
            break;
        case WM_CLOSE:
             DestroyWindow(hwndDlg);
             break;
         case WM_DESTROY:
             EnableWindow(hwndMain, TRUE);
             SetForegroundWindow(hwndMain);
             hwndActivatePro = NULL;
            break;
         default:
            return DefWindowProc(hwndDlg, msg, wParam, lParam);
     }
     return 0;
}


void OpenDonationPage() {
    ShellExecute(NULL, "open", "https://ko-fi.com/MalikHw47", NULL, NULL, SW_SHOWNORMAL);
}

void OpenActivationCodePage() {
     ShellExecute(NULL, "open", "https://ko-fi.com/s/ca68e585d2", NULL, NULL, SW_SHOWNORMAL);
}


LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_COMMAND:
            switch (LOWORD(wParam)) {
                case ID_SYNC_BUTTON:
                    SyncData();
                    break;
                case ID_SETTINGS_BUTTON:
                    ShowSettingsDialog();
                    break;
                case ID_DONATE_BUTTON:
                    OpenDonationPage();
                    break;
                case ID_ACTIVATE_PRO_BUTTON:
                    ShowActivationDialog();
                     break;
                case ID_PHONE_TO_PC_RADIO:
                case ID_PC_TO_PHONE_RADIO:
                     CheckRadioButton(hwnd, ID_PHONE_TO_PC_RADIO, ID_PC_TO_PHONE_RADIO, LOWORD(wParam));
                     break;
                 case ID_ONLY_USERDATA_RADIO:
                 case ID_ALL_DATA_RADIO:
                      CheckRadioButton(hwnd, ID_ONLY_USERDATA_RADIO, ID_ALL_DATA_RADIO, LOWORD(wParam));
                      break;
            }
            break;
        case WM_CLOSE:
            DestroyWindow(hwnd);
            break;
        case WM_DESTROY:
            PostQuitMessage(0);
            break;
        default:
            return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
}
