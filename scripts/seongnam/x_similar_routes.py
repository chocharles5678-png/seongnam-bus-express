"""유사 노선 묶기 — 정류소 중복률"""
import io,json,glob,os,sys,itertools,collections
import numpy as np
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
meta={}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    try: b=json.load(open(f,encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    except Exception: continue
    if isinstance(b,list): b=b[0]
    meta[str(b['routeId'])]=dict(name=str(b.get('routeName')),alloc=b.get('peekAlloc'),   # 평일 최소 배차(분)
        start=b.get('startStationName',''),end=b.get('endStationName',''),co=b.get('companyName',''))
R={}
for p in glob.glob('data/raw/gg_routestation/*.json'):
    rid=os.path.basename(p)[:-5]
    lst=json.load(open(p,encoding='utf-8')).get('response',{}).get('msgBody',{}).get('busRouteStationList',[])
    if isinstance(lst,dict): lst=[lst]
    if not lst: continue
    R[rid]=dict(stops=[str(s['stationId']) for s in lst],
                names={str(s['stationId']):s['stationName'] for s in lst},
                xy={str(s['stationId']):(float(s['x']),float(s['y'])) for s in lst})
print(f'노선 {len(R)}개 / 정류소 수 중앙값 {int(np.median([len(v["stops"]) for v in R.values()]))}\n')
sets={k:set(v['stops']) for k,v in R.items()}
pairs=[]
for a,b in itertools.combinations(sorted(R),2):
    A,B=sets[a],sets[b]; inter=len(A&B)
    if inter<5: continue
    pairs.append((inter/min(len(A),len(B)), inter/len(A|B), inter, a, b))
pairs.sort(reverse=True)
print('■ 경로가 가장 많이 겹치는 노선 쌍 (상위 20)')
print(f"{'중복률':>6}{'자카드':>7}{'공통':>5}  노선A          노선B          기점~종점")
for ov,ja,n,a,b in pairs[:20]:
    ma,mb=meta.get(a,{}),meta.get(b,{})
    print(f'{ov*100:>5.0f}%{ja*100:>6.0f}%{n:>5}  {ma.get("name","?"):<6}({len(sets[a]):>3})  {mb.get("name","?"):<6}({len(sets[b]):>3})  '
          f'{ma.get("start","")[:12]}~{ma.get("end","")[:12]}')
# 묶음: 중복률 0.7 이상으로 연결
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
ids=sorted(R); idx={k:i for i,k in enumerate(ids)}
rows=[idx[a] for ov,ja,n,a,b in pairs if ov>=0.7]; cols=[idx[b] for ov,ja,n,a,b in pairs if ov>=0.7]
m=sp.coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(ids),len(ids)))
nc,lab=connected_components(m,directed=False)
groups=collections.defaultdict(list)
for k,i in idx.items(): groups[lab[i]].append(k)
big=[g for g in groups.values() if len(g)>1]
big.sort(key=lambda g:-len(g))
print(f'\n■ 중복률 70% 이상으로 묶인 그룹 {len(big)}개')
for g in big:
    nm=[meta.get(r,{}).get('name','?') for r in g]
    al=[meta.get(r,{}).get('alloc') for r in g]
    common=set.intersection(*[sets[r] for r in g])
    print(f"  [{', '.join(nm)}]  배차 {al}  공통 정류소 {len(common)}개 / 각 노선 {[len(sets[r]) for r in g]}")
json.dump({'groups':[[r for r in g] for g in big]},open('data/route_groups.json','w'),ensure_ascii=False)
print('\n-> data/route_groups.json')
