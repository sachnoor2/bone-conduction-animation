import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate, spring, Audio, staticFile } from 'remotion';

// ═══════════════════════════════════════════════════════════════════
//  BONE CONDUCTION — "तुम्हारी आवाज़ Recording में DIFFERENT क्यों?"
//  Format : 1080 × 1920 portrait · 60 fps · 45 s (2700 frames)
//  Style  : 3Blue1Brown × Kurzgesagt × Veritasium
// ═══════════════════════════════════════════════════════════════════

const W = 1080, H = 1920, CX = 540, CY = 960, FPS = 60;

const BG    = '#0A0D14';
const BG2   = '#10152A';
const GOLD  = '#FDCB6E';
const TEAL  = '#00CEC9';
const CORAL = '#E17055';
const BLUE  = '#74B9FF';
const PURP  = '#A29BFE';
const WHITE = '#DFE6E9';
const RED   = '#FF7675';
const AMBER = '#F9A825';

const T = {
  HOOK_S:  0,    HOOK_E:  200,
  SET_S:   175,  SET_E:   520,
  MECH_S:  495,  MECH_E:  1220,
  PROOF_S: 1195, PROOF_E: 1780,
  TWIST_S: 1755, TWIST_E: 2340,
  OUT_S:   2315, OUT_E:   2700,
  TOTAL:   2700,
};

const SUBS = [
  { f:15,   t:175,  h:'तुम जो सुनते हो — वो तुम्हारी आवाज़ नहीं है।',        r:'Tum jo sunte ho — wo tumhari aawaaz nahi hai.',       s:'n' },
  { f:215,  t:475,  h:'तुम्हारी आवाज़ — दो रास्तों से कानों तक पहुँचती है।', r:'Tumhari aawaaz — do raston se kaano tak pahunchti hai.', s:'n' },
  { f:535,  t:760,  h:'पहला रास्ता — हवा के ज़रिए।',                         r:'Pahla raasta — hawa ke zariye.',                       s:'b' },
  { f:790,  t:1060, h:'दूसरा — तुम्हारी खोपड़ी की हड्डियों के ज़रिए।',      r:'Doosra — tumhari khopdi ki haddiyon ke zariye.',       s:'b' },
  { f:1095, t:1360, h:'हड्डियाँ low frequency को boost करती हैं।',           r:'Haddiyan low frequency ko boost karti hain.',          s:'b' },
  { f:1390, t:1640, h:'Microphone सिर्फ हवा capture करता है।',               r:'Microphone sirf hawa capture karta hai.',              s:'n' },
  { f:1795, t:1990, h:'Beethoven... पूरी तरह बहरे थे।',                       r:'Beethoven... poori tarah bahre the.',                  s:'n' },
  { f:2020, t:2290, h:'पर उन्होंने piano को छड़ी से छूकर music सुना।',       r:'Par unhone piano ko chhaddi se chhukar music suna.',   s:'n' },
  { f:2330, t:2540, h:'वो भी — bone conduction था।',                          r:'Wo bhi — bone conduction tha.',                       s:'b' },
  { f:2570, t:2680, h:'तुम्हारी असली आवाज़ वही है — जो दूसरे सुनते हैं।',  r:'Tumhari asli aawaaz wahi hai — jo doosre sunte hain.', s:'n' },
];

const SHAKES = [
  { at:0,    mag:22, dk:48 },
  { at:1755, mag:18, dk:44 },
];

const sr  = (s: number) => { const x = Math.sin(s+1.618)*43758.5453; return x-Math.floor(x); };
const eo6 = (t: number) => 1-Math.pow(1-Math.max(0,Math.min(1,t)),6);
const cl  = (v:number,lo:number,hi:number) => Math.max(lo,Math.min(hi,v));
const sp  = (f:number,st=120,dm=14) => spring({frame:f,fps:FPS,config:{stiffness:st,damping:dm}});

function shake(frame:number):{dx:number;dy:number}{
  let dx=0,dy=0;
  for(const ev of SHAKES){
    const lf=frame-ev.at;
    if(lf>=0&&lf<ev.dk){
      const m=ev.mag*Math.exp(-lf*0.14);
      dx+=(sr(frame*3.3+ev.at)-0.5)*2*m;
      dy+=(sr(frame*2.6+ev.at+1)-0.5)*m*0.5;
    }
  }
  return {dx,dy};
}

function bezierPoints(
  p0:{x:number;y:number}, p1:{x:number;y:number},
  p2:{x:number;y:number}, p3:{x:number;y:number}, n:number
):{x:number;y:number;tx:number;ty:number}[]{
  const pts=[];
  for(let i=0;i<=n;i++){
    const t=i/n, mt=1-t;
    const x=mt*mt*mt*p0.x+3*mt*mt*t*p1.x+3*mt*t*t*p2.x+t*t*t*p3.x;
    const y=mt*mt*mt*p0.y+3*mt*mt*t*p1.y+3*mt*t*t*p2.y+t*t*t*p3.y;
    const tx=3*mt*mt*(p1.x-p0.x)+6*mt*t*(p2.x-p1.x)+3*t*t*(p3.x-p2.x);
    const ty=3*mt*mt*(p1.y-p0.y)+6*mt*t*(p2.y-p1.y)+3*t*t*(p3.y-p2.y);
    pts.push({x,y,tx,ty});
  }
  return pts;
}

