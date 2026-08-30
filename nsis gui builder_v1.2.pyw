import os
import random
import subprocess
import threading
import re
import FreeSimpleGUI as sg

# v1.2 DIMM_V2


THEMES = [
    "DarkBrown3",
    "DarkTeal11",
    "DarkGray7",
    "DarkGrey5",
    "DarkGrey7",
]

theme = random.choice(THEMES)
sg.theme(theme)
print(theme)


# NSIS Theme SET
wizard_bmp = r"C:\Program Files (x86)\NSIS\Contrib\Graphics\Wizard\orange-nsis.bmp"
header_bmp = r"C:\Program Files (x86)\NSIS\Contrib\Graphics\Header\orange-r-nsis.bmp"


# Check required files and folders
def check_required_folders():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    missing = []

    for item in ["bin"]:
        if not os.path.isdir(os.path.join(script_dir, item)):
            missing.append(item)

    if not os.path.isfile(os.path.join(script_dir, "build.nsi")):
        missing.append("build.nsi")

    if missing:
        sg.popup_ok("Missing required files/folders:\n\n" + "\n".join(missing))
        raise SystemExit


check_required_folders()


# Load the last source, install folder and project name from build.nsi
def load_last_values():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    nsi_path = os.path.join(script_dir, "build.nsi")

    src = r".\src"
    dst = r".\_installed"
    project = "Installer"

    with open(nsi_path, "r", encoding="utf-8") as f:
        nsi = f.read()

    # Read: !define SOFTNAME "..."
    m = re.search(r'^!define\s+SOFTNAME\s+"(.+?)"', nsi, re.MULTILINE)
    if m:
        project = m.group(1)

    # Read: File /r "...\\*"
    m = re.search(r'^\s*File\s+/r\s+"(.+?)\\+\*"', nsi, re.MULTILINE)
    if m:
        src = m.group(1)

    # Read: InstallDir "..."
    m = re.search(r'^\s*InstallDir\s+"(.+?)"', nsi, re.MULTILINE)
    if m:
        dst = m.group(1)
        if dst.startswith("$EXEDIR\\"):
            dst = ".\\" + dst[len("$EXEDIR\\"):]

    return project, src, dst

LAST_PROJECT, LAST_SRC, LAST_DST = load_last_values()

layout = [
    [
        sg.Text("Project Name", size=(12, 1)),
        sg.Input(LAST_PROJECT, key="-PROJECTNAME-", size=(55, 1))
    ],
    [
        sg.Text("Source folder", size=(12, 1)),
        sg.Input(LAST_SRC, key="-SRC-", size=(55, 1))
    ],
    [
        sg.Text("Install folder", size=(12, 1)),
        sg.Input(LAST_DST, key="-DST-", size=(55, 1))
    ],
    [
        sg.Text("Icon file", size=(12, 1)),
        sg.Input(r".\bin\icons\pack.ico", key="-ICON-", size=(30, 1))
    ],
    [
        sg.Text("Desktop shortcut", size=(12, 1)),
        sg.Checkbox("Create", default=True, key="-SHORTCUT-")
    ],
    [
        sg.Text("Shortcut EXE", size=(12, 1)),
        sg.Input("monitor.exe", key="-SHORTCUT-EXE-", size=(30, 1))
    ],
    [
        sg.Text("Status:", size=(6, 1)),
        sg.Text("⬤", key="-STATUS-DOT-"),
        sg.Text("Ready", key="-STATUS-", size=(46, 1), pad=((0, 0), (1, 0)))
    ],
    [
        sg.Multiline(
            "",
            size=(75, 12),
            key="-LOG-",
            autoscroll=True,
            disabled=True
        )
    ],
    [
        sg.Push(),
        sg.Button("Create NSIS File", key="-BUILD-"),
        sg.Button("Test Installer", key="-TEST-"),
        sg.Button("Exit")
    ]
]

window = sg.Window("NSIS Builder", layout)


# Update the status indicator
def set_status(text, color):
    window["-STATUS-DOT-"].update(text_color=color)
    window["-STATUS-"].update(text)


