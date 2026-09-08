' ============================================================================
' export_cad.bas  -  SOLIDWORKS VBA macro
' From the ACTIVE assembly, exports:
'   - one binary STL per printed part listed in bom/rename_map.csv (new names)
'   - a STEP (AP214) of the whole assembly
' into  <assembly folder>\export\stl\  and  <assembly folder>\export\step\
'
' BEFORE RUNNING (once):  Tools > Options > System Options > Export
'   File format: STL  -> Output as Binary, Unit: Millimeters, Resolution: Fine
'                        (or Custom: deviation 0.01 mm, angle 5 deg);
'                        untick "Do not translate STL output data to positive space"
'   File format: STEP -> AP214, Export: Solid/Surface geometry
' Then: run Main with the robot assembly active, then again with the glove
' assembly active. Shared cm_* parts are exported twice (identical files).
' ============================================================================
Option Explicit

Const swDocASSEMBLY As Long = 2
Const swDocPART As Long = 1
Const swSaveAsCurrentVersion As Long = 0
Const swSaveAsOptions_Silent As Long = 1
Const swDontRebuildActiveDoc As Long = 0   ' swRebuildOnActivation_e

Dim wanted As Object

Private Sub AddName(n As String)
    wanted.Add LCase$(n), True
End Sub

Private Sub BuildList()
    Set wanted = CreateObject("Scripting.Dictionary")
    AddName "cm_camera_adaptor"
    AddName "cm_camera_mount"
    AddName "cm_electronics_box"
    AddName "cm_electronics_box_lid"
    AddName "01_Base"
    AddName "02_Hinged_cap"
    AddName "03_Receiver_8x9"
    AddName "cm_quest_mount_base"
    AddName "cm_quest_mount_hinged_cap"
    AddName "cm_quest_mount_receiver"
    AddName "gl_backplate"
    AddName "gl_encoder_case_distal"
    AddName "gl_encoder_case_proximal"
    AddName "gl_encoder_lid"
    AddName "gl_index_encoder_case_pin"
    AddName "gl_index_proximal_encoder_pin"
    AddName "gl_index_proximal_hinge_pin"
    AddName "gl_index_proximal_link"
    AddName "gl_index_tip"
    AddName "gl_index_tip_encoder_pin"
    AddName "gl_middle_proximal_encoder_pin"
    AddName "gl_middle_proximal_hinge_pin"
    AddName "gl_middle_proximal_link"
    AddName "gl_middle_tip"
    AddName "gl_middle_tip_encoder_pin"
    AddName "gl_palm_plate"
    AddName "gl_pinkyring_encoder_case_pin"
    AddName "gl_pinkyring_proximal_encoder_pin"
    AddName "gl_pinkyring_proximal_hinge_pin"
    AddName "gl_pinkyring_proximal_link"
    AddName "gl_pinkyring_tip"
    AddName "gl_pinkyring_tip_encoder_pin"
    AddName "gl_pinkyring_tip_hinge_pin"
    AddName "gl_thumb_encoder_pin"
    AddName "gl_thumb_link1"
    AddName "gl_thumb_pin"
    AddName "gl_thumb_tip"
    AddName "gl_thumb_tip_encoder_pin"
    AddName "gl_tip_hinge_pin"
    AddName "rh_backplate"
    AddName "rh_index_proximal_link"
    AddName "rh_index_tip"
    AddName "rh_middle_proximal_link"
    AddName "rh_middle_tip"
    AddName "rh_openarm_adaptor"
    AddName "rh_palm_plate"
    AddName "rh_pinkyring_proximal_link"
    AddName "rh_pinkyring_tip"
    AddName "rh_thumb_link1"
    AddName "rh_thumb_link1_support_rod"
    AddName "rh_thumb_pin"
    AddName "rh_thumb_tip"
End Sub

