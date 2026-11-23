import * as T from './vendor/three.module.min.js';

const up = new T.Vector3(0, 0, 1);
function geometry(model, id) {
  const type = model.geom_type[id],
    size = model.geom_size.subarray(3 * id, 3 * id + 3);
  if (type === 4) return new T.SphereGeometry(1, 28, 18).scale(...size);
  if (type === 5) return new T.CylinderGeometry(size[0], size[0], 2 * size[1], 36).rotateX(Math.PI / 2);
  if (type === 6) return new T.BoxGeometry(...Array.from(size, (x) => 2 * x));
  if (type !== 7) throw new Error(`Unexpected geometry type ${type}`);
  const mesh = model.geom_dataid[id],
    v = 3 * model.mesh_vertadr[mesh],
    f = 3 * model.mesh_faceadr[mesh];
  const result = new T.BufferGeometry();
  result.setAttribute(
    'position',
    new T.BufferAttribute(new Float32Array(model.mesh_vert.subarray(v, v + 3 * model.mesh_vertnum[mesh])), 3),
  );
  result.setIndex(
    new T.BufferAttribute(new Uint32Array(model.mesh_face.subarray(f, f + 3 * model.mesh_facenum[mesh])), 1),
  );
  result.computeVertexNormals();
  return result;
}

// Ranges address triangles in the simplified CAD surfaces. Split the indexed
// draw by material and retain the original normals and collision geometry.
function colorHardware(geometry, base, faceRanges, appearance) {
  const { palette, questFacePlane } = appearance;
  if (!faceRanges) return base;
  const indices = geometry.index.array;
  const groups = new Uint8Array(indices.length / 3);
  const materials = [base];
  for (const [name, ranges] of Object.entries(faceRanges)) {
    const material = base.clone();
    material.color.set(palette[name]);
    if (name === 'quest_shell') {
      // Shade the two sides of the faceplate seam within each CAD triangle.
      material.onBeforeCompile = (shader) => {
        shader.uniforms.facePlane = { value: new T.Vector4(...questFacePlane) };
        shader.uniforms.faceColor = { value: new T.Color(palette.quest_face) };
        shader.vertexShader =
          'uniform vec4 facePlane; varying float faceHeight;\n' +
          shader.vertexShader.replace(
            '#include <begin_vertex>',
            '#include <begin_vertex>\nfaceHeight = dot(facePlane,vec4(position,1.0));',
          );
        shader.fragmentShader =
          'uniform vec3 faceColor; varying float faceHeight;\n' +
          shader.fragmentShader.replace(
            '#include <color_fragment>',
            '#include <color_fragment>\ndiffuseColor.rgb = mix(diffuseColor.rgb,faceColor,smoothstep(-0.00012,0.00012,faceHeight));',
          );
      };
    }
    if (name === 'arm_silver' || name === 'pins') {
      material.metalness = 0.38;
      material.roughness = 0.42;
    }
    if (name === 'printed_shell') material.roughness = 0.82;
    if (name === 'servo_case') material.metalness = 0.35;
    if (name === 'lens_glass') material.roughness = 0.18;
    const id = materials.push(material) - 1;
    for (const [first, count] of ranges) groups.fill(id, first, first + count);
  }
  const sorted = new Uint32Array(indices.length);
  let next = 0;
  for (let id = 0; id < materials.length; id++) {
    const start = next;
    for (let f = 0; f < groups.length; f++) {
      if (groups[f] !== id) continue;
      sorted.set(indices.subarray(3 * f, 3 * f + 3), next);
      next += 3;
    }
    geometry.addGroup(start, next - start, id);
  }
  geometry.setIndex(new T.BufferAttribute(sorted, 1));
  return materials;
}

