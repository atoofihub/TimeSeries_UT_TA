/* Interactive GNSS demonstration preserved from the supplied course. */
(function(){
'use strict';
const $=s=>document.querySelector(s);
const points=(window.COURSE_ROUTE||[]).map(r=>({t:r[0],e:r[1],n:r[2],h:r[3]}));
const canvas=$('#routeCanvas');
if(!canvas||!points.length)return;
const ctx=canvas.getContext('2d');
  const mat=(r,c)=>Array.from({length:r},()=>Array(c).fill(0));
  const eye=n=>Array.from({length:n},(_,i)=>Array.from({length:n},(_,j)=>i===j?1:0));
  const tr=A=>A[0].map((_,i)=>A.map(row=>row[i]));
  const mm=(A,B)=>A.map(row=>B[0].map((_,j)=>row.reduce((s,a,k)=>s+a*B[k][j],0)));
  const plus=(A,B)=>A.map((row,i)=>row.map((v,j)=>v+B[i][j]));
  const makeF=dt=>[[1,0,dt,0],[0,1,0,dt],[0,0,1,0],[0,0,0,1]];
  const makeQ=(dt,a)=>{
    const G=[[dt*dt/2,0],[0,dt*dt/2],[dt,0],[0,dt]];
    return mm(G,tr(G)).map(row=>row.map(v=>v*a*a));
  };
  function simulate(sa,sz,gap){
    const r=sz*sz;
    // Fit the first ten observations, then start at their final timestamp.
    // Initialization observations must not be processed a second time as updates.
    const lastInit=9, n=lastInit+1, t0=points[0].t;
    const initial=points.slice(0,n), tau=initial.map(p=>p.t-t0);
    const st=tau.reduce((a,b)=>a+b,0), stt=tau.reduce((a,b)=>a+b*b,0);
    const det0=n*stt-st*st, finalTau=tau[lastInit];
    const fit=key=>{
      const sy=initial.reduce((a,p)=>a+p[key],0);
      const sty=initial.reduce((a,p,i)=>a+tau[i]*p[key],0);
      const slope=(n*sty-st*sy)/det0, intercept=(stt*sy-st*sty)/det0;
      return [intercept+finalTau*slope,slope];
    };
    const east=fit('e'), north=fit('n');
    let x=[east[0],north[0],east[1],north[1]];
    const pp=r*(stt-2*finalTau*st+finalTau*finalTau*n)/det0;
    const pv=r*(-st+finalTau*n)/det0, vv=r*n/det0;
    let P=[[pp,0,pv,0],[0,pp,0,pv],[pv,0,vv,0],[0,pv,0,vv]];
    const output=[]; let sqInnov=0,nInnov=0,sumSigma=0;
    output.push({e:x[0],n:x[1],gap:false});sumSigma+=Math.sqrt(P[0][0]+P[1][1]);
    for(let k=lastInit+1;k<points.length;k++){
      const dt=points[k].t-points[k-1].t;
      if(!(dt>0))continue;
      const F=makeF(dt),Q=makeQ(dt,sa);
      const xp=[x[0]+x[2]*dt,x[1]+x[3]*dt,x[2],x[3]];
      const PM=plus(mm(mm(F,P),tr(F)),Q);
      const inGap= gap>0 && points[k].t>=100 && points[k].t<100+gap;
      if(inGap){x=xp;P=PM;output.push({e:x[0],n:x[1],gap:true});sumSigma+=Math.sqrt(Math.max(0,P[0][0]+P[1][1]));continue;}
      const nu=[points[k].e-xp[0],points[k].n-xp[1]];
      const a=PM[0][0]+r,b=PM[0][1],c=PM[1][0],d=PM[1][1]+r,det=a*d-b*c;
      if(!(det>0)){output.push({e:xp[0],n:xp[1],gap:false});x=xp;P=PM;continue;}
      const K=mat(4,2);
      for(let i=0;i<4;i++){
        K[i][0]=(PM[i][0]*d-PM[i][1]*c)/det;
        K[i][1]=(-PM[i][0]*b+PM[i][1]*a)/det;
      }
      x=xp.map((v,i)=>v+K[i][0]*nu[0]+K[i][1]*nu[1]);
      const M=eye(4);
      for(let i=0;i<4;i++){M[i][0]-=K[i][0];M[i][1]-=K[i][1];}
      const MP=mm(mm(M,PM),tr(M));
      const KR=mm(K,tr(K)).map(row=>row.map(v=>v*r));
      P=plus(MP,KR);
      for(let i=0;i<4;i++)for(let j=i+1;j<4;j++){const avg=(P[i][j]+P[j][i])/2;P[i][j]=avg;P[j][i]=avg;}
      output.push({e:x[0],n:x[1],gap:false});
      sqInnov+=nu[0]*nu[0]+nu[1]*nu[1]; nInnov+=2;
      sumSigma+=Math.sqrt(Math.max(0,P[0][0]+P[1][1]));
    }
    return {out:output,rms:nInnov?Math.sqrt(sqInnov/nInnov):0,unc:sumSigma/output.length};
  }
  function renderRoute(){
    const sigmaA=+$('#sliderA').value,sigmaZ=+$('#sliderZ').value,gap=+$('#sliderGap').value;
    $('#outA').textContent=sigmaA.toFixed(1);
    $('#outZ').textContent=sigmaZ.toFixed(1);
    $('#outGap').textContent=gap.toString();
    const result=simulate(sigmaA,sigmaZ,gap);const filtered=result.out;
    $('#statN').textContent=(filtered.length-1).toLocaleString('en-US');
    $('#statInno').textContent=result.rms.toFixed(2)+' m';
    $('#statUncertainty').textContent=result.unc.toFixed(2)+' m';
    const W=canvas.width,H=canvas.height;
    ctx.clearRect(0,0,W,H);
    const dark=document.body.classList.contains('dark');
    ctx.fillStyle=dark?'#162a33':'#f9fcfb';ctx.fillRect(0,0,W,H);
    const allE=points.map(p=>p.e).concat(filtered.map(p=>p.e));
    const allN=points.map(p=>p.n).concat(filtered.map(p=>p.n));
    let emin=Math.min(...allE),emax=Math.max(...allE),nmin=Math.min(...allN),nmax=Math.max(...allN);
    const epad=Math.max(10,(emax-emin)*.07),npad=Math.max(10,(nmax-nmin)*.07);
    emin-=epad;emax+=epad;nmin-=npad;nmax+=npad;
    const pad={l:67,r:30,t:26,b:47};
    const plotW=W-pad.l-pad.r,plotH=H-pad.t-pad.b;
    const x=v=>pad.l+(v-emin)/(emax-emin)*plotW;
    const y=v=>H-pad.b-(v-nmin)/(nmax-nmin)*plotH;
    ctx.strokeStyle=dark?'#36505a':'#e4ecea';ctx.lineWidth=1;
    ctx.fillStyle=dark?'#9dbab8':'#5d7581';ctx.font='15px Arial';ctx.textAlign='center';
    for(let i=0;i<=5;i++){
      const xx=pad.l+i*plotW/5,yy=pad.t+i*plotH/5;
      ctx.beginPath();ctx.moveTo(xx,pad.t);ctx.lineTo(xx,H-pad.b);ctx.stroke();
      ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(W-pad.r,yy);ctx.stroke();
      ctx.fillText((emin+(emax-emin)*i/5).toFixed(0),xx,H-pad.b+23);
      ctx.textAlign='right';ctx.fillText((nmax-(nmax-nmin)*i/5).toFixed(0),pad.l-8,yy+5);ctx.textAlign='center';
    }
    ctx.font='16px Arial';ctx.fillText('E [m]',pad.l+plotW/2,H-8);
    ctx.save();ctx.translate(22,pad.t+plotH/2);ctx.rotate(-Math.PI/2);ctx.fillText('N [m]',0,0);ctx.restore();
    ctx.beginPath();ctx.strokeStyle=dark?'#839da8':'#a9b9c0';ctx.lineWidth=1.5;
    points.forEach((p,i)=>{if(i===0)ctx.moveTo(x(p.e),y(p.n));else ctx.lineTo(x(p.e),y(p.n));});ctx.stroke();
    ctx.beginPath();ctx.strokeStyle='#0b9889';ctx.lineWidth=3;
    filtered.forEach((p,i)=>{if(i===0)ctx.moveTo(x(p.e),y(p.n));else ctx.lineTo(x(p.e),y(p.n));});ctx.stroke();
    if(gap>0){ctx.beginPath();ctx.strokeStyle='#df805b';ctx.lineWidth=4;let drawing=false;filtered.forEach((p,i)=>{if(p.gap){if(!drawing&&i>0)ctx.moveTo(x(filtered[i-1].e),y(filtered[i-1].n));ctx.lineTo(x(p.e),y(p.n));drawing=true;}else if(drawing){ctx.lineTo(x(p.e),y(p.n));drawing=false;}});ctx.stroke();}
    // First and last epoch, with labels.
    ctx.fillStyle='#e3a548';for(const idx of [0,filtered.length-1]){const p=filtered[idx];ctx.beginPath();ctx.arc(x(p.e),y(p.n),5,0,2*Math.PI);ctx.fill();}
    ctx.font='15px Arial';ctx.fillStyle=dark?'#c1d3da':'#526773';ctx.textAlign='left';ctx.fillText('START',x(filtered[0].e)+9,y(filtered[0].n)-8);
    const end=filtered[filtered.length-1];ctx.fillText('END',x(end.e)+9,y(end.n)-8);
  }
  ['sliderA','sliderZ','sliderGap'].forEach(id=>document.getElementById(id).addEventListener('input',renderRoute));
  renderRoute();
})();
