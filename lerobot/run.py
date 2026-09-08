#!/usr/bin/env python3
"""One-command, synthetic-glove LeRobot demo; never opens physical devices."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build/lerobot"
sys.path.insert(0, str(ROOT))
from simulation.run import environment, execute, uv_binary  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", choices=("mujoco", "genesis", "superdex", "isaacsim"))
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--viewer", action="store_true", help="Open the engine's native viewer (default: headless)")
    parser.add_argument("--record", action="store_true", help="Save one state-only episode locally, never upload")
    parser.add_argument("--no-setup", action="store_true", help="Reuse installed environments and prepared models offline")
    parser.add_argument("--accept-isaac-eula", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        parser.error("The automatic setup is tested on Linux x86-64 only")
    if not math.isfinite(args.seconds) or not 1 <= args.seconds <= 3600 or args.timeout <= args.seconds:
        parser.error("Use --seconds in [1, 3600] and a larger --timeout")
    if args.record and not args.seconds.is_integer():
        parser.error("LeRobot episode_time_s requires a whole number of seconds")
    if args.engine == "isaacsim" and not args.accept_isaac_eula:
        parser.error("Review NVIDIA's terms first, then explicitly pass --accept-isaac-eula")
    BUILD.mkdir(parents=True, exist_ok=True)
    lock = (BUILD / "launcher.lock").open("a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error("Another LeRobot launcher is running in this checkout")
    if not args.no_setup:
        execute([sys.executable, ROOT / "simulation/run.py", "prepare"])
    elif not (ROOT / "build/simulation/generated/openarm_manual_dex.xml").is_file():
        parser.error("Missing model package: run once without --no-setup")
    # Do not rebuild shared models or install into a running engine's environment.
    sim_lock = (ROOT / "build/simulation/launcher.lock").open("a+")
    try:
        fcntl.flock(sim_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error("A simulation launcher is running; wait for it to finish")
    python = BUILD / "env/bin/python"
    if not args.no_setup:
        environment(args.engine)
        uv = uv_binary()
        if not python.is_file():
            execute([uv, "venv", "--python", "3.12.3", BUILD / "env"])
        execute([uv, "pip", "install", "--python", python, "-r", ROOT / "lerobot/requirements.txt"])
        execute([uv, "pip", "install", "--python", python, "--no-deps", "-e", ROOT / "lerobot"])
    if not python.is_file():
        parser.error("Missing LeRobot environment: run once without --no-setup")
    run_id = uuid.uuid4().hex
    cli = "lerobot-record" if args.record else "lerobot-teleoperate"
    config = "record_sim.yaml" if args.record else "teleop_sim.yaml"
    command = [python.parent / cli, f"--config_path={ROOT / 'lerobot/configs' / config}",
               "--teleop.type=manual_dex_glove", "--teleop.source=synthetic", "--robot.type=manual_dex_sim",
               f"--robot.engine={args.engine}", f"--robot.repo_root={ROOT}",
               f"--robot.headless={str(not args.viewer).lower()}",
               f"--robot.accept_isaac_eula={str(args.accept_isaac_eula).lower()}"]
    dataset = BUILD / "datasets" / f"{args.engine}-{run_id[:8]}"
    if args.record:
        command += [f"--dataset.episode_time_s={int(args.seconds)}", f"--dataset.root={dataset}",
                    "--dataset.push_to_hub=false"]
    else:
        command.append(f"--teleop_time_s={args.seconds}")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env.update(MANUAL_DEX_TELEOP_RUN_ID=run_id, HF_HUB_OFFLINE="1", HF_DATASETS_OFFLINE="1")
    if not args.viewer:
        env["DISPLAY"] = ""  # Stock record CLI uses timed episodes without a global keyboard listener.
        env["WAYLAND_DISPLAY"] = ""
    log = BUILD / "logs" / f"{cli}-{args.engine}-{run_id[:8]}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    print(f"Synthetic glove → LeRobot → {args.engine}; no hardware. Log: {log}", flush=True)
    with log.open("w") as stream:
        process = subprocess.Popen(list(map(str, command)), cwd=ROOT, env=env, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=args.timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
    if code:
        print("\n".join(log.read_text(errors="replace").splitlines()[-45:]), file=sys.stderr)
        raise SystemExit(code)
    result = BUILD / "results" / f"{args.engine}.json"
    evidence = json.loads(result.read_text())
    if evidence.get("run_id") != run_id or evidence.get("actions", 0) < 1:
        raise RuntimeError(f"No fresh LeRobot actions recorded; inspect {log}")
    for field in ("positions_rad", "motion_span_rad"):
        values = evidence.get(field, {})
        if len(values) != 8 or not all(math.isfinite(v) for v in values.values()):
            raise RuntimeError(f"Invalid simulator readback in {result}")
    if min(evidence["motion_span_rad"].values()) < .001:
        raise RuntimeError(f"Not all eight hand joints moved; inspect {result}")
    if args.record:
        info = json.loads((dataset / "meta/info.json").read_text())
        if info["total_episodes"] != 1 or info["total_frames"] < 1:
            raise RuntimeError("No complete local dataset episode")
        print(f"Local state-only dataset: {dataset}; {info['total_frames']} frames; upload disabled")
    print(json.dumps(evidence, indent=2))
    print("Passed: fresh finite eight-joint motion through the real LeRobot CLI. No dynamics/hardware validation.")


if __name__ == "__main__":
    main()
