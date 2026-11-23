# Objects into a bowl

<p align="center">
  <a href="media/bowl-policy.mp4"><img src="media/bowl-preview.gif" width="768" height="432" alt="The OpenArm and MC-Dex hand pick up a thrown building brick and release it into the bowl."></a>
</p>
<p align="center">
  <a href="media/bowl-policy.mp4">Watch both throws at simulation speed</a><br>
  <sub>The four-second excerpt speeds up the brick pickup. The full video also shows the barbell, a shape held out of training. Both runs use the actor alone.</sub>
</p>

A seven-joint OpenArm carries the eight-joint MC-Dex hand. Reset throws a freely moving object onto the table with randomized orientation and spin. The reset sampler checks for a reachable landing outside the bowl before replaying the throw. The hand must lift it with opposed fingers, carry it at least 35 mm, and release it in the bowl. The bowl and object have physical collision surfaces. The robot controls only its motors.

<a id="run-locally"></a>

## Play in your browser

[Download the standalone demo (HTML, 11.3 MB)](https://github.com/Manual-AI/MC-dex-hand/releases/download/bowl-demo-v1/MC-Dex-Bowl.html). Open **MC-Dex-Bowl.html** from Chrome’s Downloads, or use **File → Open File** to select it. If you already have a local checkout, open `simulation/browser/bowl/MC-Dex-Bowl.html` directly. You can move it to another folder or computer and play offline. It includes MuJoCo, the hand meshes, all 16 objects, the trained actor, the physics-preview worker and the recorded throws. Use a browser with WebGL 2 and WebAssembly. Chrome is tested.

- **Throw object** starts a new release. Choose an object from the menu or leave it on random. The object and seed in the address reproduce the launch.
- **Push object** applies a sideways impulse. Dragging applies a mouse force. The hand waits after a successful deposit and resumes when the object is removed. An object that falls off the table triggers a new throw.
- **Policy only** lets the trained actor select its motion directly. **Policy + physics preview**, the default, tests up to 48 of that actor’s proposals in a separate MuJoCo world before executing one. The live simulation pauses briefly during the preview and remains interactive. Switching controllers replays the same launch.
- The table, hand and arm views share the same simulation. Drag the background to orbit, or scroll to zoom.

## Objects and observations

The 12 training shapes are a building brick, wine cork, eraser, lemon, spool, toy mushroom, wooden mallet, dice block, soap bar, toy pear, cross block and jar. The **domino, acorn, barbell and T block** were reserved for evaluation. Their geometry was excluded from model fitting and checkpoint selection.

Every object is a compound of simple solids. The simulator transforms 96 sampled surface points into the current orientation using the measured object pose. A PointNet-style encoder applies the same neural layers to each point and pools them into a 48-value shape token. The actor also observes the object’s extents, pose-relative wrist target and object velocity. It receives geometric measurements from the simulator. A real depth camera would require segmentation and pose or point-cloud estimation.

The actor outputs scores and a continuous adjustment to a learned wrist-and-finger trajectory representation. At 24 Hz, the task decodes that representation relative to the object and bowl, uses the arm’s inverse-kinematics table, and applies bounded motor targets. A failed attempt triggers a new proposal using the observed state. Offline fitting first predicts physical outcomes with a world model and then trains the actor against the frozen model and measured deposits. The inference package contains the actor, shape encoder and movement decoder. [Actor weights](actor.json) · [Object geometry and point samples](objects.json) · [MuJoCo environment](environment.js) · [Policy inference](policy.js) · [Physics preview](lookahead.js) · [PointNet paper and project](https://stanford.edu/~rqi/pointnet/).

## Browser evaluation

Run `node simulation/browser/bowl/check.mjs` from the repository root for a single reproducible actor-only smoke test (Node.js 22+). The check uses the same weights and MuJoCo WASM as the browser.

Chrome ran the same 512 fresh throws per condition for each controller. Each trial allowed retries within 80 simulated seconds. Success required transport, release, 12 stable control ticks with bowl support, and a subsequent check after at least another simulated second. Every disturbed trial received its assigned push or drag. Falling off the table ended the trial.

| Controller | Clean, all 16 shapes | Disturbed, all 16 shapes | Clean, four held-out shapes | Disturbed, four held-out shapes |
|---|---:|---:|---:|---:|
| Policy only | 394/512 | 372/512 | 95/128 | 91/128 |
| Policy + physics preview | 510/512 | 477/512 | 127/128 | 118/128 |

With physics preview, 381 of the 510 clean successes finished on the first attempt. The median successful clean trial took 11.7 simulated seconds. Rounded objects remain challenging under interference. For example, the lemon reached the bowl in 25/32 disturbed trials with preview and 12/32 with the actor alone.

On a matched subset of 128 held-out actor-only trials, supplying the geometry token and extents gave 96 successful deposits. Replacing them with their training means gave 100. This experiment establishes performance on the four reserved shapes and leaves the independent benefit of shape conditioning uncertain. [Per-object results, controller comparisons and geometry ablation](evaluation.json).


For the programmed cross-engine version of this scene, see the [native videos and force traces](../../COMPARISON.md).

## Rebuild the standalone file

The editable browser app starts at [index.html](index.html). Changes to its JavaScript, weights, meshes or styles should be followed by a rebuild. With Python 3 and esbuild 0.25.11 on your path, run `python3 simulation/browser/bowl/standalone.py` from the repository root. You can pass `--esbuild /path/to/esbuild` to use an existing installation. The output is `simulation/browser/bowl/MC-Dex-Bowl.html`. Open a copy of this file by itself with networking disabled to check both controller modes.

When releasing an updated demo, attach the verified HTML file to a GitHub release in this repository and update the download links in the project, simulation and demo READMEs. GitHub serves raw repository HTML as source text.
