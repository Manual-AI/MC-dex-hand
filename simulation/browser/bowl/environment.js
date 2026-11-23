import { resourceURL } from './resources.js';
import loadMuJoCo from '../vendor/mujoco.js';
import { Simulation, mountMeshes } from '../physics.js';

async function asset(path, format) {
  const response = await fetch(resourceURL(path));
  if (!response.ok) throw Error(`Could not load ${path}`);
  if (format === 'gzip') return new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  return response[format]();
}

export async function loadBowl() {
  const [mj, xml, meshes, catalog, grid, appearance] = await Promise.all([
    loadMuJoCo({ locateFile: name => resourceURL('../vendor/' + name) }), asset('./scene.xml','text'), asset('../assets/meshes.tar.gz','gzip'),
    asset('./objects.json','json'), asset('../assets/kinematics.json','json'), asset('../assets/appearance.json','json'),
  ]);
  mountMeshes(mj.FS, meshes);
  return { catalog, create(item) {
    mj.FS.writeFile('/bowl.xml', xml.replace('<!--OBJECT_GEOMETRY-->',item.geoms.join('\n')));
    const sim = new BowlSimulation(mj, mj.MjModel.mj_loadXML('/bowl.xml'), grid, appearance);
    sim.item = item;
    return sim;
  }};
}

export function randomGenerator(seed) {
  let state = seed >>> 0;
  return () => ((state = (Math.imul(1664525,state) + 1013904223) >>> 0) / 4294967296);
}

class BowlSimulation extends Simulation {
  configureFixture() {
    const {mj, model} = this;
    this.bowlFloor = mj.mj_name2id(model, 5, 'bowl_floor');
    this.bowlCenter = Array.from(model.geom_pos.slice(3*this.bowlFloor,3*this.bowlFloor+2));
    this.walls = new Set(Array.from({length:24}, (_,i)=>mj.mj_name2id(model,5,'bowl_wall_'+i)));
  }

  setClosure(amount) {
    if (!this.handShape) return super.setClosure(amount);
    this.data.ctrl.set(this.handShape.map(value=>value*amount),7);
  }

  tablePlacement(xy) {
    const r = this.item ? Math.max(...this.item.points.map(p=>Math.hypot(...p))) : .027;
    return xy.map((v,i)=>Math.max(this.tableBounds[i][0]+r,Math.min(this.tableBounds[i][1]-r,v)));
  }

  throwOntoTable(seed) {
    // Only the unattended landing is screened. Replay that same flight for the user.
    let candidate=seed>>>0;
    for (let i=0;i<40;i++) {
      this.launch(candidate);
      let struckHand=false;
      while(!this.active && !this.dropped) {
        this.flight([0,0,0]);
        struckHand ||= this.robotContact;
      }
      const p=this.objectPosition();
      if(!struckHand && this.benchContact && this.readyTicks>=5 &&
          p[0]>.291 && p[0]<.617 && p[1]>-.193 && p[1]<.177 &&
          Math.hypot(p[0]-this.bowlCenter[0],p[1]-this.bowlCenter[1])>.105) {
        this.launch(candidate);
        return;
      }
      candidate=(Math.imul(candidate,1664525)+1013904223)>>>0;
    }
    this.launch(candidate,true);
  }

  launch(seed, overhead=false) {
    const rand = randomGenerator(Math.imul(seed^(seed>>>16),2654435761)), between = (a,b)=>a+(b-a)*rand();
    this.mj.mj_resetData(this.model, this.data);
    const d = this.data;
    // Aim a ballistic toss at the work surface, with launch side, spin and landing point varying independently.
    const dest = [between(.331,.565),between(-.157,.044)];
    const edge = Math.floor(rand()*3);
    const start = [...dest];
    if (edge===0) start[1]=-.247;
    else start[0]=edge===1 ? .247 : .666;
    const vz=between(.00,.32), height=between(.11,.19);
    const flight=(vz+Math.sqrt(vz*vz+2*9.81*(height-.017)))/9.81;
    if(overhead) { start[0]=.44;start[1]=-.10; }
    const velocity=overhead ? [.04,.02] : dest.map((v,i)=>.77*(v-start[i])/flight);
    const u=rand(),v=rand()*2*Math.PI,w=rand()*2*Math.PI;
    d.qpos.set([...start,this.tableZ+height,Math.sqrt(u)*Math.cos(w),Math.sqrt(1-u)*Math.sin(v),Math.sqrt(1-u)*Math.cos(v),Math.sqrt(u)*Math.sin(w)],15);
    d.qvel.set([...velocity,vz,between(-10,10),between(-10,10),between(-9,9)],15);
    this.target=[.43,.042,.153,0];
    const home=this.armTarget();d.ctrl.set(home);d.qpos.set(home);
    this.mj.mj_forward(this.model,d);
    this.tick=0;this.readyTicks=0;this.flightTicks=0;this.attempt=0;
    this.lifted=false;this.transported=false;this.inBowl=false;this.stable=0;this.completed=false;
    this.firstGrip=null;this.liftTicks=0;this.active=false;this.dropped=false;
    this.checkContacts();
  }

  checkContacts() {
    const d=this.data,p=this.objectPosition(), contacts=d.contact;
    let support=false,bowl=false,robot=false,finger=false,thumb=false;
    for (let i=0;i<d.ncon;i++) {
      const c=contacts.get(i);
      const other=this.model.geom_bodyid[c.geom1]===this.objectBody ? c.geom2 : this.model.geom_bodyid[c.geom2]===this.objectBody ? c.geom1 : -1;
      if(other>=0) {
        support ||= other===this.bench;
        bowl ||= other===this.bowlFloor || this.walls.has(other);
        robot ||= this.model.geom_bodyid[other]!==0;
        finger ||= this.fingers[other]===0;thumb ||= this.fingers[other]===1;
      }
      c.delete();
    }
    contacts.delete();
    this.touch=[finger,thumb];this.robotContact=robot;this.benchContact=support;this.bowlContact=bowl;
    if(this.active && finger && thumb && !bowl && !support && p[2]>.042) {
      this.firstGrip ??= p.slice(0,2);
      if(++this.liftTicks>=3) this.lifted=true;
    } else this.liftTicks=0;
    const dist=Math.hypot(p[0]-this.bowlCenter[0],p[1]-this.bowlCenter[1]);
    if(this.lifted && this.firstGrip && robot && Math.hypot(p[0]-this.firstGrip[0],p[1]-this.firstGrip[1])>.035) this.transported=true;
    this.inBowl=bowl && dist<.061 && p[2]>.002 && p[2]<.05;
    this.stable=this.transported && this.inBowl && !robot && Math.hypot(...d.qvel.subarray(15,18))<.035 ? this.stable+1 : 0;
    if(this.stable>=12) this.completed=true;
    this.dropped = p[2]<-.10;
  }

  flight(force) {
    this.advance(force);
    this.flightTicks++;
    const speed=Math.hypot(...this.data.qvel.subarray(15,18));
    this.readyTicks=this.benchContact && speed<.09 ? this.readyTicks+1 : 0;
    if(this.readyTicks>=5 || this.flightTicks>=42) this.active=true;
  }

  dispose() {
    this.integration.options.delete();
    this.data.delete();
    this.model.delete();
  }
}
