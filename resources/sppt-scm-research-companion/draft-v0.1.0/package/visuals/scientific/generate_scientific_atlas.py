#!/usr/bin/env python3
"""Deterministic original figures for the 5 October 2026 research companion.
Run: python generate_scientific_atlas.py. No downloads or archived research code.
"""
from pathlib import Path
import os, json, hashlib, subprocess, shutil, tempfile
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'astra-atlas-matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME', str(Path(tempfile.gettempdir()) / 'astra-atlas-cache'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Circle
from matplotlib.colors import ListedColormap, BoundaryNorm
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parent
STATIC=ROOT/'figures'; ANIM=ROOT/'animations'; QA=ROOT/'qa'
for p in (STATIC, ANIM, QA): p.mkdir(exist_ok=True)
C={'ink':'#142D40','muted':'#516677','blue':'#006EAD','teal':'#008477','orange':'#B65A13','purple':'#7A4B92','pale':'#EFF5F8','grid':'#D4E0E7','white':'#FFFFFF'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.color':C['ink'],
'axes.labelcolor':C['ink'],'axes.edgecolor':C['grid'],'xtick.color':C['muted'],'ytick.color':C['muted'],
'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold',
'axes.titlepad':12,'svg.fonttype':'none','savefig.facecolor':'white','figure.facecolor':'white',
'axes.unicode_minus':False,'mathtext.fontset':'dejavusans','svg.hashsalt':'astra-scientific-atlas-20261005'})
manifest=[]

def base(number,title,subtitle,size=(12,7.6)):
    f=plt.figure(figsize=size)
    f.text(.045,.957,f'{number}  /  SCIENTIFIC ATLAS',fontsize=9,fontweight='bold',color=C['teal'])
    f.text(.045,.913,title,fontsize=22,fontweight='bold')
    f.text(.045,.869,subtitle,fontsize=10.5,color=C['muted'])
    return f

def foot(f,text):
    f.text(.045,.040,text,fontsize=8.5,color=C['muted'],va='bottom',linespacing=1.5)

def panel(f,xywh):
    ax=f.add_axes(xywh);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off');return ax

def box(ax,x,y,w,h,title,body='',color=None,fs=12):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.01,rounding_size=0.02',
      fc=C['pale'],ec=color or C['grid'],lw=1.2))
    ax.text(x+.02,y+h-.05,title,va='top',fontsize=fs,fontweight='bold',color=color or C['ink'])
    if body: ax.text(x+.02,y+h-.13,body,va='top',fontsize=10,linespacing=1.55)

def arrow(ax,a,b,color=None,style='-|>',lw=1.6,rad=0):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle=style,mutation_scale=13,color=color or C['muted'],lw=lw,connectionstyle=f'arc3,rad={rad}'))

def save(f,stem,caption,params,sources):
    png=STATIC/(stem+'.png');svg=STATIC/(stem+'.svg')
    f.savefig(png,dpi=180)
    f.savefig(svg,metadata={'Date':None,'Creator':'Original deterministic research-companion figure'})
    plt.close(f)
    manifest.append({'id':stem,'kind':'static','files':[str(p.relative_to(ROOT)) for p in (svg,png)],'caption':caption,'parameters':params,'sources':sources,'evidence':'Original schematic or exact conditional model calculation; no new empirical data.'})

# 01: Complete observation contract.
f=base('01','A complete route from source to record','A shared inference contract; physical generators, units and likelihoods remain domain-specific.')
a=panel(f,[.045,.30,.91,.51])
xs=[.015,.270,.525,.780];w=.205
for x,title,body,col in zip(xs,['State + dynamics','Physical conversion','Instrument','Retained record'],
 ['State space X\nGenerator G + boundaries\nControls U','Transport / transformation\nDaughter configurations\nSurvival before detection','Observation law K\nCalibration + nuisance N\nQuantum state update','Outcome + exposure\nTiming, flags, censoring\nDeclared history R'],
 [C['blue'],C['teal'],C['purple'],C['orange']]):box(a,x,.49,w,.46,title,body,col,11.5)
for x in xs[:-1]:arrow(a,(x+w+.008,.71),(x+.245,.71))
# The three outcomes are an explicitly illustrative partition of attempts.
for x,title,body,col in zip([.245,.49,.735],['Detected','No detection','Veto / discarded'],['Retain response marks','Include counted attempts','Keep the selection flag'],[C['blue'],C['teal'],C['orange']]):
    box(a,x,.075,.22,.25,title,body,col,11)
    arrow(a,(.883,.48),(x+.11,.335),color=C['grid'],rad=0)
