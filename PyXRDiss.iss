#define MyAppName "PyXRD"
#define MyAppVersion "0.6.2"
#define OutputDir ".\dist"
#define DepDir ".\dist\deps"

;
; Simple Inno Setup file that wraps the Python installer with PyXRD's automated
; script.
; This has been tested on a clean Windows 7 system.
;

[Setup]
PrivilegesRequired=admin
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename={#MyAppName}-{#MyAppVersion}-win32-bundle
Compression=lzma
SolidCompression=yes
DisableDirPage=yes
OutputDir="{#OutputDir}"

[Files]                                                                                            
Source: "{#DepDir}\python-2.7.8.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\ez_setup.py"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\install_numpy_scipy.py"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\cpuinfo.py"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\numpy-1.7.0-nosse.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\numpy-1.7.0-sse2.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\numpy-1.7.0-sse3.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\scipy-0.14.0-nosse.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\scipy-0.14.0-sse2.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\scipy-0.14.0-sse3.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\pywin32-219.win32-py2.7.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\pygtk-all-in-one-2.24.2.win32-py2.7.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\pyparsing-2.0.3.win32-py2.7.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\matplotlib-1.2.1.win32-py2.7.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#OutputDir}\PyXRD-0.6.2.win32-py2.7.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
                                           
[Run]
StatusMsg: "Installing Python";     Filename: "msiexec.exe";                          Parameters: "/i ""{tmp}\python-2.7.8.msi"" /passive ALLUSERS=1 TARGETDIR=""C:\Python27"""; Flags: runasoriginaluser;
StatusMsg: "Installing Setuptools"; Filename: "C:\Python27\Python.exe";               Parameters: """{tmp}\ez_setup.py"""; Flags: runascurrentuser;
StatusMsg: "Installing Pip";        Filename: "C:\Python27\Scripts\easy_install.exe"; Parameters: "pip"; Flags: runascurrentuser;
StatusMsg: "Installing Pywin32";    Filename: "C:\Python27\Scripts\easy_install.exe"; Parameters: """{tmp}\pywin32-219.win32-py2.7.exe"""; Flags: runascurrentuser;
StatusMsg: "Installing Pywin32";    Filename: "C:\Python27\python.exe";               Parameters: """C:\Python27\Scripts\pywin32_postinstall.py"" -install"; Flags: runascurrentuser;
StatusMsg: "Installing PyGTK";      Filename: "msiexec.exe";                          Parameters: "/i ""{tmp}\pygtk-all-in-one-2.24.2.win32-py2.7.msi"" /passive ALLUSERS=1 TARGETDIR=""C:\Python27"""; Flags: runasoriginaluser;
StatusMsg: "Installing Numpy & Scipy"; Filename: "C:\Python27\Python.exe";  Parameters: """{tmp}\install_numpy_scipy.py"""; Flags: runascurrentuser;
StatusMsg: "Installing Pyparsing";  Filename: "C:\Python27\Scripts\easy_install.exe"; Parameters: """{tmp}\pyparsing-2.0.3.win32-py2.7.exe"""; Flags: runascurrentuser;
StatusMsg: "Installing Matplotlib"; Filename: "C:\Python27\Scripts\easy_install.exe"; Parameters: """{tmp}\matplotlib-1.2.1.win32-py2.7.exe"""; Flags: runascurrentuser;
StatusMsg: "Installing PyXRD";      Filename: "C:\Python27\Scripts\easy_install.exe"; Parameters: """{tmp}\PyXRD-0.6.2.win32-py2.7.exe"""; Flags: runascurrentuser;
StatusMsg: "Installing PyXRD";      Filename: "C:\Python27\Python.exe"; Parameters: """C:\Python27\Lib\site-packages\{#MyAppName}-{#MyAppVersion}-py2.7-win32.egg\EGG-INFO\scripts\win32_pyxrd_post_install.py"" -install"; Flags: runascurrentuser waituntilterminated;

[UninstallDelete]
Type: files; Name: "{win}\MYPROG.INI"
