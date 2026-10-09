"""급행 재편 시뮬레이션 — 급행 배정 대수별 대기시간·차내시간 변화
사용: python scripts/seongnam/x_sim.py 55 [--fleet 19] [--cycle 198] [--T 20]

모형
  · 전체 차량을 급행 N대 / 완행 M대로 나눈다 (N+M=fleet). 증차 없음.
  · 완행 왕복 = cycle (실측).  급행 왕복 = cycle - 통과횟수 × T.
  · 각 서비스는 자기 왕복시간 ÷ 자기 대수 간격으로 운행한다.
  · 승객이 무작위 시각에 정류장에 온다고 보고 평균 대기 = E[gap²]/(2·E[gap]).
  · T(정차 1회당 손실시간)는 실측 실패로 가정값이다. 범위로 돌린다.
"""
import csv, io, sys, argparse
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument('route', nargs='?', default='55')
ap.add_argument('--fleet', type=int, default=19, help='동시 운행 대수 (실측)')
ap.add_argument('--cycle', type=float, default=198, help='완행 왕복 소요시간(분, 실측)')
ap.add_argument('--T', type=float, default=20, help='정차 1회당 손실시간(초) — 가정값')
ap.add_argument('--hours', type=float, default=4, help='시뮬레이션 길이(시간)')
a = ap.parse_args()

rows = list(csv.DictReader(open(f'data/express_{a.route}.csv', encoding='utf-8-sig')))
nstop = lambda r: len(r['순서'].split(','))
N_ALL = sum(nstop(r) for r in rows)
N_EXP = sum(nstop(r) for r in rows if r['급행정차'] == '정차')
SKIP = N_ALL - N_EXP
W_STOP = sum(float(r['왕복일평균']) for r in rows if r['급행정차'] == '정차')
W_ALL = sum(float(r['왕복일평균']) for r in rows)

def wait(headways):
    """여러 서비스가 각자 등간격으로 올 때, 무작위 도착 승객의 평균·최대 대기(분)"""
    H = a.hours * 60
    arr = []
    for h in headways:
        if h and h > 0:
            arr += list(np.arange(0, H, h))
    if not arr: return None, None
    arr = np.sort(np.array(arr))
    gaps = np.diff(arr)
    gaps = gaps[gaps > 1e-9]
    if len(gaps) == 0: return None, None
    mean_w = (gaps ** 2).sum() / (2 * gaps.sum())      # 무작위 도착 승객의 평균 대기
    return mean_w, gaps.max()

print(f"■ {a.route}번 급행 재편 시뮬레이션")
print(f"  실측: 동시 운행 {a.fleet}대 · 완행 왕복 {a.cycle:.0f}분 · 현행 간격 {a.cycle/a.fleet:.1f}분")
print(f"  정차 {N_ALL}회 중 급행 {N_EXP}회 정차 / {SKIP}회 통과")
print(f"  가정: 정차 1회당 손실 {a.T:.0f}초  →  급행 왕복 {a.cycle - SKIP*a.T/60:.0f}분 "
      f"({SKIP*a.T/60:.0f}분 단축)\n")

base_h = a.cycle / a.fleet
bw, bx = wait([base_h])
print(f"{'급행':>4}{'완행':>4}  {'급행간격':>8}{'완행간격':>8}   "
      f"{'정차지점 대기':>13}{'통과지점 대기':>13}   {'급행 차내단축':>12}")
print(f"{'—':>4}{a.fleet:>4}  {'—':>8}{base_h:>7.1f}분   "
      f"{bw:>11.1f}분{bw:>12.1f}분   {'— (현행)':>12}")
best = []
for n_exp in range(1, a.fleet):
    n_loc = a.fleet - n_exp
    cyc_e = a.cycle - SKIP * a.T / 60
    h_e = cyc_e / n_exp
    h_l = a.cycle / n_loc
    w_both, x_both = wait([h_e, h_l])        # 급행·완행 모두 탈 수 있는 지점
    w_loc, x_loc = wait([h_l])               # 완행만 서는 지점
    saved = SKIP * a.T / 60
    best.append((n_exp, n_loc, h_e, h_l, w_both, w_loc, saved, x_both, x_loc))
    mark = ''
    print(f"{n_exp:>4}{n_loc:>4}  {h_e:>7.1f}분{h_l:>7.1f}분   "
          f"{w_both:>11.1f}분{w_loc:>12.1f}분   {saved:>10.0f}분{mark}")

print(f"\n■ 판정 기준")
print(f"  · 통과 지점 대기가 현행({bw:.1f}분)보다 크게 늘면 안 된다")
print(f"  · 급행 간격이 너무 길면(완행보다 길면) 급행을 기다릴 이유가 없다")
ok = [x for x in best if x[5] <= bw * 1.6 and x[2] <= x[3] * 2.5]
if ok:
    print(f"\n■ 두 조건을 만족하는 배정")
    print(f"{'급행':>4}{'완행':>4}  {'급행간격':>8}{'완행간격':>8}{'통과지점 대기':>13}{'현행 대비':>10}")
    for n_exp, n_loc, h_e, h_l, w_b, w_l, sv, xb, xl in ok:
        print(f"{n_exp:>4}{n_loc:>4}  {h_e:>7.1f}분{h_l:>7.1f}분{w_l:>11.1f}분{w_l/bw*100:>9.0f}%")
else:
    print('\n  ⚠ 두 조건을 동시에 만족하는 배정이 없다')
print(f"\n※ 급행 정차 지점이 담는 승하차 기록 {W_STOP/W_ALL*100:.1f}% — 이는 기록 구성비이며 수혜 인원이 아니다")
print(f"※ T={a.T:.0f}초는 가정값이다. 실측에 실패했으므로 --T 15/20/25/30 으로 범위를 확인할 것")
