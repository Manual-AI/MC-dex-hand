import { resourceURL, createPreviewWorker } from "./resources.js";
import { loadBowl } from "./environment.js";
import { BowlPolicy, BowlController } from "./policy.js";
import { Viewer } from "../viewer.js";
import { capture } from "./lookahead.js";

const el = (id) => document.getElementById(id);
async function main() {
  const [factory, weights] = await Promise.all([
    loadBowl(),
    fetch(resourceURL("./actor.json")).then((r) => {
      if (!r.ok) throw Error("Could not load the bowl policy");
      return r.json();
    }),
  ]);
  const policy = new BowlPolicy(weights);
  for (const item of factory.catalog)
    el("object").add(new Option(item.name, item.id));
  let sim,
    view,
    control,
    item,
    paused = false,
    last = performance.now(),
    acc = 0,
    pulse = 0,
    angle = 0,
    falls = 0,
    mode = "table";
  const randomSeed = () => crypto.getRandomValues(new Uint32Array(1))[0];
  const openedFromDisk = location.protocol === "file:";
  const params = new URLSearchParams(openedFromDisk && location.hash ? location.hash.slice(1) : location.search);
  function saveReplay() {
    const url = new URL(location.href);
    if (openedFromDisk) url.hash = params.toString();
    else url.search = params.toString();
    history.replaceState({}, "", url);
  }
  el("controller").value = params.get("mode") === "actor" ? "actor" : "preview";
  let worker = null,
    pending = 0,
    serial = 0,
    initialized = false;
  function invalidate() {
    if (pending) {
      worker?.terminate();
      worker = null;
      initialized = false;
      pending = 0;
    }
  }
  function startPreview() {
    if (!worker) {
      worker = createPreviewWorker();
      worker.onmessage = ({ data }) => {
        if (data.request !== pending) return;
        pending = 0;
        if (data.error) {
          failPreview();
          return;
        }
        control.install(data.plan);
        last = performance.now();
        acc = 0;
        update();
      };
      worker.onerror = failPreview;
    }
    pending = ++serial;
    worker.postMessage({
      request: pending,
      weights: initialized ? null : weights,
      object: item.id,
      state: capture(sim),
      history: control.history,
      budget: 48,
    });
    initialized = true;
  }
  function failPreview() {
    worker?.terminate();
    worker = null;
    pending = 0;
    initialized = false;
    el("controller").value = "actor";
    el("notice").textContent =
      "Physics preview unavailable. Using the trained actor directly.";
    params.set("mode", "actor");
    saveReplay();
  }
  el("controller").onchange = () => {
    invalidate();
    el("notice").textContent = "";
    params.set("mode", el("controller").value);
    saveReplay();
    const keepPaused = paused;
    reset(Number(params.get("seed")), item.id);
    paused = keepPaused;
    update();
  };
  function reset(seed, requested) {
    invalidate();
    const id =
      requested === "random"
        ? factory.catalog[seed % factory.catalog.length].id
        : requested;
    item =
      factory.catalog.find((x) => x.id === id) ??
      factory.catalog[seed % factory.catalog.length];
    if (!sim || sim.item.id !== item.id) {
      view?.dispose();
      sim?.dispose();
      const old = el("viewport"),
        canvas = old.cloneNode(false);
      old.replaceWith(canvas);
      sim = factory.create(item);
      sim.throwOntoTable(seed);
      view = new Viewer(canvas, sim);
      view.cameraMode(mode);
    } else sim.throwOntoTable(seed);
    control = new BowlController(sim, policy);
    view.dragTarget = view.setDown = view.pointer = null;
    paused = false;
    acc = 0;
    last = performance.now();
    pulse = 0;
    falls = 0;
    params.set("object", item.id);
    params.set("seed", seed);
    saveReplay();
    el("name").textContent = item.name;
    el("split").textContent =
      item.split === "held-out" ? "Held-out shape" : "Training shape";
    update();
    view.draw();
  }
  function update() {
    const active =
      sim.active &&
      !control.waiting &&
      !paused &&
      !falls &&
      !view.pointer?.onObject &&
      !view.setDown;
    el("run-status").dataset.source = pending
      ? "preview"
      : active
        ? "learned"
        : "idle";
    el("control-source").textContent = pending
      ? "Physics preview"
      : active
        ? "Shape-conditioned policy"
        : "";
    el("status").textContent = paused
      ? "Paused"
      : pending
        ? "Previewing learned grasps"
        : falls
          ? "Off table · rethrowing"
          : view.pointer?.onObject || view.setDown
            ? "Moving object"
            : control.waiting
              ? "In bowl · waiting for removal"
              : !sim.active
                ? "Object in flight"
                : sim.bowlContact
                  ? "Object at bowl"
                  : sim.touch.every(Boolean)
                    ? "Opposed finger contact"
                    : sim.touch.some(Boolean)
                      ? "Finger contact"
                      : sim.benchContact
                        ? "Object on work surface"
                        : "Object airborne";
    el("attempt").textContent = String(control.attempts);
    el("time").textContent = sim.data.time.toFixed(1) + " s";
    el("play").textContent = paused ? "Resume" : "Pause";
  }
  const reseed = () => reset(randomSeed(), el("object").value);
  el("object").onchange = reseed;
  el("throw").onclick = reseed;
  el("push").onclick = () => {
    angle = Math.random() * Math.PI * 2;
    pulse = 3;
    invalidate();
  };
  el("play").onclick = () => {
    paused = !paused;
    last = performance.now();
    acc = 0;
    update();
  };
  for (const k of ["table", "arm", "hand"])
    el(k).onclick = () => {
      mode = k;
      view.cameraMode(k);
      view.draw();
      for (const v of ["table", "arm", "hand"])
        el(v).setAttribute("aria-pressed", String(v === k));
    };
  for (const k of ["play", "push", "throw"]) el(k).disabled = false;
  const seed = params.get("seed");
  reset(
    seed !== null && /^\d{1,10}$/.test(seed)
      ? Number(seed) >>> 0
      : randomSeed(),
    params.get("object") || "random",
  );
  function frame(now) {
    if (!paused && !document.hidden) {
      acc += Math.min((now - last) / 1000, 0.18);
      while (acc >= 1 / 24) {
        const f = view.dragForce();
        if (pulse > 0) {
          f[0] += 0.26 * Math.cos(angle);
          f[1] += 0.26 * Math.sin(angle);
          pulse--;
        }
        const dragging = !!(view.pointer?.onObject || view.setDown);
        if (pending && (dragging || pulse > 0)) invalidate();
        if (
          !dragging &&
          !pulse &&
          control.needsPlan &&
          el("controller").value === "preview"
        ) {
          if (!pending) startPreview();
          acc = 0;
          break;
        }
        control.step(f, dragging);
        acc -= 1 / 24;
        falls = sim.dropped && !dragging ? falls + 1 : 0;
        if (falls >= 48) {
          reseed();
          break;
        }
      }
      update();
      view.draw();
    } else if (view.dirty) view.draw();
    last = now;
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
main().catch((e) => {
  el("status").textContent = e.message;
  console.error(e);
});
