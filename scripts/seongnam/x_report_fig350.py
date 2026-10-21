"""350번 중심 보고서 도면 2장 — 배차 역설(4개 노선) · 350 무증차 재편
사용: python scripts/seongnam/x_report_fig350.py [--T 20]
출력: figures/배차역설_4개노선.png · figures/무증차_350.png
입력: data/express_{88_1,380,55,350}.csv + 버스위치 API 실측 왕복·관측대수(아래 ROUTES)

x_report_fig.py(55번 보고서용)는 건드리지 않는다. 증차 도면은 만들지 않는다 —
증차는 주행거리 +19.9~26.7%로 탄소중립 취지와 상충해 제안 대상에서 제외했다.
"""
import csv, io, json, sys, argparse
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
ROUTES = [('88_1', '88-1', 4, 98.0), ('380', '380', 10, 187.0),
          ('55', '55', 18, 200.0), ('350', '350', 19, 150.0)]


_GRID = (np.arange(1500) + 0.5) / 1500.0


def model(key, fleet, cycle, keep_trips=False, parallel=False):
    """keep_trips=True면 급행이 아낀 시간을 회차 여유로 두어 왕복 횟수를 현행과 같게 유지한다.
    급행 간격이 cycle/E가 되고 총 주행거리가 늘지 않는다(탄소 비교용).

    탑승 규칙: 급행 이용 가능 통행은 완행 잔여대기와 (급행 잔여대기 - 차내단축) 중
    작은 쪽을 택한다. 차내 단축은 급행을 실제로 탄 경우에만 생긴다 —
    대기를 "먼저 오는 차"로 계산하면서 차내 단축을 전원에게 더하면 부호가 뒤집힌다.

    parallel=True면 통과 지점을 병행 노선으로 가중한다. data/par_q_<key>.json 이
    있어야 하며 x_parallel.py 가 만든다. 없으면 통과 지점 전체가 완행 간격 확대를
    그대로 받는다(병행 미반영).
    """
    R = list(csv.DictReader(open(f'data/express_{key}.csv', encoding='utf-8-sig')))
    ns = lambda r: len(r['순서'].split(','))
    skip = sum(ns(r) for r in R) - sum(ns(r) for r in R if r['급행정차'] == '정차')
    tot = sum(float(r['왕복일평균']) for r in R)
    cov = sum(float(r['왕복일평균']) for r in R if r['급행정차'] == '정차') / tot
    p = cov * cov                                  # 출발·도착 모두 급행 정차 (독립 가정)
    cyc_e = cycle - skip * a.T / 60
    gain = skip / 2 * a.T / 60 * a.trip

    def wait(hs, H=1800):
        arr = np.sort(np.concatenate([np.arange(0, H, h) for h in hs if h and h > 0]))
        g = np.diff(arr); g = g[g > 1e-9]
        return (g**2).sum() / (2 * g.sum())

    pas, hp = None, None
    if parallel:
        d = json.load(io.open(f'data/par_q_{key}.json', encoding='utf-8'))
        pas = [x for x in d['stops'] if not x['base']]
        hp = d['hp']

    w0 = wait([cycle / fleet])
    h0 = cycle / fleet
    head = cycle if keep_trips else cyc_e      # 급행 간격을 정하는 주기
    out = []
    for E in range(1, fleet):
        M = fleet - E
        he, hl = head / E, cycle / M
        # 급행 이용 가능 — 두 선택지 중 총시간이 짧은 쪽
        eff = float(np.minimum((_GRID * hl)[:, None], (_GRID * he)[None, :] - gain).mean())
        n_use = w0 - eff
        if pas:
            sq = s1 = wq = w1 = 0.0
            for x in pas:
                h = hp / x['n'] if x['n'] > 0 else None
                aa = -((wait([hl, h]) if h else wait([hl])) - (wait([h0, h]) if h else w0))
                bb = -(wait([hl]) - w0)
                sq += x['vol'] * x['q'] * aa; wq += x['vol'] * x['q']
                s1 += x['vol'] * (1 - x['q']) * bb; w1 += x['vol'] * (1 - x['q'])
            vt = wq + w1
            n_par, n_non = sq / wq, s1 / w1       # ② 병행 대체 가능 · ③ 대체 없음
            sh3 = (1 - p) * w1 / vt
            net = p * n_use + (1 - p) * (sq + s1) / vt
        else:
            n_par = n_non = -(wait([hl]) - w0)
            sh3 = 1 - p
            net = p * n_use + (1 - p) * n_non
        out.append(dict(E=E, M=M, he=he, hl=hl, n_use=n_use, n_par=n_par, n_non=n_non,
                        sh3=sh3, net=net))
    return dict(rows=out, cov=cov, p=p, cyc_e=cyc_e, gain=gain, skip=skip, w0=w0,
                h0=h0, fleet=fleet, cycle=cycle, wait=wait, hp=hp)


