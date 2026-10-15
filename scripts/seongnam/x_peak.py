# -*- coding: utf-8 -*-
"""첨두/비첨두 분리 재계산 — 관측 원본에서 운행 대수·왕복시간·배차를 시간대별로 나눠 센다.
사용: python scripts/seongnam/x_peak.py [날짜 YYYYMMDD] [--route 55] [--peak-end 9]

왜 필요한가: 관측창 전체의 중앙값은 첨두와 비첨두를 섞는다. 왕복이 200분 내외인 노선은
첨두창(2시간) 안에서 완주 차량이 구조적으로 나올 수 없으므로, 첨두 왕복은 통과 속도
환산으로만 구한다. 완주 실측값과 환산값을 반드시 분리해 출력한다.
"""
import json, io, sys, os, glob, argparse, collections, statistics as st
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument('date', nargs='?', default=None, help='YYYYMMDD. 생략하면 가장 최근 수집일')
ap.add_argument('--route', default='55')
ap.add_argument('--peak-end', type=float, default=9, help='첨두 종료 시각(시). 기본 09시')
ap.add_argument('--min-prog', type=float, default=0.3, help='환산에 쓸 최소 진행률')
ap.add_argument('--start', default=None, help='HH:MM 이전 관측을 버린다. 수집 시작 시각이 다른 날끼리 비교할 때 쓴다')
ap.add_argument('--end', default=None, help='HH:MM 이후 관측을 버린다')
a = ap.parse_args()

def hhmm(s):
    h, m = s.split(':')
    return int(h) * 60 + int(m)

T_LO = hhmm(a.start) if a.start else None
T_HI = hhmm(a.end) if a.end else None

D = 'data/raw/bus_location'
cand = sorted(glob.glob(os.path.join(D, '2*.jsonl')))
P = os.path.join(D, a.date + '.jsonl') if a.date else (cand[-1] if cand else '')
if not P or not os.path.exists(P):
    have = [os.path.basename(f)[:8] for f in cand]
    sys.exit('수집 자료 없음: %s   보유 날짜: %s' % (P, ', '.join(have) or '(없음)'))

PEAK_END = a.peak_end * 60
rows, seqs = [], []
for line in open(P, encoding='utf-8'):
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except Exception:
        continue
    if str(d['route']) != a.route:
        continue
    t = datetime.fromisoformat(d['ts'])
    m = t.hour * 60 + t.minute + t.second / 60
    if T_LO is not None and m < T_LO:
        continue
    if T_HI is not None and m > T_HI:
        continue
    seqs.append(int(d['stationSeq']))
    rows.append((m, d['plateNo'], int(d['stationSeq'])))

if not rows:
    inside = sorted({str(json.loads(l)['route']) for l in open(P, encoding='utf-8') if l.strip()})
    sys.exit('노선 %s 레코드 없음. 이 파일의 노선: %s' % (a.route, ', '.join(inside)))