Private Function BaseName(path As String) As String
    Dim f As String
    f = Mid$(path, InStrRev(path, "\") + 1)
    If InStrRev(f, ".") > 0 Then f = Left$(f, InStrRev(f, ".") - 1)
    BaseName = f
End Function

Private Function ExportName(base As String) As String
    Select Case LCase$(base)
        Case "01_base": ExportName = "cm_quest_mount_base"
        Case "02_hinged_cap": ExportName = "cm_quest_mount_hinged_cap"
        Case "03_receiver_8x9": ExportName = "cm_quest_mount_receiver"
        Case Else: ExportName = base
    End Select
End Function

Private Sub EnsureDir(p As String)
    Dim fso As Object: Set fso = CreateObject("Scripting.FileSystemObject")
    If Not fso.FolderExists(p) Then fso.CreateFolder p
End Sub

Sub Main()
    Dim swApp As Object, swAssy As Object, swPart As Object
    Dim vComps As Variant, comp As Object
    Dim i As Long, path As String, base As String, asmDir As String
    Dim stlDir As String, stepDir As String, outFile As String, asmName As String
    Dim seen As Object: Set seen = CreateObject("Scripting.Dictionary")
    Dim errs As Long, warns As Long, ok As Boolean, nOk As Long, nFail As Long
    Dim hasRobot As Boolean

    Set swApp = Application.SldWorks
    Set swAssy = swApp.ActiveDoc
    If swAssy Is Nothing Or swAssy.GetType <> swDocASSEMBLY Then
        MsgBox "Activate an assembly first.": Exit Sub
    End If
    BuildList

    asmDir = Left$(swAssy.GetPathName, InStrRev(swAssy.GetPathName, "\"))
    EnsureDir asmDir & "export"
    stlDir = asmDir & "export\stl\": EnsureDir stlDir
    stepDir = asmDir & "export\step\": EnsureDir stepDir
    Debug.Print "=== export_cad from " & swAssy.GetPathName & " ==="

    swAssy.ResolveAllLightWeightComponents False
    vComps = swAssy.GetComponents(False)

    For i = LBound(vComps) To UBound(vComps)
        Set comp = vComps(i)
        If comp.IsSuppressed Then GoTo NextComp
        path = comp.GetPathName
        If Len(path) = 0 Then GoTo NextComp
        base = BaseName(path)
        If Not wanted.Exists(LCase$(base)) Then GoTo NextComp
        If seen.Exists(LCase$(base)) Then GoTo NextComp
        seen.Add LCase$(base), True
        If Left$(LCase$(base), 3) = "rh_" Then hasRobot = True

        Set swPart = swApp.ActivateDoc3(path, False, swDontRebuildActiveDoc, errs)
        If swPart Is Nothing Then
            Debug.Print "  FAIL (cannot activate) " & base: nFail = nFail + 1: GoTo NextComp
        End If
        outFile = stlDir & ExportName(base) & ".stl"
        swPart.ClearSelection2 True
        ok = swPart.Extension.SaveAs3(outFile, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, Nothing, errs, warns)
        If ok Then
            Debug.Print "  stl  " & base: nOk = nOk + 1
        Else
            Debug.Print "  FAIL " & base & "  errors=" & errs & " warnings=" & warns: nFail = nFail + 1
        End If
        swApp.CloseDoc path     ' closes the window; doc stays loaded by the assembly
NextComp:
    Next i

    ' back to the assembly, export STEP
    swApp.ActivateDoc3 swAssy.GetPathName, False, swDontRebuildActiveDoc, errs
    asmName = IIf(hasRobot, "manual_dex_hand", "manual_dex_glove")
    swAssy.ClearSelection2 True
    outFile = stepDir & asmName & ".step"
    ok = swAssy.Extension.SaveAs3(outFile, swSaveAsCurrentVersion, swSaveAsOptions_Silent, Nothing, Nothing, errs, warns)
    Debug.Print IIf(ok, "  step " & outFile, "  FAIL STEP errors=" & errs)

    Debug.Print "=== done: stl ok=" & nOk & " failed=" & nFail & " ==="
    MsgBox "Exported " & nOk & " STL files (" & nFail & " failed) and STEP to" & vbCrLf & asmDir & "export\", vbInformation
End Sub
