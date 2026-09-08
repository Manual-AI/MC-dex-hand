"""LeRobot 3.12+ client for an isolated simulator process (including Isaac's Python 3.11)."""
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import uuid

from lerobot.robots import Robot, RobotConfig
from .calibration import JOINTS, FEATURES, finite_joints


class SimulatorClient:
    def __init__(self, repo_root, engine, engine_python="", headless=True, accept_isaac_eula=False):
        root = Path(repo_root).resolve()
        if engine not in ("mujoco", "genesis", "superdex", "isaacsim"):
            raise ValueError("Unsupported simulator")
        python = Path(engine_python).resolve() if engine_python else root / "build/simulation/envs" / engine / "bin/python"
        if not python.is_file():
            raise FileNotFoundError(f"Set up {engine} first with simulation/run.py; interpreter missing: {python}")
        parent, child = socket.socketpair()
        parent.settimeout(180)
        self.socket, self.stream, self.process, self.log = parent, parent.makefile("rwb"), None, None
        self.seq = 0
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env["MANUAL_DEX_RPC_FD"] = str(child.fileno())
        env["PYTHONUNBUFFERED"] = "1"
        if accept_isaac_eula:
            env["OMNI_KIT_ACCEPT_EULA"] = "YES"
        log_dir = root / "build/lerobot/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = log_dir / f"{engine}-{uuid.uuid4().hex[:8]}.log"
        self.log = self.log_path.open("wb")
        command = [str(python), str(root / "simulation/teleop_worker.py"), "--engine", engine]
        if headless:
            command.append("--headless")
        try:
            self.process = subprocess.Popen(command, cwd=root, env=env, pass_fds=(child.fileno(),),
                                            stdout=self.log, stderr=subprocess.STDOUT)
            child.close()
            ready = self._receive()
            if ready.get("event") != "ready" or ready.get("engine") != engine:
                raise RuntimeError(f"Worker did not initialize: {ready}")
            self.socket.settimeout(10)
            self.positions = finite_joints(ready["positions"])
        except BaseException:
            child.close()
            self.close()
            raise

    def _receive(self):
        line = self.stream.readline(65537)
        if not line or len(line) > 65536:
            raise RuntimeError(f"Simulator stopped or invalid reply; inspect {self.log_path}")
        reply = json.loads(line)
        if "error" in reply:
            raise RuntimeError(f"Simulator error: {reply['error']}; inspect {self.log_path}")
        return reply

    def request(self, operation, **fields):
        self.seq += 1
        self.stream.write((json.dumps({"op": operation, "seq": self.seq, **fields}, allow_nan=False) + "\n").encode())
        self.stream.flush()
        reply = self._receive()
        if reply.get("seq") != self.seq:
            raise RuntimeError("Simulator reply sequence mismatch")
        if "positions" in reply:
            self.positions = finite_joints(reply["positions"])
        return reply

    def close(self):
        if self.process is not None and self.process.poll() is None:
            try:
                self.socket.settimeout(2)
                self.request("close")
                self.process.wait(timeout=5)
            except Exception:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
        try:
            self.stream.close()
        except OSError:
            pass  # A failed worker may leave an unflushed reply; keep the original error.
        finally:
            self.socket.close()
        if self.log is not None:
            self.log.close()


@RobotConfig.register_subclass("manual_dex_sim")
@dataclass
class ManualDexSimConfig(RobotConfig):
    engine: str = "mujoco"
    repo_root: str = "."
    engine_python: str = ""
    headless: bool = True
    accept_isaac_eula: bool = False
    max_velocity_rad_s: float = 1.0
    control_dt_s: float = 1 / 30


class ManualDexSim(Robot):
    config_class = ManualDexSimConfig
    name = "manual_dex_sim"

    def __init__(self, config):
        super().__init__(config)
        self.config, self.client = config, None
        self._steps = 0
        self.cameras = {}
        self._run_id = os.environ.get("MANUAL_DEX_TELEOP_RUN_ID", uuid.uuid4().hex)
        self._position_min = {name: math.inf for name in JOINTS}
        self._position_max = {name: -math.inf for name in JOINTS}
        self._readback_error = {name: 0. for name in JOINTS}
        if not math.isfinite(config.max_velocity_rad_s) or not 0 < config.max_velocity_rad_s <= 5:
            raise ValueError("Set a finite positive simulated joint rate limit <= 5 rad/s")
        if not math.isfinite(config.control_dt_s) or not 0 < config.control_dt_s <= .1:
            raise ValueError("control_dt_s must be in (0, 0.1]")

    @property
    def action_features(self):
        return dict(FEATURES)

    @property
    def observation_features(self):
        return dict(FEATURES)

    @property
    def is_connected(self):
        return self.client is not None and self.client.process.poll() is None

    @property
    def is_calibrated(self):
        return True  # Simulation coordinates, not a claim about physical calibration.

    def connect(self, calibrate=True):
        if self.client is not None:
            raise RuntimeError("Simulation is already connected")
        self.client = SimulatorClient(self.config.repo_root, self.config.engine, self.config.engine_python,
                                      self.config.headless, self.config.accept_isaac_eula)

    def calibrate(self):
        print("Simulation uses CAD joint radians; calibrate the glove mapping separately.")

    def configure(self):
        pass

    def get_observation(self):
        if not self.is_connected:
            raise RuntimeError("Simulator is not connected")
        return {f"{name}.pos": value for name, value in self.client.positions.items()}

    def send_action(self, action):
        if not self.is_connected:
            raise RuntimeError("Simulator is not connected")
        if set(action) != set(FEATURES):
            raise ValueError("Expected exactly eight .pos actions, in radians")
        target = finite_joints({name: action[f"{name}.pos"] for name in JOINTS})
        # Rate limits are computed from observed, not previously requested, positions.
        delta = self.config.max_velocity_rad_s * self.config.control_dt_s
        sent = {name: max(-1.5, min(1.5, max(self.client.positions[name] - delta,
                 min(self.client.positions[name] + delta, value)))) for name, value in target.items()}
        self.client.request("step", positions=sent, dt=self.config.control_dt_s)
        self._steps += 1
        for name, position in self.client.positions.items():
            self._position_min[name] = min(self._position_min[name], position)
            self._position_max[name] = max(self._position_max[name], position)
            self._readback_error[name] = max(self._readback_error[name], abs(position - sent[name]))
        return {f"{name}.pos": sent[name] for name in JOINTS}

    def disconnect(self):
        if self.client is not None:
            try:
                evidence = {"engine": self.config.engine, "actions": self._steps,
                            "run_id": self._run_id,
                            "max_post_step_deviation_rad": self._readback_error,
                            "motion_span_rad": {name: self._position_max[name] - self._position_min[name]
                                                if self._steps else 0.0 for name in JOINTS},
                            "positions_rad": self.client.positions, "hardware": False,
                            "mode": "LeRobot prescribed simulation state", "dynamics_validated": False}
                path = Path(self.config.repo_root) / "build/lerobot/results" / f"{self.config.engine}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(evidence, indent=2) + "\n")
            finally:
                self.client.close()
                self.client = None
