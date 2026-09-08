# Manual-Dex Bill of Materials

Generated from `bom/robot_hand.csv` and `bom/glove.csv` by `tools/gen_bom_md.py`. Edit the CSVs, not this file.

**Status legend:** `in CAD` = present in the released STEP assembly; `TODO` = required for a working build but not modelled in CAD - fill in before release.

All *make* parts are FDM printed in ABS or PETG. Parts marked *mirror for left* need a mirrored copy for a left-hand variant. A TODO in that column means handedness is not yet verified.

## Robot hand

- **Make (3D printed):** 20 unique parts, 20 pieces
- **Buy:** 15 line items (25 pieces counted, 4 quantities still TODO)
- **Shared with the other assembly:** 14 line items

### Robot hand: Make - 3D printed parts

#### Structure

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| RH-001 | palm_plate_j3_robot | 1 | palm | ABS or PETG | yes | in CAD | Main palm plate; servo mounting |
| RH-002 | robot_glove_backplate_j3 | 1 | palm | ABS or PETG | yes | in CAD | Back of hand plate |
| RH-003 | index_proxy_link | 1 | index | ABS or PETG | yes | in CAD | Proximal link |
| RH-004 | index_tip_robot_j3 | 1 | index | ABS or PETG | yes | in CAD | Distal link / fingertip contact surface |
| RH-005 | middle_proxy_link_j4 | 1 | middle | ABS or PETG | yes | in CAD | Proximal link |
| RH-006 | middle_tip_robot_j3 | 1 | middle | ABS or PETG | yes | in CAD | Distal link / fingertip contact surface |
| RH-007 | pinkyring_proxy_link | 1 | pinky-ring | ABS or PETG | yes | in CAD | Combined ring+pinky proximal link |
| RH-008 | pinkyring_tip_robot | 1 | pinky-ring | ABS or PETG | yes | in CAD | Combined ring+pinky distal link |
| RH-009 | thumb_link1_test | 1 | thumb | ABS or PETG | yes | in CAD | Thumb link 1 (rename: drop _test suffix) |
| RH-010 | thumb_link1_support_rod | 1 | thumb | ABS or PETG | yes | in CAD | Printed support rod for thumb link 1 |
| RH-011 | thumb_pin | 1 | thumb | ABS or PETG | yes | in CAD | Printed pin; runs in MR105ZZ bearing |
| RH-012 | thumb_tip_robot_j3 | 1 | thumb | ABS or PETG | yes | in CAD | Thumb distal link / contact surface |
| RH-013 | OpenArm_adaptor | 1 | wrist | ABS or PETG | yes | in CAD | Wrist flange adaptor to OpenArm |

#### Enclosure

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| RH-014 | electronics_box1 | 1 | electronics | ABS or PETG | no | in CAD | Shared with glove |
| RH-015 | electronics_box1_lid | 1 | electronics | ABS or PETG | no | in CAD | Shared with glove |

#### Camera

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| RH-016 | camera_mount_v2 | 1 | camera | ABS or PETG | yes | in CAD | Shared with glove; identical camera pose on both |
| RH-017 | camera_adaptor_v2 | 1 | camera | ABS or PETG | yes | in CAD | Shared with glove |

#### Tracking

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| RH-018 | 01_Base | 1 | tracking | ABS or PETG | TODO | in CAD | Quest mount base; see bom/THIRD_PARTY.md for source status; left-hand compatibility not yet verified |
| RH-019 | 02_Hinged_cap | 1 | tracking | ABS or PETG | TODO | in CAD | Quest mount hinged cap; see bom/THIRD_PARTY.md for source status; left-hand compatibility not yet verified |
| RH-020 | 03_Receiver_8x9 | 1 | tracking | ABS or PETG | TODO | in CAD | Quest mount receiver; four 8 x 5 x 3 mm pads with centered 8 x 9 mm clear gaps; left-hand compatibility not yet verified |

### Robot hand: Buy - off-the-shelf

#### Camera

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| RH-103 | USB camera module 2 MP | 1 | camera | 2 MP, USB 2.0 UVC | TODO | TODO | in CAD | Same module and pose on glove. Fill in exact module (sensor; lens FOV; board size) |

#### Tracking

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| RH-104 | Meta Quest Touch Plus controller (right) | 1 | tracking | Quest 3 / 3S Touch Plus, right hand | Meta | TODO | in CAD | Rigidly mounted via Quest_mount_assembly (base; hinged cap; receiver); provides 6-DOF pose |

