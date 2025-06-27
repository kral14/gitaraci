; Inno Setup Script
; Git Yönetim Aracı üçün

[Setup]
; Qeyd: AppId unikal olmalıdır.
AppId={{C1A8B567-4F14-4A8E-8C49-651D835F4D3B}
AppName=Git Yönetim Aracı
AppVersion=1.0
AppPublisher=Sizin Adınız
DefaultDirName={userappdata}\GitYonetimAraci
DefaultGroupName=Git Yönetim Aracı
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputBaseFilename=GitYonetimAraci-Setup
SetupIconFile=app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; ƏN VACİB: Admin icazəsi istəməməsi üçün
PrivilegesRequired=lowest

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";

[Files]
Source: "dist\git_araci.exe"; DestDir: "{app}"; Flags: ignoreversion
; Qeyd: Əgər başqa fayllar da lazımdırsa, bura əlavə edilə bilər.

[Icons]
Name: "{group}\Git Yönetim Aracı"; Filename: "{app}\git_araci.exe"
Name: "{autodesktop}\Git Yönetim Aracı"; Filename: "{app}\git_araci.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\git_araci.exe"; Description: "{cm:LaunchProgram,Git Yönetim Aracı}"; Flags: nowait postinstall skipifsilent