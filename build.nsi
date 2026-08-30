!include "MUI2.nsh"

!define MUI_ICON "d:/Crack.exe 2/Setup/sfx builder/nsis/1.2/bin/icons/pack.ico"
!define MUI_UNICON "d:/Crack.exe 2/Setup/sfx builder/nsis/1.2/bin/icons/pack.ico"




!define MUI_WELCOMEFINISHPAGE_BITMAP "C:\Program Files (x86)\NSIS\Contrib\Graphics\Wizard\orange-nsis.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "C:\Program Files (x86)\NSIS\Contrib\Graphics\Wizard\orange-nsis.bmp"

!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "C:\Program Files (x86)\NSIS\Contrib\Graphics\Header\orange-r-nsis.bmp"
!define MUI_HEADERIMAGE_RIGHT

!define SOFTNAME "Cpu Meter v14"

Name "${SOFTNAME}"
OutFile "${SOFTNAME}.exe"
InstallDir "C:\CPU METER\"


ShowInstDetails show
ShowUninstDetails show
AutoCloseWindow false

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
; get sources files 
Section "Install"
    SetOutPath "$INSTDIR"
    File /r "D:\Soft_Win\CPU METER\*"
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    ; Desktop shortcut
    CreateShortcut "$DESKTOP\monitor.lnk" "$INSTDIR\monitor.exe"
    ; Create uninstall registry entry
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${SOFTNAME}" "DisplayName" "${SOFTNAME}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${SOFTNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${SOFTNAME}" "InstallLocation" "$INSTDIR"

SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\uninstall.exe"
    Delete "$DESKTOP\monitor.lnk"
    RMDir /r "$INSTDIR"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${SOFTNAME}"
SectionEnd


