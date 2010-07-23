;
; $Id: 00.sconsblender.nsi 20836 2009-06-12 15:37:23Z jesterking $
;
; Blender Self-Installer for Windows (NSIS - http://nsis.sourceforge.net)
;
; Requires the MoreInfo plugin - http://nsis.sourceforge.net/MoreInfo_plug-in
;

!include "MUI.nsh"
!include "WinVer.nsh"
!include "FileFunc.nsh"
!include "WordFunc.nsh"
!include "nsDialogs.nsh"

SetCompressor /SOLID lzma

Name "V-Ray/Blender 2.49.12" 

!define MUI_ABORTWARNING

!define MUI_WELCOMEPAGE_TEXT  "This wizard will guide you through the installation of V-Ray/Blender.\r\n\r\nIt is recommended that you close all other applications before starting Setup.\r\n\r\nNote to Win2k/XP/Vista/7 users: You may require administrator privileges to install V-Ray/Blender successfully."
!define MUI_WELCOMEFINISHPAGE_BITMAP "D:\devel\vrayblender\installer\01.installer.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP  "D:\devel\vrayblender\installer\00.header.bmp"
!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_FINISHPAGE_RUN "$INSTDIR\blender.exe"
!define MUI_CHECKBITMAP "D:\devel\vrayblender\installer\00.checked.bmp"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "D:\devel\vrayblender\installer\copyright.txt"
!insertmacro MUI_PAGE_COMPONENTS
    
!insertmacro MUI_PAGE_DIRECTORY
Page custom DataLocation DataLocationOnLeave
;Page custom AppDataChoice AppDataChoiceOnLeave
Page custom PreMigrateUserSettings MigrateUserSettings
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
  
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro Locate
!insertmacro VersionCompare


Icon "D:\devel\vrayblender\installer\00.installer.ico"
UninstallIcon "D:\devel\vrayblender\installer\00.installer.ico"

;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"
    
;--------------------------------
;Language Strings

  ;Description
  LangString DESC_SecCopyUI ${LANG_ENGLISH} "Copy all required files to the application folder."
  LangString DESC_Section2 ${LANG_ENGLISH} "Add shortcut items to the Start Menu. (Recommended)"
  LangString DESC_Section3 ${LANG_ENGLISH} "Add a shortcut to V-Ray/Blender on your desktop."
  LangString DESC_Section4 ${LANG_ENGLISH} "V-Ray/Blender can register itself with .blend files to allow double-clicking from Windows Explorer, etc."
  LangString TEXT_IO_TITLE ${LANG_ENGLISH} "Specify User Data Location"
;--------------------------------
;Data

Caption "V-Ray/Blender 2.49.12 Installer"
OutFile "C:\release\installer\\vrayblender-2.49.12-win32.exe"
InstallDir "$PROGRAMFILES\V-RayBlender-2.49.12"

BrandingText "http://vray.cgdo.ru"
ComponentText "This will install V-Ray/Blender 2.49.12 on your computer."

DirText "Use the field below to specify the folder where you want V-Ray/Blender to be copied to. To specify a different folder, type a new name or use the Browse button to select an existing folder."

SilentUnInstall normal

# Uses $0
Function openLinkNewWindow
  Push $3 
  Push $2
  Push $1
  Push $0
  ReadRegStr $0 HKCR "http\shell\open\command" ""
# Get browser path
    DetailPrint $0
  StrCpy $2 '"'
  StrCpy $1 $0 1
  StrCmp $1 $2 +2 # if path is not enclosed in " look for space as final char
    StrCpy $2 ' '
  StrCpy $3 1
  loop:
    StrCpy $1 $0 1 $3
    DetailPrint $1
    StrCmp $1 $2 found
    StrCmp $1 "" found
    IntOp $3 $3 + 1
    Goto loop
 
  found:
    StrCpy $1 $0 $3
    StrCmp $2 " " +2
      StrCpy $1 '$1"'
 
  Pop $0
  Exec '$1 $0'
  Pop $1
  Pop $2
  Pop $3
FunctionEnd

Var BLENDERHOME
Var PREVHOME

Function SetWinXPPathCurrentUser
  SetShellVarContext current
  StrCpy $BLENDERHOME "$APPDATA\Blender Foundation\Blender"
FunctionEnd

Function SetWinXPPathAllUsers
  SetShellVarContext all
  StrCpy $BLENDERHOME "$APPDATA\Blender Foundation\Blender"
FunctionEnd

Function SetWin9xPath
  StrCpy $BLENDERHOME $INSTDIR
FunctionEnd

; custom controls
Var HWND

Var HWND_APPDATA
Var HWND_INSTDIR
Var HWND_HOMEDIR

Var HWND_BUTTON_YES
Var HWND_BUTTON_NO

Var SETUSERCONTEXT

Function PreMigrateUserSettings
  StrCpy $PREVHOME "$PROFILE\Application Data\Blender Foundation\Blender"
  StrCpy $0 "$PROFILE\Application Data\Blender Foundation\Blender\.blender"
  
  IfFileExists $0 0 nochange
  
  StrCmp $BLENDERHOME $PREVHOME nochange
  
  nsDialogs::Create /NOUNLOAD 1018
  Pop $HWND
  
  ${If} $HWND == error
	Abort
  ${EndIf}
  
  ${NSD_CreateLabel} 0 0 100% 12u "You have existing settings at:"
  ${NSD_CreateLabel} 0 20 100% 12u $PREVHOME
  ${NSD_CreateLabel} 0 40 100% 12u "Do you wish to migrate this data to:"
  ${NSD_CreateLabel} 0 60 100% 12u $BLENDERHOME
  ${NSD_CreateLabel} 0 80 100% 12u "Please note: If you choose no, V-Ray/Blender will not be able to use these files!"
  ${NSD_CreateRadioButton} 0 100 100% 12u "Yes"
  Pop $HWND_BUTTON_YES
  ${NSD_CreateRadioButton} 0 120 100% 12u "No"
  Pop $HWND_BUTTON_NO
  
  SendMessage $HWND_BUTTON_YES ${BM_SETCHECK} 1 0
  
  nsDialogs::Show
  nochange:
  
FunctionEnd

Function MigrateUserSettings
  ${NSD_GetState} $HWND_BUTTON_YES $R0
  ${If} $R0 == "1"
    CreateDirectory $BLENDERHOME
    CopyFiles $PREVHOME\*.* $BLENDERHOME
    ;RMDir /r $PREVHOME
  ${EndIf}  
FunctionEnd

;!define DLL_VER "9.00.21022.8"
;
;Function LocateCallback_90
;    MoreInfo::GetProductVersion "$R9"
;    Pop $0
;
;       ${VersionCompare} "$0" "${DLL_VER}" $R1
;
;        StrCmp $R1 0 0 new
;      new:
;        StrCmp $R1 1 0 old
;      old:
;        StrCmp $R1 2 0 end
;    ; Found DLL is older
;        Call DownloadDLL
;
;     end:
;	StrCpy "$0" StopLocate
;	StrCpy $DLL_found "true"
;	Push "$0"
;
;FunctionEnd
;
;Function DownloadDLL
;    MessageBox MB_OK "You will need to download the Microsoft Visual C++ 2008 Redistributable Package in order to run Blender. Pressing OK will take you to the download page, please follow the instructions on the page that appears."
;    StrCpy $0 "http://www.microsoft.com/downloads/details.aspx?FamilyID=9b2da534-3e03-4391-8a4d-074b9f2bc1bf&DisplayLang=en"
;    Call openLinkNewWindow
;FunctionEnd

;Function PythonInstall
;    MessageBox MB_OK "You will need to install python 2.6.4 in order to run blender. Pressing OK will take you to the python.org website."
;    StrCpy $0 "http://www.python.org"
;    Call openLinkNewWindow
;FunctionEnd


Function DataLocation
  nsDialogs::Create /NOUNLOAD 1018
  Pop $HWND
  
  ${If} $HWND == error
    Abort
  ${EndIf}
  
  ${NSD_CreateLabel} 0 0 100% 12u "Please specify where you wish to install V-Ray/Blender's user data files."
  ${NSD_CreateRadioButton} 0 20 100% 12u "Use the Application Data directory (Windows 2000 or later)"
  Pop $HWND_APPDATA
  ${NSD_CreateRadioButton} 0 50 100% 12u "Use the installation directory (ie. location chosen to install blender.exe)."
  Pop $HWND_INSTDIR
  ${NSD_CreateRadioButton} 0 80 100% 12u "I have defined a %HOME% variable, please install files here."
  Pop $HWND_HOMEDIR
  
  ${If} ${AtMostWinME}
    GetDlgItem $0 $HWND $HWND_APPDATA
    EnableWindow $0 0
    SendMessage $HWND_INSTDIR ${BM_SETCHECK} 1 0
  ${Else}
    SendMessage $HWND_APPDATA ${BM_SETCHECK} 1 0
  ${EndIf}
  
  nsDialogs::Show
  
FunctionEnd


Function DataLocationOnLeave
	StrCpy $SETUSERCONTEXT "false"
	${NSD_GetState} $HWND_APPDATA $R0
	${If} $R0 == "1"
	  ; FIXME: disabled 'all users' until fully multi-user compatible
	  ;StrCpy $SETUSERCONTEXT "true"
	  Call SetWinXPPathCurrentUser
	${Else}
	  ${NSD_GetState} $HWND_INSTDIR $R0
	  ${If} $R0 == "1"
	    Call SetWin9xPath
	  ${Else}
	    ${NSD_GetState} $HWND_HOMEDIR $R0
	    ${If} $R0 == "1"
	      ReadEnvStr $BLENDERHOME "HOME"
	    ${EndIf}
	  ${EndIf}
	${EndIf}
FunctionEnd

Var HWND_APPDATA_CURRENT
Var HWND_APPDATA_ALLUSERS

Function AppDataChoice
  StrCmp $SETUSERCONTEXT "false" skip
  
  nsDialogs::Create /NOUNLOAD 1018
  Pop $HWND
  
  ${NSD_CreateLabel} 0 0 100% 12u "Please choose which Application Data directory to use."
  ${NSD_CreateRadioButton} 0 40 100% 12u "Current User"
  Pop $HWND_APPDATA_CURRENT
  ${NSD_CreateRadioButton} 0 70 100% 12u "All Users"
  Pop $HWND_APPDATA_ALLUSERS
  
  SendMessage $HWND_APPDATA_CURRENT ${BM_SETCHECK} 1 0
  
  StrCmp $SETUSERCONTEXT "true" 0 skip ; show dialog if we need to set context, otherwise skip it
  nsDialogs::Show
  
skip:

FunctionEnd

Function AppDataChoiceOnLeave
	StrCmp $SETUSERCONTEXT "false" skip
	${NSD_GetState} $HWND_APPDATA_CURRENT $R0
	${If} $R0 == "1"
	   Call SetWinXPPathCurrentUser
	${Else}
	   Call SetWinXPPathAllUsers
	${EndIf}
skip:

FunctionEnd

Section "V-Ray/Blender-2.49.12 (required)" SecCopyUI
  SectionIn RO

  SetOutPath $INSTDIR
  File "C:\release\vrayblender-2.49.12\avcodec-52.dll"
  File "C:\release\vrayblender-2.49.12\avdevice-52.dll"
  File "C:\release\vrayblender-2.49.12\avformat-52.dll"
  File "C:\release\vrayblender-2.49.12\avutil-50.dll"
  File "C:\release\vrayblender-2.49.12\blender.exe"
  File "C:\release\vrayblender-2.49.12\blender.html"
  File "C:\release\vrayblender-2.49.12\BlenderQuickStart.pdf"
  File "C:\release\vrayblender-2.49.12\copyright.txt"
  File "C:\release\vrayblender-2.49.12\gnu_gettext.dll"
  File "C:\release\vrayblender-2.49.12\GPL-license.txt"
  File "C:\release\vrayblender-2.49.12\libpng.dll"
  File "C:\release\vrayblender-2.49.12\libtiff.dll"
  File "C:\release\vrayblender-2.49.12\OpenAL32.dll"
  File "C:\release\vrayblender-2.49.12\pthreadVC2.dll"
  File "C:\release\vrayblender-2.49.12\Python-license.txt"
  File "C:\release\vrayblender-2.49.12\python26.dll"
  File "C:\release\vrayblender-2.49.12\python26.zip"
  File "C:\release\vrayblender-2.49.12\release_249.txt"
  File "C:\release\vrayblender-2.49.12\SDL.dll"
  File "C:\release\vrayblender-2.49.12\swscale-0.dll"
  File "C:\release\vrayblender-2.49.12\wrap_oal.dll"
  File "C:\release\vrayblender-2.49.12\zlib.dll"
  File "C:\release\vrayblender-2.49.12\zlib.pyd"



  
  SetOutPath "$BLENDERHOME\.blender"
  File "C:\release\vrayblender-2.49.12\.blender\.bfont.ttf"
  File "C:\release\vrayblender-2.49.12\.blender\.Blanguages"

  SetOutPath "$BLENDERHOME\.blender\locale"

  SetOutPath "$BLENDERHOME\.blender\locale\ar"

  SetOutPath "$BLENDERHOME\.blender\locale\ar\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\ar\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\bg"

  SetOutPath "$BLENDERHOME\.blender\locale\bg\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\bg\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\ca"

  SetOutPath "$BLENDERHOME\.blender\locale\ca\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\ca\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\cs"

  SetOutPath "$BLENDERHOME\.blender\locale\cs\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\cs\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\de"

  SetOutPath "$BLENDERHOME\.blender\locale\de\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\de\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\el"

  SetOutPath "$BLENDERHOME\.blender\locale\el\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\el\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\es"

  SetOutPath "$BLENDERHOME\.blender\locale\es\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\es\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\fi"

  SetOutPath "$BLENDERHOME\.blender\locale\fi\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\fi\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\fr"

  SetOutPath "$BLENDERHOME\.blender\locale\fr\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\fr\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\hr"

  SetOutPath "$BLENDERHOME\.blender\locale\hr\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\hr\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\hr_HR"

  SetOutPath "$BLENDERHOME\.blender\locale\hr_HR\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\hr_HR\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\it"

  SetOutPath "$BLENDERHOME\.blender\locale\it\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\it\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\ja"

  SetOutPath "$BLENDERHOME\.blender\locale\ja\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\ja\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\ko"

  SetOutPath "$BLENDERHOME\.blender\locale\ko\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\ko\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\nl"

  SetOutPath "$BLENDERHOME\.blender\locale\nl\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\nl\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\pl"

  SetOutPath "$BLENDERHOME\.blender\locale\pl\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\pl\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\pt_BR"

  SetOutPath "$BLENDERHOME\.blender\locale\pt_BR\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\pt_BR\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\ro"

  SetOutPath "$BLENDERHOME\.blender\locale\ro\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\ro\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\ru"

  SetOutPath "$BLENDERHOME\.blender\locale\ru\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\ru\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\sr"

  SetOutPath "$BLENDERHOME\.blender\locale\sr\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\sr\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\sr@Latn"

  SetOutPath "$BLENDERHOME\.blender\locale\sr@Latn\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\sr@Latn\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\sv"

  SetOutPath "$BLENDERHOME\.blender\locale\sv\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\sv\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\uk"

  SetOutPath "$BLENDERHOME\.blender\locale\uk\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\uk\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\locale\zh_CN"

  SetOutPath "$BLENDERHOME\.blender\locale\zh_CN\LC_MESSAGES"
  File "C:\release\vrayblender-2.49.12\.blender\locale\zh_CN\LC_MESSAGES\blender.mo"

  SetOutPath "$BLENDERHOME\.blender\scripts"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\3ds_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\3ds_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\ac3d_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\ac3d_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\add_mesh_empty.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\add_mesh_torus.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\animation_bake_constraints.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\animation_clean.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\animation_trajectory.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\armature_symmetry.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\Axiscopy.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bevel_center.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\blenderLipSynchro.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bvh_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\c3d_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\camera_changer.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\colladaExport14.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\colladaImport14.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\collada_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\collada_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\config.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\console.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\DirectX8Exporter.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\DirectX8Importer.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\discombobulator.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\envelope_symmetry.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\export-iv-0.1.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\export_dxf.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\export_fbx.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\export_lightwave_motion.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\export_m3g.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\export_map.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\export_mdd.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\export_obj.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\faceselect_same_weights.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\flt_defaultp.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\flt_dofedit.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\flt_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\flt_filewalker.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\flt_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\flt_lodedit.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\flt_palettemanager.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\flt_properties.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\flt_toolbar.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_bpy_api.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_browser.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_getting_started.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_manual.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_release_notes.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_tutorials.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_web_blender.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_web_devcomm.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_web_eshop.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\help_web_usercomm.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\hotkeys.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\IDPropBrowser.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\image_2d_cutout.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\image_auto_layout.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\image_billboard.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\image_edit.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\import_dxf.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\import_edl.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\import_lightwave_motion.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\import_mdd.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\import_obj.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\import_web3d.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\lightwave_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\lightwave_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\md2_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\md2_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_boneweight_copy.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_cleanup.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_edges2curves.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_mirror_tool.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_poly_reduce.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_poly_reduce_grid.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_skin.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_solidify.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_unfolder.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\mesh_wire.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\ms3d_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\ms3d_import_ascii.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\obdatacopier.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\object_active_to_other.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\object_apply_def.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\object_batch_name_edit.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\object_cookie_cutter.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\object_drop.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\object_find.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\object_random_loc_sz_rot.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\object_sel2dupgroup.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\object_timeofs_follow_act.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\off_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\off_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\paths_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\ply_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\ply_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\raw_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\raw_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\renameobjectbyblock.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\render_save_layers.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\rvk1_torvk2.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\save_theme.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_background_job.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_camera_object.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_gamelogic.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_gamelogic_basic.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_gamelogic_module.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_ipo_gen.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_mesh_edit.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_metaball_create.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_object_edit.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_pyconstraint.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\scripttemplate_text_plugin.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\slp_import.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\sysinfo.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\textplugin_convert_ge.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\textplugin_functiondocs.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\textplugin_imports.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\textplugin_membersuggest.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\textplugin_outliner.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\textplugin_suggest.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\textplugin_templates.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\unweld.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\uvcalc_follow_active_coords.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\uvcalc_lightmap.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\uvcalc_quad_clickproj.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\uvcalc_smart_project.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\uvcopy.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\uv_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\uv_seams_from_islands.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\vertexpaint_from_material.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\vertexpaint_gradient.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\vertexpaint_selfshadow_ao.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\vrayexport_2.49.12.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\vrml97_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\weightpaint_average.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\weightpaint_clean.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\weightpaint_copy.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\weightpaint_envelope_assign.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\weightpaint_gradient.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\weightpaint_grow_shrink.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\weightpaint_invert.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\weightpaint_normalize.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\widgetwizard.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\wizard_bolt_factory.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\wizard_curve2tree.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\wizard_landscape_ant.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\x3d_export.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\xsi_export.py"

  SetOutPath "$BLENDERHOME\.blender\scripts\bpydata"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpydata\KUlang.txt"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpydata\readme.txt"

  SetOutPath "$BLENDERHOME\.blender\scripts\bpydata\config"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpydata\config\readme.txt"

  SetOutPath "$BLENDERHOME\.blender\scripts\bpymodules"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\blend2renderinfo.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyAddMesh.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyArmature.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyBlender.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyCurve.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyImage.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyMathutils.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyMesh.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyMesh_redux.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyMessages.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyNMesh.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyObject.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyRegistry.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyRender.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPySys.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyTextPlugin.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\BPyWindow.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\defaultdoodads.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\dxfColorMap.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\dxfLibrary.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\dxfReader.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\meshtools.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\mesh_gradient.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\paths_ai2obj.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\paths_eps2obj.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\paths_gimp2obj.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\paths_svg2obj.py"

  SetOutPath "$BLENDERHOME\.blender\scripts\bpymodules\colladaImEx"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\colladaImEx\collada.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\colladaImEx\cstartup.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\colladaImEx\cutils.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\colladaImEx\helperObjects.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\colladaImEx\logo.png"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\colladaImEx\translator.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\colladaImEx\xmlUtils.py"
  File "C:\release\vrayblender-2.49.12\.blender\scripts\bpymodules\colladaImEx\__init__.py"

  
  SetOutPath $INSTDIR
  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\BlenderFoundation "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM SOFTWARE\BlenderFoundation "Home_Dir" "$BLENDERHOME"
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\V-RayBlender" "DisplayName" "V-RayBlender (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\V-RayBlender" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteUninstaller "uninstall.exe"

;  IfSilent 0 +2
;    Goto silentdone
; Check for msvcr80.dll - give notice to download if not found
;  MessageBox MB_OK "The installer will now check your system for the required system dlls."
;  StrCpy $1 $WINDIR
;  StrCpy $DLL_found "false"
;  ${Locate} "$1" "/L=F /M=MSVCR90.DLL /S=0B" "LocateCallback_90"
;  StrCmp $DLL_found "false" 0 +2
;    Call DownloadDLL
;  ReadRegStr $0 HKLM SOFTWARE\Python\PythonCore\2.6.4\InstallPath ""
;  StrCmp $0 "" 0 +2
;    Call PythonInstall
;silentdone:
SectionEnd

Section "Add Start Menu shortcuts" Section2
  SetOutPath $INSTDIR
  CreateDirectory "$SMPROGRAMS\V-RayBlender\"
  CreateShortCut "$SMPROGRAMS\V-RayBlender\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\V-RayBlender\V-RayBlender-2.49.12.lnk" "$INSTDIR\Blender.exe" "" "$INSTDIR\blender.exe" 0
  CreateShortCut "$SMPROGRAMS\V-RayBlender\Readme.lnk" "$INSTDIR\Blender.html" "" "" 0
  CreateShortCut "$SMPROGRAMS\V-RayBlender\Copyright.lnk" "$INSTDIR\Copyright.txt" "" "$INSTDIR\copyright.txt" 0
  CreateShortCut "$SMPROGRAMS\V-RayBlender\GPL-license.lnk" "$INSTDIR\GPL-license.txt" "" "$INSTDIR\GPL-license.txt" 0
  CreateShortCut "$SMPROGRAMS\V-RayBlender\Help.lnk" "$INSTDIR\Help.url"
SectionEnd

Section "Add Desktop V-Ray/Blender-2.49.12 shortcut" Section3
  SetOutPath $INSTDIR
  CreateShortCut "$DESKTOP\V-RayBlender-2.49.12.lnk" "$INSTDIR\blender.exe" "" "$INSTDIR\blender.exe" 0
SectionEnd


Section "Open .blend files with V-Ray/Blender-2.49.12" Section4
  SetOutPath $INSTDIR
  ;ExecShell "open" '"$INSTDIR\blender.exe"' "-R -b"
  ;do it the manual way! ;)
  
  WriteRegStr HKCR ".blend" "" "blendfile"
  WriteRegStr HKCR "blendfile" "" "Blender .blend File"
  WriteRegStr HKCR "blendfile\shell" "" "open"
  WriteRegStr HKCR "blendfile\DefaultIcon" "" $INSTDIR\blender.exe,1
  WriteRegStr HKCR "blendfile\shell\open\command" "" '"$INSTDIR\blender.exe" "%1"'
SectionEnd





UninstallText "This will uninstall V-Ray/Blender 2.49.12. Hit next to continue."


Section "Uninstall"
  Delete $INSTDIR\uninstall.exe
  
  ;ReadRegStr $BLENDERHOME HKLM "SOFTWARE\BlenderFoundation" "Home_Dir"
  
  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\V-RayBlender"
  ;DeleteRegKey HKLM SOFTWARE\BlenderFoundation

  ; remove files
  Delete $INSTDIR\.blender
  Delete $INSTDIR\avcodec-52.dll
  Delete $INSTDIR\avdevice-52.dll
  Delete $INSTDIR\avformat-52.dll
  Delete $INSTDIR\avutil-50.dll
  Delete $INSTDIR\blender.exe
  Delete $INSTDIR\blender.html
  Delete $INSTDIR\BlenderQuickStart.pdf
  Delete $INSTDIR\copyright.txt
  Delete $INSTDIR\gnu_gettext.dll
  Delete $INSTDIR\GPL-license.txt
  Delete $INSTDIR\libpng.dll
  Delete $INSTDIR\libtiff.dll
  Delete $INSTDIR\OpenAL32.dll
  Delete $INSTDIR\plugins
  Delete $INSTDIR\pthreadVC2.dll
  Delete $INSTDIR\Python-license.txt
  Delete $INSTDIR\python26.dll
  Delete $INSTDIR\python26.zip
  Delete $INSTDIR\release_249.txt
  Delete $INSTDIR\SDL.dll
  Delete $INSTDIR\swscale-0.dll
  Delete $INSTDIR\wrap_oal.dll
  Delete $INSTDIR\zlib.dll
  Delete $INSTDIR\zlib.pyd


  
  Delete $BLENDERHOME\.blender\.bfont.ttf
  Delete $BLENDERHOME\.blender\.Blanguages
  ; remove shortcuts, if any.
  Delete "$SMPROGRAMS\V-RayBlender\*.*"
  Delete "$DESKTOP\V-RayBlender-2.49.12.lnk"
  ; remove directories used.
  RMDir /r $BLENDERHOME\.blender\locale
  MessageBox MB_YESNO "Erase .blender\scripts folder? (ALL contents will be erased!)" /SD IDYES IDNO Next
  Delete "$INSTDIR\.blender.bfont.ttf"
  Delete "$INSTDIR\.blender.Blanguages"
  Delete "$INSTDIR\.blender\locale\ar\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\bg\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\ca\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\cs\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\de\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\el\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\es\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\fi\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\fr\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\hr\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\hr_HR\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\it\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\ja\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\ko\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\nl\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\pl\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\pt_BR\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\ro\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\ru\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\sr\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\sr@Latn\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\sv\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\uk\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\locale\zh_CN\LC_MESSAGESblender.mo"
  Delete "$INSTDIR\.blender\scripts3ds_export.py"
  Delete "$INSTDIR\.blender\scripts3ds_import.py"
  Delete "$INSTDIR\.blender\scriptsac3d_export.py"
  Delete "$INSTDIR\.blender\scriptsac3d_import.py"
  Delete "$INSTDIR\.blender\scriptsadd_mesh_empty.py"
  Delete "$INSTDIR\.blender\scriptsadd_mesh_torus.py"
  Delete "$INSTDIR\.blender\scriptsanimation_bake_constraints.py"
  Delete "$INSTDIR\.blender\scriptsanimation_clean.py"
  Delete "$INSTDIR\.blender\scriptsanimation_trajectory.py"
  Delete "$INSTDIR\.blender\scriptsarmature_symmetry.py"
  Delete "$INSTDIR\.blender\scriptsAxiscopy.py"
  Delete "$INSTDIR\.blender\scriptsbevel_center.py"
  Delete "$INSTDIR\.blender\scriptsblenderLipSynchro.py"
  Delete "$INSTDIR\.blender\scriptsbvh_import.py"
  Delete "$INSTDIR\.blender\scriptsc3d_import.py"
  Delete "$INSTDIR\.blender\scriptscamera_changer.py"
  Delete "$INSTDIR\.blender\scriptscolladaExport14.py"
  Delete "$INSTDIR\.blender\scriptscolladaImport14.py"
  Delete "$INSTDIR\.blender\scriptscollada_export.py"
  Delete "$INSTDIR\.blender\scriptscollada_import.py"
  Delete "$INSTDIR\.blender\scriptsconfig.py"
  Delete "$INSTDIR\.blender\scriptsconsole.py"
  Delete "$INSTDIR\.blender\scriptsDirectX8Exporter.py"
  Delete "$INSTDIR\.blender\scriptsDirectX8Importer.py"
  Delete "$INSTDIR\.blender\scriptsdiscombobulator.py"
  Delete "$INSTDIR\.blender\scriptsenvelope_symmetry.py"
  Delete "$INSTDIR\.blender\scriptsexport-iv-0.1.py"
  Delete "$INSTDIR\.blender\scriptsexport_dxf.py"
  Delete "$INSTDIR\.blender\scriptsexport_fbx.py"
  Delete "$INSTDIR\.blender\scriptsexport_lightwave_motion.py"
  Delete "$INSTDIR\.blender\scriptsexport_m3g.py"
  Delete "$INSTDIR\.blender\scriptsexport_map.py"
  Delete "$INSTDIR\.blender\scriptsexport_mdd.py"
  Delete "$INSTDIR\.blender\scriptsexport_obj.py"
  Delete "$INSTDIR\.blender\scriptsfaceselect_same_weights.py"
  Delete "$INSTDIR\.blender\scriptsflt_defaultp.py"
  Delete "$INSTDIR\.blender\scriptsflt_dofedit.py"
  Delete "$INSTDIR\.blender\scriptsflt_export.py"
  Delete "$INSTDIR\.blender\scriptsflt_filewalker.py"
  Delete "$INSTDIR\.blender\scriptsflt_import.py"
  Delete "$INSTDIR\.blender\scriptsflt_lodedit.py"
  Delete "$INSTDIR\.blender\scriptsflt_palettemanager.py"
  Delete "$INSTDIR\.blender\scriptsflt_properties.py"
  Delete "$INSTDIR\.blender\scriptsflt_toolbar.py"
  Delete "$INSTDIR\.blender\scriptshelp_bpy_api.py"
  Delete "$INSTDIR\.blender\scriptshelp_browser.py"
  Delete "$INSTDIR\.blender\scriptshelp_getting_started.py"
  Delete "$INSTDIR\.blender\scriptshelp_manual.py"
  Delete "$INSTDIR\.blender\scriptshelp_release_notes.py"
  Delete "$INSTDIR\.blender\scriptshelp_tutorials.py"
  Delete "$INSTDIR\.blender\scriptshelp_web_blender.py"
  Delete "$INSTDIR\.blender\scriptshelp_web_devcomm.py"
  Delete "$INSTDIR\.blender\scriptshelp_web_eshop.py"
  Delete "$INSTDIR\.blender\scriptshelp_web_usercomm.py"
  Delete "$INSTDIR\.blender\scriptshotkeys.py"
  Delete "$INSTDIR\.blender\scriptsIDPropBrowser.py"
  Delete "$INSTDIR\.blender\scriptsimage_2d_cutout.py"
  Delete "$INSTDIR\.blender\scriptsimage_auto_layout.py"
  Delete "$INSTDIR\.blender\scriptsimage_billboard.py"
  Delete "$INSTDIR\.blender\scriptsimage_edit.py"
  Delete "$INSTDIR\.blender\scriptsimport_dxf.py"
  Delete "$INSTDIR\.blender\scriptsimport_edl.py"
  Delete "$INSTDIR\.blender\scriptsimport_lightwave_motion.py"
  Delete "$INSTDIR\.blender\scriptsimport_mdd.py"
  Delete "$INSTDIR\.blender\scriptsimport_obj.py"
  Delete "$INSTDIR\.blender\scriptsimport_web3d.py"
  Delete "$INSTDIR\.blender\scriptslightwave_export.py"
  Delete "$INSTDIR\.blender\scriptslightwave_import.py"
  Delete "$INSTDIR\.blender\scriptsmd2_export.py"
  Delete "$INSTDIR\.blender\scriptsmd2_import.py"
  Delete "$INSTDIR\.blender\scriptsmesh_boneweight_copy.py"
  Delete "$INSTDIR\.blender\scriptsmesh_cleanup.py"
  Delete "$INSTDIR\.blender\scriptsmesh_edges2curves.py"
  Delete "$INSTDIR\.blender\scriptsmesh_mirror_tool.py"
  Delete "$INSTDIR\.blender\scriptsmesh_poly_reduce.py"
  Delete "$INSTDIR\.blender\scriptsmesh_poly_reduce_grid.py"
  Delete "$INSTDIR\.blender\scriptsmesh_skin.py"
  Delete "$INSTDIR\.blender\scriptsmesh_solidify.py"
  Delete "$INSTDIR\.blender\scriptsmesh_unfolder.py"
  Delete "$INSTDIR\.blender\scriptsmesh_wire.py"
  Delete "$INSTDIR\.blender\scriptsms3d_import.py"
  Delete "$INSTDIR\.blender\scriptsms3d_import_ascii.py"
  Delete "$INSTDIR\.blender\scriptsobdatacopier.py"
  Delete "$INSTDIR\.blender\scriptsobject_active_to_other.py"
  Delete "$INSTDIR\.blender\scriptsobject_apply_def.py"
  Delete "$INSTDIR\.blender\scriptsobject_batch_name_edit.py"
  Delete "$INSTDIR\.blender\scriptsobject_cookie_cutter.py"
  Delete "$INSTDIR\.blender\scriptsobject_drop.py"
  Delete "$INSTDIR\.blender\scriptsobject_find.py"
  Delete "$INSTDIR\.blender\scriptsobject_random_loc_sz_rot.py"
  Delete "$INSTDIR\.blender\scriptsobject_sel2dupgroup.py"
  Delete "$INSTDIR\.blender\scriptsobject_timeofs_follow_act.py"
  Delete "$INSTDIR\.blender\scriptsoff_export.py"
  Delete "$INSTDIR\.blender\scriptsoff_import.py"
  Delete "$INSTDIR\.blender\scriptspaths_import.py"
  Delete "$INSTDIR\.blender\scriptsply_export.py"
  Delete "$INSTDIR\.blender\scriptsply_import.py"
  Delete "$INSTDIR\.blender\scriptsraw_export.py"
  Delete "$INSTDIR\.blender\scriptsraw_import.py"
  Delete "$INSTDIR\.blender\scriptsrenameobjectbyblock.py"
  Delete "$INSTDIR\.blender\scriptsrender_save_layers.py"
  Delete "$INSTDIR\.blender\scriptsrvk1_torvk2.py"
  Delete "$INSTDIR\.blender\scriptssave_theme.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_background_job.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_camera_object.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_gamelogic.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_gamelogic_basic.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_gamelogic_module.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_ipo_gen.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_mesh_edit.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_metaball_create.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_object_edit.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_pyconstraint.py"
  Delete "$INSTDIR\.blender\scriptsscripttemplate_text_plugin.py"
  Delete "$INSTDIR\.blender\scriptsslp_import.py"
  Delete "$INSTDIR\.blender\scriptssysinfo.py"
  Delete "$INSTDIR\.blender\scriptstextplugin_convert_ge.py"
  Delete "$INSTDIR\.blender\scriptstextplugin_functiondocs.py"
  Delete "$INSTDIR\.blender\scriptstextplugin_imports.py"
  Delete "$INSTDIR\.blender\scriptstextplugin_membersuggest.py"
  Delete "$INSTDIR\.blender\scriptstextplugin_outliner.py"
  Delete "$INSTDIR\.blender\scriptstextplugin_suggest.py"
  Delete "$INSTDIR\.blender\scriptstextplugin_templates.py"
  Delete "$INSTDIR\.blender\scriptsunweld.py"
  Delete "$INSTDIR\.blender\scriptsuvcalc_follow_active_coords.py"
  Delete "$INSTDIR\.blender\scriptsuvcalc_lightmap.py"
  Delete "$INSTDIR\.blender\scriptsuvcalc_quad_clickproj.py"
  Delete "$INSTDIR\.blender\scriptsuvcalc_smart_project.py"
  Delete "$INSTDIR\.blender\scriptsuvcopy.py"
  Delete "$INSTDIR\.blender\scriptsuv_export.py"
  Delete "$INSTDIR\.blender\scriptsuv_seams_from_islands.py"
  Delete "$INSTDIR\.blender\scriptsvertexpaint_from_material.py"
  Delete "$INSTDIR\.blender\scriptsvertexpaint_gradient.py"
  Delete "$INSTDIR\.blender\scriptsvertexpaint_selfshadow_ao.py"
  Delete "$INSTDIR\.blender\scriptsvrayexport_2.49.12.py"
  Delete "$INSTDIR\.blender\scriptsvrml97_export.py"
  Delete "$INSTDIR\.blender\scriptsweightpaint_average.py"
  Delete "$INSTDIR\.blender\scriptsweightpaint_clean.py"
  Delete "$INSTDIR\.blender\scriptsweightpaint_copy.py"
  Delete "$INSTDIR\.blender\scriptsweightpaint_envelope_assign.py"
  Delete "$INSTDIR\.blender\scriptsweightpaint_gradient.py"
  Delete "$INSTDIR\.blender\scriptsweightpaint_grow_shrink.py"
  Delete "$INSTDIR\.blender\scriptsweightpaint_invert.py"
  Delete "$INSTDIR\.blender\scriptsweightpaint_normalize.py"
  Delete "$INSTDIR\.blender\scriptswidgetwizard.py"
  Delete "$INSTDIR\.blender\scriptswizard_bolt_factory.py"
  Delete "$INSTDIR\.blender\scriptswizard_curve2tree.py"
  Delete "$INSTDIR\.blender\scriptswizard_landscape_ant.py"
  Delete "$INSTDIR\.blender\scriptsx3d_export.py"
  Delete "$INSTDIR\.blender\scriptsxsi_export.py"
  Delete "$INSTDIR\.blender\scripts\bpydataKUlang.txt"
  Delete "$INSTDIR\.blender\scripts\bpydatareadme.txt"
  Delete "$INSTDIR\.blender\scripts\bpydata\configreadme.txt"
  Delete "$INSTDIR\.blender\scripts\bpymodulesblend2renderinfo.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyAddMesh.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyArmature.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyBlender.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyCurve.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyImage.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyMathutils.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyMesh.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyMesh_redux.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyMessages.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyNMesh.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyObject.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyRegistry.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyRender.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPySys.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyTextPlugin.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesBPyWindow.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesdefaultdoodads.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesdxfColorMap.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesdxfLibrary.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesdxfReader.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesmeshtools.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulesmesh_gradient.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulespaths_ai2obj.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulespaths_eps2obj.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulespaths_gimp2obj.py"
  Delete "$INSTDIR\.blender\scripts\bpymodulespaths_svg2obj.py"
  Delete "$INSTDIR\.blender\scripts\bpymodules\colladaImExcollada.py"
  Delete "$INSTDIR\.blender\scripts\bpymodules\colladaImExcstartup.py"
  Delete "$INSTDIR\.blender\scripts\bpymodules\colladaImExcutils.py"
  Delete "$INSTDIR\.blender\scripts\bpymodules\colladaImExhelperObjects.py"
  Delete "$INSTDIR\.blender\scripts\bpymodules\colladaImExlogo.png"
  Delete "$INSTDIR\.blender\scripts\bpymodules\colladaImExtranslator.py"
  Delete "$INSTDIR\.blender\scripts\bpymodules\colladaImExxmlUtils.py"
  Delete "$INSTDIR\.blender\scripts\bpymodules\colladaImEx__init__.py"
  RMDir /r "$INSTDIR\.blender\scripts\bpymodules\colladaImEx"
  RMDir /r "$INSTDIR\.blender\scripts\bpymodules"
  RMDir /r "$INSTDIR\.blender\scripts\bpydata\config"
  RMDir /r "$INSTDIR\.blender\scripts\bpydata"
  RMDir /r "$INSTDIR\.blender\scripts"
  RMDir /r "$INSTDIR\.blender\locale\zh_CN\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\zh_CN"
  RMDir /r "$INSTDIR\.blender\locale\uk\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\uk"
  RMDir /r "$INSTDIR\.blender\locale\sv\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\sv"
  RMDir /r "$INSTDIR\.blender\locale\sr@Latn\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\sr@Latn"
  RMDir /r "$INSTDIR\.blender\locale\sr\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\sr"
  RMDir /r "$INSTDIR\.blender\locale\ru\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\ru"
  RMDir /r "$INSTDIR\.blender\locale\ro\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\ro"
  RMDir /r "$INSTDIR\.blender\locale\pt_BR\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\pt_BR"
  RMDir /r "$INSTDIR\.blender\locale\pl\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\pl"
  RMDir /r "$INSTDIR\.blender\locale\nl\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\nl"
  RMDir /r "$INSTDIR\.blender\locale\ko\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\ko"
  RMDir /r "$INSTDIR\.blender\locale\ja\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\ja"
  RMDir /r "$INSTDIR\.blender\locale\it\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\it"
  RMDir /r "$INSTDIR\.blender\locale\hr_HR\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\hr_HR"
  RMDir /r "$INSTDIR\.blender\locale\hr\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\hr"
  RMDir /r "$INSTDIR\.blender\locale\fr\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\fr"
  RMDir /r "$INSTDIR\.blender\locale\fi\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\fi"
  RMDir /r "$INSTDIR\.blender\locale\es\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\es"
  RMDir /r "$INSTDIR\.blender\locale\el\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\el"
  RMDir /r "$INSTDIR\.blender\locale\de\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\de"
  RMDir /r "$INSTDIR\.blender\locale\cs\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\cs"
  RMDir /r "$INSTDIR\.blender\locale\ca\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\ca"
  RMDir /r "$INSTDIR\.blender\locale\bg\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\bg"
  RMDir /r "$INSTDIR\.blender\locale\ar\LC_MESSAGES"
  RMDir /r "$INSTDIR\.blender\locale\ar"
  RMDir /r "$INSTDIR\.blender\locale"
  RMDir /r "$INSTDIR\.blender"


Next:
  RMDir /r $BLENDERHOME\plugins\include
  RMDir /r $BLENDERHOME\plugins
  RMDir $BLENDERHOME\.blender
  RMDir "$SMPROGRAMS\V-RayBlender"
  RMDir "$INSTDIR"
  RMDir "$INSTDIR\.."
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecCopyUI} $(DESC_SecCopyUI)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section2} $(DESC_Section2)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section3} $(DESC_Section3)
  !insertmacro MUI_DESCRIPTION_TEXT ${Section4} $(DESC_Section4)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