// ── GLOBAL DEFS ───────────────────────────────────────────────────
const GlobalDefs:React.FC=()=>(
  <defs>
    <filter id="g3b1b" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="6" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="gcrisp" x="-35%" y="-35%" width="170%" height="170%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="ghalo" x="-100%" y="-100%" width="300%" height="300%">
      <feGaussianBlur stdDeviation="40"/>
    </filter>
    <radialGradient id="nebula" cx="50%" cy="35%" r="65%">
      <stop offset="0%"   stopColor="#A29BFE" stopOpacity="0.1"/>
      <stop offset="50%"  stopColor="#00CEC9" stopOpacity="0.05"/>
      <stop offset="100%" stopColor="#0A0D14" stopOpacity="0"/>
    </radialGradient>
    <radialGradient id="vig" cx="50%" cy="50%" r="70%">
      <stop offset="0%"   stopColor="transparent"/>
      <stop offset="100%" stopColor="#000" stopOpacity="0.78"/>
    </radialGradient>
    <pattern id="scanlines" x="0" y="0" width={W} height="3" patternUnits="userSpaceOnUse">
      <rect width={W} height="1" y="0" fill="#fff" fillOpacity="0.012"/>
    </pattern>
    <linearGradient id="scope-bg" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%"   stopColor="#10152A" stopOpacity="0.95"/>
      <stop offset="100%" stopColor="#050810" stopOpacity="0.95"/>
    </linearGradient>
  </defs>
);

// ── BACKGROUND ────────────────────────────────────────────────────
const Background:React.FC<{frame:number}>=({frame})=>{
  const stars=Array.from({length:140},(_,i)=>({
    x:sr(i*4+1)*W, y:sr(i*4+2)*H,
    r:0.5+sr(i*4+3)*2.2, sp:0.3+sr(i*4+4)*1.8, op:0.2+sr(i*4)*0.6,
  }));
  const drift=interpolate(frame,[0,T.TOTAL],[0,50],{extrapolateRight:'clamp'});
  return(
    <g>
      <rect width={W} height={H} fill={BG}/>
      <rect width={W} height={H} fill="url(#nebula)" transform={`translate(0,${-drift})`}/>
      {stars.map((s,i)=>(
        <circle key={i} cx={s.x} cy={s.y} r={s.r} fill={WHITE}
          opacity={s.op*(0.6+0.4*Math.sin(frame*s.sp*0.016+i*2.3))}/>
      ))}
      <rect width={W} height={H} fill="url(#scanlines)"/>
      <rect width={W} height={H} fill="url(#vig)"/>
    </g>
  );
};

const SoundParticles:React.FC<{frame:number}>=({frame})=>{
  const pts=Array.from({length:18},(_,i)=>({
    x:80+sr(i*3+1)*(W-160), y:200+sr(i*3+2)*(H-400),
    spx:(sr(i*3+3)-0.5)*0.6, spy:(sr(i*3)-0.5)*0.4,
    ph:sr(i*3+2)*Math.PI*2, col:[TEAL,GOLD,PURP,BLUE][i%4],
  }));
  return(
    <g opacity={0.18}>
      {pts.map((p,i)=>{
        const px=(p.x+p.spx*frame)%W;
        const py=(p.y+p.spy*frame+Math.sin(frame*0.02+p.ph)*30)%H;
        const r=3+Math.sin(frame*0.04+p.ph)*2;
        return(<circle key={i} cx={px} cy={py} r={r} fill={p.col}/>);
      })}
    </g>
  );
};

const SPK:{[k:string]:{color:string;label:string}}={
  n:{color:GOLD,label:'🎙 NARRATOR'},
  b:{color:TEAL,label:'🔬 SCIENCE'},
};

const HindiSubs:React.FC<{frame:number}>=({frame})=>{
  const active=SUBS.find(s=>frame>=s.f&&frame<=s.t);
  if(!active)return null;
  const lf=frame-active.f, dur=active.t-active.f;
  const fi=interpolate(lf,[0,12],[0,1],{extrapolateRight:'clamp'});
  const fo=interpolate(lf,[dur-16,dur],[1,0],{extrapolateRight:'clamp'});
  const sl=interpolate(sp(Math.min(lf,28),80,14),[0,1],[22,0]);
  const spk=SPK[active.s]??SPK['n'];
  const PY=H-390;
  return(
    <g opacity={Math.min(fi,fo)} transform={`translate(0,${sl})`}>
      <rect x={44} y={PY} width={W-88} height={148} rx={18}
        fill={BG2} fillOpacity={0.94} stroke={spk.color} strokeWidth={1.5} strokeOpacity={0.5}/>
      <rect x={44} y={PY} width={176} height={36} rx={10}
        fill={spk.color} fillOpacity={0.15}/>
      <text x={132} y={PY+24} textAnchor="middle"
        fontFamily="'Courier New',monospace" fontSize={13} fontWeight="700"
        fill={spk.color} letterSpacing="1">{spk.label}</text>
      <text x={CX} y={PY+74} textAnchor="middle"
        fontFamily="serif" fontSize={30} fill={WHITE} opacity={0.95}>{active.h}</text>
      <text x={CX} y={PY+114} textAnchor="middle"
        fontFamily="'Courier New',monospace" fontSize={15} fontStyle="italic"
        fill={WHITE} opacity={0.48}>{active.r}</text>
    </g>
  );
};

