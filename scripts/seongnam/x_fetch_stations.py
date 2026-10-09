"""노선별 경유정류소 목록 수집 (성남 마을버스 위주)"""
import io,json,glob,os,sys,time,urllib.parse,urllib.request
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
KEY=None
for l in open('.env',encoding='utf-8'):
    if l.startswith('DATA_GO_KR_KEY='): KEY=l.split('=',1)[1].strip()
assert KEY, '키 없음'
OUT='data/raw/gg_routestation'; os.makedirs(OUT,exist_ok=True)
# 캐시에서 노선ID -> (이름, 종류, 지역)
routes={}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    try: b=json.load(open(f,encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    except Exception: continue
    if isinstance(b,list): b=b[0]
    routes[str(b['routeId'])]=(str(b.get('routeName')), b.get('routeTypeName',''), b.get('regionName',''))
tgt={k:v for k,v in routes.items() if v[1]=='마을버스' and '성남' in v[2]}
print(f'전체 노선 {len(routes)} / 성남 마을버스 {len(tgt)}개')
base='http://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteStationListv2'
ok=skip=fail=0
for i,(rid,(nm,ty,rg)) in enumerate(sorted(tgt.items()),1):
    p=f'{OUT}/{rid}.json'
    if os.path.exists(p) and os.path.getsize(p)>200: skip+=1; continue
    url=f'{base}?serviceKey={urllib.parse.quote(KEY,safe="")}&routeId={rid}&format=json'
    try:
        with urllib.request.urlopen(url,timeout=20) as r: raw=r.read()
        json.loads(raw.decode('utf-8'))
        open(p,'wb').write(raw); ok+=1
    except Exception as e:
        fail+=1; print(f'  실패 {rid} {nm}: {str(e)[:60]}')
    time.sleep(0.12)
    if i%20==0: print(f'  {i}/{len(tgt)} ...',flush=True)
print(f'\n신규 {ok} / 캐시 {skip} / 실패 {fail}')
# 구조 확인
fs=glob.glob(f'{OUT}/*.json')
if fs:
    d=json.load(open(fs[0],encoding='utf-8'))
    body=d.get('response',{}).get('msgBody',{})
    lst=body.get('busRouteStationList',[])
    if isinstance(lst,dict): lst=[lst]
    print(f'\n예시 {os.path.basename(fs[0])} — 정류소 {len(lst)}개')
    if lst: print('  필드:',list(lst[0].keys()))
    for s in lst[:3]: print('  ',{k:s[k] for k in list(s)[:7]})
