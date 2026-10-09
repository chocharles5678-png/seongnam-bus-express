"""시내버스 급행 재편 설계 (연계형) — 마을버스가 피더, 시내버스 일부 차량을 급행화
사용: python scripts/seongnam/x_express_trunk.py 51 [--hub 3000] [--p20 2500] [--p20u 1500]
정차 규칙 = 기·종점 ∪ 거점(지점 왕복 일평균 ≥ hub) ∪ 20대거점(동 20대 ≥ p20 & 지점 ≥ p20u) ∪ 마을버스 환승거점(≥5개)
데이터: express_bus/clean/{노선,노선정류장,정류장}.csv + data/seongnam_ride_202606.csv + 주민등록 연령별인구
"""
import csv, io, sys, re, math, argparse, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument('route', nargs='?', default='51')
ap.add_argument('--hub', type=float, default=3000)
ap.add_argument('--p20', type=int, default=2500)
ap.add_argument('--p20u', type=float, default=1500)
ap.add_argument('--mb', type=int, default=5)
ap.add_argument('--univ', type=float, default=1000, help='대학 정류소는 이 이용량 이상이면 정차')
a = ap.parse_args()
UNIV_KEY = ('대학', '가천대', '을지대', '신구대')   # 정류소명에 포함되면 대학 접근 정류소로 본다

# 동별 20대 인구
rows = list(csv.reader(open('data/raw/pop_dong_202608.csv', encoding='cp949')))
h = rows[0]; tot_i = h.index('계')
C20 = [i for i, c in enumerate(h) if (m := re.match(r'(\d+)세', c)) and 20 <= int(m.group(1)) <= 29]
num = lambda x: int(str(x).replace(',', '') or 0) if str(x).replace(',', '').lstrip('-').isdigit() else 0
pop = {r[4]: (sum(num(r[i]) for i in C20), num(r[tot_i]))
       for r in rows[1:] if len(r) > 5 and '성남시' in r[3] and r[4] and r[4] not in ('소계', '합계')}

ride = {r['정류소ID']: r for r in csv.DictReader(open('data/seongnam_ride_202606.csv', encoding='utf-8-sig'))}
stopxy = {r['정류장ID']: r for r in csv.DictReader(open('express_bus/clean/정류장.csv', encoding='utf-8-sig'))}
rt = {r['노선ID']: r for r in csv.DictReader(open('express_bus/clean/노선.csv', encoding='utf-8-sig'))}
rs = collections.defaultdict(list)
for r in csv.DictReader(open('express_bus/clean/노선정류장.csv', encoding='utf-8-sig')):
    rs[r['노선ID']].append(r)

ids = [k for k, v in rt.items() if v['노선명'] == a.route and v['노선유형'] == '일반형시내버스']
if not ids: sys.exit(f'{a.route}번 일반형시내버스를 찾지 못했다')
rid = ids[0]; m = rt[rid]
st = sorted(rs[rid], key=lambda s: int(s['순서']))

# 지점(정류장명) 단위 집계 — 왕복 양방향 합산
pt = collections.OrderedDict()
for s in st:
    i = s['정류장ID']; r = ride.get(i)
    p = pt.setdefault(s['정류장명'], dict(name=s['정류장명'], seqs=[], ids=[], u=0.0, mb=0, dong=''))
    p['seqs'].append(int(s['순서'])); p['ids'].append(i)
    if r:
        p['u'] += float(r['일평균']); p['mb'] = max(p['mb'], int(r['마을버스수'] or 0)); p['dong'] = r['행정동']
P = list(pt.values())
T = sum(p['u'] for p in P)
term = {st[0]['정류장명'], st[-1]['정류장명'], m['회차점']}

for p in P:
    p20 = pop.get(p['dong'], (0, 0))[0]
    p['p20'] = p20
    p['univ'] = any(k in p['name'] for k in UNIV_KEY)
    if p['name'] in term:              p['why'] = '기종점'
    elif p['u'] >= a.hub:              p['why'] = '거점'
    elif p['univ'] and p['u'] >= a.univ: p['why'] = '대학'
    elif p['mb'] >= a.mb:              p['why'] = '환승거점'
    elif p20 >= a.p20 and p['u'] >= a.p20u: p['why'] = '20대거점'
    else:                              p['why'] = ''

