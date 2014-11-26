#define MyAppName "PyXRD"
#define MyAppVersion "0.6.2"

;
; Simple Inno Setup file that wraps the Python installer with PyXRD's automated
; script.
; This has been tested on a clean Windows 7 system.
;

[Setup]
PrivilegesRequired=Admin
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename={#MyAppName}-{#MyAppVersion}-setup
Compression=lzma
SolidCompression=yes
DisableDirPage=yes
OutputDir="dist\"

[Files]                                                                                            
Source: ".\dist\python-2.7.8.msi"; DestDir: "{tmp}"; Flags: nocompression deleteafterinstall       
Source: ".\win32_pyxrd_installation.py"; DestDir: "{tmp}"; Flags: nocompression deleteafterinstall

[Run]
Filename: "msiexec.exe"; Parameters: "/i ""{tmp}\python-2.7.8.msi""";
Filename: "C:\Python27\Python.exe"; Parameters: """{tmp}\win32_pyxrd_installation.py"" restarted";