const HUD:React.FC<{frame:number}>=({frame})=>{
  const sl=interpolate(sp(Math.min(frame,28),120,14),[0,1],[-90,0]);
  const prog=cl(frame/T.TOTAL,0,1);
  const phase=
    frame<T.HOOK_E?'HOOK':frame<T.SET_E?'SETUP':frame<T.MECH_E?'MECHANISM':
    frame<T.PROOF_E?'PROOF':frame<T.TWIST_E?'TWIST':'OUTRO';
  const PC:{[k:string]:string}={HOOK:GOLD,SETUP:TEAL,MECHANISM:PURP,PROOF:BLUE,TWIST:CORAL,OUTRO:GOLD};
  const pc=PC[phase];
  return(
    <g transform={`translate(0,${sl})`}>
      <rect x={0} y={0} width={W} height={96} fill={BG} fillOpacity={0.88}/>
      <rect x={0} y={93} width={W} height={3} fill={pc} opacity={0.9}/>
      <text x={CX} y={50} textAnchor="middle"
        fontFamily="'Impact','Arial Black',sans-serif" fontSize={26}
        fill={WHITE} letterSpacing="3" fontWeight="900">BRAIN SCIENCE</text>
      <text x={CX} y={78} textAnchor="middle"
        fontFamily="'Courier New',monospace" fontSize={14}
        fill={pc} opacity={0.88} letterSpacing="5">▶ {phase}</text>
      <rect x={44} y={H-46} width={W-88} height={6} rx={3} fill={WHITE} fillOpacity={0.1}/>
      <rect x={44} y={H-46} width={(W-88)*prog} height={6} rx={3} fill={pc}/>
      <circle cx={44+(W-88)*prog} cy={H-43} r={7} fill={pc}/>
    </g>
  );
};

const HeadProfile:React.FC<{progress:number;strokeCol?:string;fillOpacity?:number}>=
  ({progress,strokeCol=PURP,fillOpacity=0.14})=>{
  const p=cl(progress,0,1);
  const dash=1600, sdp=eo6(p)*dash;
  return(
    <g>
      <ellipse cx={0} cy={-20} rx={195} ry={215}
        fill={strokeCol} fillOpacity={fillOpacity}
        stroke={strokeCol} strokeWidth={2.8}
        strokeDasharray={`${sdp} ${dash}`} strokeLinecap="round"/>
      <ellipse cx={190} cy={40} rx={26} ry={44}
        fill={TEAL} fillOpacity={0.1*p} stroke={TEAL} strokeWidth={2.5} opacity={p}/>
      <line x1={165} y1={40} x2={110} y2={40}
        stroke={TEAL} strokeWidth={3} opacity={p} strokeLinecap="round"/>
      <circle cx={96} cy={40} r={18}
        fill={TEAL} fillOpacity={0.18*p} stroke={TEAL} strokeWidth={2.5} opacity={p}/>
      <path d="M 96,40 Q 104,32 96,24 Q 88,16 80,24" fill="none"
        stroke={TEAL} strokeWidth={1.8} opacity={0.7*p} strokeLinecap="round"/>
      <path d="M 155,-10 Q 200,30 178,80 Q 168,100 155,115"
        fill="none" stroke={strokeCol} strokeWidth={2.2} opacity={0.6*p} strokeLinecap="round"/>
      <path d="M 130,180 Q 60,240 -20,235 Q -80,225 -120,180"
        fill="none" stroke={strokeCol} strokeWidth={2.2} opacity={0.6*p} strokeLinecap="round"/>
    </g>
  );
};

const WavePath:React.FC<{
  pts:{x:number;y:number;tx:number;ty:number}[];
  frame:number;color:string;freq:number;amp:number;speed:number;opacity:number;strokeWidth?:number;
}>=({pts,frame,color,freq,amp,speed,opacity,strokeWidth=2.5})=>{
  if(pts.length<2)return null;
  const pathD=pts.map((p,i)=>{
    const t=i/pts.length, mag=Math.sin(t*Math.PI);
    const phase=freq*t*Math.PI*2-speed*frame*0.08;
    const wave=amp*mag*Math.sin(phase);
    const len=Math.sqrt(p.tx*p.tx+p.ty*p.ty)||1;
    const nx=-p.ty/len, ny=p.tx/len;
    return(i===0?`M${p.x+nx*wave},${p.y+ny*wave}`:`L${p.x+nx*wave},${p.y+ny*wave}`);
  }).join(' ');
  return <path d={pathD} fill="none" stroke={color} strokeWidth={strokeWidth}
    strokeLinecap="round" opacity={opacity}/>;
};

