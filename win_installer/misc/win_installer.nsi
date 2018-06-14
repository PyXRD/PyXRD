; Copyright 2016 Christoph Reiter
;
; This program is free software; you can redistribute it and/or modify
; it under the terms of the GNU General Public License as published by
; the Free Software Foundation; either version 2 of the License, or
; (at your option) any later version.

Unicode true

!define PYXRD_NAME "PyXRD"
!define PYXRD_ID "pyxrd"
!define PYXRD_DESC "X-ray diffraction analysis of disordered lamellar structures"
!define PYXRD_PUBLISHER "Ghent University"

!define PYXRD_WEBSITE "https://github.com/mathijs-dumon/PyXRD"

!define PYXRD_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PYXRD_NAME}"
!define PYXRD_INSTDIR_KEY "Software\${PYXRD_NAME}"
!define PYXRD_INSTDIR_VALUENAME "InstDir"

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "${PYXRD_NAME} (${VERSION})"
OutFile "pyxrd-LATEST.exe"
SetCompressor /SOLID /FINAL lzma
SetCompressorDictSize 32
InstallDir "$PROGRAMFILES\${PYXRD_NAME}"
RequestExecutionLevel admin

Var PYXRD_INST_BIN
Var UNINST_BIN

!define MUI_ABORTWARNING
!define MUI_ICON "pyxrd.ico"

!insertmacro MUI_PAGE_LICENSE "pyxrd\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetShellVarContext all

    ; Use this to make things faster for testing installer changes
    ;~ SetOutPath "$INSTDIR\bin"
    ;~ File /r "mingw32\bin\*.exe"

    SetOutPath "$INSTDIR"
    File /r "mingw32\*.*"

    ; Store installation folder
    WriteRegStr HKLM "${PYXRD_INSTDIR_KEY}" "${PYXRD_INSTDIR_VALUENAME}" $INSTDIR

    ; Set up an entry for the uninstaller
    WriteRegStr HKLM "${PYXRD_UNINST_KEY}" \
        "DisplayName" "${PYXRD_NAME} - ${PYXRD_DESC}"
    WriteRegStr HKLM "${PYXRD_UNINST_KEY}" "DisplayIcon" "$\"$PYXRD_INST_BIN$\""
    WriteRegStr HKLM "${PYXRD_UNINST_KEY}" "UninstallString" \
        "$\"$UNINST_BIN$\""
    WriteRegStr HKLM "${PYXRD_UNINST_KEY}" "QuietUninstallString" \
    "$\"$UNINST_BIN$\" /S"
    WriteRegStr HKLM "${PYXRD_UNINST_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${PYXRD_UNINST_KEY}" "HelpLink" "${PYXRD_WEBSITE}"
    WriteRegStr HKLM "${PYXRD_UNINST_KEY}" "Publisher" "${PYXRD_PUBLISHER}"
    WriteRegStr HKLM "${PYXRD_UNINST_KEY}" "DisplayVersion" "${VERSION}"
    WriteRegDWORD HKLM "${PYXRD_UNINST_KEY}" "NoModify" 0x1
    WriteRegDWORD HKLM "${PYXRD_UNINST_KEY}" "NoRepair" 0x1
    ; Installation size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${PYXRD_UNINST_KEY}" "EstimatedSize" "$0"

    ; Register a default entry for file extensions
    WriteRegStr HKLM "Software\Classes\${PYXRD_ID}.assoc.ANY\shell\open\command" "" "$\"$PYXRD_INST_BIN$\" $\"%1$\""
    WriteRegStr HKLM "Software\Classes\${PYXRD_ID}.assoc.ANY\DefaultIcon" "" "$\"$PYXRD_INST_BIN$\""
    WriteRegStr HKLM "Software\Classes\${PYXRD_ID}.assoc.ANY\shell\open" "FriendlyAppName" "${PYXRD_NAME}"

    ; Add application entry
    WriteRegStr HKLM "Software\${PYXRD_NAME}\${PYXRD_ID}\Capabilities" "ApplicationDescription" "${PYXRD_DESC}"
    WriteRegStr HKLM "Software\${PYXRD_NAME}\${PYXRD_ID}\Capabilities" "ApplicationName" "${PYXRD_NAME}"

    ; Register supported file extensions
    ; (generated using gen_supported_types.py)
    !define PYXRD_ASSOC_KEY "Software\${PYXRD_NAME}\${PYXRD_ID}\Capabilities\FileAssociations"
    WriteRegStr HKLM "${PYXRD_ASSOC_KEY}" ".pyxrd" "${PYXRD_ID}.assoc.ANY"

    ; Register application entry
    WriteRegStr HKLM "Software\RegisteredApplications" "${PYXRD_NAME}" "Software\${PYXRD_NAME}\${PYXRD_ID}\Capabilities"

    ; Register app paths
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\pyxrd.exe" "" "$PYXRD_INST_BIN"

    ; Create uninstaller
    WriteUninstaller "$UNINST_BIN"

    ; Create start menu shortcuts
    CreateDirectory "$SMPROGRAMS\${PYXRD_NAME}"
    CreateShortCut "$SMPROGRAMS\${PYXRD_NAME}\${PYXRD_NAME}.lnk" "$PYXRD_INST_BIN"
SectionEnd

Function .onInit
    ; Read the install dir and set it
    Var /GLOBAL instdir_temp
    ReadRegStr $instdir_temp HKLM "${PYXRD_INSTDIR_KEY}" "${PYXRD_INSTDIR_VALUENAME}"
    StrCmp $instdir_temp "" skip 0
        StrCpy $INSTDIR $instdir_temp
    skip:

    StrCpy $PYXRD_INST_BIN "$INSTDIR\bin\pyxrd.exe"
    StrCpy $UNINST_BIN "$INSTDIR\uninstall.exe"

    ; try to un-install existing installations first
    IfFileExists "$INSTDIR" do_uninst do_continue
    do_uninst:
        ; instdir exists
        IfFileExists "$UNINST_BIN" exec_uninst rm_instdir
        exec_uninst:
            ; uninstall.exe exists, execute it and
            ; if it returns success proceede, otherwise abort the
            ; installer (uninstall aborted by user for example)
            ExecWait '"$UNINST_BIN" _?=$INSTDIR' $R1
            ; uninstall suceeded, since the uninstall.exe is still there
            ; goto rm_instdir as well
            StrCmp $R1 0 rm_instdir
            ; uninstall failed
            Abort
        rm_instdir:
            ; either the uninstaller was sucessfull or
            ; the uninstaller.exe wasn't found
            RMDir /r "$INSTDIR"
    do_continue:
        ; the instdir shouldn't exist from here on
FunctionEnd

Section "Uninstall"
    SetShellVarContext all
    SetAutoClose true

    ; Remove start menu entries
    Delete "$SMPROGRAMS\${PYXRD_NAME}\${PYXRD_NAME}.lnk"
    RMDir "$SMPROGRAMS\${PYXRD_NAME}"

    ; Remove application registration and file assocs
    DeleteRegKey HKLM "Software\Classes\${PYXRD_ID}.assoc.ANY"
    DeleteRegKey HKLM "Software\${PYXRD_NAME}"
    DeleteRegValue HKLM "Software\RegisteredApplications" "${PYXRD_NAME}"

    ; Remove app paths
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\pyxrd.exe"

    ; Delete installation related keys
    DeleteRegKey HKLM "${PYXRD_UNINST_KEY}"
    DeleteRegKey HKLM "${PYXRD_INSTDIR_KEY}"

    ; Delete files
    RMDir /r "$INSTDIR"
SectionEnd
