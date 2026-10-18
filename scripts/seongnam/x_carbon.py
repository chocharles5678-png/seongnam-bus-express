# -*- coding: utf-8 -*-
"""급행 재편의 탄소 순효과 — 주행거리 변화와 정차 횟수 변화를 함께 센다
사용: python scripts/seongnam/x_carbon.py [--route 350] [--fleet 19] [--express 5]

왜 필요한가
  급행은 정차를 건너뛰므로 왕복 1회 배출이 완행보다 적다. 그러나 왕복시간이 짧아져
  같은 시간에 더 돌면 총 주행거리가 늘어 상쇄된다. 둘을 함께 세지 않으면 어느 쪽도 말할 수 없다.

두 운영 시나리오
  A 쉬지않고  급행이 아낀 시간만큼 왕복을 더 돈다 → 주행거리 증가, 정차 감소
  B 횟수유지  아낀 시간을 회차 여유로 둔다 → 주행거리 그대로, 정차만 감소

정차 1회 손실 = 감속으로 버린 운동에너지를 재가속으로 회복하는 연료 + 체류 중 공회전
  E = ½mv² / 구동효율 / 연료발열량 × 배출계수  +  공회전연료 × 체류시간 × 배출계수
  제동 회생이 없는 내연 차량 기준이며, 신호·정체로 어차피 멈추는 경우를 빼지 않아
  절감량의 상한으로 읽어야 한다.

주행거리 기준은 한국교통안전공단 「용도별 차종별 연료별 일평균 자동차주행거리」(2022)의
경기 사업형 승합차 기타연료(CNG) 222.4 km/대·일을 쓴다. data.go.kr/data/15088454
"""
import csv, io, sys, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument('--route', default='350')
ap.add_argument('--fleet', type=int, default=19)
ap.add_argument('--express', type=int, default=5)
ap.add_argument('--cycle', type=float, default=150.0, help='완행 왕복 실측(분)')
ap.add_argument('--km', type=float, default=40.0, help='왕복 거리(km) — 정류소 좌표 기반 추정')
ap.add_argument('--vkt', type=float, default=222.4, help='대당 일평균 주행(km) — 교통안전공단 2022')
ap.add_argument('--T', type=float, default=20, help='정차 1회당 손실시간(초) — 체류시간으로도 쓴다')
ap.add_argument('--peak-hours', type=float, default=2.0,
                help='첨두 시범운행 시간. 전일 전면 시행과 이 범위만 시행하는 경우를 함께 낸다')
a = ap.parse_args()

CNG_MJ, CNG_CO2, IDLE_KG_H = 50.0, 2.75, 0.4     # MJ/kg, kgCO2/kg, 공회전 kg/h

R = list(csv.DictReader(open(f'data/express_{a.route}.csv', encoding='utf-8-sig')))
ns = lambda r: len(r['순서'].split(','))
S_ALL = sum(ns(r) for r in R)
S_EXP = sum(ns(r) for r in R if r['급행정차'] == '정차')
SKIP = S_ALL - S_EXP
CYC_E = a.cycle - SKIP * a.T / 60


def stop_co2(m, v_kmh, eta=0.30):
    """정차 1회가 더 물리는 배출(kgCO2)"""
    kin_mj = 0.5 * m * (v_kmh / 3.6) ** 2 / 1e6
    return (kin_mj / eta / CNG_MJ + IDLE_KG_H * a.T / 3600) * CNG_CO2


LOC = a.fleet - a.express
base_km = a.fleet * a.vkt
base_rt = base_km / a.km
base_stop = base_rt * S_ALL

# A — 급행이 아낀 시간만큼 더 돈다
a_km = LOC * a.vkt + a.express * a.vkt * (a.cycle / CYC_E)
a_stop = (LOC * a.vkt / a.km) * S_ALL + (a.express * a.vkt * (a.cycle / CYC_E) / a.km) * S_EXP
# B — 왕복 횟수를 현행과 같게 유지
b_exp_rt, b_loc_rt = base_rt * a.express / a.fleet, base_rt * LOC / a.fleet
b_km = (b_exp_rt + b_loc_rt) * a.km
b_stop = b_loc_rt * S_ALL + b_exp_rt * S_EXP

print(f'■ {a.route}번 · 관측 {a.fleet}대 중 급행 {a.express}대 · 완행 왕복 {a.cycle:.0f}분 / '
      f'급행 왕복 {CYC_E:.0f}분 · 왕복 정차 {S_ALL}회 → 급행 {S_EXP}회(통과 {SKIP}회)\n')
print('■ 1. 운행 구조 (일 단위)')
print(f'  {"":12}{"주행거리":>12}{"정차 횟수":>12}')
print(f'  {"현행":12}{base_km:>10.0f} km{base_stop:>10.0f} 회')
print(f'  {"A 쉬지않고":12}{a_km:>10.0f} km{a_stop:>10.0f} 회   '
      f'({a_km/base_km-1:+.1%} / {a_stop/base_stop-1:+.1%})')
