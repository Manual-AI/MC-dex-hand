// Smoke-test a fixed held-out throw with the released actor and MuJoCo WASM.
import fs from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

globalThis.fetch = async url => new Response(await fs.readFile(fileURLToPath(url)));
const { loadBowl } = await import('./environment.js');
const { BowlPolicy, BowlController } = await import('./policy.js');
const assets = await loadBowl();
const item = assets.catalog.find(item => item.id === 'barbell');
const weights = JSON.parse(await fs.readFile(new URL('./actor.json', import.meta.url)));
const sim = assets.create(item);
const seed = 92020855;
try {
  sim.throwOntoTable(seed);
  const controller = new BowlController(sim, new BowlPolicy(weights));
  let stable = 0;
  for (let tick = 0; tick < 80 * 24; tick++) {
    controller.step();
    stable = controller.waiting && sim.completed && sim.inBowl && !sim.robotContact ? stable + 1 : 0;
    if (stable >= 24) {
      console.log(JSON.stringify({ object: item.id, seed, mode: 'actor', deposited: true, controlTicks: tick + 1 }));
      break;
    }
    if (sim.dropped || tick === 80 * 24 - 1) throw Error('The actor failed to deposit the barbell');
  }
} finally {
  sim.dispose();
}