// ── SCENE 1: HOOK ─────────────────────────────────────────────────
const SceneHook:React.FC<{frame:number}>=({frame})=>{
  const lf=frame-T.HOOK_S; if(lf<0)return null;
  const dur=T.HOOK_E-T.HOOK_S;
  const exitOp=interpolate(lf,[dur-30,dur],[1,0],{extrapolateRight:'clamp'});
  const flashOp=interpolate(lf,[0,1,10],[0.88,0.88,0],{extrapolateRight:'clamp'});
  const mkW=(d:number)=>{const s=sp(Math.max(0,lf-d),200,11);return{op:interpolate(s,[0,1],[0,1]),sc:interpolate(s,[0,1],[1.6,1])};};
  const w1=mkW(0),w2=mkW(18),w3=mkW(36);
  const wfPoints=Array.from({length:80},(_,i)=>{
    const t=i/79, x=80+t*(W-160);
    const wave=Math.sin(t*Math.PI*6-lf*0.15)*40*Math.sin(t*Math.PI)*Math.min(1,lf/40);
    return `${x},${H*0.42+wave}`;
  }).join(' ');
  return(
    <g opacity={exitOp}>
      <rect x={0} y={0} width={W} height={H} fill={WHITE} opacity={flashOp}/>
      {[0,1,2].map(i=>{
        const rr=interpolate(lf,[i*25,i*25+120],[0,480],{extrapolateRight:'clamp'});
        const ro=interpolate(lf,[i*25,i*25+20,i*25+120],[0,0.28,0],{extrapolateRight:'clamp'});
        return <ellipse key={i} cx={CX} cy={CY-80} rx={rr} ry={rr*0.55}
          fill="none" stroke={i%2===0?TEAL:GOLD} strokeWidth={2} opacity={ro}/>;
      })}
      <g opacity={interpolate(lf,[20,60],[0,1],{extrapolateRight:'clamp'})}>
        <polyline points={wfPoints} fill="none" stroke={TEAL} strokeWidth={2.5} filter="url(#gcrisp)"/>
      </g>
      {[
        {y:740,text:'तुम्हारी',size:100,col:WHITE,w:w1},
        {y:870,text:'आवाज़',size:108,col:GOLD,w:w2},
        {y:985,text:'Recording में?',size:62,col:TEAL,w:w3},
      ].map(({y,text,size,col,w},i)=>(
        <g key={i} transform={`translate(${CX},${y})`} opacity={w.op}>
          <g transform={`scale(${w.sc},1)`}>
            <text x={0} y={0} textAnchor="middle"
              fontFamily="'Impact','Arial Black',sans-serif"
              fontSize={size} fill={col} filter="url(#g3b1b)" letterSpacing="2">{text}</text>
          </g>
        </g>
      ))}
      <g transform={`translate(${CX},${H*0.72})`}
         opacity={interpolate(lf,[60,90],[0,1],{extrapolateRight:'clamp'})}>
        <text x={0} y={0} textAnchor="middle" fontFamily="serif" fontSize={200}
          fill={CORAL} fillOpacity={0.08} filter="url(#ghalo)">?</text>
        <text x={0} y={0} textAnchor="middle" fontFamily="serif" fontSize={200}
          fill={CORAL} fillOpacity={0.55}>?</text>
      </g>
    </g>
  );
};

// ── SCENE 2: SETUP ────────────────────────────────────────────────
const SceneSetup:React.FC<{frame:number}>=({frame})=>{
  const lf=frame-T.SET_S; if(lf<0)return null;
  const dur=T.SET_E-T.SET_S;
  const op=Math.min(interpolate(lf,[0,25],[0,1],{extrapolateRight:'clamp'}),
                    interpolate(lf,[dur-30,dur],[1,0],{extrapolateRight:'clamp'}));
  const headP=cl(lf/80,0,1);
  const {dx,dy}=shake(frame);
  const airPts=bezierPoints({x:CX-300,y:700},{x:CX-200,y:520},{x:CX+200,y:520},{x:CX+280,y:680},60);
  const bonePts=bezierPoints({x:CX-180,y:740},{x:CX-80,y:760},{x:CX+80,y:760},{x:CX+175,y:720},60);
  const airP=cl((lf-40)/100,0,1), boneP=cl((lf-80)/100,0,1);
  const drawPath=(pts:{x:number;y:number}[],progress:number,color:string)=>{
    const n=Math.floor(pts.length*progress); if(n<2)return null;
    const d=pts.slice(0,n).map((p,i)=>`${i===0?'M':'L'}${p.x},${p.y}`).join(' ');
    return <path d={d} fill="none" stroke={color} strokeWidth={4} strokeLinecap="round" filter="url(#gcrisp)"/>;
  };
  return(
    <g opacity={op} transform={`translate(${dx},${dy})`}>
      <text x={CX} y={220} textAnchor="middle" fontFamily="'Impact','Arial Black',sans-serif"
        fontSize={54} fill={WHITE} filter="url(#gcrisp)" letterSpacing="2">दो रास्ते</text>
      <text x={CX} y={280} textAnchor="middle" fontFamily="'Courier New',monospace"
        fontSize={22} fill={TEAL} opacity={0.8} letterSpacing="3">TWO PATHWAYS</text>
      <g transform={`translate(${CX},${CY-80})`}>
        <HeadProfile progress={headP} strokeCol={PURP} fillOpacity={0.14}/>
      </g>
      <g opacity={airP}>
        {drawPath(airPts,airP,TEAL)}
        <WavePath pts={airPts} frame={frame} color={TEAL} freq={3} amp={18} speed={2.5} opacity={0.7} strokeWidth={3}/>
        <text x={CX} y={490} textAnchor="middle" fontFamily="'Arial',sans-serif"
          fontSize={32} fill={TEAL} fontWeight="700">🌊 हवा (Air)</text>
      </g>
      <g opacity={boneP}>
        {drawPath(bonePts,boneP,GOLD)}
        <WavePath pts={bonePts} frame={frame} color={GOLD} freq={4} amp={10} speed={3} opacity={0.8} strokeWidth={3}/>
        <text x={CX} y={840} textAnchor="middle" fontFamily="'Arial',sans-serif"
          fontSize={32} fill={GOLD} fontWeight="700">🦴 हड्डी (Bone)</text>
      </g>
      <g opacity={cl((lf-120)/40,0,1)}>
        <circle cx={CX+290} cy={700} r={32} fill={TEAL} fillOpacity={0.2} stroke={TEAL} strokeWidth={2}/>
        <text x={CX+290} y={706} textAnchor="middle" fontFamily="serif" fontSize={26} fill={TEAL}>👂</text>
        <text x={CX+290} y={750} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={16} fill={TEAL} opacity={0.8}>EAR</text>
      </g>
    </g>
  );
};

