; ====================================================================
; SIGBEF - Script Inno Setup
;
; Para gerar um instalador profissional .exe que coloca atalhos no
; menu Iniciar e na area de trabalho:
;   1. Instale o Inno Setup: https://jrsoftware.org/isinfo.php
;   2. Rode o build.bat para gerar dist\SIGBEF\
;   3. Abra este arquivo no Inno Setup Compiler
;   4. Clique em "Compile" (F9)
; O instalador final e gerado em Output\SIGBEF_Setup.exe
; ====================================================================

#define MyAppName "SIGBEF"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Marcello"
#define MyAppExeName "SIGBEF.exe"

[Setup]
AppId={{8B5F2B70-9E4D-4E8F-A8E1-SIGBEFCEFE001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/SEU-USUARIO/sigbef
DefaultDirName={autopf}\SIGBEF
DefaultGroupName=SIGBEF
DisableProgramGroupPage=yes
OutputBaseFilename=SIGBEF_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\sigbef.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
LicenseFile=..\LICENSE

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "kioskshortcut"; Description: "Criar atalho separado para Modo Autoatendimento"; GroupDescription: "Atalhos opcionais"

[Files]
Source: "..\dist\SIGBEF\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SIGBEF"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\SIGBEF (Autoatendimento)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--autoatendimento"; Tasks: kioskshortcut
Name: "{group}\Desinstalar SIGBEF"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SIGBEF"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar SIGBEF agora"; Flags: nowait postinstall skipifsilent
