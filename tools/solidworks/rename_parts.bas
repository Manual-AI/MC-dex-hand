' ============================================================================
' rename_parts.bas  -  SOLIDWORKS VBA macro  (v2)
' Renames part files of the ACTIVE assembly according to the embedded map
' (generated from bom/rename_map.csv) and writes BOM_ID / PART_NAME custom
' properties.
'
' HOW TO USE
'   1. BACK UP FIRST (git commit or Pack-and-Go the whole assembly folder).
'   2. Open BOTH assemblies (robot + glove) so shared parts update in both.
'      Make the robot assembly the active window.
'   3. Tools > Macro > New..., paste this file in, run Main with DRY_RUN = True.
'   4. Read the Immediate window (Ctrl+G), then set DRY_RUN = False and run.
'   5. Activate the glove assembly, run again (renamed files are skipped).
'   6. File > Save All.  Check File > Find References for anything broken.
'
' API note: IModelDocExtension.RenameDocument renames the component that is
' currently SELECTED in the active assembly, and must be called on the
' ASSEMBLY's extension.  Components must be resolved (not lightweight).
' ============================================================================
Option Explicit

Const DRY_RUN As Boolean = True          ' <- set False to actually rename
Const WRITE_BOM_ID As Boolean = True
Const SAVE_PARTS As Boolean = True

Const swCustomInfoText As Long = 30
Const swCustomPropertyReplaceValue As Long = 2
Const swSaveAsOptions_Silent As Long = 1
Const swDocASSEMBLY As Long = 2
Const swComponentFullyResolved As Long = 2

Dim oldNames() As String, newNames() As String, bomIds() As String
Dim nMap As Long

Private Sub AddMap(oldN As String, newN As String, id As String)
    ReDim Preserve oldNames(nMap): ReDim Preserve newNames(nMap): ReDim Preserve bomIds(nMap)
    oldNames(nMap) = LCase$(oldN): newNames(nMap) = newN: bomIds(nMap) = id
    nMap = nMap + 1
End Sub

