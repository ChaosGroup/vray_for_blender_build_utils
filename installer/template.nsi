;  V-Ray/Blender Installer Template
;
;  http://chaosgroup.com
;
;  Author: Andrei Izrantcev <andrei.izrantcev@chaosgroup.com>
;
;  This program is free software; you can redistribute it and/or
;  modify it under the terms of the GNU General Public License
;  as published by the Free Software Foundation; either version 2
;  of the License, or (at your option) any later version.
;
;  This program is distributed in the hope that it will be useful,
;  but WITHOUT ANY WARRANTY; without even the implied warranty of
;  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
;  GNU General Public License for more details.
;
;  You should have received a copy of the GNU General Public License
;  along with this program.  If not, see <http://www.gnu.org/licenses/>.
;
;  All Rights Reserved. V-Ray(R) is a registered trademark of Chaos Software.
;

!include MUI.nsh
!include LogicLib.nsh
!include selections.nsh
!include uninstall_log.nsh

OutFile "{INSTALLER_OUTFILE}"

Name "V-Ray For Blender {VERSION} [Rev. {REVISION}]"

RequestExecutionLevel admin

!define REG_ROOT HKLM
!define REG_APP_PATH   "Software\Microsoft\Windows\CurrentVersion\Uninstall\VRayBlender"
!define UNINSTALL_PATH "Software\Microsoft\Windows\CurrentVersion\Uninstall\VRayBlender"

!define MUI_ICON                       "{INSTALLER_SCRIPT_ROOT}\\style\\icon.ico"
!define MUI_UNICON                     "{INSTALLER_SCRIPT_ROOT}\\style\\icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP         "{INSTALLER_SCRIPT_ROOT}\\style\\header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP   "{INSTALLER_SCRIPT_ROOT}\\style\\installer.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "{INSTALLER_SCRIPT_ROOT}\\style\\installer.bmp"
!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_FINISHPAGE_RUN "$INSTDIR\blender.exe"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.rtf"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

BrandingText "V-Ray For Blender {VERSION} | http://www.chaosgroup.com/"

InstallDir "$PROGRAMFILES{IF64}\VRayBlender-{VERSION}"


Var VB_TMP
Var VB_UNINST


Section "V-Ray/Blender" VBINST
{INSTALLER_FILES}
SectionEnd


Section "Uninstaller" VBUNINST
	SectionIn RO
	
	StrCpy $VB_UNINST "Software\Microsoft\Windows\CurrentVersion\Uninstall\VRayBlender"
	
	WriteRegStr   HKLM $VB_UNINST "DisplayName"     "V-Ray For Blender"
	WriteRegStr   HKLM $VB_UNINST "UninstallString" "$\"$INSTDIR\uninstaller.exe$\""
	WriteRegStr   HKLM $VB_UNINST "Publisher"       "Andrei Izrantcev"
	WriteRegStr   HKLM $VB_UNINST "URLInfoAbout"    "http://www.chaosgroup.com/"
	WriteRegStr   HKLM $VB_UNINST "HelpLink"        "http://www.chaosgroup.com/"
	WriteRegDWORD HKLM $VB_UNINST "NoModify"  1
	WriteRegDWORD HKLM $VB_UNINST "NoRepair " 1
	
	${WriteUninstaller} "$INSTDIR\uninstaller.exe"
	
	; Write the installation path into the registry
	${WriteRegStr} "${REG_ROOT}" "${REG_APP_PATH}" "Install Directory" "$INSTDIR"
	
	; Write the Uninstall information into the registry
	${WriteRegStr} "${REG_ROOT}" "${UNINSTALL_PATH}" "UninstallString" "$INSTDIR\uninstaller.exe"
SectionEnd


Section "Add Start Menu Shortcuts" VBSTART
	SetShellVarContext all
  
	; Menu section
	${CreateDirectory} "$SMPROGRAMS\VRayBlender {VERSION}\"

	; Blender
	${CreateShortCut}  "$SMPROGRAMS\VRayBlender {VERSION}\VRayForBlender.lnk" "$INSTDIR\blender.exe" "" "$INSTDIR\blender.exe" 0
	
	; Uninstaller
	${CreateShortCut}  "$SMPROGRAMS\VRayBlender {VERSION}\Uninstall.lnk" "$INSTDIR\uninstaller.exe" "" "$INSTDIR\uninstaller.exe" 0
	
	; Refresh icons
	System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (0x08000000, 0, 0, 0)'
SectionEnd


Section "Open .blend files with Blender" BlendRegister
	ExecWait '"$INSTDIR\blender.exe" -r'
SectionEnd


Section "Uninstall"
{UNINSTALLER_FILES}
RMDir "$INSTDIR/uninstaller.exe"
RMDir "$INSTDIR"
SectionEnd
