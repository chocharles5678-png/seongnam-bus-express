"""동료 공유용 2차 패키지 — 10/7 관측 원본·산출표, 55번 급행 정차표, 시뮬레이션 코드·결과"""
import csv, io, sys, os, json, glob, shutil, itertools, collections, subprocess
from datetime import datetime
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = '공유_자료패키지_2차'
for d in ('01_관측원본', '02_산출표', '03_급행정차표', '04_시뮬레이션'):
    os.makedirs(f'{P}/{d}', exist_ok=True)

SRC = 'data/raw/bus_location/20261007.jsonl'
R = [json.loads(l) for l in open(SRC, encoding='utf-8')]
NSTOP = {'88-1': 71, '55': 127, '380': 106}

# ── 01. 원본 + 수집 조건
shutil.copy(SRC, f'{P}/01_관측원본/원시관측_20261007.jsonl')
sess = [('2026-10-07 07:04~09:03', '88-1, 55, 380', 30, '아침 시간대'),
        ('2026-10-07 09:08~12:52', '55 단독', 45, '왕복 완주 확보')]
with open(f'{P}/01_관측원본/수집조건.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['수집구간', '대상노선', '폴링간격_초', '목적', '비고'])
    for a, b, c, d in sess:
        w.writerow([a, b, c, d, 'API: 경기도_버스위치정보 조회 getBusLocationListv2 / 개발계정 하루 1,000회'])
print(f'01 원시 {len(R):,}건 + 수집조건')

# ── 02. 산출표
# (a) 차량별 추적
tr = []
for rt in ('88-1', '55', '380'):
    g = [r for r in R if r['route'] == rt]
    for p, v in itertools.groupby(sorted(g, key=lambda x: (x['plateNo'], x['ts'])), key=lambda x: x['plateNo']):
        v = list(v)
        for i, x in enumerate(v):
            prev = v[i-1]['stationSeq'] if i else ''
            tr.append(dict(노선=rt, 차량=p, 시각=x['ts'], 정류소순번=x['stationSeq'],
                           정류소ID=x['stationId'], 이전순번=prev,
                           되감김=('O' if i and x['stationSeq'] < v[i-1]['stationSeq'] - 5 else '')))
with open(f'{P}/02_산출표/차량별_추적표.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(tr[0].keys())); w.writeheader(); w.writerows(tr)
print(f'02 차량별 추적 {len(tr):,}행')

# (b) 왕복 소요시간 산출
rows = []
for rt in ('88-1', '55', '380'):
    N = NSTOP[rt]
    g = [r for r in R if r['route'] == rt]
    if rt == '55': g = [r for r in g if r['ts'] >= '2026-10-07T09:08']   # 단독 수집 구간
    for p, v in itertools.groupby(sorted(g, key=lambda x: (x['plateNo'], x['ts'])), key=lambda x: x['plateNo']):
        s = [(datetime.fromisoformat(x['ts']), x['stationSeq']) for x in v]
        runs = []; cur = [s[0]]
        for i in range(1, len(s)):
            if s[i][1] >= s[i-1][1] - 2: cur.append(s[i])
            else: runs.append(cur); cur = [s[i]]
        runs.append(cur)
        b = max(runs, key=lambda r: r[-1][1] - r[0][1])
        lo, hi = b[0][1], b[-1][1]
        if hi <= lo: continue
        span = (b[-1][0] - b[0][0]).total_seconds() / 60
        rows.append(dict(노선=rt, 차량=p, 시작순번=lo, 끝순번=hi, 관측구간수=hi-lo,
                         진행률=f'{(hi-lo)/(N-1)*100:.0f}%', 시작시각=b[0][0].strftime('%H:%M:%S'),
                         끝시각=b[-1][0].strftime('%H:%M:%S'), 관측소요_분=round(span, 1),
                         전구간환산_분=round(span*(N-1)/(hi-lo), 1), 전체구간수=N-1,
                         산출식='관측소요 × (전체구간수) ÷ 관측구간수'))
rows.sort(key=lambda x: (x['노선'], -x['관측구간수']))
with open(f'{P}/02_산출표/왕복소요시간_산출표.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for rt in ('88-1', '55', '380'):
    v = [x['전구간환산_분'] for x in rows if x['노선'] == rt and x['관측구간수'] >= NSTOP[rt]*0.6]
    if v: print(f'02 왕복 {rt}: 중앙 {np.median(v):.0f}분 (n={len(v)}, 진행률 60% 이상)')

# (c) 회차점 통과 간격
wr = []
for rt in ('88-1', '55', '380'):
    g = [r for r in R if r['route'] == rt]
    if rt == '55': g = [r for r in g if r['ts'] >= '2026-10-07T09:08']
    ws = []
    for p, v in itertools.groupby(sorted(g, key=lambda x: (x['plateNo'], x['ts'])), key=lambda x: x['plateNo']):
        s = [(datetime.fromisoformat(x['ts']), x['stationSeq'], x['plateNo']) for x in v]
        for i in range(1, len(s)):
            if s[i][1] < s[i-1][1] - 5: ws.append((s[i][0], p, s[i-1][1], s[i][1]))
    ws.sort()
    for i, (t, p, a, b) in enumerate(ws):
        wr.append(dict(노선=rt, 순서=i+1, 통과시각=t.strftime('%H:%M:%S'), 차량=p,
                       순번=f'{a}→{b}',
                       직전과의간격_분=('' if i == 0 else round((t - ws[i-1][0]).total_seconds()/60, 1))))
with open(f'{P}/02_산출표/회차점통과_간격표.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(wr[0].keys())); w.writeheader(); w.writerows(wr)
print(f'02 회차점 통과 {len(wr)}행')

# (d) 10분 단위 운행 대수
bk = []
for rt in ('88-1', '55', '380'):
    g = [r for r in R if r['route'] == rt]
    d = collections.defaultdict(set)
    for r in g: d[r['ts'][11:16][:4] + '0'].add(r['plateNo'])
    for k in sorted(d):
        bk.append(dict(노선=rt, 구간=f'{k}~', 고유차량수=len(d[k]),
                       차량목록=' '.join(sorted(d[k]))))
with open(f'{P}/02_산출표/10분단위_운행대수.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(bk[0].keys())); w.writeheader(); w.writerows(bk)
for rt in ('88-1', '55', '380'):
    v = [x['고유차량수'] for x in bk if x['노선'] == rt]
    print(f'02 10분단위 대수 {rt}: 중앙 {int(np.median(v))}대 (범위 {min(v)}~{max(v)})')

# ── 03. 55번 급행 정차표 (방향·순번 포함)
rt2 = {r['노선ID']: r for r in csv.DictReader(open('express_bus/clean/노선.csv', encoding='utf-8-sig'))}
rs = collections.defaultdict(list)
for r in csv.DictReader(open('express_bus/clean/노선정류장.csv', encoding='utf-8-sig')): rs[r['노선ID']].append(r)
rid = [k for k, v in rt2.items() if v['노선명'] == '55' and v['노선유형'] == '일반형시내버스'][0]
m = rt2[rid]
st = sorted(rs[rid], key=lambda s: int(s['순서']))
turn = max([int(s['순서']) for s in st if s['정류장명'] == m['회차점']], default=len(st)//2)
stopxy = {r['정류장ID']: r for r in csv.DictReader(open('express_bus/clean/정류장.csv', encoding='utf-8-sig'))}
exp = {r['정류소명']: r for r in csv.DictReader(open('data/express_55.csv', encoding='utf-8-sig'))}
out = []
for s in st:
    r = exp.get(s['정류장명'], {})
    xy = stopxy.get(s['정류장ID'], {})
    out.append(dict(노선='55', 순번=int(s['순서']), 방향=('상행' if int(s['순서']) <= turn else '하행'),
                    정류소ID=s['정류장ID'], 정류소명=s['정류장명'],
                    경도=xy.get('경도', ''), 위도=xy.get('위도', ''),
                    행정동=r.get('행정동', ''), 동20대인구=r.get('동20대인구', ''),
                    지점왕복일평균=r.get('왕복일평균', ''), 마을버스수=r.get('마을버스수', ''),
                    급행정차=r.get('급행정차', ''), 선정사유=r.get('사유', '')))
with open(f'{P}/03_급행정차표/급행정차표_55.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
ns = sum(1 for x in out if x['급행정차'] == '정차')
print(f'03 55번 정차표 {len(out)}행 (회차점 순번 {turn}) — 정차 {ns} / 통과 {len(out)-ns}')

# ── 04. 시뮬레이션 코드 + 결과
shutil.copy('scripts/seongnam/x_sim.py', f'{P}/04_시뮬레이션/x_sim.py')
sim = []
for T in (15, 20, 25, 30):
    r = subprocess.run([sys.executable, 'scripts/seongnam/x_sim.py', '55',
                        '--fleet', '18', '--cycle', '195', '--T', str(T)],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    open(f'{P}/04_시뮬레이션/시뮬레이션출력_T{T}초.txt', 'w', encoding='utf-8').write(r.stdout)
    for line in r.stdout.splitlines():
        p = line.split()
        if len(p) >= 7 and p[0].isdigit() and p[1].isdigit():
            sim.append(dict(T초=T, 급행대수=int(p[0]), 완행대수=int(p[1]),
                            급행간격_분=p[2].replace('분', ''), 완행간격_분=p[3].replace('분', ''),
                            정차지점대기_분=p[4].replace('분', ''), 통과지점대기_분=p[5].replace('분', ''),
                            급행차내단축_분=p[6].replace('분', '')))
with open(f'{P}/04_시뮬레이션/시뮬레이션결과_T별.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(sim[0].keys())); w.writeheader(); w.writerows(sim)
print(f'04 시뮬레이션 {len(sim)}행 (T 4개 × 급행대수 17개) + 출력 4개')