a.text(.015,.27,'COMPLETE\nOUTCOME LAW',fontsize=10,fontweight='bold',color=C['muted'],va='top',linespacing=1.6)
f.text(.058,.234,'Classical kernels',fontweight='bold',fontsize=11)
f.text(.21,.23,r'$P_u(dy)=\int K_u(dy\mid z,\nu)\,C_u(dz\mid x,\nu)\,r(dx)$',fontsize=15)
f.text(.058,.167,'Quantum instrument',fontweight='bold',fontsize=11)
f.text(.245,.164,r'$P_u(y\mid\rho)=\mathrm{Tr}\,\mathcal{I}_{y,u}(\rho),\qquad \sum_y\mathcal{I}_{y,u}\ \mathrm{is\ trace\ preserving}$',fontsize=14)
foot(f,'Schematic. Define the attempt denominator before adding no-detection outcomes; missing coverage is not a negative result.\nRejection criterion V and nuisance support must be declared for each model. Source: research companion, Section 2, Eqs. (1)-(2).')
save(f,'01_complete_observation_contract',
'A schematic of the common observation contract, not a universal physical law. Classical source and conversion kernels are normalized over full states or daughter configurations; daughter counts instead require an intensity measure. A complete quantum instrument supplies outcome probabilities and conditional state updates. Detected, no-detection and veto outcomes are an illustrative partition only when the attempt denominator is operationally recorded. Missing coverage must remain distinct. The rejection criterion, units, conservation laws, controls and nuisance support stay model-specific.',
{'diagram':'Conceptual; no numerical inputs','outcomes':'Illustrative disjoint outcome classes for counted attempts'},
[{'label':'Physics Synthesis and Research Priorities for ASTRA SPPT and SCM (5 Oct 2026), Section 2, equations 1-2','type':'supplied report'},
 {'label':'Combes et al., post-selected metrology and full resource accounting (2014)','url':'https://arxiv.org/abs/1309.6620'}])

# Analytic helix and orthographic projection. Coordinates use an arbitrary length L0.
elev=np.deg2rad(23.)
P=np.array([[np.sqrt(3)/2,-.5,0.],[.5*np.sin(elev),np.sqrt(3)/2*np.sin(elev),np.cos(elev)]])
def helix(x,A=.6,k=1.):return np.column_stack((x,A*np.cos(k*x),A*np.sin(k*x)))
def frame(x,A=.6,k=1.):
    h=np.sqrt(1+(A*k)**2)
    T=np.array([1,-A*k*np.sin(k*x),A*k*np.cos(k*x)])/h
    N=np.array([0,-np.cos(k*x),-np.sin(k*x)])
    B=np.cross(T,N)
    return T,N,B

def draw_geometry(ax,A=.6,x0=3.5,labels=True):
    x=np.linspace(0,8,800);curve=helix(x,A);p=helix(np.array([x0]),A)[0];T,N,B=frame(x0,A)
    ax.set_aspect('equal');ax.axis('off');ax.set_xlim(-1.0,7.8);ax.set_ylim(-1.7,3.2)
    origin=np.array([x0,0,0]);
    for basis,col in [(np.array([[0,1,0],[0,0,1]]),C['orange']),(np.array([N,B]),C['teal'])]:
        pts=np.array([p+u*basis[0]+v*basis[1] for u,v in [(-.85,-.85),(.85,-.85),(.85,.85),(-.85,.85)]])@P.T
        ax.add_patch(Polygon(pts,fc=col,ec=col,alpha=.16,lw=1.4))
    q=helix(np.linspace(0,8,200),0)@P.T;ax.plot(q[:,0],q[:,1],color=C['grid'],ls='--',lw=1.5)
    q=curve@P.T;ax.plot(q[:,0],q[:,1],color=C['blue'],lw=3)
    pp=p@P.T;op=origin@P.T
    ax.plot([op[0],pp[0]],[op[1],pp[1]],ls=':',color=C['orange'],lw=2)
    ax.scatter([pp[0]],[pp[1]],s=35,color=C['ink'],zorder=5)
    for vec,lab,col,length in [(T,'T',C['ink'],1.55),(N,'N',C['teal'],1.3),(B,'B',C['purple'],1.3)]:
        end=(p+length*vec)@P.T;arrow(ax,pp,end,col)
        if labels:ax.text(*(end+.07),lab,color=col,fontweight='bold',fontsize=12)
    if labels:
        ax.text(.15,2.7,'Orthographic view of an analytic helix',fontsize=11,fontweight='bold')
        ax.text(.0,-1.16,'Blue: centerline F(x)\nTeal: normal plane span{N, B}\nOrange: fixed-x transverse plane',fontsize=10,linespacing=1.55)
        ax.text(5.9,.55,'base x',color=C['muted'],fontsize=10)
    return T,N,B

f=base('02','A complex graph and its normal plane','The two transverse graph coordinates and the geometric normal frame are distinct constructions.')
ax=f.add_axes([.045,.19,.57,.62]);draw_geometry(ax)
r=panel(f,[.65,.18,.30,.63])
r.text(0,.95,'EXACT ILLUSTRATIVE GEOMETRY',fontsize=10,fontweight='bold',color=C['teal'])
r.text(0,.84,r'$F(x)=(x,A\cos kx,A\sin kx)$',fontsize=13)
r.text(0,.70,r'$T=F_x/|F_x|,\quad B=T\times N$',fontsize=13)
r.text(0,.58,r'$N=(0,-\cos kx,-\sin kx)$',fontsize=12)
r.text(0,.46,'N and B span the plane\nperpendicular to the tangent T.',fontsize=11,linespacing=1.6)
r.text(0,.29,'The fixed-x plane instead holds\nthe complex graph height\nU = a(Re ψ, Im ψ).',fontsize=11,linespacing=1.6)
r.text(0,.065,'Finite slope requires a tangential\nreparametrization in graph flow.',fontsize=11,color=C['orange'],linespacing=1.5)
foot(f,'Analytic geometry, not a time-evolved PDE solution or a model of matter. A = 0.6 L₀, k = 1/L₀; arbitrary length L₀.\nThe normal frame does not establish spin, charge or a gravitational metric. Sources: report Section 3; Hasimoto (1972).')
save(f,'02_complex_graph_normal_plane',
'Exact analytic geometry for F(x)=(x,A cos(kx),A sin(kx)), shown in a fixed orthographic projection. T is the unit tangent, N the principal normal, and B=T cross N. The teal plane is normal to T. The orange fixed-x transverse plane contains the graph-height coordinates and is generally a different plane at finite slope. Their projected overlap is a perspective effect. An ambient binormal motion and a fixed graph gauge require different tangential bookkeeping. This original drawing is neither an evolved SCM solution nor a microscopic interpretation.',
{'A_in_L0':0.6,'k_in_inverse_L0':1,'x_range_in_L0':[0,8],'frame_x_in_L0':3.5,'projection_rows':P.tolist()},
[{'label':'Report Section 3: graph gauge and encoding','type':'supplied report'},
 {'label':'Hasimoto, A soliton on a vortex filament (1972)','url':'https://doi.org/10.1017/S0022112072002307'}])

