"""증차 시나리오 — 완행을 줄이지 않고 급행을 더하면 얼마가 드는가
사용: python scripts/seongnam/x_sim_fleet.py [--T 20]

두 시나리오를 비교한다.
  A 무증차 : 기존 18대를 급행 E / 완행 M 으로 나눈다 (E+M=18). 완행이 줄어 통과 지점이 손해를 본다.
  B 증차   : 완행 18대를 그대로 두고 급행 N대를 더한다. 통과 지점은 손해가 없다.

승객 구분
  · 급행 이용 가능 : 출발·도착이 모두 급행 정차 지점 → 급행·완행 중 먼저 오는 차를 탄다
  · 급행 이용 불가 : 한쪽이라도 통과 지점 → 완행만 탄다
"""
import csv, io, sys, argparse
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument('route', nargs='?', default='55')
ap.add_argument('--T', type=float, default=20, help='정차 1회당 손실시간(초) — 가정값')
ap.add_argument('--fleet', type=int, default=18)
ap.add_argument('--cycle', type=float, default=195)
ap.add_argument('--trip', type=float, default=1/3, help='평균 통행 길이 = 편도의 이 비율 (가정)')
a = ap.parse_args()

R = list(csv.DictReader(open(f'data/express_{a.route}.csv', encoding='utf-8-sig')))
ns = lambda r: len(r['순서'].split(','))
NA = sum(ns(r) for r in R); NS = sum(ns(r) for r in R if r['급행정차'] == '정차'); SKIP = NA - NS
TOT = sum(float(r['왕복일평균']) for r in R)
ST = sum(float(r['왕복일평균']) for r in R if r['급행정차'] == '정차')
p = ST / TOT                      # 급행 정차 지점 기록 비중
P_USE = p * p                     # 출발·도착 모두 급행 정차 (독립 가정)
CYC_E = a.cycle - SKIP * a.T / 60
GAIN = SKIP / 2 * a.T / 60 * a.trip   # 급행 이용자의 차내 단축(분)

def wait(hs, H=240):
    arr = np.sort(np.concatenate([np.arange(0, H, h) for h in hs if h and h > 0]))
    g = np.diff(arr); g = g[g > 1e-9]
    return (g**2).sum() / (2 * g.sum())

h0 = a.cycle / a.fleet
W0 = wait([h0])
print(f"■ {a.route}번 증차 시나리오  (완행 왕복 {a.cycle:.0f}분 · 급행 왕복 {CYC_E:.0f}분 · 정차손실 {a.T:.0f}초 가정)")
print(f"  현행: 관측 {a.fleet}대 전부 완행 · 간격 {h0:.1f}분 · 대기 {W0:.1f}분")
print(f"  급행 이용 가능 비중 {P_USE*100:.0f}% (기록 {p*100:.1f}% 의 제곱, 독립 가정) · 차내 단축 {GAIN:.1f}분\n")

def net(h_e, h_l):
    w_use = wait([h_e, h_l]) if h_e else wait([h_l])
    w_non = wait([h_l])
    n_use = GAIN - (w_use - W0)
    n_non = -(w_non - W0)
    return w_use, w_non, n_use, n_non, P_USE * n_use + (1 - P_USE) * n_non

print(f'■ A. 무증차 — 기존 {a.fleet}대를 나눈다')
print(f"{'급행':>4}{'완행':>4}{'급행간격':>8}{'완행간격':>8}{'급행이용 대기':>12}{'불가 대기':>10}"
      f"{'급행이용 순':>11}{'불가 순':>9}{'평균 순':>9}")
best_a = None
for E in range(1, a.fleet):                      # 전수. 후보를 간추리면 양수 구간을 놓친다
    M = a.fleet - E
    w1, w2, n1, n2, nn = net(CYC_E / E, a.cycle / M)
    if best_a is None or nn > best_a[1]: best_a = (E, nn)
    print(f"{E:>4}{M:>4}{CYC_E/E:>7.1f}분{a.cycle/M:>7.1f}분{w1:>11.1f}분{w2:>9.1f}분"
          f"{n1:>+10.1f}분{n2:>+8.1f}분{nn:>+8.1f}분")
print(f'  평균 순효과 최대: 급행 {best_a[0]}대 {best_a[1]:+.2f}분'
      f'  — 다만 그때 급행 간격은 {CYC_E/best_a[0]:.1f}분이다. 간격 기준을 함께 볼 것')

print(f'\n■ B. 증차 — 완행 {a.fleet}대를 그대로 두고 급행을 더한다 (통과 지점 손해 없음)')
print(f"{'증차':>4}{'총대수':>6}{'증차율':>7}{'급행간격':>8}{'완행간격':>8}{'급행이용 대기':>12}{'불가 대기':>10}"
      f"{'급행이용 순':>11}{'불가 순':>9}{'평균 순':>9}")
rows = []
for N in range(1, a.fleet + 1):                  # 전수
    w1, w2, n1, n2, nn = net(CYC_E / N, h0)
    rows.append((N, CYC_E / N, nn, n1))
    print(f"{N:>4}{a.fleet+N:>6}{N/a.fleet*100:>6.0f}%{CYC_E/N:>7.1f}분{h0:>7.1f}분{w1:>11.1f}분{w2:>9.1f}분"
          f"{n1:>+10.1f}분{n2:>+8.1f}분{nn:>+8.1f}분")
print('  평균 순효과는 증차 대수에 둔감하다(이득이 차내 단축에서 나온다). 대수는 아래 급행 간격으로 정할 것')

print('\n■ 최소 증차 — 급행 간격 기준')
for tgt in (30, 20, 15, h0):
    ok = [r for r in rows if r[1] <= tgt]
    if ok:
        N, he, nn, n1 = ok[0]
        print(f"  급행 간격 {tgt:>4.1f}분 이하  →  증차 {N}대 (총 {a.fleet+N}대, +{N/a.fleet*100:.0f}%)"
              f"  평균 순효과 {nn:+.1f}분/통행")
print(f"\n※ 무증차(급행 5대) 평균 순효과와 비교할 것. 증차는 통과 지점 손해가 0이므로 평균이 높게 나온다.")
print(f"※ 가정: 정차손실 {a.T:.0f}초 · 평균 통행 = 편도의 {a.trip*100:.0f}% · 출발·도착 독립")
