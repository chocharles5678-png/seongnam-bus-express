"""급행 재편 전후 비교 그림 — x_express.py 결과(data/express_*.csv)를 그린다
사용: python scripts/seongnam/x_express_fig.py 88-1 | 32
"""
import csv,io,sys,json,glob,collections
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
plt.rcParams['font.family']='Malgun Gothic'; plt.rcParams['axes.unicode_minus']=False
name=sys.argv[1] if len(sys.argv)>1 else '88-1'
TITLE={'88-1':'88-1번 (원도심 · 모란↔태평↔산성역↔영원무역)','32':'32번 (분당·판교 · 미금역↔서판교↔판교역↔서현역)'}
C_STOP='#C8102E'; C_PASS='#9AA5B1'
rows=list(csv.DictReader(open(f'data/express_{name.replace("-","_")}.csv',encoding='utf-8-sig')))
# 좌표: 노선 경유정류소 캐시에서 정류소ID로
routes={}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    b=json.load(open(f,encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    if isinstance(b,list): b=b[0]
    routes[str(b['routeId'])]=(str(b.get('routeName')),b.get('routeTypeName',''),b.get('peekAlloc'))
rid=[k for k,v in routes.items() if v[0]==name and v[1]=='마을버스'][0]
alloc=routes[rid][2]
A=json.load(open(f'data/raw/gg_routestation/{rid}.json',encoding='utf-8'))['response']['msgBody']['busRouteStationList']
xy={str(s['stationId']):(float(s['x']),float(s['y'])) for s in A}
seq=[s for s in A if '(경유)' not in s['stationName']]
info={r['정류소명']:r for r in rows}
fig=plt.figure(figsize=(15.5,7.4))
gs=fig.add_gridspec(2,2,width_ratios=[1.15,1],height_ratios=[1,1],hspace=0.45,wspace=0.16)
# ── (좌) 노선도
ax=fig.add_subplot(gs[:,0])
px=[xy[str(s['stationId'])][0] for s in seq]; py=[xy[str(s['stationId'])][1] for s in seq]
ax.plot(px,py,'-',color='#CBD2D9',lw=2.2,zorder=1,solid_capstyle='round')
for r in rows:
    ids=r['정류소ID'].split(); pts=[xy[i] for i in ids if i in xy]
    if not pts: continue
    u=float(r['왕복일평균']); on=r['급행정차']=='정차'
    s=18+ (u**0.62)*1.5
    for x,y in pts:
        ax.scatter(x,y,s=s if on else 22,c=C_STOP if on else 'none',
                   edgecolors=C_STOP if on else C_PASS,linewidths=1.6 if on else 1.0,
                   alpha=0.9 if on else 0.75,zorder=3 if on else 2)
import math
cx,cy=np.mean(px),np.mean(py)
ax.set_aspect(1/math.cos(math.radians(cy)))   # 위경도 → 실제 축척
lab=sorted([r for r in rows if r['급행정차']=='정차'],key=lambda r:-float(r['왕복일평균']))[:7]
placed=[]
for r in lab:
    i=r['정류소ID'].split()[0]
    if i not in xy: continue
    x,y=xy[i]
    dx,dy=x-cx,y-cy; m=math.hypot(dx,dy) or 1          # 중심에서 바깥쪽으로 밀어낸다
    ox,oy=dx/m*46,dy/m*46
    for q in placed:                                    # 이미 놓인 라벨과 겹치면 더 민다
        if abs(ox-q[0])<58 and abs(oy-q[1])<20: oy+= 26 if oy>=0 else -26
    placed.append((ox,oy))
    ax.annotate(r['정류소명'][:13],(x,y),textcoords='offset points',xytext=(ox,oy),fontsize=9,
                ha='center',va='center',color='#1F2933',weight='bold',zorder=5,
                bbox=dict(boxstyle='round,pad=0.26',fc='white',ec='#CBD2D9',alpha=0.93,lw=0.8),
                arrowprops=dict(arrowstyle='-',color='#9AA5B1',lw=0.9,shrinkA=0,shrinkB=4))
ax.set_title(f'{TITLE.get(name,name)}\n급행 정차역 (원 크기 = 일평균 이용)',fontsize=12,weight='bold',pad=16)
ax.margins(0.28)          # 라벨이 축 밖으로 나가지 않게 여백
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_color('#E4E7EB')
ax.legend(handles=[Line2D([],[],marker='o',ls='',mfc=C_STOP,mec=C_STOP,ms=9,label='급행 정차'),
                   Line2D([],[],marker='o',ls='',mfc='none',mec=C_PASS,ms=7,label='급행 통과 (완행만 정차)')],
          loc='upper left',frameon=False,fontsize=9.5,bbox_to_anchor=(0.0,1.0))
# ── (우상) 기존 vs 급행 띠
ax2=fig.add_subplot(gs[0,1])
n=len(seq)
for k,s in enumerate(seq):
    r=info.get(s['stationName'])
    on=r and r['급행정차']=='정차'
    ax2.scatter(k,1,s=26,c='#52606D',zorder=2)
    if on: ax2.scatter(k,0,s=40,c=C_STOP,zorder=2)
ax2.plot([0,n-1],[1,1],color='#CBD2D9',lw=1.4,zorder=1)
ax2.plot([0,n-1],[0,0],color='#CBD2D9',lw=1.4,zorder=1)
nstop=sum(1 for s in seq if info.get(s['stationName'],{}).get('급행정차')=='정차')
ax2.set_yticks([1,0]); ax2.set_yticklabels([f'기존 (모두 정차)\n{n}회',f'급행\n{nstop}회'],fontsize=10)
ax2.set_xlim(-1,n); ax2.set_ylim(-0.6,1.6); ax2.set_xticks([])
ax2.set_title(f'왕복 1회 정차 횟수:  {n}회 → {nstop}회  (통과 {n-nstop}회)',fontsize=11.5,weight='bold',pad=9)
for sp in ax2.spines.values(): sp.set_visible(False)
# ── (우하) 순서별 수요
ax3=fig.add_subplot(gs[1,1])
vals=[]; cols=[]
for s in seq:
    r=info.get(s['stationName'])
    u=float(r['왕복일평균'])/len(r['정류소ID'].split()) if r else 0
    on=r and r['급행정차']=='정차'
    vals.append(u); cols.append(C_STOP if on else C_PASS)
ax3.bar(range(n),vals,color=cols,width=0.82)
ax3.set_title('정류소 순서별 일평균 이용 — 빨강이 급행 정차',fontsize=11.5,weight='bold',pad=9)
ax3.set_xlabel('노선 진행 순서 →',fontsize=9.5); ax3.set_ylabel('일평균 이용(건)',fontsize=9.5)
ax3.set_xlim(-1,n); ax3.set_xticks([])
ax3.grid(axis='y',color='#F0F2F5',lw=0.9); ax3.set_axisbelow(True)
for sp in ('top','right'): ax3.spines[sp].set_visible(False)
for sp in ('left','bottom'): ax3.spines[sp].set_color('#CBD2D9')
cov=sum(float(r['왕복일평균']) for r in rows if r['급행정차']=='정차')/sum(float(r['왕복일평균']) for r in rows)*100
fig.text(0.985,0.015,f'평일 최소배차 {alloc}분 · 급행이 담는 기록 {cov:.0f}%  |  자료: 경기도 정류소별 승하차(2026.6), 경기버스정보 노선·정류소',
         ha='right',fontsize=8.5,color='#7B8794')
out=f'figures/급행_{name.replace("-","_")}_전후비교.png'
fig.savefig(out,dpi=170,bbox_inches='tight',facecolor='white')
print(f'-> {out}  (정차 {nstop}/{n}, 수요커버 {cov:.0f}%)')
