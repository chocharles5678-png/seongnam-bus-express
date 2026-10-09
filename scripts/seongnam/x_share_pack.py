"""동료 공유용 자료 패키지 생성 — 원본표·정제표·산출코드를 한 폴더로 묶는다. 인증키는 포함하지 않는다."""
import csv, io, sys, os, json, glob, math, shutil, itertools
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = '공유_자료패키지'
for d in ('01_급행정차표', '02_효과계산', '03_위치관측', '04_거점목록', '05_인구', '06_코드'):
    os.makedirs(f'{P}/{d}', exist_ok=True)

ride = {r['정류소ID']: r for r in csv.DictReader(open('data/seongnam_ride_202606.csv', encoding='utf-8-sig'))}
routes = {}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    b = json.load(open(f, encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    if isinstance(b, list): b = b[0]
    routes[(str(b.get('routeName')), b.get('routeTypeName'))] = str(b['routeId'])

def hav(a, b):
    R = 6371000; p = math.pi / 180
    h = math.sin((b[1]-a[1])*p/2)**2 + math.cos(a[1]*p)*math.cos(b[1]*p)*math.sin((b[0]-a[0])*p/2)**2
    return 2 * R * math.asin(math.sqrt(h))

# ── 01. 급행 정차표 — 정류소ID · 방향 · 순번 · 정차/통과 · 선정사유
for nm, src in (('88-1', 'data/express_88_1.csv'), ('32', 'data/express_32.csv')):
    rid = routes[(nm, '마을버스')]
    A = json.load(open(f'data/raw/gg_routestation/{rid}.json', encoding='utf-8'))['response']['msgBody']['busRouteStationList']
    turn = A[0].get('turnSeq')
    meta = {str(s['stationId']): s for s in A}
    out = []
    for r in csv.DictReader(open(src, encoding='utf-8-sig')):
        for sq, sid in zip(r['순서'].split(','), r['정류소ID'].split()):
            sq = int(sq); m = meta.get(sid, {})
            out.append(dict(노선=nm, 정류소ID=sid, 정류소명=r['정류소명'],
                            방향=('상행' if sq <= turn else '하행'), 순번=sq,
                            모바일번호=str(m.get('mobileNo', '')).strip(),
                            경도=m.get('x', ''), 위도=m.get('y', ''), 행정동=r['행정동'],
                            급행정차=r['급행정차'], 선정사유=r['사유'],
                            지점왕복일평균=r['왕복일평균'], 짝노선공유=r['짝노선공유'],
                            마을버스수=r['마을버스수']))
    out.sort(key=lambda x: x['순번'])
    p = f'{P}/01_급행정차표/급행정차표_{nm.replace("-", "_")}.csv'
    with open(p, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print(f'01 {nm}: {len(out)}행 (회차점 순번 {turn}) -> {p}')

# ── 02. 효과 계산표 — 분모·분자를 모두 노출
rows = []
for nm, src in (('88-1', 'data/express_88_1.csv'), ('32', 'data/express_32.csv')):
    R = list(csv.DictReader(open(src, encoding='utf-8-sig')))
    tot = sum(float(r['왕복일평균']) for r in R)
    nstop = lambda r: len(r['순서'].split(','))
    grp = (('급행정차지점',        [r for r in R if r['급행정차'] == '정차']),
           ('통과·짝노선이완행담당', [r for r in R if r['급행정차'] == '통과' and r['짝노선공유'] == 'o']),
           ('통과·완행배차증가',    [r for r in R if r['급행정차'] == '통과' and r['짝노선공유'] != 'o']))
    for lab, g in grp:
        s = sum(float(r['왕복일평균']) for r in g)
        rows.append(dict(노선=nm, 구분=lab, 지점수=len(g), 정차횟수=sum(nstop(r) for r in g),
                         지점왕복일평균합=round(s), 분모=round(tot), 비중백분율=round(s/tot*100, 1)))
    nA = sum(nstop(r) for r in R); nS = sum(nstop(r) for r in R if r['급행정차'] == '정차')
    rows.append(dict(노선=nm, 구분='[합계]', 지점수=len(R), 정차횟수=nA,
                     지점왕복일평균합=round(tot), 분모=round(tot), 비중백분율=100.0))
    # 이용량 가중 절감 몫 = 통과 지점의 정차비용 몫 ÷ 전체 (정차비용 ∝ 정차횟수 × log(1+지점당 이용))
    wgt = lambda r: nstop(r) * math.log1p(float(r['왕복일평균']) / max(nstop(r), 1))
    allw = sum(wgt(r) for r in R); skipw = sum(wgt(r) for r in R if r['급행정차'] == '통과')
    rows.append(dict(노선=nm, 구분='[이용량가중 절감몫]', 지점수='', 정차횟수=f'{nA}→{nS}',
                     지점왕복일평균합=round(skipw, 1), 분모=round(allw, 1),
                     비중백분율=round(skipw/allw*100, 1)))
p = f'{P}/02_효과계산/효과계산표.csv'
with open(p, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f'02 효과계산표 {len(rows)}행 -> {p}')

# ── 03. 위치 관측 — 원시 + 구간 산출 + 제외 사유
obs = [json.loads(l) for f in glob.glob('data/raw/bus_location/*.jsonl') for l in open(f, encoding='utf-8')]
for f in glob.glob('data/raw/bus_location/*.jsonl'):
    shutil.copy(f, f'{P}/03_위치관측/원시관측_{os.path.basename(f)}')
seg = []
for rt in ('88-1', '32'):
    A = json.load(open(f"data/raw/gg_routestation/{routes[(rt, '마을버스')]}.json", encoding='utf-8'))['response']['msgBody']['busRouteStationList']
    XY = {s['stationSeq']: (float(s['x']), float(s['y'])) for s in A}
    NM = {s['stationSeq']: s['stationName'] for s in A}
    g = [r for r in obs if r['route'] == rt]
    for pl, vg in itertools.groupby(sorted(g, key=lambda r: (r['plateNo'], r['ts'])), key=lambda r: r['plateNo']):
        runs = [(s, x[0]['ts'], x[-1]['ts']) for s, x in
                ((k, list(v)) for k, v in itertools.groupby(list(vg), key=lambda r: r['stationSeq']))]
        arr = {}
        for i in range(1, len(runs)):
            if runs[i][0] == runs[i-1][0] + 1:
                t0 = datetime.fromisoformat(runs[i-1][2]); t1 = datetime.fromisoformat(runs[i][1])
                arr[runs[i][0]] = t0 + (t1 - t0) / 2
            else:
                seg.append(dict(노선=rt, 차량=pl, 구간=f'{runs[i-1][0]}→{runs[i][0]}', 사용여부='제외',
                                제외사유='순번 불연속(관측 누락)', 소요초='', 거리m='', 도착추정시각=''))
        for s in sorted(arr):
            if s - 1 not in arr: continue
            dt = (arr[s] - arr[s-1]).total_seconds(); d = hav(XY[s-1], XY[s])
            ok = 5 < dt < 600
            seg.append(dict(노선=rt, 차량=pl, 구간=f'{s-1}→{s} ({NM[s-1][:10]}→{NM[s][:10]})',
                            사용여부=('사용' if ok else '제외'),
                            제외사유=('' if ok else '소요시간 범위 밖(5~600초)'),
                            소요초=round(dt), 거리m=round(d),
                            도착추정시각=arr[s].isoformat(timespec='seconds')))
p = f'{P}/03_위치관측/구간소요_산출표.csv'
with open(p, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(seg[0].keys())); w.writeheader(); w.writerows(seg)
used = [s for s in seg if s['사용여부'] == '사용']
print(f'03 구간 {len(seg)}행 (사용 {len(used)} / 제외 {len(seg)-len(used)}) -> {p}')

# ── 04. 거점 목록
hub = [r for r in ride.values() if int(r['마을버스수'] or 0) >= 4]
cols = ['정류소ID', '정류소명', '구', '행정동', '마을버스수', '마을버스', '일평균', '위도', '경도']
p = f'{P}/04_거점목록/마을버스거점_4개이상.csv'
with open(p, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in sorted(hub, key=lambda x: -int(x['마을버스수'])): w.writerow({k: r[k] for k in cols})
print(f'04 마을버스 거점 {len(hub)}곳 -> {p}')

rt2 = {r['노선ID']: r for r in csv.DictReader(open('express_bus/clean/노선.csv', encoding='utf-8-sig'))}
rid380 = [k for k, v in rt2.items() if v['노선명'] == '380' and v['노선유형'] == '일반형시내버스'][0]
st380 = [s for s in csv.DictReader(open('express_bus/clean/노선정류장.csv', encoding='utf-8-sig')) if s['노선ID'] == rid380]
H = {r['정류소ID'] for r in hub}
seen = {}
for s in st380:
    if s['정류장ID'] in H and s['정류장ID'] not in seen: seen[s['정류장ID']] = s
p = f'{P}/04_거점목록/380번_통과거점.csv'
with open(p, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['정류소ID', '정류소명', '380순번', '구', '행정동', '마을버스수', '일평균'])
    for i, s in sorted(seen.items(), key=lambda x: -float(ride[x[0]]['일평균'])):
        r = ride[i]; w.writerow([i, r['정류소명'], s['순서'], r['구'], r['행정동'], r['마을버스수'], r['일평균']])
print(f'04 380번 통과 거점 {len(seen)}곳 -> {p}')

# ── 05·06. 인구 원본 / 코드
shutil.copy('data/raw/pop_dong_202608.csv', f'{P}/05_인구/주민등록_연령별인구_202608.csv')
shutil.copy('성남_20대_거주분포.md', f'{P}/05_인구/성남_20대_거주분포.md')
src = 'express_bus/raw/seongnam_social_survey_2025.xlsx'
if os.path.exists(src): shutil.copy(src, f'{P}/05_인구/성남시_사회조사_2025.xlsx'); print('05 사회조사 원문 포함')
for s in ('x_hub.py', 'x_agg.py', 'x_cross.py', 'x_express.py', 'x_express_fig.py',
          'x_dwell.py', 'x_collect_location.py', 'x_similar_routes.py', 'x_fetch_stations.py',
          'x_carbon.py', 'x_share_pack.py',
          '4_contour_dem.py', '5_stop_slope.py', 'tm.py'):   # 경사 계산 코드 + 좌표변환 의존성
    shutil.copy(f'scripts/seongnam/{s}', f'{P}/06_코드/{s}')
print('06 코드 14개 복사 (경사 계산 코드 포함)')

# ── 07. 성남 마을버스 73개 노선 목록
vil = []
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    b = json.load(open(f, encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    if isinstance(b, list): b = b[0]
    if b.get('routeTypeName') != '마을버스' or '성남' not in str(b.get('regionName')): continue
    rid = str(b['routeId'])
    n = 0
    p2 = f'data/raw/gg_routestation/{rid}.json'
    if os.path.exists(p2):
        A = json.load(open(p2, encoding='utf-8'))['response']['msgBody'].get('busRouteStationList', [])
        n = len(A if isinstance(A, list) else [A])
    vil.append(dict(노선ID=rid, 노선명=b.get('routeName'), 운수사=b.get('companyName'),
                    지역=b.get('regionName'), 기점=b.get('startStationName'), 종점=b.get('endStationName'),
                    평일최소배차=b.get('peekAlloc'), 평일최대배차=b.get('nPeekAlloc'),
                    평일첫차=b.get('downFirstTime'), 평일막차=b.get('downLastTime'), 정차수=n))
os.makedirs(f'{P}/07_노선목록', exist_ok=True)
vil.sort(key=lambda x: str(x['노선명']))
p = f'{P}/07_노선목록/성남_마을버스_73개노선.csv'
with open(p, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(vil[0].keys())); w.writeheader(); w.writerows(vil)
dupn = [k for k, v in __import__('collections').Counter(str(x['노선명']) for x in vil).items() if v > 1]
print(f'07 마을버스 {len(vil)}개 노선 (성남 내 이름 중복: {dupn}) -> {p}')

# ── 08. 이름 기준 집계가 틀리는 정류소 (동명 다ID)
cross = list(csv.DictReader(open('data/seongnam_hub_cross.csv', encoding='utf-8-sig')))
byname = {}
for r in cross: byname.setdefault(r['정류소명'], []).append(r)
rows2 = []
for nm2, g in byname.items():
    if len(g) < 2: continue
    vals = {int(x['마을버스수'] or 0) for x in g}
    for x in g:
        rows2.append(dict(정류소명=nm2, 정류소ID=x['정류소ID'], 정류소번호=x['정류소번호'],
                          구=x['구'], 행정동=x['행정동'],
                          마을버스수_ID기준=x['마을버스수'], 일평균=x['일평균'],
                          동명ID수=len(g), 값이갈림=('O' if len(vals) > 1 else '')))
diffn = len({r['정류소명'] for r in rows2 if r['값이갈림'] == 'O'})
p = f'{P}/07_노선목록/동명정류소_ID별차이.csv'
with open(p, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows2[0].keys())); w.writeheader(); w.writerows(rows2)
print(f'08 동명 그룹 {len(byname)}개 중 다ID {len([g for g in byname.values() if len(g)>1])}개 / '
      f'값이 갈리는 그룹 {diffn}개 ({len(rows2)}행) -> {p}')

# ── 09. 성남 내부 전용 급행 계열 (S1·S2·반디) 정류소·시각표
raw = {}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    b = json.load(open(f, encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    if isinstance(b, list): b = b[0]
    raw[str(b.get('routeName'))] = b
rt2 = {r['노선ID']: r for r in csv.DictReader(open('express_bus/clean/노선.csv', encoding='utf-8-sig'))}
rsall = list(csv.DictReader(open('express_bus/clean/노선정류장.csv', encoding='utf-8-sig')))
os.makedirs(f'{P}/08_성남내부급행', exist_ok=True)
tt, stops_out = [], []
for nm2 in ('S1', 'S2', '반디1', '반디1-1', '반디2'):
    ids = [k for k, v in rt2.items() if v['노선명'] == nm2]
    if not ids: continue
    m = rt2[ids[0]]; b = raw.get(nm2, {})
    tt.append(dict(노선명=nm2, 노선ID=ids[0], 노선유형=m['노선유형'], 운수사=m['운수사'],
                   기점=m['기점'], 종점=m['종점'],
                   평일상행=f"{b.get('upFirstTime')}~{b.get('upLastTime')}",
                   평일하행=f"{b.get('downFirstTime')}~{b.get('downLastTime')}",
                   토상행=f"{b.get('satUpFirstTime')}~{b.get('satUpLastTime')}",
                   일상행=f"{b.get('sunUpFirstTime')}~{b.get('sunUpLastTime')}",
                   평일최소배차=b.get('peekAlloc'), 평일최대배차=b.get('nPeekAlloc'), 심야배차=b.get('nightAlloc'),
                   정차수=len([s for s in rsall if s['노선ID'] == ids[0]])))
    for s in [s for s in rsall if s['노선ID'] == ids[0]]:
        r = ride.get(s['정류장ID'], {})
        stops_out.append(dict(노선명=nm2, 순번=s['순서'], 정류소ID=s['정류장ID'], 정류소명=s['정류장명'],
                              구=r.get('구', ''), 행정동=r.get('행정동', ''),
                              일평균=r.get('일평균', ''), 마을버스수=r.get('마을버스수', '')))
for fn, rr in (('성남내부급행_운행시각.csv', tt), ('성남내부급행_정류소목록.csv', stops_out)):
    p = f'{P}/08_성남내부급행/{fn}'
    with open(p, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rr[0].keys())); w.writeheader(); w.writerows(rr)
print(f'09 성남 내부 전용 급행 {len(tt)}개 노선 / 정류소 {len(stops_out)}행 -> {P}/08_성남내부급행/')

# ── 10. 정차 횟수 집계표 + 거점묶음(지점명 → 정류소ID) 규칙
agg, grp = [], []
for nm2, src in (('88-1', 'data/express_88_1.csv'), ('32', 'data/express_32.csv')):
    R = list(csv.DictReader(open(src, encoding='utf-8-sig')))
    ns = lambda r: len(r['순서'].split(','))
    tot_n = sum(ns(r) for r in R); stop_n = sum(ns(r) for r in R if r['급행정차'] == '정차')
    agg.append(dict(노선=nm2, 전체지점=len(R), 전체정차횟수=tot_n,
                    급행정차지점=len([r for r in R if r['급행정차'] == '정차']),
                    급행정차횟수=stop_n, 통과횟수=tot_n - stop_n,
                    기종점=len([r for r in R if r['사유'] == '기종점']),
                    거점=len([r for r in R if r['사유'] == '거점']),
                    이차기준=len([r for r in R if r['사유'] not in ('기종점', '거점', '')])))
    for r in R:
        grp.append(dict(노선=nm2, 지점명=r['정류소명'], 묶인정류소ID=r['정류소ID'],
                        묶인순번=r['순서'], ID수=len(r['정류소ID'].split()),
                        지점왕복일평균=r['왕복일평균'], 급행정차=r['급행정차']))
for fn, rr in (('정차횟수_집계표.csv', agg), ('거점묶음_지점명대ID.csv', grp)):
    p = f'{P}/02_효과계산/{fn}'
    with open(p, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rr[0].keys())); w.writeheader(); w.writerows(rr)
print(f'10 정차횟수 집계 {len(agg)}행 / 거점묶음 {len(grp)}행 -> {P}/02_효과계산/')