SEQ_MAX = max(seqs)
rows.sort()
hm = lambda m: '%02d:%02d' % (m // 60, m % 60)
print('자료 %s · 노선 %s' % (P, a.route))
print('레코드 %d개 · 관측 %s~%s · 고유 차량 %d대 · 최대 순번 %d (왕복 1주 = %d구간)'
      % (len(rows), hm(rows[0][0]), hm(rows[-1][0]), len({r[1] for r in rows}), SEQ_MAX, SEQ_MAX - 1))
print('첨두창 %s~%s (%.0f분)  |  비첨두창 %s~%s (%.0f분)'
      % (hm(rows[0][0]), hm(PEAK_END), max(0, PEAK_END - rows[0][0]),
         hm(PEAK_END), hm(rows[-1][0]), max(0, rows[-1][0] - PEAK_END)))

# ── 1. 운행 대수: 10분 단위 고유 차량 수 ────────────────────────────────
bins = collections.defaultdict(set)
for m, plate, _ in rows:
    bins[int(m // 10) * 10].add(plate)
print('\n■ 1. 운행 대수 — 10분 단위 고유 차량 수')
ks = sorted(bins)
for i in range(0, len(ks), 12):
    chunk = ks[i:i + 12]
    print('   ' + ' '.join('%5s' % hm(b) for b in chunk))
    print('   ' + ' '.join('%5d' % len(bins[b]) for b in chunk))

peak_bins = [len(bins[b]) for b in ks if b < PEAK_END]
off_bins = [len(bins[b]) for b in ks if b >= PEAK_END]
all_bins = [len(bins[b]) for b in ks]
for nm, g in (('첨두', peak_bins), ('비첨두', off_bins), ('전체', all_bins)):
    if g:
        print('\n   %-4s 중앙값 %.1f대  (범위 %d~%d, 10분구간 %d개)'
              % (nm, st.median(g), min(g), max(g), len(g)))

# ── 2. 왕복 소요시간: 차량별 순번 단조증가 구간 ─────────────────────────
byplate = collections.defaultdict(list)
for m, plate, seq in rows:
    byplate[plate].append((m, seq))

runs = []
for plate, pts in byplate.items():
    pts.sort()
    cur = [pts[0]]
    for m, seq in pts[1:]:
        if seq < cur[-1][1]:           # 순번 하락 = 왕복 1주 종료
            if len(cur) > 1:
                runs.append((plate, cur))
            cur = [(m, seq)]
        else:
            cur.append((m, seq))
    if len(cur) > 1:
        runs.append((plate, cur))

rec = []
for plate, pts in runs:
    t0, s0 = pts[0]
    t1, s1 = pts[-1]
    segs, dur = s1 - s0, t1 - t0
    if segs < 1 or dur <= 0:
        continue
    rec.append(dict(plate=plate, s0=s0, s1=s1, segs=segs, dur=dur,
                    prog=segs / (SEQ_MAX - 1), rate=segs / dur,
                    mid=(t0 + t1) / 2, t0=t0, t1=t1))

print('\n■ 2. 왕복 소요시간 — 단조증가 구간 %d개 (완주만이 실측)' % len(rec))
full = sorted([r for r in rec if r['prog'] >= 0.95], key=lambda x: x['t0'])
if full:
    print('   완주(진행률 ≥95%%) %d대:' % len(full))
    for r in full:
        tag = '첨두출발' if r['t0'] < PEAK_END else '비첨두출발'
        print('     %s  순번 %3d→%3d (%3.0f%%)  %5.0f분  %s~%s  %s'
              % (r['plate'], r['s0'], r['s1'], r['prog'] * 100, r['dur'],
                 hm(r['t0']), hm(r['t1']), tag))
    fv = sorted(r['dur'] for r in full)
    print('     → 완주 실측 왕복 중앙값 %.0f분 (범위 %.0f~%.0f, n=%d)'
          % (st.median(fv), fv[0], fv[-1], len(fv)))
    for nm, sel in (('첨두 출발', [r for r in full if r['t0'] < PEAK_END]),
                    ('비첨두 출발', [r for r in full if r['t0'] >= PEAK_END])):
        if sel:
            v = sorted(r['dur'] for r in sel)
            print('       %s n=%d  중앙값 %.0f분 (범위 %.0f~%.0f)'
                  % (nm, len(v), st.median(v), v[0], v[-1]))
else:
    print('   완주 차량 없음 — 관측창이 왕복보다 짧다. 아래 환산값만 사용 가능.')

conv = sorted(r['dur'] * (SEQ_MAX - 1) / r['segs'] for r in rec if r['prog'] >= a.min_prog)
if conv:
    print('\n   진행률 %.0f%% 이상 %d개 구간의 전구간 환산: 중앙값 %.0f분 (범위 %.0f~%.0f)'
          % (a.min_prog * 100, len(conv), st.median(conv), conv[0], conv[-1]))

# ── 3. 첨두 vs 비첨두 통과 속도 ────────────────────────────────────────
# 연속 관측쌍 중 "양 끝 시각이 모두 같은 창 안"인 것만 쓴다.
# 구간(run) 단위로 중간시각으로 분류하면 안 된다 — run 길이가 150분대라
# 97분짜리 첨두창을 넘어가므로 첨두를 전혀 분리하지 못한다.
print('\n■ 3. 통과 속도(정류소/분) — 연속 관측쌍 기준, 창을 걸친 쌍은 제외')
buckets = {'첨두': [0.0, 0.0, 0], '비첨두': [0.0, 0.0, 0]}
for plate, pts in byplate.items():
    pts.sort()
    for (m0, s0), (m1, s1) in zip(pts, pts[1:]):
        if s1 < s0:
            continue                       # 왕복 경계
        dt, ds = m1 - m0, s1 - s0
        if dt <= 0 or dt > 3:
            continue                       # 폴링 끊김(정상 간격 30~45초)
        k = '첨두' if m1 < PEAK_END else ('비첨두' if m0 >= PEAK_END else None)
        if k is None:
            continue                       # 창 경계를 걸친 쌍
        b = buckets[k]
        b[0] += ds
        b[1] += dt
        b[2] += 1
cyc = {}
for nm, (ds, dt, n) in buckets.items():
    if dt <= 0:
        print('   %-4s 해당 관측쌍 없음' % nm)
        continue
    r = ds / dt
    cyc[nm] = (SEQ_MAX - 1) / r
    print('   %-4s 관측쌍 %5d개 · 누적 %.0f정류소 / %.0f분 · 속도 %.3f → 왕복 환산 %.0f분'
          % (nm, n, ds, dt, r, cyc[nm]))

# ── 4. 배차 = 왕복 ÷ 대수 ──────────────────────────────────────────────
print('\n■ 4. 배차(왕복 ÷ 대수)')
for nm, fleet in (('첨두', peak_bins), ('비첨두', off_bins)):
    if nm in cyc and fleet:
        f = st.median(fleet)
        print('   %-4s %.0f분 ÷ %.1f대 = %.1f분' % (nm, cyc[nm], f, cyc[nm] / f))

print("""
※ 두 지표는 서로 다른 것을 재므로 섞지 말 것.
   · §2 완주 왕복 = 차량이 실제로 왕복을 마친 시간. 직접 측정이지만 왕복(약 200분)이
     첨두창(약 100분)보다 길어 첨두·비첨두가 섞인 값이다. 차량 회전·배차 설계용.
   · §3 환산 왕복 = 그 창의 통과 속도가 왕복 전체에 유지된다면 걸릴 시간. 혼잡도 지표다.
   · §2의 완주 집합은 관측 종료 시각에 절단되어 빠른 차량 쪽으로 치우친다. 관측창이
     왕복의 2배가 되기 전에는 과소추정으로 읽어야 한다.""")
