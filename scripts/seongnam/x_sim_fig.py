"""시뮬레이션 결과 도면 — 급행 배정 대수에 따른 배차 간격·대기시간 변화
사용: python scripts/seongnam/x_sim_fig.py [--T 20]
입력: x_sim.py 를 직접 호출해 결과를 받는다.
"""
import io, sys, subprocess, argparse
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
plt.rcParams['font.family'] = 'Malgun Gothic'; plt.rcParams['axes.unicode_minus'] = False

ap = argparse.ArgumentParser()
ap.add_argument('--T', type=int, default=20)
ap.add_argument('--fleet', type=int, default=18)
ap.add_argument('--cycle', type=float, default=195)
a = ap.parse_args()

# 검증된 카테고리 팔레트 (validate_palette.js 전 항목 PASS)
C1, C2 = '#2a78d6', '#eb6834'          # 슬롯1 blue, 슬롯2 orange
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e8e8e6'
BAND = '#f2f5fa'

r = subprocess.run([sys.executable, 'scripts/seongnam/x_sim.py', '55',
                    '--fleet', str(a.fleet), '--cycle', str(a.cycle), '--T', str(a.T)],
                   capture_output=True, text=True, encoding='utf-8', errors='replace')
rows, base = [], None
for line in r.stdout.splitlines():
    p = line.split()
    if len(p) >= 6 and p[0] == '—':
        base = float(p[4].replace('분', ''))          # 현행 대기 (p[3]=현행 간격)
    if len(p) >= 7 and p[0].isdigit() and p[1].isdigit():
        rows.append(dict(exp=int(p[0]), loc=int(p[1]),
                         h_e=float(p[2].replace('분', '')), h_l=float(p[3].replace('분', '')),
                         w_s=float(p[4].replace('분', '')), w_p=float(p[5].replace('분', ''))))
X = np.array([x['exp'] for x in rows])
base_h = a.cycle / a.fleet

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.6, 6.0))
REC = (5, 6)   # 권장 구간

for ax in (ax1, ax2):
    ax.axvspan(REC[0] - 0.4, REC[1] + 0.4, color=BAND, zorder=0)
    ax.grid(axis='y', color=GRID, lw=0.9); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color('#cfcfcc')
    ax.set_xlabel('급행으로 배정하는 차량 수 (전체 18대 중)', fontsize=10, color=INK2)
    ax.set_xticks(range(1, 18, 2)); ax.set_xlim(0.3, 17.7)
    ax.tick_params(colors=INK2, labelsize=9)

# ── 좌: 대기시간
y_s = np.array([x['w_s'] for x in rows]); y_p = np.array([x['w_p'] for x in rows])
ax1.axhline(base, color=INK2, lw=1.4, ls=(0, (5, 3)), zorder=1)
ax1.annotate(f'현행 {base:.1f}분', (17.5, base), xytext=(0, -14), textcoords='offset points',
             ha='right', fontsize=9.5, color=INK2)
ax1.plot(X, y_p, '-o', color=C2, lw=2, ms=5, zorder=3)
ax1.plot(X, y_s, '-o', color=C1, lw=2, ms=5, zorder=3)
ax1.set_ylim(0, 26)
ax1.annotate('급행이 통과하는 지점', (X[6], y_p[6]), xytext=(10, 14), textcoords='offset points',
             fontsize=10, weight='bold', color=C2)
ax1.annotate('급행이 정차하는 지점', (X[9], y_s[9]), xytext=(6, -22), textcoords='offset points',
             fontsize=10, weight='bold', color=C1)
ax1.set_ylabel('승객 평균 대기시간 (분)', fontsize=10.5, color=INK)
ax1.set_title('대기시간은 모든 지점에서 늘어난다', fontsize=12.5, weight='bold', color=INK, pad=12)

# ── 우: 배차 간격
h_e = np.array([x['h_e'] for x in rows]); h_l = np.array([x['h_l'] for x in rows])
ax2.axhline(base_h, color=INK2, lw=1.4, ls=(0, (5, 3)), zorder=1)
ax2.annotate(f'현행 {base_h:.1f}분', (17.5, base_h), xytext=(0, -14), textcoords='offset points',
             ha='right', fontsize=9.5, color=INK2)
ax2.plot(X, h_l, '-o', color=C2, lw=2, ms=5, zorder=3)
ax2.plot(X, h_e, '-o', color=C1, lw=2, ms=5, zorder=3)
ax2.set_ylim(0, 70)
ax2.annotate('완행 배차 간격', (X[8], h_l[8]), xytext=(8, 10), textcoords='offset points',
             fontsize=10, weight='bold', color=C2)
ax2.annotate('급행 배차 간격', (X[5], h_e[5]), xytext=(10, 8), textcoords='offset points',
             fontsize=10, weight='bold', color=C1)
ax2.set_ylabel('배차 간격 (분)', fontsize=10.5, color=INK)
ax2.set_title('급행을 늘릴수록 완행이 벌어진다', fontsize=12.5, weight='bold', color=INK, pad=12)

for ax in (ax1, ax2):
    ax.annotate('권장\n5~6대', (5.5, ax.get_ylim()[1] * 0.93), ha='center', va='top',
                fontsize=9.5, color=INK2, weight='bold')

fig.suptitle(f'55번 급행 재편 — 급행 배정 대수별 영향  (관측 18대 · 완행 왕복 195분 · 정차손실 {a.T}초 가정)',
             fontsize=13.5, weight='bold', color=INK, y=0.99)
fig.legend(handles=[Line2D([], [], color=C1, lw=2, marker='o', ms=5, label='급행 정차 지점 / 급행'),
                    Line2D([], [], color=C2, lw=2, marker='o', ms=5, label='급행 통과 지점 / 완행'),
                    Line2D([], [], color=INK2, lw=1.4, ls=(0, (5, 3)), label='현행 (18대 전부 완행)')],
           loc='lower center', ncol=3, frameon=False, fontsize=10, bbox_to_anchor=(0.5, -0.015))
fig.text(0.995, 0.005, '자료: 경기도 버스위치정보 실측(2026-10-07) · 경기도 정류소별 승하차(2026.6)',
         ha='right', fontsize=8.5, color='#8a8a86')
fig.tight_layout(rect=[0, 0.06, 1, 0.96])
out = f'figures/시뮬레이션_55_T{a.T}초.png'
fig.savefig(out, dpi=170, facecolor='white', bbox_inches='tight')
print(f'-> {out}')
print(f'   현행 대기 {base:.1f}분 / 현행 간격 {base_h:.1f}분')
for x in rows:
    if x['exp'] in REC:
        print(f"   급행 {x['exp']}대: 급행{x['h_e']:.1f}분 완행{x['h_l']:.1f}분 "
              f"정차지점대기 {x['w_s']:.1f}분 통과지점대기 {x['w_p']:.1f}분")
