import React from 'react';
import {Img,useCurrentFrame,useVideoConfig} from 'remotion';
export default function A09Photo({item}){const f=useCurrentFrame();const {fps}=useVideoConfig();const p=item.props;const t=f/fps;const q=1-Math.pow(1-Math.min(1,t/p.seconds),3);return <div style={{width:1080,height:p.photoHeight,overflow:'hidden'}}><Img src={p.imageId} style={{width:1080,height:p.photoHeight,transform:`translateX(${p.direction*1080*(1-q)}px)`,filter:`blur(${(1-q)*10}px)`}}/></div>;}
