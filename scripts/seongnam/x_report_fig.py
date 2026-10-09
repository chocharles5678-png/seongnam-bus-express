"""보고서 도면 2장 — 배차 역설 · 증차 효과
사용: python scripts/seongnam/x_report_fig.py [--T 20]
출력: figures/배차역설_3개노선.png · figures/증차효과_55.png
입력: data/express_{88_1,55,380}.csv + 실측 왕복·관측대수(아래 ROUTES)
"""
import csv, io, sys, argparse
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
plt.rcParams['font.family'] = 'Malgun Gothic'; plt.rcParams['axes.unicode_minus'] = False

ap = argparse.ArgumentParser()
ap.add_argument('--T', type=float, default=20, help='정차 1회당 손실시간(초) — 가정값')
ap.add_argument('--trip', type=float, default=1/3)
a = ap.parse_args()

C1, C2, C3 = '#2a78d6', '#eb6834', '#4f9d57'      # 검증된 카테고리 팔레트
INK, INK2, GRID, BAND = '#0b0b0b', '#52514e', '#e8e8e6', '#f2f5fa'
NEG = '#fdeeea'

# (파일키, 표시명, 관측대수, 실측 왕복(분))
ROUTES = [('88_1', '88-1', 4, 98.0), ('55', '55', 18, 195.0), ('380', '380', 10, 200.0)]


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
        net = p * (gain - (wait([he, hl]) - w0)) + (1 - p) * (-(wait([hl]) - w0))
        out.append(dict(E=E, M=M, he=he, hl=hl, net=net))
    return dict(rows=out, cov=cov, p=p, cyc_e=cyc_e, gain=gain, skip=skip, w0=w0,
                h0=cycle / fleet, fleet=fleet, cycle=cycle, wait=wait)


# ─────────────────────────────── 그림 A. 배차 역설
fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.5), sharey=True)
for ax, (key, nm, fleet, cycle) in zip(axes, ROUTES):
    m = model(key, fleet, cycle)
    E = [r['E'] for r in m['rows']]; net = [r['net'] for r in m['rows']]
    he = [r['he'] for r in m['rows']]
    ax.axhspan(-20, 0, color=NEG, zorder=0)
    ax.axhline(0, color=INK2, lw=0.9, zorder=2)
    # 급행 간격 30분 이하 구간을 음영으로
    ok = [i for i, h in enumerate(he) if h <= 30]
    if ok:
        ax.axvspan(E[ok[0]] - 0.5, E[-1] + 0.5, color=BAND, zorder=1)
        ax.text(E[ok[0]] - 0.3, -18.6, '← 급행 간격 30분 이하', fontsize=8.5, color=C1,
                va='bottom', ha='left')
    ax.plot(E, net, '-o', color=C2, ms=4.5, lw=1.8, zorder=3)
    # 두 조건을 모두 만족하는 점
    hit = [r for r in m['rows'] if r['he'] <= 30 and r['net'] > 0]
    if hit:
        r = hit[0]
        ax.plot([r['E']], [r['net']], 'o', ms=13, mfc='none', mec=C3, mew=2.4, zorder=4)
        ax.annotate(f"급행 {r['E']}대 · {r['net']:+.2f}분", (r['E'], r['net']),
                    textcoords='offset points', xytext=(-104, -36), fontsize=9.5,
                    color=C3, fontweight='bold',
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
fig.suptitle('배차 역설 — 나눌 수 있는 노선은 이미 배차가 촘촘한 노선뿐이다',
             fontsize=13.5, color=INK, y=1.0, fontweight='bold')
fig.text(0.5, -0.03,
         f'무증차 재편. 정차 1회당 손실 {a.T:.0f}초·평균 통행 = 편도의 {a.trip*100:.0f}% 가정. '
         '붉은 영역은 평균이 음수인 구간. 왕복·관측대수는 버스위치 API 실측값.',
         ha='center', fontsize=8.5, color=INK2)
fig.tight_layout()
fig.savefig('figures/배차역설_3개노선.png', dpi=190, bbox_inches='tight', facecolor='white')
print('-> figures/배차역설_3개노선.png')

# ─────────────────────────────── 그림 B. 증차 효과
m = model('55', 18, 195)
wait, w0, h0 = m['wait'], m['w0'], m['h0']
p, gain, cyc_e = m['p'], m['gain'], m['cyc_e']
adds = list(range(0, 13))
use, non, avg = [], [], []
for N in adds:
    if N == 0:
        use.append(0.0); non.append(0.0); avg.append(0.0); continue
    he = cyc_e / N
    n_use = gain - (wait([he, h0]) - w0)
    n_non = -(wait([h0]) - w0)
    use.append(n_use); non.append(n_non); avg.append(p * n_use + (1 - p) * n_non)

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.4, 4.6),
                              gridspec_kw=dict(width_ratios=[1.55, 1]))

