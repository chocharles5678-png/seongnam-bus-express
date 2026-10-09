"""정차 1회당 손실시간(T) 추정 — 버스 위치 관측에서 구간 소요시간을 복원해 회귀
  구간 소요시간 = T + 구간거리 / 주행속도   →  절편 T가 정차 고정비용(감속+승하차+가속)
사용: python scripts/seongnam/x_dwell.py [노선...]
"""
import json,io,sys,glob,math,collections,itertools
from datetime import datetime
import numpy as np
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
want=sys.argv[1:] or None
routes={}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    b=json.load(open(f,encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    if isinstance(b,list): b=b[0]
    routes[str(b.get('routeName'))]=str(b['routeId']) if b.get('routeTypeName')=='마을버스' else routes.get(str(b.get('routeName')))
def coords(nm):
    A=json.load(open(f'data/raw/gg_routestation/{routes[nm]}.json',encoding='utf-8'))['response']['msgBody']['busRouteStationList']
    return {s['stationSeq']:(float(s['x']),float(s['y']),s['stationName']) for s in A}
def hav(a,b):
    R=6371000;p=math.pi/180
    h=math.sin((b[1]-a[1])*p/2)**2+math.cos(a[1]*p)*math.cos(b[1]*p)*math.sin((b[0]-a[0])*p/2)**2
    return 2*R*math.asin(math.sqrt(h))
obs=[]
for f in glob.glob('data/raw/bus_location/*.jsonl'):
    for l in open(f,encoding='utf-8'): obs.append(json.loads(l))
print(f'관측 {len(obs)}건 / 파일 {len(glob.glob("data/raw/bus_location/*.jsonl"))}개\n')
for rt,g in itertools.groupby(sorted(obs,key=lambda r:r['route']),key=lambda r:r['route']):
    if want and rt not in want: continue
    g=list(g); XY=coords(rt); segs=[]
    for pl,vg in itertools.groupby(sorted(g,key=lambda r:(r['plateNo'],r['ts'])),key=lambda r:r['plateNo']):
        vg=list(vg)
        # 정류소별 첫·마지막 관측 시각 → 도착시각은 (이전 정류소 마지막 관측, 현 정류소 첫 관측)의 중점
        runs=[]
        for seq,sg in itertools.groupby(vg,key=lambda r:r['stationSeq']):
            sg=list(sg); runs.append((seq,datetime.fromisoformat(sg[0]['ts']),datetime.fromisoformat(sg[-1]['ts'])))
        arr={}
        for i in range(1,len(runs)):
            s0,_,l0=runs[i-1]; s1,f1,_=runs[i]
            if s1!=s0+1: continue                      # 연속 정류소만 사용 (관측 누락 구간 제외)
            arr[s1]=l0+(f1-l0)/2
        for s in sorted(arr):
            if s-1 in arr and s-1 in XY and s in XY:
                dt=(arr[s]-arr[s-1]).total_seconds()
                d=hav(XY[s-1][:2],XY[s][:2])
                if 0<dt<900 and 20<d<2000: segs.append((d,dt,pl,s))
    if len(segs)<8: print(f'[{rt}] 구간 관측 {len(segs)}건 — 회귀에 부족\n'); continue
    d=np.array([s[0] for s in segs]); t=np.array([s[1] for s in segs])
    b,a=np.polyfit(d,t,1)                              # t = a + b*d
    pred=a+b*d; ss=1-((t-pred)**2).sum()/((t-t.mean())**2).sum()
    n=len(segs); se=math.sqrt(((t-pred)**2).sum()/(n-2)/((d-d.mean())**2).sum())
    sa=se*math.sqrt((d**2).sum()/n)
    print(f'[{rt}] 구간 관측 {n}건 / 차량 {len({s[2] for s in segs})}대')
    print(f'   구간거리 중앙 {np.median(d):.0f}m, 소요 중앙 {np.median(t):.0f}초')
    print(f'   회귀: 소요(초) = {a:.1f} + {b:.4f} × 거리(m)     R²={ss:.2f}')
    print(f'   → 정차 고정 손실 T = {a:.1f}초  (±{1.96*sa:.1f}, 95%)')
    v=3.6/b if b>0 else -1.0
    print(f'   → 주행속도 = {v:.1f} km/h' if v>0 else '   → 기울기가 음수다. 식별 실패')
    # 타당성 검사 — 마을버스 구간 주행속도는 대체로 15~40km/h. 벗어나면 회귀가 식별되지 않은 것이다.
    bad=[]
    if not (10<=v<=45): bad.append(f'환산 주행속도 {v:.0f}km/h 가 비현실적')
    if ss<0.30: bad.append(f'R²={ss:.2f} — 거리가 소요시간을 설명하지 못함')
    if n<300: bad.append(f'구간 관측 {n}건 (권장 300건 이상)')
    print('   ⚠ 이 T는 쓸 수 없다: ' + ' / '.join(bad) if bad else '   ✓ 타당성 검사 통과')
    print()