# Update all editable values inside build.nsi
def update_nsi(nsi, project_name, src, set_out, icon_nsis, create_shortcut, shortcut_exe):

    # Shortcut name without .exe
    shortcut_name = os.path.splitext(shortcut_exe)[0]

    nsi = (
        nsi.replace("__ICON__", icon_nsis)
           .replace("__WIZARD_BMP__", wizard_bmp)
           .replace("__HEADER_BMP__", header_bmp)
    )

    # Replace one NSIS line
    def replace_line(pattern, new_line):
        nonlocal nsi
        nsi = re.sub(
            pattern,
            lambda m: new_line,
            nsi,
            count=1,
            flags=re.MULTILINE
        )

    # Desktop shortcut line
    if create_shortcut:
        shortcut_line = (
            f'CreateShortcut "$DESKTOP\\{shortcut_name}.lnk" '
            f'"$INSTDIR\\{shortcut_exe}"'
        )
    else:
        shortcut_line = "; CreateShortcut disabled"

    
    replace_line(
    r'^\s*Delete\s+"\$DESKTOP\\.*\.lnk"$',
    f'    Delete "$DESKTOP\\{shortcut_name}.lnk"'
)

    # Replace: File /r
    replace_line(
        r'^\s*File\s+/r\s+".*"$',
        f'    File /r "{src}\\*"'
    )

    # Replace: CreateShortcut
    replace_line(
        r'^\s*CreateShortcut\s+".*"$|^\s*;\s*CreateShortcut.*$',
        f'    {shortcut_line}'
    )

    # Replace: !define SOFTNAME
    replace_line(
        r'^!define\s+SOFTNAME\s+".*"$',
        f'!define SOFTNAME "{project_name}"'
    )

    # Replace: InstallDir
    replace_line(
        r'^\s*InstallDir\s+".*"$',
        f'InstallDir "{set_out}"'
    )
    
    
    # Replace: MUI_ICON
    replace_line(
        r'^!define\s+MUI_ICON\s+".*"$',
        f'!define MUI_ICON "{icon_nsis}"'
    )

    # Replace: MUI_UNICON
    replace_line(
        r'^!define\s+MUI_UNICON\s+".*"$',
        f'!define MUI_UNICON "{icon_nsis}"'
    )
    
    

    return nsi




# Build the NSIS installer
def build(project_name, src, dst, icon, create_shortcut, shortcut_exe):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    nsi_path = os.path.join(script_dir, "build.nsi")
    makensis = r"C:\Program Files (x86)\NSIS\Bin\makensis.exe"

    exe = f"{project_name}.exe"

    icon_path = os.path.abspath(os.path.join(script_dir, icon))
    icon_nsis = (
        icon_path.replace("\\", "/")
        if icon and os.path.isfile(icon_path)
        else ""
    )

    # Install path
    if os.path.isabs(dst):
        set_out = dst.replace("\\\\", "\\")
    else:
        install = dst.replace(".\\", "").replace("./", "").strip("\\/")
        set_out = f"$EXEDIR\\{install}"

    if not os.path.isfile(nsi_path):
        window.write_event_value(
            "-DONE-",
            ("error", f"Missing template:\n{nsi_path}")
        )
        return

    with open(nsi_path, "r", encoding="utf-8") as f:
        nsi = f.read()

    nsi = update_nsi(
        nsi,
        project_name,
        src,
        set_out,
        icon_nsis,
        create_shortcut,
        shortcut_exe,
    )

    with open(nsi_path, "w", encoding="utf-8") as f:
        f.write(nsi)

    window.write_event_value("-STATUS_EVENT-", ("Building EXE...", "yellow"))

    if not os.path.exists(makensis):
        window.write_event_value(
            "-DONE-",
            ("error", f"makensis.exe not found:\n{makensis}")
        )
        return

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    proc = subprocess.Popen(
        [makensis, nsi_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=script_dir,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    for line in proc.stdout:
        window.write_event_value("-LINE-", line.rstrip())

    proc.wait()

    if proc.returncode == 0:
        window.write_event_value(
            "-DONE-",
            ("ok", os.path.join(script_dir, exe))
        )
    else:
        window.write_event_value(
            "-DONE-",
            ("error", f"Build failed (code {proc.returncode})")
        )


while True:
    event, values = window.read(timeout=100)

    if event in (sg.WIN_CLOSED, "Exit"):
        break

    elif event == "-BUILD-":
        window["-BUILD-"].update(disabled=True)
        window["-LOG-"].update("")
        set_status("Creating NSIS script...", "yellow")

        threading.Thread(
            target=build,
            args=(
                values["-PROJECTNAME-"].strip(),
                values["-SRC-"].strip(),
                values["-DST-"].strip(),
                values["-ICON-"].strip(),
                values["-SHORTCUT-"],
                values["-SHORTCUT-EXE-"].strip(),
            ),
            daemon=True,
        ).start()

    elif event == "-TEST-":
        exe_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f'{values["-PROJECTNAME-"].strip()}.exe'
        )

        if os.path.isfile(exe_path):
            os.startfile(exe_path)
        else:
            sg.popup_error(f"Installer not found:\n{exe_path}")

    elif event == "-LINE-":
        window["-LOG-"].update(values["-LINE-"] + "\n", append=True)

    elif event == "-STATUS_EVENT-":
        text, color = values["-STATUS_EVENT-"]
        set_status(text, color)

    elif event == "-DONE-":
        window["-BUILD-"].update(disabled=False)

        status, msg = values["-DONE-"]

        if status == "ok":
            set_status("Done", "#00FF66")
            window["-LOG-"].update("\nBuild completed!\n", append=True)
            print("Build completed successfully.")
        else:
            set_status("Build failed", "red")
            window["-LOG-"].update("\nBuild failed!\n", append=True)
            sg.popup_error(msg)

window.close()