Private Sub BuildMap()
    nMap = 0
    AddMap "palm_plate_j3_robot", "rh_palm_plate", "RH-001"
    AddMap "robot_glove_backplate_j3", "rh_backplate", "RH-002"
    AddMap "index_proxy_link", "rh_index_proximal_link", "RH-003"
    AddMap "index_tip_robot_j3", "rh_index_tip", "RH-004"
    AddMap "middle_proxy_link_j4", "rh_middle_proximal_link", "RH-005"
    AddMap "middle_tip_robot_j3", "rh_middle_tip", "RH-006"
    AddMap "pinkyring_proxy_link", "rh_pinkyring_proximal_link", "RH-007"
    AddMap "pinkyring_tip_robot", "rh_pinkyring_tip", "RH-008"
    AddMap "thumb_link1_test", "rh_thumb_link1", "RH-009"
    AddMap "thumb_link1_support_rod", "rh_thumb_link1_support_rod", "RH-010"
    AddMap "thumb_pin", "rh_thumb_pin", "RH-011"
    AddMap "thumb_tip_robot_j3", "rh_thumb_tip", "RH-012"
    AddMap "OpenArm_adaptor", "rh_openarm_adaptor", "RH-013"
    AddMap "electronics_box1", "cm_electronics_box", "RH-014 / GL-030"
    AddMap "electronics_box1_lid", "cm_electronics_box_lid", "RH-015 / GL-031"
    AddMap "camera_mount_v2", "cm_camera_mount", "RH-016 / GL-032"
    AddMap "camera_adaptor_v2", "cm_camera_adaptor", "RH-017 / GL-033"
    AddMap "01_Base", "cm_quest_mount_base", "RH-018 / GL-034"
    AddMap "02_Hinged_cap", "cm_quest_mount_hinged_cap", "RH-019 / GL-035"
    AddMap "03_Receiver_8x9", "cm_quest_mount_receiver", "RH-020 / GL-036"
    AddMap "palm_plate_j3_glove", "gl_palm_plate", "GL-001"
    AddMap "backplate_j4", "gl_backplate", "GL-002"
    AddMap "link1_index_j3", "gl_index_proximal_link", "GL-003"
    AddMap "index_tip_glove_j3", "gl_index_tip", "GL-004"
    AddMap "link1_middle_j4", "gl_middle_proximal_link", "GL-005"
    AddMap "middle_tip_glove_j3", "gl_middle_tip", "GL-006"
    AddMap "link1_pinkyring_j3", "gl_pinkyring_proximal_link", "GL-007"
    AddMap "pinkyring_tip_glove", "gl_pinkyring_tip", "GL-008"
    AddMap "thumb_link1_encoder_inner_glove", "gl_thumb_link1", "GL-009"
    AddMap "thumb_tip_glove_j3", "gl_thumb_tip", "GL-010"
    AddMap "encoder_case_index_proxy", "gl_encoder_case_proximal", "GL-011"
    AddMap "encoder_case_index_distal", "gl_encoder_case_distal", "GL-012"
    AddMap "encoder_case_index_distal_pin", "gl_index_encoder_case_pin", "GL-013"
    AddMap "encoder_case_pinkyring_distal_pin", "gl_pinkyring_encoder_case_pin", "GL-014"
    AddMap "distal_encoder_lid", "gl_encoder_lid", "GL-015"
    AddMap "index_proxy_hinge_pin", "gl_index_proximal_hinge_pin", "GL-016"
    AddMap "index_proxy_encoder_pin", "gl_index_proximal_encoder_pin", "GL-017"
    AddMap "index_tip_hinge_pin", "gl_tip_hinge_pin", "GL-018"
    AddMap "index_tip_encoder_pin", "gl_index_tip_encoder_pin", "GL-019"
    AddMap "middle_proxy_hinge_pin", "gl_middle_proximal_hinge_pin", "GL-020"
    AddMap "middle_proxy_encoder_pin3", "gl_middle_proximal_encoder_pin", "GL-021"
    AddMap "middle_tip_encoder_pin", "gl_middle_tip_encoder_pin", "GL-022"
    AddMap "pinkyring_proxy_hinge_pin", "gl_pinkyring_proximal_hinge_pin", "GL-023"
    AddMap "pinkyring_proxy_encoder_pin", "gl_pinkyring_proximal_encoder_pin", "GL-024"
    AddMap "pinkyring_distal_hinge_pin", "gl_pinkyring_tip_hinge_pin", "GL-025"
    AddMap "pinkyring_tip_encoder_pin", "gl_pinkyring_tip_encoder_pin", "GL-026"
    AddMap "thumb_pin2", "gl_thumb_pin", "GL-027"
    AddMap "thumb_encoder_pin2", "gl_thumb_encoder_pin", "GL-028"
    AddMap "thumb_tip_encoder_pin", "gl_thumb_tip_encoder_pin", "GL-029"
End Sub

Private Function LookupIndex(baseName As String) As Long
    Dim i As Long
    LookupIndex = -1
    For i = 0 To nMap - 1
        If LCase$(baseName) = oldNames(i) Or LCase$(baseName) = LCase$(newNames(i)) Then
            LookupIndex = i: Exit Function
        End If
    Next i
End Function