# ───────────────────────── 그림 1. 배차 역설 (4개 노선)
fig, axes = plt.subplots(1, 4, figsize=(17.0, 4.5), sharey=True)
BEST = []
for ax, (key, nm, fleet, cycle) in zip(axes, ROUTES):
    m = model(key, fleet, cycle, keep_trips=True)        # 제안인 운영 방식 B 기준
    E = [r['E'] for r in m['rows']]; net = [r['net'] for r in m['rows']]
    ax.axhspan(-20, 0, color=NEG, zorder=0)
    ax.axhline(0, color=INK2, lw=0.9, zorder=2)
    ax.plot(E, net, '-o', color=C2, ms=4.5, lw=1.8, zorder=3)
    r = max(m['rows'], key=lambda x: x['net'])
    BEST.append((nm, m['h0'], r['net']))
    ax.plot([r['E']], [r['net']], 'o', ms=13, mfc='none', mec=INK, mew=2.2, zorder=4)
    dx = 34 if r['E'] <= max(E) * 0.4 else -34
    ax.annotate(f"최선: 급행 {r['E']}대\n{r['net']:+.2f}분", (r['E'], r['net']),
                textcoords='offset points', xytext=(dx, -48), fontsize=9.5,
                color=INK, fontweight='bold', ha='center', linespacing=1.4,
                arrowprops=dict(arrowstyle='-', color=INK, lw=1.1))
    ax.set_title(f'{nm}번   관측 {fleet}대 · 왕복 {cycle:.0f}분\n현행 간격 {m["h0"]:.1f}분',
                 fontsize=10.5, color=INK, linespacing=1.5, pad=9)
    ax.set_xlabel('급행으로 돌리는 차량 수(대)', fontsize=9.5, color=INK2)
    ax.set_ylim(-20, 3.5); ax.set_xlim(0.3, max(E) + 0.7)
    ax.set_xticks(E if len(E) <= 10 else [e for e in E if e % 2 == 0])
    ax.grid(axis='y', color=GRID, lw=0.7); ax.set_axisbelow(True)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=9, colors=INK2)
axes[0].set_ylabel('통행당 평균 순효과(분)', fontsize=9.5, color=INK2)
axes[0].text(0.03, 0.06, '붉은 영역 = 평균이 음수', transform=axes[0].transAxes,
             fontsize=8.8, color=C2, va='bottom')
fig.suptitle('배차 역설 — 최선값의 순서가 현행 배차 순서와 정확히 일치한다. 네 노선 모두 음수이고, 350번이 가장 덜 나쁘다',
             fontsize=13.0, color=INK, y=1.0, fontweight='bold')
fig.text(0.5, -0.115,
         '무증차 재편, 운영 방식 B(왕복 횟수 유지). 급행 이용 가능 통행은 완행과 급행 중 '
         f'총시간이 짧은 쪽을 타고, 차내 단축은 급행을 실제로 탄 경우에만 생긴다. 정차 1회당 손실 {a.T:.0f}초·'
         f'평균 통행 = 편도의 {a.trip*100:.0f}% 가정 — 이 가정이 부호를 가른다.\n'
         '병행 노선 보완은 350번에만 적용해 이 도면에서는 뺐다. 왕복·관측대수는 모두 x_peak.py 재계산값 — '
         '88-1·380은 10-07, 55는 10-12, 350은 10-14 첨두. 380은 완주 차량이 없어 통과 속도 환산값이다.',
         ha='center', fontsize=8.5, color=INK2, linespacing=1.7)
fig.tight_layout()
fig.savefig('figures/배차역설_4개노선.png', dpi=190, bbox_inches='tight', facecolor='white')
print('-> figures/배차역설_4개노선.png')

# ───────────────────────── 그림 2. 350 무증차 재편 — 운영 방식 B(왕복 횟수 유지)
mB = model('350', 19, 150.0, keep_trips=True, parallel=True)    # 제안: 회차 여유 + 병행 반영
mA = model('350', 19, 150.0, parallel=True)                     # 대안: 쉬지 않고 더 돈다
rows = mB['rows']
E = [r['E'] for r in rows]
r5 = next(r for r in rows if r['E'] == 5)

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.8, 4.6),
                              gridspec_kw=dict(width_ratios=[1.5, 1]))

ax.axhline(0, color=INK2, lw=0.9)
ax.plot(E, [r['n_use'] for r in rows], '-o', color=C1, ms=4.5, lw=1.9,
        label=f"① 급행 이용 가능 ({mB['p']*100:.1f}%)")
ax.plot(E, [r['n_par'] for r in rows], '-D', color=C3, ms=4.0, lw=1.7,
        label=f"② 통과 · 병행 대체 가능 ({(1-mB['p'])*(1-r5['sh3']/(1-mB['p']))*100:.1f}%)")
ax.plot(E, [r['n_non'] for r in rows], '-s', color=C2, ms=4.5, lw=1.9,
        label=f"③ 통과 · 대체 없음 ({r5['sh3']*100:.1f}%)")