sel = [p for p in P if p['why']]
nA = len(st); nS = sum(len(p['seqs']) for p in sel)
cov = sum(p['u'] for p in sel) / T * 100
print(f"■ {a.route}번 급행 설계 (연계형)  {m['기점']} → {m['종점']}")
print(f"  평일 배차 최소 {m['첨두배차_분']}분 / 최대 {m['비첨두배차_분']}분  (GBIS 명세: peekAlloc=최소, nPeekAlloc=최대)")
print(f"  평일 운행 {m['평일_첫차']}~{m['평일_막차']}")
print(f"  지점 {len(P)}곳 / 정차 {nA}회  →  급행 정차 {len(sel)}지점 {nS}회 / 통과 {nA-nS}회")
print(f"  급행이 담는 기록 {sum(p['u'] for p in sel):,.0f} / {T:,.0f} = {cov:.1f}%")
print(f"  규칙: 거점≥{a.hub:,.0f} · 대학 정류소≥{a.univ:,.0f} · 환승거점 마을버스≥{a.mb}개 "
      f"· 20대거점(동 20대≥{a.p20:,} & 지점≥{a.p20u:,.0f})\n")
print(f"{'순서':<12}{'정류소명':<28}{'왕복일평균':>9}{'마을':>5}{'행정동':<9}{'동20대':>7}  사유")
for p in P:
    if not p['why']: continue
    print(f"{','.join(map(str, p['seqs'][:3])):<12}{p['name'][:26]:<28}{p['u']:>9,.0f}{p['mb']:>4}개"
          f"{p['dong']:<9}{p['p20']:>7,}  {p['why']}")
print(f"\n■ 통과 지점 상위 6 (완행이 계속 담당)")
for p in sorted([x for x in P if not x['why']], key=lambda x: -x['u'])[:6]:
    print(f"  {p['name'][:28]:<30}{p['u']:>8,.0f}  {p['dong']} (20대 {p['p20']:,})")
print(f"\n■ 20대 상위 동 포함 여부")
top = sorted(pop.items(), key=lambda x: -x[1][0])[:12]
for dn, (c20, tt) in top:
    on = [p for p in P if p['dong'] == dn]
    if not on: continue
    s_ = [p for p in on if p['why']]
    print(f"  {dn:<9}20대 {c20:>6,}  51번 지점 {len(on):>2}곳 중 급행 정차 {len(s_):>2}곳"
          f"  {'· ' + ', '.join(p['name'][:12] for p in s_[:3]) if s_ else '— 정차 없음'}")

# 배차 설계
try: al = int(m['첨두배차_분'])   # 원본 컬럼명 유지. 의미는 '평일 최소 배차'
except Exception: al = 0
if al:
    print('\n' + '─' * 66)
    print('■ 배차 설계 — 운행 대수가 공개되지 않아 비율로 설계한다')
    for k in (2, 3):
        print(f"  [{k}회 중 1회 급행]  급행 {al*k}분 간격 / 완행 {al*k/(k-1):.0f}분 간격"
              f"  (급행 정차 지점은 약 {1/(1/(al*k)+1/(al*k/(k-1))):.0f}분 간격 유지)")

out = f'data/express_{a.route}.csv'
with open(out, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['순서', '정류소명', '정류소ID', '행정동', '동20대인구', '왕복일평균', '마을버스수', '급행정차', '사유', '경도', '위도'])
    for p in P:
        xy = stopxy.get(p['ids'][0], {})
        w.writerow([','.join(map(str, p['seqs'])), p['name'], ' '.join(p['ids']), p['dong'], p['p20'],
                    round(p['u']), p['mb'], '정차' if p['why'] else '통과', p['why'],
                    xy.get('경도', ''), xy.get('위도', '')])
print(f'\n-> {out}')
