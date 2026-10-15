"""350번 중심 보고서 도면 2장 — 배차 역설(4개 노선) · 350 무증차 재편
사용: python scripts/seongnam/x_report_fig350.py [--T 20]
출력: figures/배차역설_4개노선.png · figures/무증차_350.png
입력: data/express_{88_1,380,55,350}.csv + 버스위치 API 실측 왕복·관측대수(아래 ROUTES)

x_report_fig.py(55번 보고서용)는 건드리지 않는다. 증차 도면은 만들지 않는다 —
증차는 주행거리 +19.9~26.7%로 탄소중립 취지와 상충해 제안 대상에서 제외했다.
"""
import csv, io, sys, argparse
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
plt.rcParams['font.family'] = 'Malgun Gothic'; plt.rcParams['axes.unicode_minus'] = False

ap = argparse.ArgumentParser()
ap.add_argument('--T', type=float, default=20, help='정차 1회당 손실시간(초) — 가정값')
ap.add_argument('--trip', type=float, default=1/3, help='평균 통행 = 편도의 이 비율 — 가정값')
a = ap.parse_args()

C1, C2, C3 = '#2a78d6', '#eb6834', '#4f9d57'
INK, INK2, GRID, BAND = '#0b0b0b', '#52514e', '#e8e8e6', '#f2f5fa'
NEG = '#fdeeea'

# (파일키, 표시명, 관측대수, 실측 왕복(분)) — 배차가 긴 쪽부터
ROUTES = [('88_1', '88-1', 4, 98.0), ('380', '380', 10, 200.0),
          ('55', '55', 18, 195.0), ('350', '350', 19, 150.0)]


def model(key, fleet, cycle):
    R = list(csv.DictReader(open(f'data/express_{key}.csv', encoding='utf-8-sig')))
    ns = lambda r: len(r['순서'].split(','))
    skip = sum(ns(r) for r in R) - sum(ns(r) for r in R if r['급행정차'] == '정차')
    tot = sum(float(r['왕복일평균']) for r in R)
    cov = sum(float(r['왕복일평균']) for r in R if r['급행정차'] == '정차') / tot
    p = cov * cov                                  # 출발·도착 모두 급행 정차 (독립 가정)
    cyc_e = cycle - skip * a.T / 60
    gain = skip / 2 * a.T / 60 * a.trip

    def wait(hs, H=240):
        arr = np.sort(np.concatenate([np.arange(0, H, h) for h in hs if h and h > 0]))
        g = np.diff(arr); g = g[g > 1e-9]
        return (g**2).sum() / (2 * g.sum())

    w0 = wait([cycle / fleet])
    out = []
    for E in range(1, fleet):
        M = fleet - E
        he, hl = cyc_e / E, cycle / M
        n_use = gain - (wait([he, hl]) - w0)
        n_non = -(wait([hl]) - w0)
        out.append(dict(E=E, M=M, he=he, hl=hl, n_use=n_use, n_non=n_non,
                        net=p * n_use + (1 - p) * n_non))
    return dict(rows=out, cov=cov, p=p, cyc_e=cyc_e, gain=gain, skip=skip, w0=w0,
                h0=cycle / fleet, fleet=fleet, cycle=cycle, wait=wait)


