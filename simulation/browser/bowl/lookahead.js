import {actionAt,knots,stride} from './motion.js';

const memory=['tick','readyTicks','flightTicks','attempt','lifted','transported','inBowl','stable','completed',
  'firstGrip','liftTicks','active','dropped','touch','robotContact','benchContact','bowlContact','target','handShape'];
export function capture(sim) {
  const d=sim.data,flags={};
  for(const name of memory) flags[name]=Array.isArray(sim[name])?[...sim[name]]:sim[name];
  return {q:Array.from(d.qpos),v:Array.from(d.qvel),u:Array.from(d.ctrl),warm:Array.from(d.qacc_warmstart),time:d.time,flags};
}
export function restore(sim,state) {
  const d=sim.data;
  sim.mj.mj_resetData(sim.model,d);
  d.qpos.set(state.q);d.qvel.set(state.v);d.ctrl.set(state.u);d.time=state.time;
  d.qacc_warmstart.set(state.warm);
  sim.mj.mj_forward(sim.model,d);
  d.qacc_warmstart.set(state.warm);
  for(const [k,v] of Object.entries(state.flags)) sim[k]=Array.isArray(v)?[...v]:v;
}

function evaluate(sim,plan) {
  sim.handShape=plan.chunk.slice(105,113);
  for(let t=0;t<knots*stride;t++) {
    sim.drive(actionAt(plan.chunk,t,plan.anchor,sim.bowlCenter,sim.objectPosition()),[0,0,0]);
    if(sim.dropped)return {success:false,retry:false};
    if(t>=18*stride && sim.completed && sim.inBowl && !sim.robotContact)return {success:true};
  }
  for(let t=0;t<720&&sim.transported&&sim.inBowl&&!sim.robotContact&&!sim.completed;t++)sim.advance([0,0,0]);
  return {success:sim.completed&&sim.inBowl&&!sim.robotContact,retry:!sim.dropped&&sim.benchContact};
}

// Rank the actor's proposals with forward simulation of the same 15 physical motors.
// Only a transported object released into the bowl can verify a successful proposal.
export function choose(sim,policy,state,previous=[],budget=48) {
  restore(sim,state);
  const proposals=policy.proposals(sim,previous), visited=new Set(), order=[];
  const append=i=>{if(i<proposals.length&&!visited.has(i)){visited.add(i);order.push(i);}};
  for(let i=0;i<12;i++)append(i);
  for(let i=0;i<budget;i++){append(Math.floor(i*(proposals.length-1)/budget));append(i+12);}
  let trials=0,safe=null;
  for(const rank of order.slice(0,budget)) {
    restore(sim,state);const p=proposals[rank],result=evaluate(sim,p);trials++;
    if(result.success)return {plan:p,trials,verified:true};
    if(!safe&&result.retry)safe=p;
  }
  return {plan:safe??proposals[0],trials,verified:false};
}