#### Actuator

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| RH-101 | Feetech HLS3606 dual-shaft serial bus servo | 8 | fingers | HLS3606, dual shaft, serial bus | Feetech / AliExpress | HLS3606 | in CAD | 2 per finger group (index; middle; pinky-ring; thumb). CAD model is Feetech HL_3606_C002 |

#### Hardware

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| RH-102 | Ball bearing MR105ZZ 5x10x4 mm | 1 | thumb | 5 mm ID x 10 mm OD x 4 mm, shielded | Generic | MR105ZZ | in CAD | Thumb pin bearing; the only bearing in the design - all other joints rotate directly on the servo dual-shaft output |

#### Electronics

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| RH-201 | Serial bus servo driver board | 1 | electronics | TTL serial bus servo adapter (e.g. Feetech FE-URT-1 or Waveshare Bus Servo Adapter) | TODO | TODO | TODO | Not in CAD. Confirm which board is used and whether it fits electronics_box1 |
| RH-202 | Servo power supply | 1 | electronics | TODO: voltage/current (HLS3606 nominal V; ~8 servos peak) | TODO | TODO | TODO | Not in CAD |
| RH-203 | Servo daisy-chain cables | 8 | wiring | 3-pin servo bus cables, length TODO | Feetech | TODO | TODO | Not in CAD; count assumes one cable per servo |
| RH-204 | USB cable for camera | 1 | wiring | TODO | TODO | TODO | TODO | Not in CAD |

#### Fastener

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| RH-105 | Quest mount hinge pin 2 x 20 mm | 1 | tracking | 2 mm diameter x 20 mm length; material TODO | Generic | TODO | in CAD | Quest mount hardware; CAD reference: 04_Pin_2x20_reference; confirm hardware grade and exact standard before purchase |
| RH-106 | Quest mount M3 x 12 mm screw | 1 | tracking | M3 x 12 mm; head style and grade TODO | Generic | TODO | in CAD | Quest mount hardware; CAD reference: 05_M3x12_screw_reference; confirm hardware grade and exact standard before purchase |
| RH-107 | Quest mount M3 nut | 1 | tracking | M3; standard and grade TODO | Generic | TODO | in CAD | Quest mount hardware; CAD reference: 06_M3_nut_reference; confirm hardware grade and exact standard before purchase |
| RH-205 | Servo mounting screws | TODO | fasteners | TODO: e.g. M2 x L self-tapping / machine | Generic | TODO | TODO | Not in CAD; count per servo x 8 |
| RH-206 | Servo horn / output screws | TODO | fasteners | TODO: typically supplied with servo | Feetech | TODO | TODO | Not in CAD |
| RH-207 | Structural screws and heat-set inserts | TODO | fasteners | TODO: sizes (M2/M2.5/M3), lengths, insert type | Generic | TODO | TODO | Not in CAD; palm plate; backplate; camera mount; electronics box; OpenArm flange |

#### Contact

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| RH-208 | Fingertip friction / contact material | TODO | fingers | TODO: e.g. TPU pad, silicone, grip tape | TODO | TODO | TODO | Not in CAD; only if contact surfaces are covered on both hand and glove |

## Glove

- **Make (3D printed):** 36 unique parts, 44 pieces
- **Buy:** 15 line items (33 pieces counted, 3 quantities still TODO)
- **Shared with the other assembly:** 14 line items

### Glove: Make - 3D printed parts

#### Structure

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| GL-001 | palm_plate_j3_glove | 1 | palm | ABS or PETG | yes | in CAD | Glove palm plate; kinematics match palm_plate_j3_robot |
| GL-002 | backplate_j4 | 1 | palm | ABS or PETG | yes | in CAD | Back of hand plate |
| GL-003 | link1_index_j3 | 1 | index | ABS or PETG | yes | in CAD | Proximal link |
| GL-004 | index_tip_glove_j3 | 1 | index | ABS or PETG | yes | in CAD | Distal link / contact surface |
| GL-005 | link1_middle_j4 | 1 | middle | ABS or PETG | yes | in CAD | Proximal link |
| GL-006 | middle_tip_glove_j3 | 1 | middle | ABS or PETG | yes | in CAD | Distal link / contact surface |
| GL-007 | link1_pinkyring_j3 | 1 | pinky-ring | ABS or PETG | yes | in CAD | Combined ring+pinky proximal link |
| GL-008 | pinkyring_tip_glove | 1 | pinky-ring | ABS or PETG | yes | in CAD | Combined ring+pinky distal link |
| GL-009 | thumb_link1_encoder_inner_glove | 1 | thumb | ABS or PETG | yes | in CAD | Thumb link 1 with integrated encoder seat |
| GL-010 | thumb_tip_glove_j3 | 1 | thumb | ABS or PETG | yes | in CAD | Thumb distal link / contact surface |