ax.axhline(0, color=INK2, lw=0.9)
ax.plot(adds, use, '-o', color=C1, ms=4.5, lw=1.9, label=f'급행 이용 가능 통행 ({p*100:.0f}%)')
ax.plot(adds, non, '-s', color=C2, ms=4.5, lw=1.9, label=f'급행 이용 불가 통행 ({(1-p)*100:.0f}%)')
ax.plot(adds, avg, '-^', color=INK, ms=5.5, lw=2.3, label='전체 평균')
ax.set_title('증차 — 완행 18대를 그대로 두고 급행을 더한다', fontsize=11, color=INK, pad=9)
ax.set_xlabel('증차 대수(대)', fontsize=9.5, color=INK2)
ax.set_ylabel('통행당 순효과(분)', fontsize=9.5, color=INK2)
ax.set_xticks(adds); ax.set_ylim(-0.6, 7.6)
ax.grid(axis='y', color=GRID, lw=0.7); ax.set_axisbelow(True)
for s in ('top',): ax.spines[s].set_visible(False)
ax.tick_params(labelsize=9, colors=INK2)

# 오른쪽 축 — 증차 대수를 정하는 실제 기준은 평균이 아니라 급행 간격이다
axr = ax.twinx()
gaps = [cyc_e / N if N else np.nan for N in adds]
axr.plot(adds, gaps, ls=(0, (4, 3)), color=C3, lw=1.7, marker='D', ms=3.5,
         label='급행 간격(오른쪽 축)')
axr.axhline(30, color=C3, lw=0.9, alpha=0.5)
axr.text(12.2, 32, '30분', fontsize=8.5, color=C3, ha='right')
axr.set_ylim(0, 180); axr.set_ylabel('급행 간격(분)', fontsize=9.5, color=C3)
axr.tick_params(labelsize=9, colors=C3); axr.spines['top'].set_visible(False)
axr.spines['right'].set_color(C3)
for N in (3, 6):
    axr.annotate(f'{N}대\n{cyc_e/N:.0f}분', (N, cyc_e / N), textcoords='offset points',
                 xytext=(6, 6), fontsize=8.5, color=C3, fontweight='bold', linespacing=1.3)

h1, l1 = ax.get_legend_handles_labels(); h2, l2 = axr.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=8.8, frameon=False,
          loc='upper left', bbox_to_anchor=(0.20, 0.70))

# 오른쪽 — 무증차 대 증차
lab = ['무증차\n급행 5대 분리', '무증차\n급행 6대 분리', '증차 3대\n(+17%)', '증차 6대\n(+33%)']
r5 = next(r for r in m['rows'] if r['E'] == 5); r6 = next(r for r in m['rows'] if r['E'] == 6)
val = [r5['net'], r6['net'], avg[3], avg[6]]
sub = [f"완행 {r5['hl']:.1f}분", f"완행 {r6['hl']:.1f}분", '완행 10.8분 유지', '완행 10.8분 유지']
col = [C2, C2, C1, C1]
b = ax2.bar(range(4), val, color=col, width=0.62)
for i, (v, s) in enumerate(zip(val, sub)):
    ax2.text(i, v + 0.11, f'{v:+.2f}분', ha='center', fontsize=10.5, fontweight='bold', color=INK)
    ax2.text(i, -0.26, s, ha='center', fontsize=8.5, color=INK2)
ax2.axhline(0, color=INK2, lw=0.9)
ax2.set_xticks(range(4)); ax2.set_xticklabels(lab, fontsize=9, color=INK2, linespacing=1.5)
ax2.set_ylim(-0.55, 3.0)
ax2.set_title('기존 이용자의 손해 유무가 가른다', fontsize=11, color=INK, pad=9)
ax2.set_ylabel('통행당 평균 순효과(분)', fontsize=9.5, color=INK2)
ax2.grid(axis='y', color=GRID, lw=0.7); ax2.set_axisbelow(True)
for s in ('top', 'right', 'bottom'): ax2.spines[s].set_visible(False)
ax2.tick_params(labelsize=9, colors=INK2, bottom=False)

fig.suptitle('55번 — 증차 3대(+17%)면 아무도 손해 보지 않는다',
             fontsize=13.5, color=INK, y=1.0, fontweight='bold')
fig.text(0.5, -0.04,
         '평균 순효과는 증차 대수에 거의 둔감하다 — 이득이 차내 단축에서 나오기 때문이다. '
         '증차 대수를 정하는 것은 평균이 아니라 급행 간격이다.\n'
         f'관측 18대·왕복 195분 실측. 정차 1회당 손실 {a.T:.0f}초·평균 통행 = 편도의 {a.trip*100:.0f}% 가정. '
         f'급행 이용 가능 {p*100:.0f}%는 승하차 기록 구성비 {m["cov"]*100:.1f}%의 제곱(출발·도착 독립 가정).',
         ha='center', fontsize=8.5, color=INK2, linespacing=1.7)
fig.tight_layout()
fig.savefig('figures/증차효과_55.png', dpi=190, bbox_inches='tight', facecolor='white')
print('-> figures/증차효과_55.png')
