# OpenArm places a brick in a bowl

<p align="center">
  <a href="../docs/assets/simulation/bowl/bowl-engines.mp4"><img src="../docs/assets/simulation/bowl/preview.gif" width="768" height="432" alt="OpenArm carries a building brick to a bowl, shown through the native engine cameras."></a>
</p>
<p align="center">
  <a href="../docs/assets/simulation/bowl/bowl-engines.mp4">Watch the complete synchronized montage</a><br>
  <sub>The close-up excerpt shows the carry and release. The full video includes the approach, grasp, lift and settling period, with a vertical force trace for each engine.</sub>
</p>

The vertical OpenArm, eight-joint MC-Dex hand, table, bowl and red building brick come from the [interactive demo](browser/bowl/README.md). Each panel uses the same programmed arm and finger trajectory. Each engine advances its own rigid brick at 240 Hz and renders the resulting motion with its own camera. [Reproduce the captures](bowl_showcase/README.md).

<!-- BEGIN measurements -->

| Native video | Renderer | Lift | Peak landing Fz | Settled Fz |
|---|---|---:|---:|---:|
| [Isaac Sim](../docs/assets/simulation/bowl/isaacsim.mp4) | Isaac Sim RTX / Replicator | 94 mm | 0.750 N | 0.248 N |
| [MuJoCo](../docs/assets/simulation/bowl/mujoco.mp4) | MuJoCo offscreen OpenGL | 94 mm | 0.779 N | 0.248 N |
| [Genesis](../docs/assets/simulation/bowl/genesis.mp4) | Genesis rasterizer | 94 mm | 0.762 N | 0.248 N |
| [SuperDex](../docs/assets/simulation/bowl/superdex.mp4) | SuperDex SDK / Polyscope EGL | 94 mm | 0.746 N | 0.248 N |
| [Alloy](../docs/assets/simulation/bowl/alloy.mp4) | Alloy path-traced camera | 94 mm | 0.750 N | 0.248 N |
| [Steel](../docs/assets/simulation/bowl/steel.mp4) | Newton ViewerGL / SolverSteel | 94 mm | 0.753 N | 0.248 N |

<!-- END measurements -->

## What is programmed

The reference trajectory runs once in the browser’s MuJoCo plant to verify that the MC-Dex fingers grasp the brick and deposit it. The native captures start with the brick at rest in its measured landing pose. They replay the same arm and finger angles. During closure, a compliant grasp couples the measured brick position to the moving wrist. The coupling engages only within 40 mm of the intended grasp point, applies up to 2 N and switches off when the hand opens. Gravity, object motion and table and bowl contacts are integrated by each engine throughout. The object uses a common box collision proxy and the mass of the complete brick. The four studs remain visible. The bowl uses a floor and 24 tilted wall segments.

This setup compares the motion and release under a repeatable programmed grasp. Finger pad forces and grasp quality across different contact models would require an experiment with independently resolved finger contacts. The interactive browser policy does use opposed finger contacts and can respond to pushes and dragging. [Browser controller and success criteria](browser/bowl/README.md) · [Fixed motion program](bowl_showcase/program.json).

## Reading the force traces

**Fz** is the estimated vertical interaction force on the brick in newtons, with upward positive. From each engine’s own 240 Hz position samples, the capture adapter estimates vertical velocity and computes `Fz = m × (Δvz / Δt + 9.81)` over each 1/24-second window. It includes support and the programmed grasp force. For this 25.26 g brick, a reading near **0.248 N** is expected at rest in the bowl and near zero during free fall.

The table reports the peak window in the first second after release and the mean over the final half-second. Shorter impact peaks can exceed the displayed window average. In the CSV, `mean_grasp_force_norm_N` is the magnitude of the applied wrist spring force averaged over the same window. The collision geometry, contact settings and temporal averaging are part of the measurement. These simulated values are independent of motor current or physical load-cell readings. [Per-engine force and position samples](../docs/assets/simulation/bowl/forces.csv) · [Versions, camera identities and capture hashes](../docs/assets/simulation/bowl/results.json).

The [four-engine cube tutorial](CUBE_COMPARISON.md) is a separate exercise in opposing finger contacts and placement without a grasp constraint.