// ── SCENE 3: MECHANISM ────────────────────────────────────────────
const SceneMechanism:React.FC<{frame:number}>=({frame})=>{
  const lf=frame-T.MECH_S; if(lf<0)return null;
  const dur=T.MECH_E-T.MECH_S;
  const op=Math.min(interpolate(lf,[0,25],[0,1],{extrapolateRight:'clamp'}),
                    interpolate(lf,[dur-30,dur],[1,0],{extrapolateRight:'clamp'}));
  const phase2Start=360, isPhase2=lf>=phase2Start, p2lf=lf-phase2Start;
  const boneVibeAmp=isPhase2?interpolate(p2lf,[0,60],[0,1],{extrapolateRight:'clamp'}):0;
  const freqBars=Array.from({length:14},(_,i)=>({
    x:120+i*62, h:(60+sr(i*2)*120)*(0.4+0.6*Math.abs(Math.sin(lf*0.12+i*0.7))),
    col:i%3===0?TEAL:i%3===1?BLUE:PURP,
  }));
  const boneFreqBars=Array.from({length:14},(_,i)=>({
    x:120+i*62,
    h:(80+sr(i*2+1)*100)*(i<5?1.6:i<8?1.1:0.7)*(0.4+0.6*Math.abs(Math.sin(lf*0.12+i*0.7+2)))*boneVibeAmp,
    col:i<5?GOLD:i<8?AMBER:CORAL,
  }));
  return(
    <g opacity={op}>
      <text x={CX} y={180} textAnchor="middle" fontFamily="'Impact','Arial Black',sans-serif"
        fontSize={46} fill={WHITE} letterSpacing="2">क्या होता है अंदर?</text>
      <text x={CX} y={232} textAnchor="middle" fontFamily="'Courier New',monospace"
        fontSize={20} fill={PURP} opacity={0.8} letterSpacing="4">INSIDE THE SKULL</text>
      <g opacity={interpolate(lf,[0,30],[0,1],{extrapolateRight:'clamp'})}>
        <text x={CX} y={370} textAnchor="middle" fontFamily="'Arial',sans-serif"
          fontSize={28} fill={TEAL} fontWeight="700">🎙 Microphone सुनता है</text>
        <rect x={100} y={390} width={880} height={280} rx={16}
          fill={BG2} fillOpacity={0.7} stroke={TEAL} strokeWidth={1.5} strokeOpacity={0.4}/>
        {freqBars.map((b,i)=>(
          <rect key={i} x={b.x} y={630-b.h} width={46} height={b.h} rx={6} fill={b.col} fillOpacity={0.85}/>
        ))}
        <text x={CX} y={700} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={16} fill={TEAL} opacity={0.6}>AIR CONDUCTION — balanced</text>
      </g>
      <g opacity={boneVibeAmp}>
        <text x={CX} y={900} textAnchor="middle" fontFamily="'Arial',sans-serif"
          fontSize={28} fill={GOLD} fontWeight="700">🦴 हड्डी से आवाज़</text>
        <rect x={100} y={920} width={880} height={280} rx={16}
          fill={BG2} fillOpacity={0.7} stroke={GOLD} strokeWidth={1.5} strokeOpacity={0.4}/>
        {boneFreqBars.map((b,i)=>(
          <rect key={i} x={b.x} y={1160-b.h} width={46} height={b.h} rx={6} fill={b.col} fillOpacity={0.85}/>
        ))}
        <rect x={110} y={1060} width={240} height={50} rx={8}
          fill={GOLD} fillOpacity={0.15} stroke={GOLD} strokeWidth={1.5}/>
        <text x={230} y={1092} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={16} fill={GOLD}>↑ LOW FREQ BOOST</text>
        <text x={CX} y={1230} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={16} fill={GOLD} opacity={0.6}>BONE CONDUCTION — bass boosted</text>
      </g>
      <g opacity={isPhase2?interpolate(p2lf,[30,70],[0,1],{extrapolateRight:'clamp'}):0}>
        <text x={CX} y={1420} textAnchor="middle" fontFamily="serif"
          fontSize={34} fill={WHITE} opacity={0.9}>इसीलिए Recording में आवाज़</text>
        <text x={CX} y={1470} textAnchor="middle" fontFamily="serif"
          fontSize={34} fill={CORAL} fontWeight="700">पतली लगती है।</text>
      </g>
    </g>
  );
};

