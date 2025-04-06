// GDSync for Windows - C GUI App using WinAPI
// Syncs Geometry Dash data between PC and Android device via ADB
// Requires: adb.exe in the same folder as this executable

#include <windows.h>
#include <shlobj.h> // For SHGetFolderPath
#include <stdio.h>
#include <stdlib.h>

#define ID_PUSH 1
#define ID_PULL 2
#define ID_USERDATA 3
#define ID_ALLFILES 4
#define ID_EXECUTE 5

HINSTANCE hInst;
HWND hwndMain, hwndDir, hwndMode, hwndStatus;
int syncDirection = ID_PUSH;
int syncMode = ID_USERDATA;

char adbPath[MAX_PATH];
char gdPath[MAX_PATH];
char phonePath[] = "/storage/emulated/0/Android/media/com.geode.launcher/save";
const char* userFiles[] = {"CCLocalLevels.dat", "CCLocalLevels2.dat", "CCGameManager.dat", "CCGameManager2.dat"};

void getLocalGDPath() {
    char localAppData[MAX_PATH];
    SHGetFolderPath(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, localAppData);
    sprintf(gdPath, "%s\\GeometryDash", localAppData);
}

void getADBPath() {
    GetModuleFileName(NULL, adbPath, MAX_PATH);
    char* lastSlash = strrchr(adbPath, '\\');
    if (lastSlash) *(lastSlash + 1) = '\0';
    strcat(adbPath, "adb.exe");
}

int adbDeviceConnected() {
    FILE* pipe = _popen("adb devices", "r");
    if (!pipe) return 0;
    char buffer[128];
    int found = 0;
    while (fgets(buffer, sizeof(buffer), pipe)) {
        if (strstr(buffer, "\tdevice")) {
            found = 1;
            break;
        }
    }
    _pclose(pipe);
    return found;
}

void showMessage(const char* title, const char* text) {
    MessageBox(hwndMain, text, title, MB_OK | MB_ICONINFORMATION);
}

void syncFiles() {
    if (!adbDeviceConnected()) {
        showMessage("Error", "No Android device connected. Make sure USB debugging is enabled.");
        return;
    }

    char cmd[MAX_PATH * 3];

    if (syncDirection == ID_PUSH) {
        for (int i = 0; i < (syncMode == ID_USERDATA ? 4 : 0); ++i) {
            sprintf(cmd, "\"%s\" push \"%s\\%s\" \"%s/\"", adbPath, gdPath, userFiles[i], phonePath);
            system(cmd);
        }
        if (syncMode == ID_ALLFILES) {
            sprintf(cmd, "\"%s\" push \"%s/*\" \"%s/\"", adbPath, gdPath, phonePath);
            system(cmd);
        }
        showMessage("Success", "Data pushed to phone!");
    } else {
        for (int i = 0; i < (syncMode == ID_USERDATA ? 4 : 0); ++i) {
            sprintf(cmd, "\"%s\" pull \"%s/%s\" \"%s\\\"", adbPath, phonePath, userFiles[i], gdPath);
            system(cmd);
        }
        if (syncMode == ID_ALLFILES) {
            sprintf(cmd, "\"%s\" pull \"%s/*\" \"%s\\\"", adbPath, phonePath, gdPath);
            system(cmd);
        }
        showMessage("Success", "Data pulled from phone!");
    }
}

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_CREATE:
            CreateWindow("STATIC", "Sync Direction:", WS_VISIBLE | WS_CHILD, 10, 10, 120, 20, hwnd, NULL, hInst, NULL);
            CreateWindow("BUTTON", "Push", WS_VISIBLE | WS_CHILD | BS_AUTORADIOBUTTON | WS_GROUP, 10, 30, 80, 20, hwnd, (HMENU)ID_PUSH, hInst, NULL);
            CreateWindow("BUTTON", "Pull", WS_VISIBLE | WS_CHILD | BS_AUTORADIOBUTTON, 100, 30, 80, 20, hwnd, (HMENU)ID_PULL, hInst, NULL);
            SendMessage(GetDlgItem(hwnd, ID_PUSH), BM_SETCHECK, BST_CHECKED, 0);

            CreateWindow("STATIC", "Sync Mode:", WS_VISIBLE | WS_CHILD, 10, 60, 120, 20, hwnd, NULL, hInst, NULL);
            CreateWindow("BUTTON", "User Data Only", WS_VISIBLE | WS_CHILD | BS_AUTORADIOBUTTON | WS_GROUP, 10, 80, 120, 20, hwnd, (HMENU)ID_USERDATA, hInst, NULL);
            CreateWindow("BUTTON", "All Files", WS_VISIBLE | WS_CHILD | BS_AUTORADIOBUTTON, 140, 80, 120, 20, hwnd, (HMENU)ID_ALLFILES, hInst, NULL);
            SendMessage(GetDlgItem(hwnd, ID_USERDATA), BM_SETCHECK, BST_CHECKED, 0);

            CreateWindow("BUTTON", "Execute", WS_VISIBLE | WS_CHILD, 10, 120, 100, 30, hwnd, (HMENU)ID_EXECUTE, hInst, NULL);
            break;

        case WM_COMMAND:
            switch (LOWORD(wParam)) {
                case ID_PUSH: syncDirection = ID_PUSH; break;
                case ID_PULL: syncDirection = ID_PULL; break;
                case ID_USERDATA: syncMode = ID_USERDATA; break;
                case ID_ALLFILES: syncMode = ID_ALLFILES; break;
                case ID_EXECUTE: syncFiles(); break;
            }
            break;

        case WM_DESTROY:
            PostQuitMessage(0);
            break;
        default:
            return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    hInst = hInstance;
    getLocalGDPath();
    getADBPath();

    WNDCLASS wc = {0};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = "GDSyncClass";
    RegisterClass(&wc);

    hwndMain = CreateWindow("GDSyncClass", "GDSync - Windows", WS_OVERLAPPEDWINDOW,
                            CW_USEDEFAULT, CW_USEDEFAULT, 300, 200,
                            NULL, NULL, hInstance, NULL);

    ShowWindow(hwndMain, nCmdShow);
    UpdateWindow(hwndMain);

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    return (int)msg.wParam;
}

