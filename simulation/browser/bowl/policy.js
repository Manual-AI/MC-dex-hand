import { shapeObservation, knots, stride, actionAt } from './motion.js';

function unpack(layers) {
  const decode=s=>new Float32Array(Uint8Array.from(atob(s),c=>c.charCodeAt(0)).buffer);
  return layers.map(l=>({w:decode(l.w),b:decode(l.b)}));
}

function forward(layers, input, point=false) {
  for(let k=0;k<layers.length;k++) {
    const {w,b}=layers[k],out=new Float32Array(b.length);
    for(let j=0;j<out.length;j++) {
      let y=b[j],at=j*input.length;
      for(let i=0;i<input.length;i++) y+=w[at+i]*input[i];
      out[j]=k===layers.length-1 ? y : point ? Math.max(0,y) : y<0 ? Math.expm1(y) : y;
    }
    input=out;
  }
  return input;
}

export class BowlPolicy {
  constructor(spec) {
    this.spec=spec;
    this.point=unpack(spec.pointLayers);
    this.actor=unpack(spec.actorLayers);
  }

  observe(sim, ignoreShape=false) {
    const {points,state}=shapeObservation(sim), pooled=new Float32Array(48).fill(-Infinity);
    const high=[-Infinity,-Infinity,-Infinity],low=[Infinity,Infinity,Infinity];
    for(const p of points) {
      const z=forward(this.point,p,true);
      for(let j=0;j<z.length;j++) pooled[j]=Math.max(pooled[j],z[j]);
      for(let j=0;j<3;j++) { high[j]=Math.max(high[j],p[j]);low[j]=Math.min(low[j],p[j]); }
    }
    const x=[...pooled,...high,...low,...state];
    return x.map((v,i)=>ignoreShape&&i<54 ? 0 : (v-this.spec.mean[i])/this.spec.std[i]);
  }

  proposals(sim, previous=[], ignoreShape=false) {
    const x=this.observe(sim,ignoreShape);
    const y=forward(this.actor,x), {prototypes,mean,basis}=this.spec.decoder;
    const scores=Array.from(y.slice(0,prototypes.length));
    // Diversify only after an unsuccessful real attempt on the same object.
    for(const old of previous) scores[old]-=8;
    const order=scores.map((_,i)=>i).sort((a,b)=>scores[b]-scores[a]);
    const residual=basis.map((_,i)=>this.spec.residual*Math.tanh(y[prototypes.length+i]));
    const anchor=sim.objectPosition().slice(0,2);
    return order.map((first,rank)=>{
      const second=order[rank===0?1:0], blend=this.spec.blend;
      const latent=prototypes[first].map((v,i)=>v*(1-blend)+blend*prototypes[second][i]+residual[i]);
      const chunk=mean.map((v,j)=>latent.reduce((sum,c,i)=>sum+c*basis[i][j],v));
      return {chunk,index:first,anchor,tick:0,score:scores[first]};
    });
  }

  plan(sim,previous=[],ignoreShape=false) {
    return this.proposals(sim,previous,ignoreShape)[0];
  }
}

export class BowlController {
  constructor(sim,policy,ignoreShape=false) {
    this.sim=sim;this.policy=policy;this.ignoreShape=ignoreShape;
    this.history=[];this.plan=null;this.waiting=false;this.attempts=0;
    this.heldTicks=0;this.lastUserHold=false;
  }
  get needsPlan() {
    const s=this.sim;
    return s.active&&!this.plan&&!this.waiting&&!s.dropped&&!(s.transported&&s.inBowl&&!s.robotContact);
  }
  install(plan) {
    this.plan=plan;this.attempts++;
    this.sim.handShape=plan.chunk.slice(105,113);
  }
  step(force=[0,0,0],userHold=false) {
    const s=this.sim;
    if(!s.active) {s.flight(force);return;}
    if(userHold) {
      // A mouse-held object cannot earn a deposit. Start a new pickup from its released pose.
      s.completed=false;s.lifted=false;s.transported=false;s.firstGrip=null;s.stable=0;
      this.waiting=false;this.plan=null;this.history=[];
      s.advance(force);this.lastUserHold=true;return;
    }
    if(this.lastUserHold) {
      this.lastUserHold=false;s.lifted=false;s.transported=false;s.firstGrip=null;s.stable=0;s.completed=false;
    }
    if(this.waiting) {
      s.advance(force);
      if(s.inBowl) return;
      this.waiting=false;s.completed=false;s.lifted=false;s.transported=false;s.firstGrip=null;
      this.plan=null;this.history=[];
    }
    if(!this.plan && s.transported && s.inBowl && !s.robotContact) {
      s.advance(force);
      if(s.completed && s.inBowl) this.waiting=true;
      return;
    }
    if(!this.plan) {
      this.install(this.policy.plan(s,this.history,this.ignoreShape));
    }
    const m=this.plan;
    const target=actionAt(m.chunk,m.tick,m.anchor,s.bowlCenter,s.objectPosition());
    s.drive(target,force);m.tick++;
    if(s.completed&&s.inBowl&&!s.robotContact&&m.tick>=18*stride) {
      this.waiting=true;return;
    }
    if(m.tick>=knots*stride) {
      this.history.push(m.index);if(this.history.length>7)this.history.shift();
      this.plan=null;
    }
  }
}
