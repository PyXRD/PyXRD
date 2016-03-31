#define MyAppName "PyXRD"
#define MyAppVersion "|||VERSION|||"

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
Source: "{#DepDir}\python-2.7.11.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\pygtk-all-in-one-2.24.2.win32-py2.7.msi"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\scipy-0.17.0-cp27-none-win32.whl"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#DepDir}\numpy-1.11.0+mkl-cp27-cp27m-win32.whl"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "{#OutputDir}\PyXRD-{#MyAppVersion}-py2-none-any.whl"; DestDir: "{tmp}"; Flags: deleteafterinstall
                                           
[Run]
StatusMsg: "Installing Python";     Filename: "msiexec.exe";            Parameters: "/i ""{tmp}\python-2.7.11.msi"" /passive ALLUSERS=1 TARGETDIR=""C:\Python27"""; Flags: runasoriginaluser;
StatusMsg: "Installing PyGTK";      Filename: "msiexec.exe";            Parameters: "/i ""{tmp}\pygtk-all-in-one-2.24.2.win32-py2.7.msi"" /passive ALLUSERS=1 TARGETDIR=""C:\Python27"""; Flags: runasoriginaluser;
StatusMsg: "Installing Setuptools"; Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install -U pip setuptools"; Flags: runascurrentuser;
StatusMsg: "Installing Wheel";      Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install -U wheel"; Flags: runascurrentuser;
StatusMsg: "Installing Pyro";       Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install -U Pyro4"; Flags: runascurrentuser;
StatusMsg: "Installing Deap";       Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install -U deap"; Flags: runascurrentuser;
StatusMsg: "Installing Pywin32";    Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install -U pypiwin32"; Flags: runascurrentuser;
StatusMsg: "Installing Numpy";      Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install ""{tmp}\numpy-1.11.0+mkl-cp27-cp27m-win32.whl"""; Flags: runascurrentuser;
StatusMsg: "Installing Scipy";      Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install ""{tmp}\scipy-0.17.0-cp27-none-win32.whl"""; Flags: runascurrentuser;
StatusMsg: "Installing Pyparsing";  Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install -U pyparsing"; Flags: runascurrentuser;
StatusMsg: "Installing Matplotlib"; Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install -U matplotlib"; Flags: runascurrentuser;
StatusMsg: "Installing PyXRD";      Filename: "C:\Python27\Python.exe"; Parameters: "-m pip install -U ""{tmp}\PyXRD-{#MyAppVersion}-py2-none-any.whl"""; Flags: runascurrentuser;
StatusMsg: "Installing PyXRD";      Filename: "C:\Python27\Python.exe"; Parameters: """C:\Python27\Scripts\win32_pyxrd_post_install.py"" -install"; Flags: runascurrentuser waituntilterminated;

[UninstallDelete]
Type: files; Name: "{win}\MYPROG.INI"
