import React from 'react';
import {useCurrentFrame,useVideoConfig} from 'remotion';
export default function A09Text({item}){
 const frame=useCurrentFrame();const {fps}=useVideoConfig();const t=frame/fps;
 const p=item.props;const {text,kind,fontSize:fs,cx,cy,font:family}=p;
 const vertical=['vertical','welcome','stack'].includes(kind),welcome=kind==='welcome',gold=kind==='gold',small=kind==='small';
 const orange=p.color==='#ffad05'||p.color==='#f6a600',green=p.color==='#10b636',redCTA=p.color==='#ed0015'||p.color==='#ec001b';
 const accents=JSON.parse(p.accents||'{}');const colors={red:'#f00000',yellow:'#edf000',cyan:'#00e7e2'};
 const motion=p.motion;const lines=text.split('\n');
 const duration=welcome?.43:motion==='shake'?.4:motion==='wipe'?(gold?.22:.36):gold&&motion!=='wipe'?.42:orange&&motion==='rise'?.3:motion==='drop'?.23:motion==='rise'?.2:motion==='pop'?.13:motion==='bounce'?.3:motion==='right'?.26:motion==='left'?.16:small||motion==='cut'?0:.1;
 const clamp=v=>Math.min(1,Math.max(0,v));
 const position=at=>{const q=duration?clamp(at/duration):1,e=1-Math.pow(1-q,(motion==='left'||motion==='right')?2:3);let scale=1,x=0,y=0;
  if(welcome){scale=.07+.93*e;x=(540-cx)*(1-e);y=(900-cy)*(1-e);}
  else if(gold&&motion!=='wipe'){scale=3.4-2.4*e;y=380*(1-e);}
  else if(motion==='pop')scale=.08+.92*e;
  else if(motion==='bounce')scale=q<.65?.06+1.08*(1-Math.pow(1-q/.65,2)):1+.14*(1-clamp((q-.65)/.35));
  if(motion==='left')x=-700*(1-e);if(motion==='right')x=700*(1-e);
  if(motion==='rise')y=(orange?800:430)*(1-e);if(motion==='drop')y=-430*(1-e);
  if(motion==='shake')x=Math.sin(at*65)*22*(1-q);
  return {q,e,scale,x,y};};
 const colorAt=(line,index)=>{for(const [word,col]of Object.entries(accents)){const at=line.indexOf(word);if(at>=0&&index>=at&&index<at+word.length)return colors[col]||col;}return gold?'url(#a09gold)':p.color;};
 // SVG strokes are centered: these widths leave a ~10px black rim and ~6px white outer rim.
 const layers=small?[['#111',5],['fill',0]]:kind==='stack'?[['#190000',27],['fill',4]]:vertical?[['white',16],['fill',2]]:gold?[['white',40],['#4c2800',31],['fill',5]]:orange?[[p.color,34],['white',25],['fill',5]]:green?[[p.color,38],['white',28],['fill',5]]:redCTA?[['white',40],['#090909',33],['white',23],['fill',5]]:[['white',40],['#07080a',27],['fill',4]];
 const textLine=(line,x,y,stroke,width,key)=><text key={key} x={x} y={y} textAnchor="middle" dominantBaseline="central" fontFamily={family} fontSize={fs} fontWeight={p.weight} stroke={stroke==='fill'?undefined:stroke} strokeWidth={width} strokeLinejoin="round" paintOrder="stroke fill">{[...line].map((ch,i)=><tspan key={i} fill={colorAt(line,i)} stroke={stroke==='fill'?colorAt(line,i):undefined}>{ch}</tspan>)}</text>;
 const content=()=>layers.map(([stroke,width],li)=><g key={li}>{vertical?lines.map((line,col)=>[...line].map((ch,ci)=>textLine(ch,cx-col*fs*1.17,cy+(col?fs*2.65:0)+ci*fs*(welcome?.9:.98),stroke,width,`${col}-${ci}`))):lines.map((line,i)=>textLine(line,cx,cy+(i-(lines.length-1)/2)*fs*(gold?1.16:1.23),stroke,width,i))}</g>);
 const state=position(t);const horizontal=motion==='left'||motion==='right';const trail=!small&&(horizontal||['rise','drop','pop'].includes(motion)||(gold&&motion!=='wipe'));
 const transformed=(at,opacity,key)=>{const s=position(at);return <g key={key} opacity={opacity} transform={`translate(${cx+s.x} ${cy+s.y}) scale(${s.scale}) translate(${-cx} ${-cy})`}>{content()}</g>;};
 const blur=small?0:(1-state.q)*(horizontal?2:gold?5:3);
 const glow=welcome?' drop-shadow(0px 0px 18px #ffff45)':gold?' drop-shadow(0px 0px 11px white)':vertical?' drop-shadow(0px 2px 6px #180000)':'';
 return <div style={{position:'absolute',left:0,top:0,width:motion==='wipe'?1080*state.e:1080,height:1920,overflow:'hidden'}}><svg width="1080" height="1920" viewBox="0 0 1080 1920"><defs><linearGradient id="a09gold" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0" stopColor="#fff4bd"/><stop offset=".28" stopColor="#fffbd2"/><stop offset=".45" stopColor="#e4ab20"/><stop offset=".53" stopColor="#8e5100"/><stop offset=".65" stopColor="#e7ad13"/><stop offset="1" stopColor="#ffdf48"/></linearGradient><clipPath id="a09reveal"><rect x="0" y="0" width={motion==='wipe'?1080*state.e:1080} height="1920"/></clipPath></defs><g opacity={small||motion==='cut'||gold?1:Math.min(1,.15+state.q*4)} style={{filter:`blur(${blur}px)${glow}`}}>
 {trail&&state.q<1?[6,5,4,3,2,1].map(n=>transformed(Math.max(0,t-n*.012),.14*(1-state.q),n)):null}
 {transformed(t,trail&&state.q<1?.35+.65*state.q:1,'main')}
 </g></svg></div>;
}