print(f'  {"B 횟수유지":12}{b_km:>10.0f} km{b_stop:>10.0f} 회   '
      f'({b_km/base_km-1:+.1%} / {b_stop/base_stop-1:+.1%})\n')

PARAMS = [(11000, 25, '보수'), (13000, 30, '중간'), (16000, 35, '적극')]
print('■ 2. 왕복 1회당 배출 (총 배출계수 e를 주행분과 정차분으로 분해)')
print(f'  {"가정":22}{"정차1회":>9}{"완행 왕복":>11}{"급행 왕복":>11}{"차이":>11}')
for e_tot in (1.0, 1.1, 1.3):
    for m, v, lab in PARAMS:
        if lab != '중간':
            continue
        s = stop_co2(m, v)
        cruise = (base_km * e_tot - base_stop * s) / base_km
        loc_rt_co2, exp_rt_co2 = a.km * cruise + S_ALL * s, a.km * cruise + S_EXP * s
        print(f'  e={e_tot:.1f} {lab}({m}kg {v}km/h) {s:>8.3f}{loc_rt_co2:>10.1f}kg'
              f'{exp_rt_co2:>10.1f}kg{exp_rt_co2-loc_rt_co2:>9.1f}kg '
              f'({exp_rt_co2/loc_rt_co2-1:+.0%})')
print()

print('■ 3. 일일 총 배출 변화')
print(f'  {"가정":26}{"현행":>11}{"A 쉬지않고":>14}{"B 횟수유지":>14}')
rows = []
for e_tot in (1.0, 1.1, 1.3):
    for m, v, lab in PARAMS:
        s = stop_co2(m, v)
        cruise = (base_km * e_tot - base_stop * s) / base_km
        if cruise <= 0:
            continue
        now = base_km * e_tot
        A = a_km * cruise + a_stop * s
        B = b_km * cruise + b_stop * s
        rows.append((A / now - 1, B / now - 1))
        if abs(e_tot - 1.1) < 1e-9 and lab == '중간':
            MAIN = (A / now - 1, B / now - 1)      # 본문이 쓰는 가정
        print(f'  e={e_tot:.1f} {lab}({m//1000}t {v}km/h){" ":6}{now:>9.0f}kg'
              f'{A-now:>+10.0f}kg({A/now-1:+.1%}){B-now:>+10.0f}kg({B/now-1:+.1%})')
lo_a, hi_a = min(r[0] for r in rows), max(r[0] for r in rows)
lo_b, hi_b = min(r[1] for r in rows), max(r[1] for r in rows)
print(f'\n  → A 쉬지않고 {lo_a:+.1%} ~ {hi_a:+.1%}   |   B 횟수유지 {lo_b:+.1%} ~ {hi_b:+.1%}')

# ── 적용 범위 — 제안이 첨두 2시간 시범운행이면 전일 기준 수치를 그대로 쓸 수 없다
rt_day = a.vkt / a.km                       # 대당 일평균 왕복 횟수
rt_peak = a.peak_hours * 60 / a.cycle       # 첨두 중 한 대가 도는 왕복 횟수
share = rt_peak / rt_day
hours_day = rt_day * a.cycle / 60
print(f'\n■ 4. 적용 범위 — 전일 전면 시행 vs 첨두 {a.peak_hours:g}시간 시범')
print(f'  대당 일평균 왕복 {rt_day:.2f}회 (= {a.vkt:.1f}km ÷ {a.km:.0f}km) → 일 운행 약 {hours_day:.1f}시간')
print(f'  첨두 {a.peak_hours:g}시간에 한 대가 도는 왕복 {rt_peak:.2f}회 → '
      f'전일 운행의 {share:.1%}')
print(f'  {"":14}{"전일 전면":>12}{"첨두 "+format(a.peak_hours,"g")+"시간":>12}')
print(f'  {"정차 감소":14}{b_stop/base_stop-1:>11.1%}{(b_stop/base_stop-1)*share:>11.1%}')
print(f'  {"탄소 (본문 가정)":14}{MAIN[1]:>11.1%}{MAIN[1]*share:>11.2%}')
print(f'  {"탄소 (범위)":14}{f"{lo_b:+.1%} ~ {hi_b:+.1%}":>14}'
      f'{f"{lo_b*share:+.2%} ~ {hi_b*share:+.2%}":>16}')
print('\n※ 범위를 섞지 말 것. 제안이 첨두 시범운행이면 오른쪽 열을 쓴다.')
print('\n※ 상한 추정이다. 신호·정체로 어차피 멈추는 경우를 빼지 않았고, 350번의 실제 연료를'
      '\n   확인하지 않아 경기 사업형 승합 CNG 통계를 대리값으로 썼다.')