// ── SCENE 4: PROOF ────────────────────────────────────────────────
const SceneProof:React.FC<{frame:number}>=({frame})=>{
  const lf=frame-T.PROOF_S; if(lf<0)return null;
  const dur=T.PROOF_E-T.PROOF_S;
  const op=Math.min(interpolate(lf,[0,25],[0,1],{extrapolateRight:'clamp'}),
                    interpolate(lf,[dur-30,dur],[1,0],{extrapolateRight:'clamp'}));
  const scopeW=880,scopeH=280,scopeX=100,scopeAirY=380,scopeBoneY=780;
  const drawScope=(yOff:number,color:string,ampM:number,freqM:number)=>{
    const pts=Array.from({length:120},(_,i)=>{
      const t=i/119, x=scopeX+t*scopeW;
      const y=yOff+scopeH/2+Math.sin(t*Math.PI*freqM*2-lf*0.14)*ampM*90
              +Math.sin(t*Math.PI*freqM*4-lf*0.22)*ampM*22;
      return `${x},${y}`;
    }).join(' ');
    return(
      <g>
        <rect x={scopeX} y={yOff} width={scopeW} height={scopeH} rx={14}
          fill="url(#scope-bg)" stroke={color} strokeWidth={1.8} strokeOpacity={0.5}/>
        <line x1={scopeX+10} x2={scopeX+scopeW-10} y1={yOff+scopeH/2} y2={yOff+scopeH/2}
          stroke={color} strokeWidth={0.8} strokeOpacity={0.25} strokeDasharray="6,6"/>
        <polyline points={pts} fill="none" stroke={color}
          strokeWidth={2.8} strokeLinecap="round" filter="url(#gcrisp)"/>
        <rect x={scopeX+(lf%scopeW)} y={yOff} width={2} height={scopeH}
          fill={color} fillOpacity={0.3}/>
      </g>
    );
  };
  return(
    <g opacity={op}>
      <text x={CX} y={200} textAnchor="middle" fontFamily="'Impact','Arial Black',sans-serif"
        fontSize={46} fill={WHITE} letterSpacing="2">Oscilloscope Proof</text>
      <text x={CX} y={252} textAnchor="middle" fontFamily="'Courier New',monospace"
        fontSize={20} fill={BLUE} opacity={0.8} letterSpacing="4">WAVEFORM COMPARISON</text>
      <g opacity={interpolate(lf,[0,40],[0,1],{extrapolateRight:'clamp'})}>
        <text x={CX} y={360} textAnchor="middle" fontFamily="'Arial',sans-serif"
          fontSize={26} fill={TEAL} fontWeight="700">🌊 हवा — जो mic सुनता है</text>
        {drawScope(scopeAirY,TEAL,0.6,2)}
        <text x={CX} y={scopeAirY+scopeH+40} textAnchor="middle"
          fontFamily="'Courier New',monospace" fontSize={15} fill={TEAL} opacity={0.6}>
          Balanced frequency response</text>
      </g>
      <g opacity={interpolate(lf,[60,100],[0,1],{extrapolateRight:'clamp'})}>
        <text x={CX} y={760} textAnchor="middle" fontFamily="'Arial',sans-serif"
          fontSize={26} fill={GOLD} fontWeight="700">🦴 हड्डी — जो तुम सुनते हो</text>
        {drawScope(scopeBoneY,GOLD,1.0,1.2)}
        <text x={CX} y={scopeBoneY+scopeH+40} textAnchor="middle"
          fontFamily="'Courier New',monospace" fontSize={15} fill={GOLD} opacity={0.6}>
          Bass-boosted (low freq enhanced)</text>
      </g>
      <g opacity={interpolate(lf,[120,160],[0,1],{extrapolateRight:'clamp'})}>
        <line x1={CX} y1={scopeAirY+scopeH+60} x2={CX} y2={scopeBoneY-20}
          stroke={CORAL} strokeWidth={3} strokeDasharray="10,6"/>
        <text x={CX+40} y={(scopeAirY+scopeH+scopeBoneY)/2+10}
          fontFamily="'Courier New',monospace" fontSize={18} fill={CORAL}>DIFFERENT!</text>
      </g>
      <g opacity={interpolate(lf,[200,240],[0,1],{extrapolateRight:'clamp'})}>
        <rect x={80} y={1360} width={920} height={100} rx={16}
          fill={CORAL} fillOpacity={0.12} stroke={CORAL} strokeWidth={1.5}/>
        <text x={CX} y={1402} textAnchor="middle" fontFamily="serif"
          fontSize={28} fill={WHITE}>Recording = सिर्फ हवा</text>
        <text x={CX} y={1442} textAnchor="middle" fontFamily="serif"
          fontSize={28} fill={CORAL} fontWeight="700">∴ तुम्हारी आवाज़ अलग लगती है</text>
      </g>
    </g>
  );
};