# 03: WKI finite-domain growth.
f=base('03','A growth band is not a stability verdict','Exact linearized predictions for a specified periodic WKI carrier; all plotted inputs are synthetic.')
ax=f.add_axes([.075,.28,.40,.48]);q=np.linspace(0,1.02,1000);s=1.
growth=lambda z,ss: np.sqrt(np.maximum(0,z*z*(ss-(1+ss)*z*z)/(1+ss)**3))
ax.plot(q,growth(q,s),c=C['blue'],lw=2.5,label='continuum envelope, s = 1')
ax.axvspan(0,1/np.sqrt(2),color=C['teal'],alpha=.08)
for n in range(1,5):
    qn=n/4;yn=growth(qn,s)
    ax.plot(qn,yn,'o',ms=8,mfc=C['teal'] if yn>0 else 'white',mec=C['teal'],mew=1.7)
    ax.annotate(f'n={n}',(qn,yn),xytext=(0,12),textcoords='offset points',ha='center',fontsize=9)
ax.axvline(1/np.sqrt(2),color=C['orange'],ls='--',lw=1.5)
ax.text(.715,.092,'cutoff\nγ = 0',fontsize=10,color=C['orange'])
ax.plot(1,0,'s',ms=12,mfc='none',mec=C['purple'],mew=1.7)
ax.text(.54,-.019,'m = 1: first mode at q = 1',fontsize=9,color=C['purple'])
ax.set_xlim(0,1.055);ax.set_ylim(-.024,.155);ax.set_xlabel(r'$q=|Q|/|k|$  (dimensionless)');ax.set_ylabel(r'$\gamma/(\beta k^2)$  (dimensionless)')
ax.set_title('A  |  Finite modes sample the band',fontsize=12,loc='left');ax.grid(alpha=.3);ax.legend(fontsize=9,loc='upper left',frameon=False)
ax=f.add_axes([.585,.28,.34,.48]);ms=np.arange(1,7)
sv_edges=np.array(sorted({.01,10.}|{n*n/(m*m-n*n) for m in ms for n in range(1,m) if .01<n*n/(m*m-n*n)<10.}))
sv=np.sqrt(sv_edges[:-1]*sv_edges[1:])
arr=np.array([[sum(n*n < m*m*ss/(1+ss)-1e-12 for n in range(1,m+1)) for m in ms] for ss in sv])
cmap=ListedColormap(['#F1F5F7','#C8E6EF','#82C7DB','#3E9DBD','#12749C','#154A71']);norm=BoundaryNorm(np.arange(-.5,6.5),6)
mesh=ax.pcolormesh(np.arange(.5,7),sv_edges,arr,cmap=cmap,norm=norm,shading='flat',rasterized=False)
for m in ms[1:]:ax.plot(m,1/(m*m-1),'D',ms=5,mfc='white',mec=C['orange'],mew=1.5)
ax.set_yscale('log');ax.set_ylim(.01,10);ax.set_xticks(ms);ax.set_xlabel('Carrier index |m|');ax.set_ylabel(r'Slope intensity $s=a^2 A^2 k^2$');ax.set_title('B  |  Number of growing ±n pairs',loc='left',fontsize=12)
cb=f.colorbar(mesh,ax=ax,ticks=range(6),pad=.045,fraction=.045);cb.ax.set_ylabel('Pair count',fontsize=9)
f.text(.078,.188,r'$0<n^2< m^2s/(1+s),\qquad k=2\pi m/L,\quad Q=2\pi n/L$',fontsize=15)
f.text(.078,.125,'Diamonds mark the first-mode threshold. Equality is marginal: a nonzero cutoff can have Jordan-block secular growth.',fontsize=10,color=C['orange'])
foot(f,'No growing mode is not proof of nonlinear stability. β has units L₀²/T₀; rates are scaled by βk². Left: s = 1, m = 4.\nRight: exact integer count on each plotted grid cell. Sources: report Section 4, Eqs. (15)-(23); Zhang et al. (2019) for the WKI equation.')
save(f,'03_wki_discrete_growth_bands',
'Exact linearized sideband growth of the report’s potential-WKI carrier. The continuum envelope is gamma/(beta k^2)=sqrt(max(0,q^2[s-(1+s)q^2]/(1+s)^3)). At s=1, m=4, the n=1 and n=2 pairs grow exponentially; n=3 and n=4 do not. A carrier with |m|=1 has no growing nonzero periodic sideband for finite s. The right panel counts allowed positive n, each representing a coupled plus/minus pair. Diamonds locate the n=1 threshold s=1/(m^2-1); the strict inequality excludes the cutoff. A nonzero cutoff may have a Jordan block and secular growth, and the zero mode needs its own norm/phase treatment. These results establish neither nonlinear stability nor experimental validation; the older transformed-background stability comparison remains unresolved.',
{'left_s':1,'left_carrier_m':4,'q_range':[0,1.02],'right_m':[1,2,3,4,5,6],'right_s_range':[.01,10],
'illustrative_units':'L0 and T0 arbitrary; beta has L0^2/T0, k and Q have 1/L0, gamma and omega have 1/T0',
'growth_equation':'gamma^2 = beta^2 Q^2 [k^2 s - (1+s)Q^2]/(1+s)^3 inside the band; gamma=0 outside',
'phase_relation':'omega/(beta k^2)=1/sqrt(1+s)'},
[{'label':'Report Section 4, Eqs. 15-23; direct conditional linearization','type':'supplied report'},
 {'label':'Zhang et al., Physica D (2019), equation source; transformed stability conventions not resolved here','url':'https://doi.org/10.1016/j.physd.2019.05.008'}])

