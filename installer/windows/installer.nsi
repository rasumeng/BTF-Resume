; BTF Resume NSIS Installer Script
; Requires NSIS 3.x

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Application Info
!define APPNAME "BT Resume"
!define COMPANYNAME "BTF"
!define DESCRIPTION "A free, local AI resume helper - Polish, Tailor, and Format your resume privately on your own machine."
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://github.com/rasumeng/BT-Resume"
!define UPDATEURL "https://github.com/rasumeng/BT-Resume/releases"
!define ABOUTURL "https://github.com/rasumeng/BT-Resume"

; Installer Settings
Name "${APPNAME}"
OutFile "BT-Resume-Setup.exe"
InstallDir "$PROGRAMFILES64\${APPNAME}"
InstallDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" "InstallDir"
RequestExecutionLevel admin

; Compression
SetCompressor /SOLID lzma

; Interface Settings
!define MUI_ICON "..\..\flutter_app\windows\runner\resources\app_icon.ico"
!define MUI_UNICON "..\..\flutter_app\windows\runner\resources\app_icon.ico"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${APPNAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of ${APPNAME}.$\r$\n$\r$\n${DESCRIPTION}$\r$\n$\r$\nClick Next to continue."
!define MUI_FINISHPAGE_RUN "$INSTDIR\btf_resume.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APPNAME}"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version Info
VIProductVersion "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.0"
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "${APPNAME}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "${COMPANYNAME}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "${DESCRIPTION}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"

; Installer Section
Section "Install"
    SetOutPath $INSTDIR

    ; Copy all files from Release folder
    File /r "..\..\flutter_app\build\windows\x64\runner\Release\*.*"

    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\btf_resume.exe"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"

    ; Create Desktop shortcut
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\btf_resume.exe"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Write registry keys for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\btf_resume.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1

    ; Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" "$0"

    ; Store install directory
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" "InstallDir" "$INSTDIR"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Ask user if they want to keep user data
    MessageBox MB_YESNO "Do you want to keep your saved resumes and settings?$\r$\n$\r$\nClick YES to keep your data (stored in Documents/BT Resume)$\r$\nClick NO to remove all data" IDNO RemoveUserData IDYES KeepUserData

    RemoveUserData:
        ; Remove user data folder if it exists
        RMDir /r "$DOCUMENTS\BTFResume"
        RMDir /r "$DOCUMENTS\BT Resume"
        goto ContinueUninstall

    KeepUserData:
        ; Just remove the app installation directory
        ; User data in Documents is preserved
        goto ContinueUninstall

    ContinueUninstall:
        ; Remove Start Menu shortcuts
        Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
        Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
        RMDir "$SMPROGRAMS\${APPNAME}"

        ; Remove Desktop shortcut
        Delete "$DESKTOP\${APPNAME}.lnk"

        ; Remove installation directory (files only, not user data)
        RMDir /r "$INSTDIR"

        ; Remove registry keys
        DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
        DeleteRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}"
SectionEnd