export class Viewer {
  constructor(canvas, sim) {
    this.sim = sim;
    this.canvas = canvas;
    this.scene = new T.Scene();
    this.scene.background = new T.Color(0xe5eae5);
    this.camera = new T.PerspectiveCamera(32, 1, 0.01, 12);
    this.camera.up.copy(up);
    this.renderer = new T.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = T.PCFSoftShadowMap;
    this.scene.add(new T.HemisphereLight(0xffffff, 0xbac0c1, 2.1));
    const light = new T.DirectionalLight(0xfffcf5, 2.6);
    light.position.set(0.3, -0.5, 1.4);
    light.target.position.set(0.25, 0, 0);
    Object.assign(light.shadow.camera, { left: -0.7, right: 0.7, top: 0.7, bottom: -0.7, near: 0.2, far: 3 });
    light.shadow.mapSize.set(2048, 2048);
    light.shadow.normalBias = 0.0007;
    light.castShadow = true;
    this.scene.add(light, light.target);
    this.objects = [];
    this.objectMeshes = [];
    for (let i = 0; i < sim.model.ngeom; i++) {
      if (sim.model.geom_group[i] === 3) continue;
      const rgba = sim.model.geom_rgba.subarray(4 * i, 4 * i + 3);
      const material = new T.MeshStandardMaterial({
        color: new T.Color().setRGB(...rgba, T.SRGBColorSpace),
        roughness: 0.64,
        metalness: 0.08,
      });
      const shape = geometry(sim.model, i);
      const name = sim.mj.mj_id2name(sim.model, 5, i);
      const mesh = new T.Mesh(
        shape,
        colorHardware(shape, material, sim.appearance.faces[name], sim.appearance),
      );
      mesh.matrixAutoUpdate = false;
      mesh.castShadow = i !== sim.bench;
      mesh.receiveShadow = true;
      this.scene.add(mesh);
      this.objects.push([i, mesh]);
      if (sim.model.geom_bodyid[i] === sim.objectBody) this.objectMeshes.push(mesh);
    }
    const grid = new T.GridHelper(6, 120, 0xb3bfb6, 0xcdd7cf);
    grid.rotation.x = Math.PI / 2;
    grid.position.z = -0.2395843;
    this.scene.add(grid);
    const [[xmin, xmax], [ymin, ymax]] = sim.tableBounds;
    const ink = new T.MeshBasicMaterial({
      color: 0x368052,
      transparent: true,
      opacity: 0.78,
      depthWrite: false,
    });
    const width = 0.0014;
    for (const x of [xmin + width / 2, xmax - width / 2]) {
      const edge = new T.Mesh(new T.PlaneGeometry(width, ymax - ymin), ink);
      edge.position.set(x, (ymin + ymax) / 2, sim.tableZ + 0.00055);
      this.scene.add(edge);
    }
    for (const y of [ymin + width / 2, ymax - width / 2]) {
      const edge = new T.Mesh(new T.PlaneGeometry(xmax - xmin, width), ink);
      edge.position.set((xmin + xmax) / 2, y, sim.tableZ + 0.00055);
      this.scene.add(edge);
    }
    const tint = new T.Mesh(
      new T.PlaneGeometry(xmax - xmin, ymax - ymin),
      new T.MeshBasicMaterial({ color: 0x63ad78, transparent: true, opacity: 0.14, depthWrite: false }),
    );
    tint.position.set((xmin + xmax) / 2, (ymin + ymax) / 2, sim.tableZ + 0.00025);
    this.scene.add(tint);
    this.focus = new T.Vector3();
    this.cameraMode('arm');
    this.pointerControls();
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(canvas);
    this.resize();
    this.draw();
  }

  dispose() {
    this.resizeObserver.disconnect();
    this.scene.traverse((object) => {
      object.geometry?.dispose();
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      for (const material of materials) material?.dispose();
    });
    this.renderer.dispose();
    this.renderer.forceContextLoss();
  }

  resize() {
    const width = this.canvas.clientWidth,
      height = this.canvas.clientHeight;
    if (!width || !height) return;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
    this.dirty = true;
  }

  cameraMode(mode) {
    this.focus.set(...(mode === 'hand' ? [0.425, -0.025, this.sim.tableZ + 0.075] : [0.36, 0, 0.17]));
    this.radius = mode === 'hand' ? 0.63 : 1.7;
    this.angle = mode === 'hand' ? -0.85 : 0.28;
    this.elevation = mode === 'hand' ? 0.69 : 0.38;
    if (mode === 'table') {
      this.focus.set(0.435, 0.0, this.sim.tableZ + 0.085);
      this.radius = 1.04;
      this.angle = -0.82;
      this.elevation = 0.66;
    }
    this.updateCamera();
  }

  updateCamera() {
    const r = this.radius * Math.cos(this.elevation);
    this.camera.position.set(
      this.focus.x + r * Math.cos(this.angle),
      this.focus.y + r * Math.sin(this.angle),
      this.focus.z + this.radius * Math.sin(this.elevation),
    );
    this.camera.lookAt(this.focus);
    this.camera.updateMatrixWorld();
    this.dirty = true;
  }

  draw() {
    const d = this.sim.data;
    for (const [id, mesh] of this.objects) {
      const p = d.geom_xpos.subarray(3 * id, 3 * id + 3),
        m = d.geom_xmat.subarray(9 * id, 9 * id + 9);
      mesh.matrix.set(m[0], m[1], m[2], p[0], m[3], m[4], m[5], p[1], m[6], m[7], m[8], p[2], 0, 0, 0, 1);
      mesh.matrixWorldNeedsUpdate = true;
    }
    this.renderer.render(this.scene, this.camera);
    this.dirty = false;
  }

