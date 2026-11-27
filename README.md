# MC-dex-hand

<p align="center">
  <a href="#paper">Paper</a> ·
  <a href="#simulation">Simulation</a> ·
  <a href="#hardware">Hardware</a> ·
  <a href="bom/README.md">Bill of materials</a> ·
  <a href="lerobot/README.md">Teleoperation</a> ·
  <a href="#contact">Contact</a> ·
  <a href="#citation">Citation</a>
</p>

<p align="center">
  <a href="docs/assets/mc-dex-hand-demo.gif"><img src="docs/assets/prototype-preview.gif" alt="The robot hand mirroring the operator’s wearable glove" width="614"></a>
</p>

Collecting high-quality robot demonstrations remains a major practical bottleneck for robot learning.
Teleoperation requires continuous access to the target robot and can be substantially slower than
natural human manipulation. MC-DexHand is a co-designed glove and robot gripper intended to
facilitate data-efficient robot learning from demonstrations collected without the target robot.

During manipulation, the glove records synchronized wrist-camera images, six-degree-of-freedom
wrist poses, and eight finger joint angles. The gripper has eight active degrees of freedom and
shares the glove’s finger linkages and contact surfaces, so each calibrated glove angle maps
directly to its corresponding gripper joint. Lightweight post-processing recolors visible skin
to match the glove and aligns each demonstration with the robot’s execution speed. The estimated
component cost is $80 for the glove, or $430 including the Quest wrist-tracking kit.

## Paper

Our NeurIPS 2026 workshop paper describes how we align the glove recordings with the robot’s timing and
evaluate the resulting policies on the Cube in Cup and Egg Carton tasks.

📖 [Democratizing Data-Efficient Robot Learning with Robot-Free Demonstrations (PDF)](docs/paper/mc-dex-hand-neurips2026.pdf).

## Simulation

We wanted to make MC-Dex as easy as possible to work with, so we’ve prepared assets and initial simulation samples for a range of engines. Below you’ll find samples from Isaac Sim, MuJoCo, Genesis, SuperDex, Alloy and Steel, with force estimates from each.

[Get started with simulation of MC-DexHand](https://github.com/Manual-AI/MC-dex-hand/blob/main/simulation/README.md).

<p align="center">
  <a href="docs/assets/simulation/bowl/bowl-engines.mp4"><img src="docs/assets/simulation/bowl/preview.gif" width="768" height="432" alt="Native simulator views of the MC-Dex hand carrying a brick to the bowl on OpenArm, with a force trace for each capture."></a>
</p>

📣 [<img src="docs/assets/new-badge.svg" alt="New!" width="42" height="20" align="middle"> Try the interactive browser policy](https://manual-ai.github.io/MC-dex-hand/). Throw an object onto the table, push it during the reach, or drag it back out of the bowl. The simulation and policy run in your browser. [Controls, results and offline version](simulation/browser/bowl/README.md).

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

For any questions about the glove, reach out to [aaron@manualcognition.ai](mailto:aaron@manualcognition.ai)

## License

The glove and hand designs use the [noncommercial hardware terms](hardware/LICENSE). See [licenses by component](LICENSING.md) or contact [Aaron](mailto:aaron@manualcognition.ai) for commercial licensing.

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
