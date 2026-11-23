# MC-dex-hand

[Paper](#paper) · [Simulation](#simulation) · [Hardware](#hardware) · [Bill of materials](bom/README.md) · [Teleoperation](lerobot/README.md) · [Contact](#contact) · [Citation](#citation)

<p align="center">
  <a href="docs/assets/mc-dex-hand-demo.gif"><img src="docs/assets/prototype-preview.gif" alt="The robot hand mirroring the operator’s wearable glove" width="614"></a>
</p>

MC-dex-hand pairs a wearable sensing glove with an eight-joint robot hand. The two
shells have matching finger linkages and contact surfaces. After calibration, each
glove joint angle maps to the corresponding robot joint. Both assemblies are right-handed.

## Paper

The glove records finger angles, wrist pose and wrist-camera video while a person manipulates objects.
Our NeurIPS 2026 workshop paper describes how we map those demonstrations to the robot and
evaluate the resulting policies on the Cube in Cup and Egg Carton tasks.

[Democratizing Data-Efficient Robot Learning with Robot-Free Demonstrations (PDF)](docs/paper/mc-dex-hand-neurips2026.pdf).

## [Simulation](simulation/README.md)

We wanted to make MC-Dex as easy as possible to work with, so we’ve prepared assets and initial simulation samples for a range of engines. Below you’ll find samples from Isaac Sim, MuJoCo, Genesis, SuperDex, Alloy and Steel, with force estimates from each.

**New!** [Try the interactive browser policy](https://manual-ai.github.io/MC-dex-hand/). Throw an object onto the table, push it during the reach, or drag it back out of the bowl. The simulation and policy run in your browser. [Controls, results and offline version](simulation/browser/bowl/README.md).

<p align="center">
  <a href="docs/assets/simulation/bowl/bowl-engines.mp4"><img src="docs/assets/simulation/bowl/preview.gif" width="768" height="432" alt="Native simulator views of the MC-Dex hand carrying a brick to the bowl on OpenArm, with a force trace for each capture."></a>
</p>
<p align="center">
  <a href="docs/assets/simulation/bowl/bowl-engines.mp4">Watch the full object-to-bowl comparison</a><br>
  <sub>Close-up excerpt of the scripted carry and release. Each engine simulates the moving brick and renders its own camera.</sub>
</p>

[Individual engine videos and force estimates](simulation/COMPARISON.md) · [Simulation assets and setup](simulation/README.md) · [Standalone hand models](models/manual_dex/README.md).

<a id="meet-the-glove-and-robot-hand"></a>

## Hardware

![Glove shell driven by human hand. Four finger groups pivot on a backplate. The glove carries a wrist-tracking controller and an ESP32 that reads eight rotary potentiometers.](docs/images/wearable-glove-wrist-side.png)

![Matched robot shell driven by compact actuators. The frame holds the proximal servos and each moving proximal link carries a distal servo. The controller mount and enclosure match the glove.](docs/images/robot-hand-wrist-side.png)

Both wrist-side views use the same scale. The glove and robot share white printed shells, a white Quest controller with a black upper face, and an Arducam with a green board and black M12 lens holder. The robot’s finger links expose the red-and-black Feetech servos.

The [paired kinematics animation](docs/assets/manual-dex-paired-kinematics.gif) shows the
corresponding joints through a flexion cycle. The controller mounts match so that the
two devices have the same controller silhouette in an overhead view. For the wrist-camera
view, the operator wears a black fingerless glove and the paper’s preprocessing recolors exposed skin.

To build either assembly, start with the [hardware comparison and parts lists](bom/README.md),
then follow the [illustrated assembly guide](docs/assembly/README.md).
The [STEP assemblies](hardware/step/), printable meshes, images and videos use Git LFS.
After cloning, run `git lfs install --local` and then `git lfs pull` from the repository root.

## Teleoperation

The [LeRobot tutorial](lerobot/README.md) uses a synthetic glove to drive the simulated
fingers with the arm held fixed. It includes calibration and local recording of joint
commands and measured simulator positions. The physical setup still needs released glove
firmware, a verified servo-bus driver and synchronized camera and wrist-pose capture.
[Physical hardware integration](lerobot/HARDWARE.md)

## Contact

For any questions about the glove, reach out to [amir@manualcognition.ai](mailto:amir@manualcognition.ai)

## License

See the [licenses and attribution](NOTICE).

## Citation

```bibtex
@inproceedings{belder2026democratizing,
  title     = {Democratizing Data-Efficient Robot Learning with Robot-Free Demonstrations},
  author    = {Belder, Amir and Berman, Omri and Rabinovich, Roman and Oz, Navot and Barazida, Nir and Wetzler, Aaron},
  booktitle = {8th Robot Learning Workshop: Is Physical AI Going Zero-Shot? at the 40th Conference on Neural Information Processing Systems (NeurIPS)},
  year      = {2026},
  url       = {https://github.com/Manual-AI/MC-dex-hand}
}
```
