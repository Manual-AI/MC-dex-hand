# Host software

The [LeRobot tutorial](../lerobot/README.md) maps eight glove channels to the
simulated hand and records local joint-state episodes. Start with the synthetic
glove to exercise the mapping, or use the [calibration guide](../lerobot/CALIBRATION.md)
to prepare a physical glove.

Physical operation still requires glove firmware, a verified Feetech HLS3606 bus
driver, wiring and measured calibration. The physical teleoperation adapter still needs Quest wrist tracking, wrist-camera capture
and an arm controller. The independent browser task includes its own OpenArm inverse kinematics. See the [hardware integration guide](../lerobot/HARDWARE.md).