# 04: Exact two-qubit dephasing model.
def neg(a,b,d):return np.maximum(0,(np.sqrt((a-b)**2+4*a*b*np.sin(d/2)**2)-(1-a*b))/4)
f=base('04','Entanglement needs phase and surviving coherence','A two-qubit model map, not an observed gravity signal or a new entanglement formula.')
ax=f.add_axes([.075,.28,.40,.49]);d=np.linspace(0,2*np.pi,501);av=np.linspace(0,1,401);D,A=np.meshgrid(d,av);b=.8;N=neg(A,b,D)
cm=plt.get_cmap('viridis').copy();cm.set_bad('#F0F3F5');img=ax.pcolormesh(d/np.pi,av,np.ma.masked_where(N<=1e-12,N),cmap=cm,vmin=0,vmax=.4,rasterized=True,shading='auto')
E=4*A*b*np.sin(D/2)**2-(1-A*A)*(1-b*b)
ax.contour(d/np.pi,av,E,levels=[0],colors=[C['ink']],linewidths=1.4)
ax.text(.99,.052,'separable',ha='center',color=C['muted'],fontsize=11)
ax.set_xticks([0,.5,1,1.5,2]);ax.set_xlabel(r'Nonlocal phase $\delta/\pi$');ax.set_ylabel('Coherence factor a');ax.set_title('A  |  Negativity, fixed b = 0.8',loc='left',fontsize=12)
cb=f.colorbar(img,ax=ax,fraction=.047,pad=.04);cb.set_label('Negativity N',fontsize=10)
ax=f.add_axes([.60,.28,.34,.49]);tau=np.linspace(0,1.5,700)
for ratio,col,ls in [(5,C['blue'],'-'),(3,C['teal'],'-'),(2,C['orange'],'--')]:
    ax.plot(tau,neg(np.exp(-tau),np.exp(-tau),ratio*tau),c=col,lw=2.2,ls=ls,label=fr'$|\kappa|/\gamma={ratio}$')
ax.axvline(np.arcsinh(1),color=C['muted'],ls=':',lw=1.5)
ax.text(.91,.22,'upper time bound\nfor equal γ > 0',fontsize=9,color=C['muted'])
ax.set_xlim(0,1.5);ax.set_ylim(-.008,.29);ax.set_xlabel(r'Scaled time $\gamma T$');ax.set_ylabel('Negativity N');ax.set_title('B  |  Constant, equal dephasing rates',loc='left',fontsize=12);ax.grid(alpha=.25);ax.legend(fontsize=10,frameon=False,loc='upper left')
f.text(.078,.188,r'$\mathcal{N}>0\ \Longleftrightarrow\ 4ab\sin^2(\delta/2)>(1-a^2)(1-b^2)$',fontsize=16)
f.text(.078,.12,'Balanced path qubits; deterministic diagonal interaction; independent local Z dephasing. For panel B: a = b = exp(−γT), δ = κT.',fontsize=10)
foot(f,'Synthetic parameter scan. No apparatus sensitivity, witness uncertainty or gravitational-origin inference is modeled.\nSpectrum prior art: Rizaldy et al., arXiv:2609.10697v1 (2026), Eqs. 28-30 and 61-62. Report Section 5 supplies the rate consequence.')
save(f,'04_phase_coherence_entanglement',
'An original plot of an established two-qubit partial-transpose result, attributed to Rizaldy et al. (September 2026 preprint) rather than claimed as new. Panel A shows negativity for the report’s balanced-path, deterministic-phase model with independent local Z dephasing and b=0.8. Gray denotes exact model separability, not an experimental nondetection threshold. The boundary is 4ab sin^2(delta/2)=(1-a^2)(1-b^2). Panel B specializes to equal constant rates and delta=kappa T. The ratio |kappa|/gamma=2 yields no entangling time; any positive negativity requires |kappa|>2gamma. All entangling times in that specialization obey gamma T<asinh(1). Other noise models, uncertain phase, finite witness sensitivity and a gravitational-origin inference require additional analysis. Coherence a is unrelated to the graph-encoding scale called a elsewhere.',
{'b_panel_A':.8,'a_range':[0,1],'delta_range_radians':[0,2*np.pi],'panel_B_kappa_over_gamma':[2,3,5],'gammaT_range':[0,1.5],'noise':'independent local Z dephasing; balanced factorized initial path qubits'},
[{'label':'Rizaldy, Sheehy, Zhou and Mazumdar (9 Sep 2026), preprint v1, Eqs. 28-30 and 61-62','url':'https://arxiv.org/html/2609.10697v1'},
 {'label':'Report Section 5, Eqs. 24-30','type':'supplied report'}])

