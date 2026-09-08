# Manual-Dex host software

Implemented host examples live in [`../lerobot/`](../lerobot/README.md): LeRobot 0.6.1
device plugins, one-command synthetic teleoperation in four simulators, eight-channel
glove calibration, a documented serial input contract and state-only local recording.

Still pending: verified HLS3606 physical bus driver/controller, glove firmware and
wiring, measured calibration, Quest 6-DOF pose, wrist-camera acquisition and arm IK.
The [hardware integration guide](../lerobot/HARDWARE.md) lists the required artifacts;
its inert template is not a working physical-hand driver.