Private Function BaseName(path As String) As String
    Dim f As String
    f = Mid$(path, InStrRev(path, "\") + 1)
    If InStrRev(f, ".") > 0 Then f = Left$(f, InStrRev(f, ".") - 1)
    BaseName = f
End Function

Private Function ErrName(code As Long) As String
    Select Case code
        Case 0: ErrName = "None"
        Case 1: ErrName = "UnspecifiedInternalError"
        Case 2: ErrName = "InvalidSelection"
        Case 3: ErrName = "InvalidForDrawings"
        Case 4: ErrName = "NoModelLoaded"
        Case 5: ErrName = "ComponentNotResolved"
        Case 6: ErrName = "LightWeightComponent"
        Case 7: ErrName = "RoutingComponent"
        Case 8: ErrName = "FileAlreadyExists"
        Case 9: ErrName = "InvalidCharactersInName"
        Case 10: ErrName = "InvalidVirtualComponent"
        Case 11: ErrName = "NameTooLong"
        Case 12: ErrName = "DocumentNameInUse"
        Case 13: ErrName = "PendingNameAlreadyInUse"
        Case 14: ErrName = "ReadOnlyDocument"
        Case 15: ErrName = "DocumentNotSaved"
        Case Else: ErrName = "code " & code & " (see swRenameDocumentError_e)"
    End Select
End Function

Sub Main()
    Dim swApp As Object, swModel As Object, swAssy As Object, swExt As Object
    Dim vComps As Variant, comp As Object, compDoc As Object
    Dim i As Long, idx As Long, path As String, base As String, key As String
    Dim byPath As Object: Set byPath = CreateObject("Scripting.Dictionary")   ' path -> Collection of components
    Dim done As Object: Set done = CreateObject("Scripting.Dictionary")
    Dim nRenamed As Long, nSkipped As Long, nErr As Long, ret As Long
    Dim errs As Long, warns As Long, ok As Boolean, inst As Variant

    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    If swModel Is Nothing Then MsgBox "No active document.": Exit Sub
    If swModel.GetType <> swDocASSEMBLY Then MsgBox "Active document must be an assembly.": Exit Sub
    Set swAssy = swModel
    Set swExt = swModel.Extension

    BuildMap
    Debug.Print "=== rename_parts v2 on " & swModel.GetPathName & "  DRY_RUN=" & DRY_RUN & " ==="

    ' Resolve everything so RenameDocument does not choke on lightweight comps
    If Not DRY_RUN Then swAssy.ResolveAllLightWeightComponents False

    vComps = swAssy.GetComponents(False)
    If IsEmpty(vComps) Then MsgBox "No components found.": Exit Sub

    ' group component instances by file path
    For i = LBound(vComps) To UBound(vComps)
        Set comp = vComps(i)
        If comp.IsSuppressed Then GoTo NextGroup
        path = comp.GetPathName
        If Len(path) = 0 Then GoTo NextGroup
        key = LCase$(path)
        If Not byPath.Exists(key) Then byPath.Add key, New Collection
        byPath(key).Add comp
NextGroup:
    Next i

    Dim k As Variant
    For Each k In byPath.Keys
        Set comp = byPath(k)(1)
        base = BaseName(comp.GetPathName)
        idx = LookupIndex(base)
        If idx < 0 Then
            Debug.Print "  (not in map)  " & base
            GoTo NextFile
        End If
        If LCase$(base) = LCase$(newNames(idx)) Then
            Debug.Print "  already named  " & base
            nSkipped = nSkipped + 1
            GoTo TagProps
        End If
        If DRY_RUN Then
            Debug.Print "  WOULD RENAME   " & base & "  ->  " & newNames(idx) & "   [" & bomIds(idx) & "]  (" & byPath(k).Count & " instance(s))"
            GoTo NextFile
        End If

        ' try each instance until one is accepted (pattern instances are rejected)
        ok = False
        For Each inst In byPath(k)
            Set comp = inst
            comp.SetSuppression2 swComponentFullyResolved
            swModel.ClearSelection2 True
            If comp.Select4(False, Nothing, False) Then
                ret = swExt.RenameDocument(newNames(idx))
                swModel.ClearSelection2 True
                If ret = 0 Then
                    ok = True: Exit For
                Else
                    Debug.Print "     instance " & comp.Name2 & " -> " & ErrName(ret)
                End If
            Else
                Debug.Print "     instance " & comp.Name2 & " -> could not select"
            End If
        Next inst
        If ok Then
            Debug.Print "  renamed        " & base & "  ->  " & newNames(idx)
            nRenamed = nRenamed + 1
        Else
            Debug.Print "  ERROR renaming " & base
            nErr = nErr + 1
            GoTo NextFile
        End If

TagProps:
        If WRITE_BOM_ID And Not DRY_RUN Then
            Set compDoc = comp.GetModelDoc2
            If Not compDoc Is Nothing Then
                compDoc.Extension.CustomPropertyManager("").Add3 "BOM_ID", swCustomInfoText, bomIds(idx), swCustomPropertyReplaceValue
                compDoc.Extension.CustomPropertyManager("").Add3 "PART_NAME", swCustomInfoText, newNames(idx), swCustomPropertyReplaceValue
                If SAVE_PARTS Then compDoc.Save3 swSaveAsOptions_Silent, errs, warns
            End If
        End If
NextFile:
    Next k

    Debug.Print "=== done: renamed=" & nRenamed & " already-ok=" & nSkipped & " errors=" & nErr & " ==="
    If Not DRY_RUN Then
        swModel.Save3 swSaveAsOptions_Silent, errs, warns
        MsgBox "Renamed " & nRenamed & ", skipped " & nSkipped & ", errors " & nErr & vbCrLf & _
               "Now activate the other assembly and run again, then File > Save All.", vbInformation
    Else
        MsgBox "Dry run complete - see Immediate window (Ctrl+G). Set DRY_RUN = False to apply.", vbInformation
    End If
End Sub