# 05: Separate optical and material ledgers.
f=base('05','A clean ring is not a unique formation clock','A saturating inventory loses time sensitivity; optical alteration and physical export need separate measurements.')
ax=f.add_axes([.08,.29,.37,.48]);theta=np.linspace(0,5,501)
ax.plot(theta,1-np.exp(-theta),lw=2.7,c=C['teal'],label=r'Inventory $\lambda x/a$')
ax.plot(theta,np.exp(-theta),lw=2.4,c=C['orange'],ls='--',label=r'Sensitivity $(dx/dt)/a$')
ax.axhline(1,c=C['grid'],lw=1);ax.fill_between(theta,0,1,where=theta>=3,color=C['pale'],zorder=0)
ax.text(3.02,.50,'Near equilibrium:\nlittle change\nwith added time',fontsize=10,color=C['muted'],linespacing=1.5)
ax.set_xlabel(r'Scaled time $\theta=\lambda t$');ax.set_ylabel('Dimensionless response');ax.set_ylim(-.02,1.06);ax.set_xlim(0,5);ax.grid(alpha=.25);ax.legend(fontsize=10,frameon=False,loc='lower left',bbox_to_anchor=(.33,.20));ax.set_title('A  |  Constant-mass removal toy',loc='left',fontsize=12)
a=panel(f,[.51,.23,.45,.57]);a.text(0,.99,'B  |  Keep both ledgers',fontsize=12,fontweight='bold',va='top')
box(a,.20,.55,.57,.22,'Material inventory C','Elemental mass in the ring',C['teal'],12)
arrow(a,(.04,.66),(.19,.66),C['blue']);a.text(.035,.72,'input S',fontsize=9,color=C['blue'])
arrow(a,(.78,.66),(.98,.66),C['orange']);a.text(.78,.73,'export λphys C',fontsize=9,color=C['orange'])
box(a,.20,.11,.57,.25,'Optical absorption','Composition + optical state\n+ size and observing geometry',C['purple'],12)
arrow(a,(.48,.54),(.48,.37),C['muted']);a.text(.51,.44,'response',fontsize=9,color=C['muted'])
a.text(.00,-.025,'Altered absorption need not remove an element.',fontsize=10,color=C['purple'])
f.text(.08,.185,r'$\dot{x}=a-\lambda x,\quad x(0)=0,\qquad x=\frac{a}{\lambda}(1-e^{-\lambda t})$',fontsize=15)
f.text(.08,.12,'Toy assumptions: constant total ring mass, input and physical removal; initially clean, dilute inventory. No ring age is fitted.',fontsize=10)
foot(f,'Here a and λ have units 1/time; x is a mass fraction. An all-time literal fraction requires a/λ ≤ 1 (or a restricted dilute regime).\nSources: report Appendix C2, Eqs. P1-P2; Ricerchi & Crida (2026). The plotted toy is not their complete ring-evolution model.')
save(f,'05_ring_inventory_optical_clock',
'An exact solution of a deliberately restricted inventory toy and a schematic of two distinct measurement targets. With constant ring mass, constant retained input a, constant physical contaminant removal lambda>0 and x(0)=0, the scaled inventory is lambda*x/a=1-exp(-lambda*t), while normalized time sensitivity is exp(-lambda*t). Approaching equilibrium makes inverse age ill-conditioned. The material ledger is not identical to optical absorption: chemical or structural alteration may change absorption without exporting the corresponding element. Variable total mass, changing input and unknown initial pollution add ambiguity. This is neither a ring formation age determination nor the complete published Ricerchi-Crida model. Use a/lambda<=1 for an all-time literal mass fraction, or restrict to a dilute valid interval.',
{'theta_range':[0,5],'normalized_inventory':'1-exp(-theta)','normalized_sensitivity':'exp(-theta)','units':'x dimensionless; a and lambda inverse time','not_estimated':'No Saturn age, measured rate or contamination fraction'},
[{'label':'Ricerchi & Crida, Saturn’s rings age I (2026), author manuscript v1; optical-removal realism remains uncertain','url':'https://arxiv.org/html/2603.04102v1'},
 {'label':'Report Appendix C2, Eqs. P1-P2','type':'supplied report'}])

