"""버스 실시간 위치 수집 — 정류소 간 실제 통행시간을 재기 위한 원자료
사용: python scripts/seongnam/x_collect_location.py [노선...] [--interval 30] [--minutes 120] [--budget 900]
※ 공공데이터포털 '경기도_버스위치정보 조회'(data/15080648) 활용신청 필요. 개발계정 하루 1,000회 제한.
출력: data/raw/bus_location/YYYYMMDD.jsonl  (한 줄 = 한 관측)
"""
import io,sys,os,json,time,glob,argparse,urllib.parse,urllib.request
from datetime import datetime
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
ap=argparse.ArgumentParser()
ap.add_argument('routes',nargs='*',default=['88-1','32'])
ap.add_argument('--interval',type=int,default=30,help='폴링 간격(초)')
ap.add_argument('--minutes',type=int,default=120,help='수집 시간(분)')
ap.add_argument('--budget',type=int,default=900,help='이번 실행의 최대 호출 수 (일 1,000회 제한 대비)')
a=ap.parse_args()
KEY=[l.split('=',1)[1].strip() for l in open('.env',encoding='utf-8') if l.startswith('DATA_GO_KR_KEY=')][0]
rid={}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    b=json.load(open(f,encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    if isinstance(b,list): b=b[0]
    if b.get('routeTypeName') in ('마을버스','일반형시내버스') and '성남' in str(b.get('regionName')):
        rid[str(b.get('routeName'))]=str(b['routeId'])
tgt=[(n,rid[n]) for n in a.routes if n in rid]
miss=[n for n in a.routes if n not in rid]
if miss: print(f'노선ID 못 찾음: {miss}')
if not tgt: sys.exit('수집할 노선이 없다')
os.makedirs('data/raw/bus_location',exist_ok=True)
out=f'data/raw/bus_location/{datetime.now():%Y%m%d}.jsonl'
base='https://apis.data.go.kr/6410000/buslocationservice/v2/getBusLocationListv2'
need=(a.minutes*60//a.interval)*len(tgt)
print(f'노선 {[n for n,_ in tgt]} / {a.interval}초 간격 / {a.minutes}분 → 예상 호출 {need}회 (예산 {a.budget})')
if need>a.budget: print(f'⚠ 예산 초과. 간격을 {a.minutes*60*len(tgt)//a.budget}초 이상으로 늘리거나 시간을 줄일 것')
calls=obs=err=0; end=time.time()+a.minutes*60
with open(out,'a',encoding='utf-8') as fo:
    while time.time()<end and calls<a.budget:
        t0=time.time()
        for nm,r in tgt:
            url=f'{base}?serviceKey={urllib.parse.quote(KEY,safe="")}&routeId={r}&format=json'
            try:
                with urllib.request.urlopen(url,timeout=15) as rs: d=json.loads(rs.read().decode('utf-8'))
                calls+=1
                body=d.get('response',{}).get('msgBody') or {}
                lst=body.get('busLocationList') or []
                if isinstance(lst,dict): lst=[lst]
                ts=datetime.now().isoformat(timespec='seconds')
                for s in lst:
                    fo.write(json.dumps(dict(ts=ts,route=nm,routeId=r,
                        plateNo=s.get('plateNo'),stationId=str(s.get('stationId')),
                        stationSeq=s.get('stationSeq'),endBus=s.get('endBus'),
                        remainSeat=s.get('remainSeatCnt')),ensure_ascii=False)+'\n')
                    obs+=1
                fo.flush()
            except Exception as e:
                err+=1; calls+=1
                if err<=3: print(f'  오류 {nm}: {str(e)[:80]}')
                if err==1 and '403' in str(e): print('  → 활용신청이 안 된 것으로 보인다. data.go.kr/data/15080648 에서 신청할 것'); sys.exit(1)
        el=time.time()-t0
        if el<a.interval: time.sleep(a.interval-el)
        if calls%60<len(tgt): print(f'  {calls}회 호출 / 관측 {obs}건 / 오류 {err}  ({datetime.now():%H:%M:%S})',flush=True)
print(f'\n완료: 호출 {calls} / 관측 {obs} / 오류 {err}\n-> {out}')
