;AddItem macro
  !macro AddItem Path
    FileWrite $UninstLog "${Path}$\r$\n"
  !macroend
 
;File macro
  !macro File FilePath FileName TargetPath
     FileWrite $UninstLog "${TargetPath}\${FileName}$\r$\n"
     File "${FilePath}\${FileName}"
  !macroend
 
;CreateShortcut macro
  !macro CreateShortcut FilePath FilePointer Pamameters Icon IconIndex
    FileWrite $UninstLog "${FilePath}$\r$\n"
    CreateShortcut "${FilePath}" "${FilePointer}" "${Pamameters}" "${Icon}" "${IconIndex}"
  !macroend
 
;Copy files macro
  !macro CopyFiles SourcePath DestPath
    IfFileExists "${DestPath}" +2
    FileWrite $UninstLog "${DestPath}$\r$\n"
    CopyFiles "${SourcePath}" "${DestPath}"
  !macroend
 
;Rename macro
  !macro Rename SourcePath DestPath
    IfFileExists "${DestPath}" +2
    FileWrite $UninstLog "${DestPath}$\r$\n"
    Rename "${SourcePath}" "${DestPath}"
  !macroend
 
;CreateDirectory macro
  !macro CreateDirectory Path
    CreateDirectory "${Path}"
    FileWrite $UninstLog "${Path}$\r$\n"
  !macroend
 
;SetOutPath macro
  !macro SetOutPath Path
    SetOutPath "${Path}"
    ;FileWrite $UninstLog "${Path}$\r$\n"
  !macroend
 
;WriteUninstaller macro
  !macro WriteUninstaller Path
    WriteUninstaller "${Path}"
    FileWrite $UninstLog "${Path}$\r$\n"
  !macroend
 
;WriteRegStr macro
  !macro WriteRegStr RegRoot UnInstallPath Key Value
     FileWrite $UninstLog "${RegRoot} ${UnInstallPath}$\r$\n"
     WriteRegStr "${RegRoot}" "${UnInstallPath}" "${Key}" "${Value}"
  !macroend
 
;WriteRegDWORD macro
  !macro WriteRegDWORD RegRoot UnInstallPath Key Value
     FileWrite $UninstLog "${RegRoot} ${UnInstallPath}$\r$\n"
     WriteRegStr "${RegRoot}" "${UnInstallPath}" "${Key}" "${Value}"
  !macroend
  
  ;Set the name of the uninstall log
    !define UninstLog "uninstall.log"
    Var UninstLog
 
  ;Uninstall log file missing.
    LangString UninstLogMissing ${LANG_ENGLISH} "${UninstLog} not found!$\r$\nUninstallation cannot proceed!"
 
  ;AddItem macro
    !define AddItem "!insertmacro AddItem"
 
  ;File macro
    !define File "!insertmacro File"
 
  ;CreateShortcut macro
    !define CreateShortcut "!insertmacro CreateShortcut"
 
  ;Copy files macro
    !define CopyFiles "!insertmacro CopyFiles"
 
  ;Rename macro
    !define Rename "!insertmacro Rename"
 
  ;CreateDirectory macro
    !define CreateDirectory "!insertmacro CreateDirectory"
 
  ;SetOutPath macro
    !define SetOutPath "!insertmacro SetOutPath"
 
  ;WriteUninstaller macro
    !define WriteUninstaller "!insertmacro WriteUninstaller"
 
  ;WriteRegStr macro
    !define WriteRegStr "!insertmacro WriteRegStr"
 
  ;WriteRegDWORD macro
    !define WriteRegDWORD "!insertmacro WriteRegDWORD" 
 
  Section -openlogfile
    CreateDirectory "$INSTDIR"
    IfFileExists "$INSTDIR\${UninstLog}" +3
      FileOpen $UninstLog "$INSTDIR\${UninstLog}" w
    Goto +4
      SetFileAttributes "$INSTDIR\${UninstLog}" NORMAL
      FileOpen $UninstLog "$INSTDIR\${UninstLog}" a
      FileSeek $UninstLog 0 END
  SectionEnd