// ── SCENE 5: TWIST ────────────────────────────────────────────────
const SceneTwist:React.FC<{frame:number}>=({frame})=>{
  const lf=frame-T.TWIST_S; if(lf<0)return null;
  const dur=T.TWIST_E-T.TWIST_S;
  const op=Math.min(interpolate(lf,[0,25],[0,1],{extrapolateRight:'clamp'}),
                    interpolate(lf,[dur-30,dur],[1,0],{extrapolateRight:'clamp'}));
  const {dx,dy}=shake(frame);
  const notes=['♩','♪','♫','♬'];
  const noteParts=Array.from({length:12},(_,i)=>({
    x:100+sr(i*3+1)*(W-200), y:300+sr(i*3+2)*1200,
    sp:(sr(i*3+3)-0.5)*1.2, ph:sr(i*3)*Math.PI*2,
    note:notes[i%4], col:[GOLD,PURP,TEAL,CORAL][i%4],
  }));
  const pianoY=1500, pianoOp=interpolate(lf,[80,120],[0,1],{extrapolateRight:'clamp'});
  const whiteKeys=Array.from({length:14},(_,i)=>({x:108+i*60}));
  const blackKeyPos=[1,2,4,5,6,8,9,11,12];
  return(
    <g opacity={op} transform={`translate(${dx},${dy})`}>
      {noteParts.map((n,i)=>(
        <text key={i} x={(n.x+n.sp*lf)%W}
          y={(n.y-lf*0.4+Math.sin(lf*0.03+n.ph)*20)%H}
          textAnchor="middle" fontFamily="serif" fontSize={28} fill={n.col} opacity={0.22}>{n.note}</text>
      ))}
      <g opacity={interpolate(lf,[0,30],[0,1],{extrapolateRight:'clamp'})}>
        <text x={CX} y={260} textAnchor="middle" fontFamily="'Impact','Arial Black',sans-serif"
          fontSize={80} fill={GOLD} filter="url(#g3b1b)">Beethoven</text>
        <text x={CX} y={340} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={22} fill={WHITE} opacity={0.7} letterSpacing="3">THE BONE CONDUCTION MASTER</text>
      </g>
      <g opacity={interpolate(lf,[40,80],[0,1],{extrapolateRight:'clamp'})}>
        <rect x={240} y={380} width={600} height={100} rx={18}
          fill={RED} fillOpacity={0.18} stroke={RED} strokeWidth={2}/>
        <text x={CX} y={422} textAnchor="middle" fontFamily="'Impact','Arial Black',sans-serif"
          fontSize={32} fill={RED} letterSpacing="3">पूरी तरह बहरे थे</text>
        <text x={CX} y={462} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={18} fill={RED} opacity={0.7}>COMPLETELY DEAF</text>
      </g>
      <g opacity={interpolate(lf,[80,120],[0,1],{extrapolateRight:'clamp'})}>
        {['पर उन्होंने Piano की','छड़ी दाँत से पकड़कर','music सुना।'].map((t,i)=>(
          <text key={i} x={CX} y={620+i*58} textAnchor="middle"
            fontFamily="serif" fontSize={i===2?36:32}
            fill={i===2?GOLD:WHITE} fontWeight={i===2?'700':'400'} opacity={0.9}>{t}</text>
        ))}
      </g>
      <g opacity={pianoOp}>
        <rect x={90} y={pianoY} width={900} height={180} rx={12} fill="#1a0a00" stroke={AMBER} strokeWidth={2}/>
        {whiteKeys.map((k,i)=>(
          <rect key={i} x={k.x} y={pianoY+10} width={54} height={160} rx={4}
            fill={WHITE} fillOpacity={0.92} stroke="#333" strokeWidth={1}/>
        ))}
        {blackKeyPos.map((pos,i)=>(
          <rect key={i} x={108+pos*60-14} y={pianoY+10} width={28} height={100} rx={3} fill="#0d0d0d"/>
        ))}
        <line x1={CX} y1={pianoY-30} x2={CX+20} y2={pianoY+10}
          stroke={CORAL} strokeWidth={6} strokeLinecap="round"
          opacity={interpolate(lf,[100,140],[0,1],{extrapolateRight:'clamp'})}/>
      </g>
      <g opacity={interpolate(lf,[140,180],[0,1],{extrapolateRight:'clamp'})}>
        {Array.from({length:8},(_,i)=>{
          const baseX=200+i*90;
          const pts=Array.from({length:20},(_,j)=>{
            const t=j/19, y=pianoY-t*200;
            const x=baseX+Math.sin(t*Math.PI*4+lf*0.2+i)*(20+sr(i)*15)*Math.sin(t*Math.PI);
            return`${x},${y}`;
          }).join(' ');
          return <polyline key={i} points={pts} fill="none" stroke={GOLD}
            strokeWidth={1.8} strokeLinecap="round" opacity={0.5}/>;
        })}
        <text x={CX} y={1270} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={20} fill={GOLD} opacity={0.8} letterSpacing="2">BONE VIBRATION ↑</text>
      </g>
      <g opacity={interpolate(lf,[200,240],[0,1],{extrapolateRight:'clamp'})}>
        <rect x={60} y={1750} width={960} height={110} rx={18}
          fill={TEAL} fillOpacity={0.12} stroke={TEAL} strokeWidth={1.5}/>
        <text x={CX} y={1796} textAnchor="middle" fontFamily="serif"
          fontSize={30} fill={WHITE}>वो भी — Bone Conduction था</text>
        <text x={CX} y={1844} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={18} fill={TEAL} opacity={0.8} letterSpacing="2">SAME PHENOMENON</text>
      </g>
    </g>
  );
};