# ───────────────────────── 그림 1. 배차 역설 (4개 노선)
fig, axes = plt.subplots(1, 4, figsize=(17.0, 4.5), sharey=True)
for ax, (key, nm, fleet, cycle) in zip(axes, ROUTES):
    m = model(key, fleet, cycle)
    E = [r['E'] for r in m['rows']]; net = [r['net'] for r in m['rows']]
    he = [r['he'] for r in m['rows']]
    ax.axhspan(-20, 0, color=NEG, zorder=0)
    ax.axhline(0, color=INK2, lw=0.9, zorder=2)
    ok = [i for i, h in enumerate(he) if h <= 30]
    if ok:
        ax.axvspan(E[ok[0]] - 0.5, E[-1] + 0.5, color=BAND, zorder=1)
        ax.text(E[ok[0]] - 0.3, -18.6, '← 급행 간격 30분 이하', fontsize=8.5, color=C1,
                va='bottom', ha='left')
    ax.plot(E, net, '-o', color=C2, ms=4.5, lw=1.8, zorder=3)
    hit = [r for r in m['rows'] if r['he'] <= 30 and r['net'] > 0]
    if hit:
        r = hit[0]
        ax.plot([r['E']], [r['net']], 'o', ms=13, mfc='none', mec=C3, mew=2.4, zorder=4)
        # 앵커가 왼쪽에 치우치면 라벨을 오른쪽으로 빼야 축에 걸리지 않는다
        dx = 34 if r['E'] <= max(E) * 0.4 else -34
        ax.annotate(f"급행 {r['E']}대 · {r['net']:+.2f}분", (r['E'], r['net']),
                    textcoords='offset points', xytext=(dx, -44), fontsize=9.5,
                    color=C3, fontweight='bold', ha='center',
                    arrowprops=dict(arrowstyle='-', color=C3, lw=1.1))
    else:
        ax.text(0.5, 0.30, '두 조건을 함께 만족하는\n배정이 없다', transform=ax.transAxes,
                ha='center', fontsize=9.5, color=C2, fontweight='bold', linespacing=1.5)
    ax.set_title(f'{nm}번   관측 {fleet}대 · 왕복 {cycle:.0f}분\n현행 간격 {m["h0"]:.1f}분',
                 fontsize=10.5, color=INK, linespacing=1.5, pad=9)
    ax.set_xlabel('급행으로 돌리는 차량 수(대)', fontsize=9.5, color=INK2)
    ax.set_ylim(-20, 3.5); ax.set_xlim(0.3, max(E) + 0.7)
    ax.set_xticks(E if len(E) <= 10 else [e for e in E if e % 2 == 0])
    ax.grid(axis='y', color=GRID, lw=0.7); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=9, colors=INK2)
axes[0].set_ylabel('통행당 평균 순효과(분)', fontsize=9.5, color=INK2)
fig.suptitle('배차 역설 — 나눌 수 있는 노선은 이미 배차가 촘촘한 노선뿐이고, 가장 촘촘한 350번이 유일하게 쓸 만하다',
             fontsize=13.5, color=INK, y=1.0, fontweight='bold')
fig.text(0.5, -0.03,
         f'무증차 재편. 정차 1회당 손실 {a.T:.0f}초·평균 통행 = 편도의 {a.trip*100:.0f}% 가정. '
         '붉은 영역은 평균이 음수인 구간. 왕복·관측대수는 버스위치 API 실측값(88-1·380·55는 10-07, 350은 10-14 첨두).',
         ha='center', fontsize=8.5, color=INK2)
fig.tight_layout()
fig.savefig('figures/배차역설_4개노선.png', dpi=190, bbox_inches='tight', facecolor='white')
print('-> figures/배차역설_4개노선.png')

# ───────────────────────── 그림 2. 350 무증차 재편
m = model('350', 19, 150.0)
m55 = model('55', 18, 195.0)
rows = m['rows']
E = [r['E'] for r in rows]

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.6, 4.6),
                              gridspec_kw=dict(width_ratios=[1.55, 1]))

ax.axhline(0, color=INK2, lw=0.9)
ax.plot(E, [r['n_use'] for r in rows], '-o', color=C1, ms=4.5, lw=1.9,
        label=f"급행 이용 가능 통행 ({m['p']*100:.0f}%)")
ax.plot(E, [r['n_non'] for r in rows], '-s', color=C2, ms=4.5, lw=1.9,
        label=f"급행 이용 불가 통행 ({(1-m['p'])*100:.0f}%)")
ax.plot(E, [r['net'] for r in rows], '-^', color=INK, ms=5.5, lw=2.3, label='전체 평균')
ax.set_title('350번 무증차 — 관측 19대를 급행과 완행으로 나눈다', fontsize=11, color=INK, pad=9)
ax.set_xlabel('급행으로 돌리는 차량 수(대)', fontsize=9.5, color=INK2)
ax.set_ylabel('통행당 순효과(분)', fontsize=9.5, color=INK2)
ax.set_xticks([e for e in E if e % 2 == 1]); ax.set_ylim(-9.5, 5.6)
ax.grid(axis='y', color=GRID, lw=0.7); ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.tick_params(labelsize=9, colors=INK2)

