// Run the fixed Cartesian and finger commands in the browser's MuJoCo plant.
import fs from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const [runtimePath, programPath, outputPath] = process.argv.slice(2);
if (!outputPath) throw Error('Usage: node reference.mjs BROWSER_DIR PROGRAM.json OUTPUT.json');
globalThis.fetch = async url => new Response(fs.readFileSync(fileURLToPath(url)));
const runtime = pathToFileURL(resolve(runtimePath) + '/');
const { loadBowl } = await import(new URL('bowl/environment.js', runtime));
const { actionAt } = await import(new URL('bowl/motion.js', runtime));
const program = JSON.parse(fs.readFileSync(programPath));
const factory = await loadBowl();
const item = factory.catalog.find(item => item.id === program.object);
if (!item) throw Error('Unknown object in the programmed trajectory');
const sim = factory.create(item);
sim.throwOntoTable(program.seed);
while (!sim.active && !sim.dropped) sim.flight([0, 0, 0]);
const anchor = sim.objectPosition().slice(0, 2);
const sample = () => ({
  q: Array.from(sim.data.qpos), u: Array.from(sim.data.ctrl), v: Array.from(sim.data.qvel),
  hand: sim.robotContact, bowl: sim.bowlContact, carried: sim.transported, lift: sim.lifted,
});
const rows = [sample()];
const trajectory = program.knots.flat();
for (let tick = 0; tick < 258; tick++) {
  sim.drive(actionAt(trajectory, tick, anchor, sim.bowlCenter, sim.objectPosition()), [0, 0, 0]);
  rows.push(sample());
}
if (!sim.completed) throw Error('The programmed reference failed to deposit the brick');
fs.writeFileSync(outputPath, JSON.stringify(rows));
console.log('Recorded', rows.length, 'control samples at 24 Hz.');
sim.dispose();
