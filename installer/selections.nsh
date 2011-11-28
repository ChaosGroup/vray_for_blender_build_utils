!define SF_USELECTED  0
 
!macro SecSelect SecId
  Push $0
  IntOp $0 ${SF_SELECTED} | ${SF_RO}
  SectionSetFlags ${SecId} $0
  SectionSetInstTypes ${SecId} 1
  Pop $0
!macroend
 
!define SelectSection '!insertmacro SecSelect'
 
!macro SecUnSelect SecId
  Push $0
  IntOp $0 ${SF_USELECTED} | ${SF_RO}
  SectionSetFlags ${SecId} $0
  Pop $0
!macroend
 
!define UnSelectSection '!insertmacro SecUnSelect'