#### Encoder housing

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| GL-011 | encoder_case_index_proxy | 2 | index / middle | ABS or PETG | yes | in CAD | 2 in assembly: used on index and middle |
| GL-012 | encoder_case_index_distal | 2 | index / middle | ABS or PETG | yes | in CAD | 2 in assembly: used on index and middle |
| GL-013 | encoder_case_index_distal_pin | 1 | index | ABS or PETG | yes | in CAD |  |
| GL-014 | encoder_case_pinkyring_distal_pin | 1 | pinky-ring | ABS or PETG | yes | in CAD |  |
| GL-015 | distal_encoder_lid | 5 | all fingers | ABS or PETG | no | in CAD | 5 lids: index proxy/distal, middle proxy/distal, pinky-ring (confirm). The remaining 3 pots are secured with hot glue instead of a lid |

#### Pin

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| GL-016 | index_proxy_hinge_pin | 1 | index | ABS or PETG | no | in CAD | Printed hinge pin. Plain printed hinge, no bearing |
| GL-017 | index_proxy_encoder_pin | 1 | index | ABS or PETG | no | in CAD | Printed pin coupling joint to pot shaft |
| GL-018 | index_tip_hinge_pin | 3 | index / middle / pinky-ring | ABS or PETG | no | in CAD | 3 in assembly: reused across fingertips. Plain printed hinge, no bearing |
| GL-019 | index_tip_encoder_pin | 1 | index | ABS or PETG | no | in CAD |  |
| GL-020 | middle_proxy_hinge_pin | 1 | middle | ABS or PETG | no | in CAD | Plain printed hinge, no bearing |
| GL-021 | middle_proxy_encoder_pin3 | 1 | middle | ABS or PETG | no | in CAD | Rename: drop numeric suffix |
| GL-022 | middle_tip_encoder_pin | 1 | middle | ABS or PETG | no | in CAD |  |
| GL-023 | pinkyring_proxy_hinge_pin | 1 | pinky-ring | ABS or PETG | no | in CAD | Plain printed hinge, no bearing |
| GL-024 | pinkyring_proxy_encoder_pin | 1 | pinky-ring | ABS or PETG | no | in CAD |  |
| GL-025 | pinkyring_distal_hinge_pin | 1 | pinky-ring | ABS or PETG | no | in CAD | Plain printed hinge, no bearing |
| GL-026 | pinkyring_tip_encoder_pin | 1 | pinky-ring | ABS or PETG | no | in CAD |  |
| GL-027 | thumb_pin2 | 1 | thumb | ABS or PETG | no | in CAD | Rename: drop numeric suffix |
| GL-028 | thumb_encoder_pin2 | 1 | thumb | ABS or PETG | no | in CAD | Rename: drop numeric suffix |
| GL-029 | thumb_tip_encoder_pin | 1 | thumb | ABS or PETG | no | in CAD |  |

#### Enclosure

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| GL-030 | electronics_box1 | 1 | electronics | ABS or PETG | no | in CAD | Shared with robot hand; houses ESP32 Feather |
| GL-031 | electronics_box1_lid | 1 | electronics | ABS or PETG | no | in CAD | Shared with robot hand |

#### Camera

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| GL-032 | camera_mount_v2 | 1 | camera | ABS or PETG | yes | in CAD | Shared with robot hand; identical camera pose |
| GL-033 | camera_adaptor_v2 | 1 | camera | ABS or PETG | yes | in CAD | Shared with robot hand |

#### Tracking

| ID | Part (CAD name) | Qty | Subsystem | Material | Mirror for left | Status | Notes |
|---|---|---|---|---|---|---|---|
| GL-034 | 01_Base | 1 | tracking | ABS or PETG | TODO | in CAD | Quest mount base; see bom/THIRD_PARTY.md for source status; left-hand compatibility not yet verified |
| GL-035 | 02_Hinged_cap | 1 | tracking | ABS or PETG | TODO | in CAD | Quest mount hinged cap; see bom/THIRD_PARTY.md for source status; left-hand compatibility not yet verified |
| GL-036 | 03_Receiver_8x9 | 1 | tracking | ABS or PETG | TODO | in CAD | Quest mount receiver; four 8 x 5 x 3 mm pads with centered 8 x 9 mm clear gaps; left-hand compatibility not yet verified |

### Glove: Buy - off-the-shelf

#### Camera

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| GL-103 | USB camera module 2 MP | 1 | camera | 2 MP, USB 2.0 UVC | TODO | TODO | in CAD | Same module and pose as robot hand |