ax.plot(E, [r['net'] for r in rows], '-^', color=INK, ms=5.5, lw=2.4, label='전체 평균')
ax.set_title('350번 무증차 — 관측 19대를 급행과 완행으로 나눈다', fontsize=11, color=INK, pad=9)
ax.set_xlabel('급행으로 돌리는 차량 수(대)', fontsize=9.5, color=INK2)
ax.set_ylabel('통행당 순효과(분)', fontsize=9.5, color=INK2)
ax.set_xticks([e for e in E if e % 2 == 1]); ax.set_ylim(-9.5, 5.6)
ax.grid(axis='y', color=GRID, lw=0.7); ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.tick_params(labelsize=9, colors=INK2)

axr = ax.twinx()
axr.plot(E, [r['he'] for r in rows], ls=(0, (4, 3)), color='#9a9a97', lw=1.5, marker='D', ms=3.0,
         label='급행 간격(오른쪽 축)')
axr.set_ylim(0, 160); axr.set_ylabel('급행 간격(분)', fontsize=9.5, color=INK2)
axr.tick_params(labelsize=9, colors=INK2); axr.spines['top'].set_visible(False)

ax.axvline(5, color=INK2, lw=1.1, ls=(0, (2, 2)), zorder=1)
ax.text(5.35, 5.35, f"제안: 급행 5대 · 간격 {r5['he']:.1f}분 · 평균 {r5['net']:+.3f}분",
        fontsize=9.5, color=INK, fontweight='bold', va='top', ha='left')

h1, l1 = ax.get_legend_handles_labels(); h2, l2 = axr.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=8.5, frameon=False,
          loc='lower left', bbox_to_anchor=(0.02, 0.02))

# 오른쪽 — 급행이 아낀 시간을 어디에 쓰는가: 효과 대 탄소
rA = next(r for r in mA['rows'] if r['E'] == 5)
labs = ['A. 쉬지 않고\n더 돈다', 'B. 회차 여유로 둔다\n(제안)']
eff = [rA['net'], r5['net']]
co2 = [0.4, -3.7]          # x_carbon.py, e=1.1·13t·30km/h, 전일 전면 시행 기준
x = np.arange(2); w = 0.34

ax2.bar(x - w/2, eff, width=w, color=C1, label='통행당 평균 순효과(분)')
ax2.bar(x + w/2, co2, width=w, color=C3, label='일일 탄소 변화(%) — 전일 전면 시행')
for xi, v in zip(x - w/2, eff):
    ax2.text(xi, v + (0.12 if v >= 0 else -0.42), f'{v:+.3f}분', ha='center',
             fontsize=9.5, fontweight='bold', color=INK)
for xi, v in zip(x + w/2, co2):
    ax2.text(xi, v + (0.12 if v >= 0 else -0.45), f'{v:+.1f}%', ha='center',
             fontsize=9.5, fontweight='bold', color=INK)
ax2.axhline(0, color=INK2, lw=0.9)
ax2.set_xticks(x); ax2.set_xticklabels(labs, fontsize=9.3, color=INK2, linespacing=1.5)
ax2.set_ylim(-4.6, 2.2)
# 분과 %는 단위가 달라 막대 높이를 서로 비교해서는 안 된다
ax2.set_ylabel('왼쪽 막대 = 분 · 오른쪽 막대 = %  (서로 다른 단위)', fontsize=8.6, color=INK2)
ax2.set_title('아낀 23분을 어디에 쓰는가', fontsize=11, color=INK, pad=9)
ax2.legend(fontsize=8.3, frameon=False, loc='lower left')
ax2.grid(axis='y', color=GRID, lw=0.7); ax2.set_axisbelow(True)
for sp in ('top', 'right', 'bottom'): ax2.spines[sp].set_visible(False)
ax2.tick_params(labelsize=9, colors=INK2, bottom=False)

fig.suptitle('350번 무증차 재편 — 평균은 0 근처이고, 이득과 손해가 집단별로 갈린다',
             fontsize=13.0, color=INK, y=1.0, fontweight='bold')
fig.text(0.5, -0.135,
         "350번 관측 19대·왕복 150분(10-14 첨두 실측, 완주 13대). 급행 왕복 127분. "
         f"정차 1회당 손실 {a.T:.0f}초·평균 통행 = 편도의 {a.trip*100:.0f}%·병행 노선 1개 {mB['hp']:.0f}분 가정.\n"
         "급행 이용 가능 통행은 완행과 급행 중 총시간이 짧은 쪽을 타고, 차내 단축은 급행을 실제로 탄 경우에만 생긴다. "
         f"집단 비중은 승하차 기록으로 가중한 모형 비중이며(커버 {mB['cov']*100:.1f}%의 제곱, 출발·도착 독립 가정)\n"
         "실제 수혜·피해 인구 비율이 아니다. 정차손실을 25초로 보면 전체 평균이 양수로 바뀐다 — 12조건 민감도는 본문 §7-3. "
         "탄소는 주행거리와 정차 횟수를 함께 센 전일 기준 값이다(x_carbon.py, e=1.1·13t·30km/h). 첨두 2시간 환산은 -0.53%.",
         ha='center', fontsize=8.5, color=INK2, linespacing=1.7)
fig.tight_layout()
fig.savefig('figures/무증차_350.png', dpi=190, bbox_inches='tight', facecolor='white')
print('-> figures/무증차_350.png')