# 06: Two physical transfer pathways; common discipline, distinct kernels.
f=base('06','Formation is only the start of a detected sample','Enceladus grains and lunar ions share an inference discipline, with different physics at every stage.')
a=panel(f,[.045,.255,.91,.56]);xs=[.015,.270,.525,.780];w=.205
for j,(lab,titles,bodies,col) in enumerate([
 ('ENCELADUS',['Formation history','Daughter configuration','Physical survival','Instrument record'],['Recipe + cooling\nPhase + microstructure','Fragment sizes + marks\nElemental balance','Sublimation / transport\nExposure + speed','Trigger + telemetry\nImpact response'],C['teal']),
 ('LUNAR SURFACE',['Incident population','Particle production','Physical survival','Instrument record'],['Upstream source\nMaterial + disturbance','Scattering / sputtering\nCharge conversion','Photodetachment\nAngular transport','Acceptance + efficiency\nEnergy / species response'],C['blue'])]):
    y=.54 if j==0 else .03
    a.text(.016,y+.40,lab,fontsize=10,fontweight='bold',color=col)
    for x,t,bod in zip(xs,titles,bodies):box(a,x,y,w,.34,t,bod,col,10.6)
    for x in xs[:-1]:arrow(a,(x+w+.008,y+.17),(x+.245,y+.17),col)
# Deliberately minimal lower control statements, not a third physical pathway.
f.text(.061,.213,'Control the Enceladus comparison',fontsize=11,fontweight='bold',color=C['teal'])
f.text(.061,.157,'Measure chemistry and phase before and after drying.\nCompare the same grain, or a declared matched population.',fontsize=10,linespacing=1.65)
f.text(.525,.213,'Control the lunar comparison',fontsize=11,fontweight='bold',color=C['blue'])
f.text(.525,.157,'Separate ionization probability from detector calibration.\nRetain source exposure, angular support and non-detections.',fontsize=10,linespacing=1.65)
foot(f,'Proposed experimental / inference design, not a Cassini or lunar reconstruction. Physical loss precedes detector selection.\nSources: report Sections 6 and C4-C6; Postberg et al. (2026), EPSC2026-1326, and the Chang’e-6 studies (2025-2026).')
save(f,'06_planetary_transfer_comparison',
'An original comparison of two source-to-record designs. The Enceladus route preserves formation history, phase assemblage, fragmentation, elemental balance, physical survival, and instrument selection as distinct stages. The lunar route separates incident populations, production and negative-ion conversion, physical survival and angular transport, and the detector response. Similar diagram positions do not imply shared kernels or dynamics. Proposed laboratory controls include paired pre/post-drying phase and chemistry measurements and independently constrained detector calibration. The drawing does not imply Cassini CAT can identify crystallographic phases. The final slow-freezing methods/supplement and exact selected-event manifest were not recovered in the source review; rapid-decompression evidence remains conference-level. Lunar results retain their site, exposure and calibration limits.',
{'diagram':'Conceptual proposed measurement pathways; no measured counts or inferred proportions','distinction':'physical survival is not detector selection'},
[{'label':'Postberg et al., slow-freezing and fragmentation, Science Advances (2026); full methods/supplement access incomplete','url':'https://doi.org/10.1126/sciadv.aee7256'},
 {'label':'Hogan et al., EPSC2026-1326, conference abstract; freeze-dried residue analysis','url':'https://meetingorganizer.copernicus.org/EPSC2026/EPSC2026-1326.html'},
 {'label':'Chang’e-6 negative-ion study (2025)','url':'https://www.nature.com/articles/s43247-025-02399-7'},
 {'label':'Chang’e-6 negative-ion author manuscript (2026), calibration coupling','url':'https://arxiv.org/html/2602.16567v1'},
 {'label':'Report Sections 6, C4 and C6','type':'supplied report'}])

# Animations are analytic kinematics, not solutions of a fluid or filament PDE.
def canvas_frame(f):
    f.canvas.draw();return Image.fromarray(np.asarray(f.canvas.buffer_rgba())[:,:,:3].copy())