#### Tracking

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| GL-104 | Meta Quest Touch Plus controller (right) | 1 | tracking | Quest 3 / 3S Touch Plus, right hand | Meta | TODO | in CAD | Rigidly mounted via Quest_mount_assembly (base; hinged cap; receiver); provides 6-DOF pose |

#### Sensor

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| GL-101 | Bourns 3382G-2-103G rotary position sensor (10 kOhm) | 8 | fingers | 3382G series, 9 mm, single-turn, 10 kOhm, linear taper | Bourns / DigiKey / Mouser | 3382G-2-103G | in CAD | One per joint (2 per finger group). CAD model is 3382g-001-xxx. 5 pots held by printed lids (GL-015), 3 by hot glue |

#### Electronics

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| GL-102 | Adafruit HUZZAH32 ESP32 Feather | 1 | electronics | ESP32-WROOM-32, CP2104 USB-serial, LiPo charger | Adafruit | 3405 | in CAD | Identified from PCB component sub-assembly (CP2104; MCP73831; ESP32_WROOM32; JST-PH). Confirm exact variant (Feather vs Feather V2) |
| GL-201 | LiPo battery for Feather | 1 | electronics | TODO: 3.7 V, capacity, JST-PH 2-pin | TODO | TODO | TODO | Not in CAD; only if glove runs untethered (else USB power) |
| GL-202 | Encoder wiring harness | 8 | wiring | 3 wires per pot (VCC/GND/signal) to ESP32 ADC; wire gauge TODO | Generic | TODO | TODO | Not in CAD; count assumes one harness per pot |
| GL-203 | USB cable for camera | 1 | wiring | TODO | TODO | TODO | TODO | Not in CAD |
| GL-204 | USB cable for ESP32 Feather (data/power) | 1 | wiring | Micro-USB | Generic | TODO | TODO | Not in CAD |

#### Fastener

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| GL-105 | Quest mount hinge pin 2 x 20 mm | 1 | tracking | 2 mm diameter x 20 mm length; material TODO | Generic | TODO | in CAD | Quest mount hardware; CAD reference: 04_Pin_2x20_reference; confirm hardware grade and exact standard before purchase |
| GL-106 | Quest mount M3 x 12 mm screw | 1 | tracking | M3 x 12 mm; head style and grade TODO | Generic | TODO | in CAD | Quest mount hardware; CAD reference: 05_M3x12_screw_reference; confirm hardware grade and exact standard before purchase |
| GL-107 | Quest mount M3 nut | 1 | tracking | M3; standard and grade TODO | Generic | TODO | in CAD | Quest mount hardware; CAD reference: 06_M3_nut_reference; confirm hardware grade and exact standard before purchase |
| GL-206 | Structural screws and heat-set inserts | TODO | fasteners | TODO: sizes (M2/M2.5/M3), lengths, insert type | Generic | TODO | TODO | Not in CAD; encoder cases; palm plate; camera mount; electronics box |
| GL-207 | Potentiometer mounting hardware | 8 | fasteners | TODO: pot nut/washer or press fit | Generic | TODO | remove? | Not in CAD. Pots are held by printed lids or hot glue - likely no dedicated hardware; delete this row if so |

#### Wearable

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| GL-205 | Finger / hand straps | TODO | fingers | TODO: velcro straps, elastic, finger loops | Generic | TODO | TODO | Not in CAD; how the glove attaches to the operator hand |

#### Contact

| ID | Item | Qty | Subsystem | Spec | Supplier | Part no. | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| GL-208 | Fingertip friction / contact material | TODO | fingers | TODO: match robot hand | TODO | TODO | TODO | Not in CAD; only if contact surfaces are covered |

## Shared parts (identical on robot hand and glove)

These are the same physical design on both assemblies - print/buy two of each for a full system.

| Part | BOM IDs |
|---|---|
| 01_Base | RH-018, GL-034 |
| 02_Hinged_cap | RH-019, GL-035 |
| 03_Receiver_8x9 | RH-020, GL-036 |
| Fingertip friction / contact material | RH-208, GL-208 |
| Meta Quest Touch Plus controller (right) | RH-104, GL-104 |
| Quest mount M3 nut | RH-107, GL-107 |
| Quest mount M3 x 12 mm screw | RH-106, GL-106 |
| Quest mount hinge pin 2 x 20 mm | RH-105, GL-105 |
| USB cable for camera | RH-204, GL-203 |
| USB camera module 2 MP | RH-103, GL-103 |
| camera_adaptor_v2 | RH-017, GL-033 |
| camera_mount_v2 | RH-016, GL-032 |
| electronics_box1 | RH-014, GL-030 |
| electronics_box1_lid | RH-015, GL-031 |
