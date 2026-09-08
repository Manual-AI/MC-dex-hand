# Manual-Dex ESP32 glove firmware

Planned firmware reads the eight Bourns 3382G joint potentiometers on an Adafruit
HUZZAH32 ESP32 Feather and streams measurements to the host. **TODO:** source, exact
board variant, ADC pin map and verified wiring.

The new [LeRobot host adapter](../../lerobot/README.md) expects the versioned
[raw-ADC serial contract](../../lerobot/PROTOCOL.md). This is a proposed interface,
not a protocol already implemented by released firmware. The host-side
[two-pose calibration tutorial](../../lerobot/CALIBRATION.md) is included; measured
glove/hand calibration and physical acquisition remain unverified.
