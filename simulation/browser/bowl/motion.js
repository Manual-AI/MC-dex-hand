// An action chunk contains uniformly spaced wrist and finger target samples.
// The horizontal coordinate is expressed between the observed pickup point and bowl.
export const stride = 12;
export const knots = 21;
export const featuresPerKnot = 5;

export function actionAt(chunk, t, anchor, bowl, object = anchor) {
  const f = Math.min(knots-1, Math.max(0,t/stride));
  const lo = Math.floor(f), hi = Math.min(lo+1,knots-1);
  const a = Array.from({length:featuresPerKnot}, (_,i)=>
    chunk[lo*5+i]+(f-lo)*(chunk[hi*5+i]-chunk[lo*5+i]));
  const correction = chunk[knots*5+8] ?? 0;
  const xy = anchor.map((v,i)=>{
    const shift = Math.max(-.042,Math.min(.042,object[i]-v));
    return v+a[0]*(bowl[i]-v)+.03*a[1+i]+(1-a[0])*correction*shift;
  });
  return [...xy,.1*a[3],a[4]];
}

export function shapeObservation(sim) {
  const p=sim.objectPosition(), rot=sim.data.xmat.subarray(9*sim.objectBody,9*sim.objectBody+9);
  const points=sim.item.points.map(point=>[0,1,2].map(i=>
    40*(rot[3*i]*point[0]+rot[3*i+1]*point[1]+rot[3*i+2]*point[2])));
  const target=sim.target;
  return {points,state:[(p[0]-.45)*6,p[1]*5,p[2]*30,
    (target[0]-p[0])*4,(target[1]-p[1])*4,target[2]*6,target[3],
    ...Array.from(sim.data.qvel.subarray(15,18),v=>Math.max(-1,Math.min(1,v*3)))]};
}