  pointerControls() {
    const ray = new T.Raycaster(),
      plane = new T.Plane(up),
      hit = new T.Vector3();
    const aim = (event) => {
      const box = this.canvas.getBoundingClientRect();
      ray.setFromCamera(
        new T.Vector2(
          (2 * (event.clientX - box.left)) / box.width - 1,
          1 - (2 * (event.clientY - box.top)) / box.height,
        ),
        this.camera,
      );
    };
    this.canvas.addEventListener('pointerdown', (event) => {
      if (event.button !== 0 || this.pointer) return;
      aim(event);
      const picked = ray.intersectObjects(this.objectMeshes, false)[0];
      this.setDown = null;
      this.pointer = { id: event.pointerId, x: event.clientX, y: event.clientY, onObject: !!picked };
      if (picked) {
        plane.constant = -picked.point.z;
        const p = this.sim.objectPosition();
        // Lift objects from the bowl or from outside the pickup area.
        this.pointer.extract =
          this.sim.inBowl || !this.sim.pickupInReach(p);
        this.pointer.offset = [p[0] - picked.point.x, p[1] - picked.point.y];
      }
      this.canvas.setPointerCapture(event.pointerId);
      this.canvas.style.cursor = 'grabbing';
    });
    this.canvas.addEventListener('pointermove', (event) => {
      aim(event);
      const p = this.pointer;
      if (!p) {
        this.canvas.style.cursor = ray.intersectObjects(this.objectMeshes, false).length ? 'pointer' : 'grab';
        return;
      }
      if (event.pointerId !== p.id) return;
      if (p.onObject) {
        if (ray.ray.intersectPlane(plane, hit)) this.dragTarget = [hit.x + p.offset[0], hit.y + p.offset[1]];
      } else {
        this.angle -= (event.clientX - p.x) * 0.006;
        this.elevation = Math.max(0.1, Math.min(1.4, this.elevation + (event.clientY - p.y) * 0.006));
        this.updateCamera();
      }
      p.x = event.clientX;
      p.y = event.clientY;
    });
    const release = () => {
      // A fast pointer can reach its drop point before the object clears
      // the rim. Let the mouse spring finish that short move before releasing.
      if (this.pointer?.extract && this.dragTarget) {
        this.setDown = { xy: this.dragTarget, until: this.sim.data.time + 1.6 };
      }
      this.pointer = null;
      this.dragTarget = null;
      this.canvas.style.cursor = 'grab';
    };
    this.canvas.addEventListener('lostpointercapture', release);
    this.canvas.addEventListener('pointercancel', release);
    this.canvas.addEventListener(
      'wheel',
      (event) => {
        event.preventDefault();
        this.radius = Math.max(0.34, Math.min(1.8, this.radius * Math.exp(event.deltaY * 0.001)));
        this.updateCamera();
      },
      { passive: false },
    );
  }

  dragForce() {
    const target = this.dragTarget || this.setDown?.xy;
    if (!target) return [0, 0, 0];
    const p = this.sim.objectPosition(),
      v = this.sim.data.qvel;
    if (this.pointer?.extract || this.setDown) {
      // Lift the object clear of the rim before pulling sideways.
      const mass = this.sim.model.body_mass[this.sim.objectBody];
      const desiredHeight = 0.071;
      const clearance = Math.max(0, Math.min(1, (p[2] - 0.053) / 0.012));
      const wanted = this.sim.tablePlacement(target);
      if (
        this.setDown &&
        (this.sim.data.time >= this.setDown.until ||
          (Math.hypot(wanted[0] - p[0], wanted[1] - p[1]) < 0.003 && Math.hypot(v[15], v[16]) < 0.025))
      ) {
        this.setDown = null;
        return [0, 0, 0];
      }
      const planar = wanted.map((value, i) => clearance * 9 * (value - p[i]) - 0.49 * v[15 + i]);
      const gain = Math.min(1, 0.48 / (Math.hypot(...planar) || 1));
      return [
        planar[0] * gain,
        planar[1] * gain,
        Math.max(0, Math.min(0.7, mass * 9.81 + 12 * (desiredHeight - p[2]) - 0.49 * v[17])),
      ];
    }
    const f = this.sim.tablePlacement(this.dragTarget).map((x, i) => 5 * (x - p[i]) - 0.18 * v[15 + i]);
    const scale = Math.min(1, 0.65 / (Math.hypot(...f) || 1));
    return [scale * f[0], scale * f[1], 0];
  }
}
