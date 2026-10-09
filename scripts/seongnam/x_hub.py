"""마을버스 공통 정차 정류장 + 운행량 (정류소ID 기준)"""
import csv, io, json, sys, glob, os, collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
# 노선ID -> 이름. 종류/지역은 노선ID로 받은 값이라 노선명 중복과 무관하다
routes={}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    try: b=json.load(open(f,encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    except Exception: continue
    if isinstance(b,list): b=b[0]
    routes[str(b['routeId'])]=(str(b.get('routeName')),b.get('routeTypeName',''),b.get('regionName',''))
village={k:v[0] for k,v in routes.items() if v[1]=='마을버스' and '성남' in v[2]}
print(f'성남 마을버스 노선 {len(village)}개')
# 정류소ID -> 경유 마을버스 노선명
byid=collections.defaultdict(set)
miss=[]
for rid,nm in village.items():
    p=f'data/raw/gg_routestation/{rid}.json'
    if not os.path.exists(p): miss.append((rid,nm)); continue
    lst=json.load(open(p,encoding='utf-8'))['response']['msgBody'].get('busRouteStationList',[])
    if isinstance(lst,dict): lst=[lst]
    for s in lst: byid[str(s['stationId'])].add(nm)
if miss: print(f'  경유정류소 캐시 없음 {len(miss)}개: {miss[:5]}')
print(f'마을버스가 서는 정류소 {len(byid)}개 (성남 외 정류소 포함)\n')
rows=[r for r in csv.DictReader(open('data/seongnam_stop_frequency.csv',encoding='utf-8-sig')) if r['미정차']=='N']
print(f'성남 정류장 {len(rows)}개')
out=[]
for r in rows:
    sid=r['정류장번호'][3:] if r['정류장번호'].startswith('GGB') else r['정류장번호']
    v=sorted(byid.get(sid,()))
    out.append(dict(정류소ID=sid,정류장명=r['정류장명'],번호=r['모바일단축번호'],
        구=r['구'],행정동=r['행정동'],
        마을버스수=len(v),마을버스=','.join(v),
        전체노선수=len(r['경유노선'].split()),하루운행=int(r['도내노선_운행횟수']),
        위도=r['위도'],경도=r['경도']))
print(f'그 중 마을버스가 서는 곳 {sum(1 for x in out if x["마을버스수"])}개\n')
out.sort(key=lambda x:(-x['마을버스수'],-x['하루운행']))
print('■ 마을버스가 가장 많이 지나는 정류장 (상위 20)')
print(f"{'#':>2} {'마을':>4}{'운행':>7}  {'구':<4}{'행정동':<8}{'정류장명':<26} 마을버스 노선")
for i,x in enumerate(out[:20],1):
    print(f"{i:>2} {x['마을버스수']:>3}개{x['하루운행']:>6}회  {x['구'][:2]:<4}{x['행정동']:<8}{x['정류장명'][:24]:<26}{x['마을버스'][:34]}")
print()
d=collections.Counter(x['마을버스수'] for x in out)
print('■ 마을버스 경유 수 분포')
for k in sorted(d,reverse=True)[:10]: print(f'  {k}개 경유: 정류장 {d[k]}곳')
print(f'  0개(마을버스 없음): {d[0]}곳')
with open('data/seongnam_village_hub.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print('\n-> data/seongnam_village_hub.csv')