// ── SCENE 6: OUTRO ────────────────────────────────────────────────
const SceneOutro:React.FC<{frame:number}>=({frame})=>{
  const lf=frame-T.OUT_S; if(lf<0)return null;
  const dur=T.OUT_E-T.OUT_S;
  const op=Math.min(interpolate(lf,[0,30],[0,1],{extrapolateRight:'clamp'}),
                    interpolate(lf,[dur-50,dur],[1,0],{extrapolateRight:'clamp'}));
  const rays=Array.from({length:16},(_,i)=>{
    const angle=(i/16)*Math.PI*2, len=interpolate(lf,[0,120],[0,380],{extrapolateRight:'clamp'});
    return{
      x1:CX+Math.cos(angle)*80, y1:CY-200+Math.sin(angle)*80,
      x2:CX+Math.cos(angle)*(80+len), y2:CY-200+Math.sin(angle)*(80+len),
      col:i%4===0?GOLD:i%4===1?TEAL:i%4===2?PURP:CORAL,
    };
  });
  return(
    <g opacity={op}>
      <circle cx={CX} cy={CY-200} r={interpolate(lf,[0,60],[0,300],{extrapolateRight:'clamp'})}
        fill={GOLD} fillOpacity={0.06} filter="url(#ghalo)"/>
      {rays.map((r,i)=>(
        <line key={i} x1={r.x1} y1={r.y1} x2={r.x2} y2={r.y2}
          stroke={r.col} strokeWidth={2} opacity={0.4}/>
      ))}
      <circle cx={CX} cy={CY-200} r={80} fill={GOLD} fillOpacity={0.15}
        stroke={GOLD} strokeWidth={3} filter="url(#gcrisp)"/>
      <text x={CX} y={CY-185} textAnchor="middle" fontFamily="serif" fontSize={60} fill={GOLD}>🎙</text>
      <g opacity={interpolate(lf,[40,80],[0,1],{extrapolateRight:'clamp'})}>
        <text x={CX} y={CY+180} textAnchor="middle" fontFamily="'Impact','Arial Black',sans-serif"
          fontSize={64} fill={WHITE} filter="url(#g3b1b)" letterSpacing="1">तुम्हारी असली</text>
        <text x={CX} y={CY+260} textAnchor="middle" fontFamily="'Impact','Arial Black',sans-serif"
          fontSize={72} fill={GOLD} filter="url(#g3b1b)">आवाज़</text>
        <text x={CX} y={CY+340} textAnchor="middle" fontFamily="serif"
          fontSize={36} fill={WHITE} opacity={0.85}>वही है — जो दूसरे सुनते हैं।</text>
      </g>
      <g opacity={interpolate(lf,[100,140],[0,1],{extrapolateRight:'clamp'})}>
        <rect x={280} y={CY+400} width={520} height={60} rx={14}
          fill={TEAL} fillOpacity={0.15} stroke={TEAL} strokeWidth={1.5}/>
        <text x={CX} y={CY+440} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={20} fill={TEAL} letterSpacing="3">BONE CONDUCTION</text>
      </g>
      <g opacity={interpolate(lf,[160,200],[0,1],{extrapolateRight:'clamp'})}>
        <rect x={160} y={CY+520} width={760} height={90} rx={20} fill={CORAL} fillOpacity={0.9}/>
        <text x={CX} y={CY+572} textAnchor="middle" fontFamily="'Impact','Arial Black',sans-serif"
          fontSize={34} fill={WHITE} letterSpacing="2">🔔 Subscribe करो</text>
        <text x={CX} y={CY+604} textAnchor="middle" fontFamily="serif"
          fontSize={20} fill={WHITE} opacity={0.85}>हर हफ्ते नया science</text>
      </g>
      <g opacity={interpolate(lf,[220,260],[0,1],{extrapolateRight:'clamp'})}>
        <text x={CX} y={H-140} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={18} fill={WHITE} opacity={0.5} letterSpacing="4">HIDICT STUDIO</text>
        <text x={CX} y={H-100} textAnchor="middle" fontFamily="'Courier New',monospace"
          fontSize={14} fill={PURP} opacity={0.4} letterSpacing="6">SCIENCE IN HINDI</text>
      </g>
    </g>
  );
};

// ── ROOT COMPOSITION ──────────────────────────────────────────────
export const BoneConduction: React.FC = () => {
  const frame = useCurrentFrame();
  const {dx,dy} = shake(frame);
  return (
    <AbsoluteFill style={{background: BG}}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}
        style={{position:'absolute',top:0,left:0}}>
        <GlobalDefs/>
        <g transform={`translate(${dx},${dy})`}>
          <Background      frame={frame}/>
          <SoundParticles  frame={frame}/>
          <SceneHook       frame={frame}/>
          <SceneSetup      frame={frame}/>
          <SceneMechanism  frame={frame}/>
          <SceneProof      frame={frame}/>
          <SceneTwist      frame={frame}/>
          <SceneOutro      frame={frame}/>
          <HindiSubs       frame={frame}/>
          <HUD             frame={frame}/>
        </g>
      </svg>
      <Audio src={staticFile('audio/narration_final.mp3')} />
    </AbsoluteFill>
  );
};
