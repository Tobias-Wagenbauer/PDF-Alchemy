; Inno Setup script for PDF Alchemy. Build after `pyinstaller pdfalchemy.spec`:
;   iscc installer\pdfalchemy.iss

#define MyAppName "PDF Alchemy"
#define MyAppVersion "0.2.0"
#define MyAppExe "PDFAlchemy.exe"
#define MyAppUserModelID "PDFAlchemy.PDFAlchemy"

[Setup]
AppId={{6E0B8E0B-7C57-4C57-9F0A-5D1F2A7B3C11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=Output
OutputBaseFilename=PDFAlchemy-Setup-{#MyAppVersion}
SetupIconFile=..\src\pdfalchemy\resources\icons\app.ico
UninstallDisplayIcon={app}\{#MyAppExe}
ChangesAssociations=yes
Compression=lzma2
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; Flags: unchecked
Name: "pdfassoc"; Description: "Register {#MyAppName} for .pdf files (&Open with / Default apps)"

[InstallDelete]
; On upgrade, drop libraries left over from the previous version
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "..\dist\PDFAlchemy\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "..\src\pdfalchemy\resources\icons\app.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; IconFilename: "{app}\app.ico"; AppUserModelID: "{#MyAppUserModelID}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; IconFilename: "{app}\app.ico"; AppUserModelID: "{#MyAppUserModelID}"; Tasks: desktopicon

[Registry]
Root: HKA; Subkey: "Software\Classes\PDFAlchemy.pdf"; ValueType: string; ValueData: "PDF Document"; Flags: uninsdeletekey; Tasks: pdfassoc
Root: HKA; Subkey: "Software\Classes\PDFAlchemy.pdf\DefaultIcon"; ValueType: string; ValueData: "{app}\app.ico"; Tasks: pdfassoc
Root: HKA; Subkey: "Software\Classes\PDFAlchemy.pdf\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExe}"" ""%1"""; Tasks: pdfassoc
Root: HKA; Subkey: "Software\Classes\.pdf\OpenWithProgids"; ValueType: string; ValueName: "PDFAlchemy.pdf"; ValueData: ""; Flags: uninsdeletevalue; Tasks: pdfassoc
; Name/icon shown in "Open with" and the Default apps picker
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExe}"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey; Tasks: pdfassoc
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExe}\DefaultIcon"; ValueType: string; ValueData: "{app}\app.ico"; Tasks: pdfassoc
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExe}\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExe}"" ""%1"""; Tasks: pdfassoc
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExe}\SupportedTypes"; ValueType: string; ValueName: ".pdf"; ValueData: ""; Tasks: pdfassoc
; Lists the app under Settings > Apps > Default apps (the user still picks the default)
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey; Tasks: pdfassoc
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "View and edit PDF files"; Tasks: pdfassoc
Root: HKA; Subkey: "Software\{#MyAppName}\Capabilities\FileAssociations"; ValueType: string; ValueName: ".pdf"; ValueData: "PDFAlchemy.pdf"; Tasks: pdfassoc
Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: "Software\{#MyAppName}\Capabilities"; Flags: uninsdeletevalue; Tasks: pdfassoc
[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
