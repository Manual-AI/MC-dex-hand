const rate = [0.0045, 0.0065, 0.004, 0.09];
const closure = [0.74203792, 0.94971132, 0.74203792, 0.94971132, 0.74203792, 0.94971132, 0, 0.62386193];
const clamp = (x, lo, hi) => Math.min(hi, Math.max(lo, x));

// Meshes are ordinary STL files in a USTAR archive. Keep the XML separately readable.
export function mountMeshes(fs, buffer) {
  const bytes = new Uint8Array(buffer);
  const decoder = new TextDecoder();
  for (let i = 0; i + 512 <= bytes.length && bytes[i]; ) {
    const field = (a, b) =>
      decoder
        .decode(bytes.subarray(i + a, i + b))
        .replace(/\0.*$/s, '')
        .trim();
    const name = field(0, 100),
      size = Number.parseInt(field(124, 136), 8);
    if (!/^[\w-]+\.stl$/.test(name) || !Number.isSafeInteger(size) || i + 512 + size > bytes.length) {
      throw new Error('Invalid mesh archive');
    }
    fs.writeFile('/' + name, bytes.subarray(i + 512, i + 512 + size));
    i += 512 + Math.ceil(size / 512) * 512;
  }
}

export class Simulation {
  constructor(mj, model, grid, appearance) {
    this.appearance = appearance;
    this.mj = mj;
    this.model = model;
    this.data = new mj.MjData(model);
    this.integration = {
      options: model.opt,
      timestep: model.opt.timestep,
      qpos: new Float64Array(model.nq),
      qvel: new Float64Array(model.nv),
      ctrl: new Float64Array(model.nu),
      warm: new Float64Array(model.nv),
    };
    this.grid = grid;
    this.objectBody = mj.mj_name2id(model, 1, 'object');
    this.bench = mj.mj_name2id(model, 5, 'bench');
    this.tableBounds = [0, 1].map((axis) => {
      const index = this.bench * 3 + axis,
        mid = model.geom_pos[index],
        half = model.geom_size[index];
      return [mid - half, mid + half];
    });
    this.tableZ = model.geom_pos[3 * this.bench + 2] + model.geom_size[3 * this.bench + 2];
    this.configureFixture();
    this.fingers = Array.from({ length: model.ngeom }, (_, i) => {
      const body = mj.mj_id2name(model, 1, model.geom_bodyid[i]);
      return body.startsWith('md_') ? Number(body.includes('thumb')) : -1;
    });
  }

  armTarget(target = this.target) {
    const { axes, joints } = this.grid;
    const base = [],
      mix = [];
    for (let j = 0; j < 3; j++) {
      const a = axes[j],
        f = (target[j] - a[0]) / (a[1] - a[0]);
      base[j] = clamp(Math.floor(f), 0, a.length - 2);
      mix[j] = f - base[j];
    }
    const result = Array(7).fill(0);
    for (let k = 0; k < 8; k++) {
      const x = k >> 2,
        y = (k >> 1) & 1,
        z = k & 1;
      const weight = (x ? mix[0] : 1 - mix[0]) * (y ? mix[1] : 1 - mix[1]) * (z ? mix[2] : 1 - mix[2]);
      const index = ((base[0] + x) * axes[1].length + base[1] + y) * axes[2].length + base[2] + z;
      for (let j = 0; j < 7; j++) result[j] += weight * joints[index * 7 + j];
    }
    return result;
  }

  objectPosition() {
    return Array.from(
      this.data.xpos.subarray(this.objectBody * 3, this.objectBody * 3 + 3),
      (value, i) => value - (i === 2 ? this.tableZ : 0),
    );
  }

  pickupInReach(position = this.objectPosition(), margin = 0) {
    return this.grid.axes
      .slice(0, 2)
      .every((axis, i) => position[i] >= axis[0] - margin && position[i] <= axis.at(-1) + margin);
  }

  drive(target, force) {
    const d = this.data,
      model = this.model;
    for (let i = 0; i < 4; i++) {
      const axis = this.grid.axes[i];
      this.target[i] = clamp(
        this.target[i] + clamp(target[i] - this.target[i], -rate[i], rate[i]),
        axis ? axis[0] : 0,
        axis ? axis.at(-1) : 1,
      );
    }
    d.ctrl.set(this.armTarget());
    this.setClosure(this.target[3]);
    this.advance(force);
  }

  setClosure(value) {
    this.data.ctrl.set(
      closure.map((v) => v * value),
      7,
    );
  }

  advance(force) {
    const { data: d, model } = this;
    const wrench = d.xfrc_applied.subarray(this.objectBody * 6, this.objectBody * 6 + 6);
    wrench.fill(0);
    wrench.set(force);
    // Reintegrate an unusually energetic contact at finer resolution. The
    // checkpoint starts this same control interval, including its applied force.
    const checkpoint = this.integration,
      start = d.time;
    checkpoint.qpos.set(d.qpos);
    checkpoint.qvel.set(d.qvel);
    checkpoint.ctrl.set(d.ctrl);
    checkpoint.warm.set(d.qacc_warmstart);
    const restore = () => {
      d.qpos.set(checkpoint.qpos);
      d.qvel.set(checkpoint.qvel);
      d.ctrl.set(checkpoint.ctrl);
      d.time = start;
      d.qacc_warmstart.set(checkpoint.warm);
      this.mj.mj_forward(model, d);
      d.qacc_warmstart.set(checkpoint.warm);
      wrench.set(force);
    };
    const integrate = (count) => {
      for (let i = 0; i < count; i++) {
        this.mj.mj_step(model, d);
        const v = d.qvel;
        const speedSquared = v[15] * v[15] + v[16] * v[16] + v[17] * v[17];
        const spinSquared = v[18] * v[18] + v[19] * v[19] + v[20] * v[20];
        if (!(speedSquared < 64 && spinSquared < 450 * 450 && d.time > start)) return false;
      }
      return true;
    };
    const dt = checkpoint.timestep;
    if (!integrate(10)) {
      let resolved = false;
      try {
        for (const factor of [2, 4, 8, 16]) {
          checkpoint.options.timestep = dt / factor;
          restore();
          if (integrate(10 * factor)) {
            resolved = true;
            break;
          }
        }
        if (!resolved) restore();
      } finally {
        checkpoint.options.timestep = dt;
      }
    }
    this.mj.mj_forward(model, d);
    this.checkContacts();
  }

}