axr = ax.twinx()
axr.plot(E, [r['he'] for r in rows], ls=(0, (4, 3)), color=C3, lw=1.7, marker='D', ms=3.5,
         label='급행 간격(오른쪽 축)')
axr.axhline(30, color=C3, lw=0.9, alpha=0.5)
axr.text(max(E) - 0.2, 32, '30분', fontsize=8.5, color=C3, ha='right')
axr.set_ylim(0, 160); axr.set_ylabel('급행 간격(분)', fontsize=9.5, color=C3)
axr.tick_params(labelsize=9, colors=C3); axr.spines['top'].set_visible(False)
axr.spines['right'].set_color(C3)
r5 = next(r for r in rows if r['E'] == 5)
# 권장 배정은 세로선으로 표시한다 — 데이터 점에 라벨을 붙이면 범례와 겹친다
ax.axvline(5, color=C3, lw=1.1, ls=(0, (2, 2)), zorder=1)
ax.text(5.35, 5.35, f"급행 5대 · 간격 {r5['he']:.1f}분 · 평균 {r5['net']:+.2f}분",
        fontsize=9.5, color=C3, fontweight='bold', va='top', ha='left')

h1, l1 = ax.get_legend_handles_labels(); h2, l2 = axr.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=8.8, frameon=False,
          loc='lower left', bbox_to_anchor=(0.03, 0.03))

# 오른쪽 — 350 대 55번, 같은 조건(급행 간격 30분 이하 최소 대수)
r350 = next(r for r in rows if r['he'] <= 30)
r55 = next(r for r in m55['rows'] if r['he'] <= 30)
lab = [f"350번\n급행 {r350['E']}대", f"55번\n급행 {r55['E']}대"]
groups = [('급행 이용 가능', [r350['n_use'], r55['n_use']], C1),
          ('급행 이용 불가', [r350['n_non'], r55['n_non']], C2),
          ('전체 평균', [r350['net'], r55['net']], INK)]
x = np.arange(2); w = 0.26
for i, (nm, vals, col) in enumerate(groups):
    b = ax2.bar(x + (i - 1) * w, vals, width=w, color=col, label=nm)
    for xi, v in zip(x + (i - 1) * w, vals):
        ax2.text(xi, v + (0.14 if v >= 0 else -0.42), f'{v:+.1f}', ha='center',
                 fontsize=9, fontweight='bold', color=INK)
ax2.axhline(0, color=INK2, lw=0.9)
ax2.set_xticks(x); ax2.set_xticklabels(lab, fontsize=9.5, color=INK2, linespacing=1.5)
ax2.set_ylim(-4.2, 5.4)
ax2.set_title('같은 조건에서 350번이 적게 잃는다', fontsize=11, color=INK, pad=9)
ax2.set_ylabel('통행당 순효과(분)', fontsize=9.5, color=INK2)
ax2.legend(fontsize=8.8, frameon=False, loc='upper right')
ax2.grid(axis='y', color=GRID, lw=0.7); ax2.set_axisbelow(True)
for s in ('top', 'right', 'bottom'): ax2.spines[s].set_visible(False)
ax2.tick_params(labelsize=9, colors=INK2, bottom=False)

fig.suptitle('350번 무증차 재편 — 급행 5대에서 평균 +0.5분, 손해는 55번의 절반',
             fontsize=13.5, color=INK, y=1.0, fontweight='bold')
fig.text(0.5, -0.045,
         f"350번 관측 19대·왕복 150분(10-14 첨두 실측, 완주 13대). 55번 관측 18대·왕복 195분. "
         f"정차 1회당 손실 {a.T:.0f}초·평균 통행 = 편도의 {a.trip*100:.0f}% 가정.\n"
         f"급행 이용 가능 {m['p']*100:.0f}%는 승하차 기록 구성비 {m['cov']*100:.1f}%의 제곱(출발·도착 독립 가정)이며 "
         "실제 승객 비율이 아니다. 오른쪽은 급행 간격 30분 이하가 되는 최소 대수끼리의 비교.",
         ha='center', fontsize=8.5, color=INK2, linespacing=1.7)
fig.tight_layout()
fig.savefig('figures/무증차_350.png', dpi=190, bbox_inches='tight', facecolor='white')
print('-> figures/무증차_350.png')
