#!/usr/bin/env python3
"""One-command setup and finite OpenArm + Manual-Dex demos; no global package installs."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import venv
import uuid

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "simulation"
BUILD = ROOT / "build/simulation"
VERSIONS = json.loads((HERE / "versions.json").read_text())


def execute(command, **kwargs):
    print("+ " + shlex.join(map(str, command)), flush=True)
    kwargs.setdefault("cwd", ROOT)
    subprocess.run(list(map(str, command)), check=True, **kwargs)


def uv_binary():
    found = shutil.which("uv")
    if found:
        return found
    bootstrap = BUILD / "bootstrap"
    if not (bootstrap / "bin/python").exists():
        venv.EnvBuilder(with_pip=True).create(bootstrap)
    binary = bootstrap / "bin/uv"
    if not binary.exists():
        execute([bootstrap / "bin/python", "-m", "pip", "install", "uv==0.11.16"])
    return binary


def environment(label):
    uv = uv_binary()
    dest = BUILD / "envs" / label
    python = dest / "bin/python"
    if not python.exists():
        execute([uv, "venv", "--python", VERSIONS["python"][label], dest])
    requirements = HERE / "requirements-prepare.txt" if label == "prepare" else HERE / label / "requirements.txt"
    execute([uv, "pip", "install", "--python", python, "-r", requirements])
    return python


def input_digest():
    digest = hashlib.sha256()
    files = [HERE / p for p in ("prepare.py", "check.py", "common.py", "versions.json", "mount.json", "requirements-prepare.txt")]
    files += sorted((ROOT / "models/manual_dex/hand").rglob("*"))
    for path in files:
        if path.is_file():
            digest.update(str(path.relative_to(ROOT)).encode())
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engine", choices=["prepare", "mujoco", "genesis", "superdex", "isaacsim"])
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=1200)
    parser.add_argument("--screenshot", action="store_true")
    parser.add_argument("--backend", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument("--python", type=Path, help="Use an existing engine interpreter without modifying its packages")
    parser.add_argument("--prepare-python", type=Path, help="Use an existing model-builder interpreter")
    parser.add_argument("--no-setup", action="store_true", help="Offline: use prepared models and an existing engine environment")
    parser.add_argument("--rebuild", action="store_true", help="Regenerate assembled models even if input checksums match")
    parser.add_argument("--accept-isaac-eula", action="store_true", help="Explicitly accept NVIDIA's Isaac Sim EULA for this process")
    parser.add_argument("--timeout", type=int, default=900, help="Maximum engine run time in seconds, including initial compilation")
    args = parser.parse_args()
    if platform.system() != "Linux":
        parser.error("The automated bootstrap is tested on Linux. See the engine tutorials for manual setup on other systems.")
    if args.steps < 1 or args.timeout < 1:
        parser.error("--steps and --timeout must be positive")
    if args.engine == "superdex" and args.screenshot:
        parser.error("SuperDex uses its debugger for screenshots; headless runs produce JSON only")
    if args.engine == "isaacsim" and not args.accept_isaac_eula and not args.python and not args.no_setup:
        parser.error("Review NVIDIA's EULA, then pass --accept-isaac-eula, or use --python with an already-accepted installation. See simulation/isaacsim/README.md.")
    BUILD.mkdir(parents=True, exist_ok=True)
    # Keep the descriptor alive for the full launch: shared assets, per-engine
    # environments and result filenames must not be overwritten by another run.
    lock = (BUILD / "launcher.lock").open("a+")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error("Another simulation launcher is running in this checkout. Wait for it to finish.")
    stamp = BUILD / "prepared.sha256"
    model = BUILD / "generated/openarm_manual_dex.xml"
    if args.no_setup:
        if not model.exists():
            parser.error("No prepared model: run without --no-setup once while online")
    else:
        if not shutil.which("git"):
            parser.error("Install Git and Git LFS first; see simulation/README.md")
        execute(["git", "lfs", "pull", "--include=models/manual_dex/hand/meshes/*,models/manual_dex/urdf/meshes/*", "--exclude="])
        key = input_digest()
        if args.rebuild or not model.exists() or not stamp.exists() or stamp.read_text().strip() != key:
            python = args.prepare_python or environment("prepare")
            execute([python, HERE / "prepare.py"])
            execute([python, HERE / "check.py"])
            stamp.write_text(key + "\n")
    if args.engine == "prepare":
        print(f"Prepared model package: {BUILD / 'generated'}")
        return
    python = args.python or (BUILD / "envs" / args.engine / "bin/python" if args.no_setup else environment(args.engine))
    if not python.is_file():
        parser.error(f"Python interpreter not found: {python}")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    run_id = uuid.uuid4().hex
    env["MANUAL_DEX_RUN_ID"] = run_id
    if args.accept_isaac_eula:
        env["OMNI_KIT_ACCEPT_EULA"] = "YES"
    command = [python, HERE / args.engine / "demo.py", "--steps", str(args.steps), "--backend", args.backend]
    if args.headless:
        command.append("--headless")
    if args.screenshot:
        command.append("--screenshot")
    logs = BUILD / "logs"
    logs.mkdir(exist_ok=True)
    log = logs / f"{args.engine}.log"
    print(f"Engine log: {log}", flush=True)
    try:
        with log.open("w") as stream:
            execute(command, cwd=BUILD, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=args.timeout)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print("\n".join(log.read_text(errors="replace").splitlines()[-60:]), file=sys.stderr)
        raise
    result = BUILD / "results" / f"{args.engine}.json"
    if not result.exists():
        raise RuntimeError(f"Engine exited without a result. Inspect {log}")
    result_data = json.loads(result.read_text())
    if result_data.get("run_id") != run_id or result_data.get("status") != "passed":
        raise RuntimeError(f"No successful result from this run (an old result may remain). Inspect {log}")
    print(json.dumps(result_data, indent=2))
    print(f"Run passed. Results: {result.parent}")


if __name__ == "__main__":
    main()