def save_anim(frames,stem,fps,caption,params,sources):
    gif=ANIM/(stem+'.gif');dur=int(round(1000/fps))
    # A shared palette prevents frame-dependent recoloring. No full-frame color flashes.
    strip=Image.new('RGB',(frames[0].width*4,frames[0].height))
    for j,idx in enumerate(np.linspace(0,len(frames)-1,4,dtype=int)):strip.paste(frames[idx],(j*frames[0].width,0))
    pal=strip.quantize(colors=256)
    quant=[im.quantize(palette=pal,dither=Image.Dither.NONE) for im in frames]
    quant[0].save(gif,save_all=True,append_images=quant[1:],duration=dur,loop=0,optimize=False,disposal=2)
    # Preserve full-frame PNGs for independent QA and lossless reproducibility.
    fd=QA/(stem+'_frames');fd.mkdir(exist_ok=True)
    for i,im in enumerate(frames):im.save(fd/f'{i:03d}.png')
    poster=ANIM/(stem+'_poster.png');frames[0].save(poster)
    files=[str(gif.relative_to(ROOT)),str(poster.relative_to(ROOT))]
    if shutil.which('ffmpeg'):
        mp4=ANIM/(stem+'.mp4')
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(fps),'-i',str(fd/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(mp4)],check=True)
        files.append(str(mp4.relative_to(ROOT)))
    thumbw=260;thumbh=round(frames[0].height*thumbw/frames[0].width)
    sheet=Image.new('RGB',(thumbw*8,(thumbh+22)*int(np.ceil(len(frames)/8))),'white');draw=ImageDraw.Draw(sheet)
    for i,im in enumerate(frames):
        x=(i%8)*thumbw;y=(i//8)*(thumbh+22);sheet.paste(im.resize((thumbw,thumbh)),(x,y));draw.text((x+8,y+thumbh+3),f'Frame {i:03d}',fill=C['ink'])
    sheet.save(QA/(stem+'_all_frames.jpg'),quality=92)
    # Direct difference audit, including the loop boundary. This is not a medical flash-safety certification.
    diffs=[]
    for i in range(len(frames)):
        a=np.asarray(frames[i],dtype=float);bb=np.asarray(frames[(i+1)%len(frames)],dtype=float)
        diffs.append(float(np.abs(a-bb).mean()/255))
    manifest.append({'id':stem,'kind':'animation','files':files,'caption':caption,'parameters':params,'sources':sources,
      'frames':len(frames),'fps':fps,'duration_seconds':len(frames)/fps,'qa':{'all_frame_sheet':str((QA/(stem+'_all_frames.jpg')).relative_to(ROOT)), 'maximum_mean_RGB_frame_difference':max(diffs),'loop_mean_RGB_difference':diffs[-1],'fixed_palette':True,'full_frame_flashes':False}})

frames=[];Tloop=10.;nframe=100;op=2*np.pi/(10*Tloop);om=4*np.pi/Tloop;theta=np.linspace(0,2*np.pi,1000)
f=base('A1','Pattern speed is not material speed','A synthetic ten-lobed wave and prescribed tracers, shown from above. No Saturn speed is fitted.',size=(10,6.4));f.set_dpi(110)
ax=f.add_axes([.045,.14,.51,.65]);ax.set_aspect('equal');ax.set_xlim(-1.27,1.27);ax.set_ylim(-1.27,1.27);ax.axis('off')
for rr in [.84,1.]:ax.add_patch(Circle((0,0),rr,fill=False,ec=C['grid'],lw=1,ls='--'))
ax.add_patch(Circle((0,0),.64,fc=C['pale'],ec='none'))
line,=ax.plot([],[],color=C['blue'],lw=2.7);pts=ax.scatter([],[],c=C['orange'],s=36,zorder=5);one=ax.scatter([],[],c=C['orange'],s=110,edgecolors=C['ink'],linewidths=1.1,zorder=6)
ax.text(0,0,'POLAR\nPROJECTION',ha='center',va='center',fontsize=10,color=C['muted'],linespacing=1.7)
r=panel(f,[.61,.20,.34,.58]);r.text(0,.95,'BLUE  |  wave pattern',fontsize=12,fontweight='bold',color=C['blue']);r.text(0,.83,'r = 1 + ε cos[10(θ − Ωp t)]\nOne wavelength advances per loop.',fontsize=10.5,linespacing=1.65)
r.text(0,.60,'ORANGE  |  tracers',fontsize=12,fontweight='bold',color=C['orange']);r.text(0,.48,'θj(t) = θj(0) + Ωm t\nTwo circuits per loop at fixed radius.',fontsize=10.5,linespacing=1.65)
r.text(0,.25,'These motions were prescribed\nindependently. No advection or\nshallow-water equations were solved.',fontsize=11,linespacing=1.65)
foot(f,'Kinematic illustration only. Radius and angular rates are arbitrary; not a spacecraft image or a reconstruction.\nMotivation: report Appendix C3 and ESA/Hubble’s 2 September 2026 Saturn-decagon release.')
for i in range(nframe):
    t=Tloop*i/nframe;rr=1+.065*np.cos(10*(theta-op*t));line.set_data(rr*np.cos(theta),rr*np.sin(theta))
    ang=np.arange(8)*2*np.pi/8+om*t;xy=np.column_stack((.84*np.cos(ang),.84*np.sin(ang)));pts.set_offsets(xy);one.set_offsets(xy[:1]);frames.append(canvas_frame(f))
plt.close(f)
save_anim(frames,'A1_pattern_vs_material_motion',10,
'A looped analytic kinematic illustration motivated by the distinction between a planetary wave pattern and material motion. A synthetic polar trace r=1+0.065 cos[10(theta-Omega_p t)] advances by one wavelength in ten seconds, while prescribed orange markers at radius 0.84 make two complete circuits. The rates, radii and amplitudes are arbitrary display parameters, not measured Saturn quantities. The marker paths are not computed by advecting particles in a self-consistent fluid field. Neither the shape nor its animation is evidence for SCM or a shallow-water mechanism.',
{'loop_seconds':10,'lobes':10,'epsilon':.065,'mean_radius_arbitrary_units':1,'tracer_radius':.84,'Omega_pattern_radians_per_display_second':op,'Omega_material_radians_per_display_second':om,'tracers':8,'not_a_model_solution':True},
[{'label':'ESA/Hubble, Saturn decagon release, 2 Sep 2026; observational motivation only','url':'https://esahubble.org/news/heic2612/'}, {'label':'Report Appendix C3','type':'supplied report'}])

frames=[];Tloop=8.;nframe=80
f=base('A2','A bending graph and its moving normal plane','Analytic geometric interpolation; displayed time is a drawing parameter, not physical evolution.',size=(10,6.4));f.set_dpi(110)
ax=f.add_axes([.035,.18,.61,.62]);r=panel(f,[.68,.19,.29,.62])
r.text(0,.96,'BLUE  |  centerline',fontsize=11.5,fontweight='bold',color=C['blue']);r.text(0,.83,'F(x, t) =\n(x, A(t) cos kx, A(t) sin kx)',fontsize=11,linespacing=1.6)
r.text(0,.60,'TEAL  |  normal plane',fontsize=11.5,fontweight='bold',color=C['teal']);r.text(0,.49,'The frame is recomputed\nfrom the tangent at each step.',fontsize=10.5,linespacing=1.6)
r.text(0,.29,'ORANGE  |  fixed-x plane',fontsize=11.5,fontweight='bold',color=C['orange']);r.text(0,.18,'Finite slope keeps graph\nand normal planes distinct.',fontsize=10.5,linespacing=1.6)
foot(f,'A(t)/L₀ = 0.55 + 0.15 cos(2πt/8); k = 1/L₀. Length and display time are arbitrary. No PDE is integrated.\nT, N and B are orthonormal analytically in every frame. This is geometry, not a microscopic material mechanism.')
for i in range(nframe):
    A=.55+.15*np.cos(2*np.pi*i/nframe);ax.clear();draw_geometry(ax,A=A,labels=True);frames.append(canvas_frame(f))
plt.close(f)
save_anim(frames,'A2_bending_graph_normal_frame',10,
'A smooth loop through a prescribed family of helices F(x,t)=(x,A(t)cos(kx),A(t)sin(kx)), with A(t)/L0=0.55+0.15 cos(2*pi*t/8), k=1/L0 and fixed frame location x=3.5L0. Each frame recomputes the exact tangent, principal normal and binormal. The changing teal plane stays perpendicular to the tangent; the orange fixed-x plane contains transverse graph coordinates. This is a geometric interpolation with arbitrary display time, not an integrated SCM, WKI, binormal-flow or quantum-dynamical solution. It does not establish material content, spin, charge or gravity.',
{'A_mean_in_L0':.55,'A_amplitude_in_L0':.15,'k_in_inverse_L0':1,'x_range_in_L0':[0,8],'frame_x_in_L0':3.5,'display_period_seconds':8,'projection_rows':P.tolist(),'not_a_model_solution':True},
[{'label':'Report Section 3: graph gauge and geometric caveats','type':'supplied report'}, {'label':'Hasimoto, A soliton on a vortex filament (1972)','url':'https://doi.org/10.1017/S0022112072002307'}])

# Independent numerical controls of equations used in the drawings.
checks={}
worst=0
for A in np.linspace(.4,.7,81):
    T,N,B=frame(3.5,A);M=np.stack([T,N,B]);worst=max(worst,float(np.max(np.abs(M@M.T-np.eye(3)))))
checks['maximum_normal_frame_orthogonality_error']=worst
checks['projection_orthonormality_error']=float(np.max(np.abs(P@P.T-np.eye(2))))
checks['wki_m4_s1_growing_positive_indices']=[n for n in range(1,5) if n*n<16/2]
checks['wki_m1_s1_growing_positive_indices']=[n for n in range(1,5) if n*n<1/2]
checks['wki_max_scaled_at_s1_qhalf']=float(growth(.5,1))
checks['quantum_negativity_controls']={'a1_b1_delta_pi':float(neg(1,1,np.pi)),'delta0':float(neg(.8,.7,0)),'a0':float(neg(0,.7,1))}
# Independently build the 4x4 state and partial transpose instead of checking the formula against itself.
rng=np.random.default_rng(20261005);errors=[];I=np.eye(2);X=np.array([[0,1],[1,0]])
for _ in range(200):
    aa,bb=rng.random(2);dd=rng.uniform(0,2*np.pi);rho0=np.kron((I+aa*X)/2,(I+bb*X)/2)
    U=np.diag(np.exp(1j*dd*np.array([1,-1,-1,1])/4));rho=U@rho0@U.conj().T
    pt=rho.reshape(2,2,2,2).transpose(0,3,2,1).reshape(4,4);eig=np.linalg.eigvalsh(pt)
    numeric=-eig[eig<0].sum();errors.append(abs(numeric-neg(aa,bb,dd)))
checks['quantum_formula_vs_independent_partial_transpose_max_error']=float(max(errors))
checks['random_test_seed']=20261005
assert worst<1e-12 and max(errors)<1e-12
assert checks['wki_m4_s1_growing_positive_indices']==[1,2]
assert checks['wki_max_scaled_at_s1_qhalf']==.125
(ROOT/'validation.json').write_text(json.dumps(checks,indent=2)+'\n')
# Public-safe manifest and captions use relative paths only.
for entry in manifest:
    entry['sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in entry['files']}
(ROOT/'manifest.json').write_text(json.dumps({'title':'Scientific Visual Atlas: ASTRA SPPT SCM research companion','date':'2026-10-05','status':'Unpromoted research companion; synthetic / schematic figures; no empirical validation','assets':manifest},indent=2,ensure_ascii=False)+'\n')
md=['# Scientific Visual Atlas','', 'Original deterministic figures for the research companion dated 5 October 2026. All scientific claims retain the report’s evidence status. This atlas is an unpromoted companion, not a new theory, experimental validation or update to stable science authority.','']
for ent in manifest:
    md+=['## '+ent['id'],'',ent['caption'],'','Files: '+', '.join('`'+p+'`' for p in ent['files']), '','Sources:']
    for src in ent['sources']:md+=['- '+src['label']+(' — '+src['url'] if 'url'in src else '')]
    md+=['']
(ROOT/'CAPTIONS_AND_SOURCES.md').write_text('\n'.join(md)+'\n')
print('Created',len(manifest),'assets. Validation:',json.dumps(checks))
