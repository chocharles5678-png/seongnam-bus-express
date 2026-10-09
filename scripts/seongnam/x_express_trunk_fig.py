"""시내버스 급행 재편 노선도 — x_express_trunk.py 결과(data/express_<노선>.csv)를 그린다
사용: python scripts/seongnam/x_express_trunk_fig.py 51
"""
import csv, io, sys, math, collections
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
plt.rcParams['font.family'] = 'Malgun Gothic'; plt.rcParams['axes.unicode_minus'] = False

name = sys.argv[1] if len(sys.argv) > 1 else '51'
TITLE = {'51': '51번 (사기막골 ↔ 모란역 ↔ 야탑역 ↔ 서현역 ↔ 서울대병원)',
         '55': '55번 (판교테크노밸리 ↔ 야탑역 ↔ 모란역 ↔ 신구대 ↔ 을지대 ↔ 남위례)'}
C_STOP, C_PASS, C_P20, C_UNI = '#C8102E', '#9AA5B1', '#1E6FBF', '#14866D'

rows = list(csv.DictReader(open(f'data/express_{name}.csv', encoding='utf-8-sig')))
stopxy = {r['정류장ID']: (float(r['경도']), float(r['위도']))
          for r in csv.DictReader(open('express_bus/clean/정류장.csv', encoding='utf-8-sig')) if r['경도']}
rt = {r['노선ID']: r for r in csv.DictReader(open('express_bus/clean/노선.csv', encoding='utf-8-sig'))}
rs = collections.defaultdict(list)
for r in csv.DictReader(open('express_bus/clean/노선정류장.csv', encoding='utf-8-sig')): rs[r['노선ID']].append(r)
rid = [k for k, v in rt.items() if v['노선명'] == name and v['노선유형'] == '일반형시내버스'][0]
seq = sorted(rs[rid], key=lambda s: int(s['순서']))
alloc = rt[rid]['첨두배차_분']   # 의미: 평일 최소 배차(분)
info = {r['정류소명']: r for r in rows}

fig = plt.figure(figsize=(17, 8.6))
gs = fig.add_gridspec(2, 2, width_ratios=[0.78, 1], hspace=0.45, wspace=0.20)

# ── (좌) 노선도
ax = fig.add_subplot(gs[:, 0])
px = [stopxy[s['정류장ID']][0] for s in seq if s['정류장ID'] in stopxy]
py = [stopxy[s['정류장ID']][1] for s in seq if s['정류장ID'] in stopxy]
ax.plot(px, py, '-', color='#CBD2D9', lw=2.2, zorder=1, solid_capstyle='round')
for r in rows:
    pts = [stopxy[i] for i in r['정류소ID'].split() if i in stopxy]
    if not pts: continue
    u = float(r['왕복일평균']); on = r['급행정차'] == '정차'
    c = C_UNI if r['사유'] == '대학' else (C_P20 if r['사유'] == '20대거점' else C_STOP)
    s = 20 + (u ** 0.62) * 1.5
    for x, y in pts:
        ax.scatter(x, y, s=s if on else 22, c=c if on else 'none',
                   edgecolors=c if on else C_PASS, linewidths=1.6 if on else 1.0,
                   alpha=0.9 if on else 0.75, zorder=3 if on else 2)
cx, cy = sum(px) / len(px), sum(py) / len(py)
ax.set_aspect(1 / math.cos(math.radians(cy)))
ax.margins(0.26)
y0, y1 = ax.get_ylim(); ax.set_ylim(y0, y1 + (y1 - y0) * 0.16)   # 라벨이 제목을 침범하지 않게 여백
fig.canvas.draw()                                                 # transData 확정 — 아래 충돌 검사가 쓴다

lab = sorted([r for r in rows if r['급행정차'] == '정차'], key=lambda r: -float(r['왕복일평균']))[:7]
placed = []          # 라벨의 최종 중심 (화면 pt) — 오프셋이 아니라 이것으로 겹침을 본다
PTPX = fig.dpi / 72
for r in lab:
    i = r['정류소ID'].split()[0]
    if i not in stopxy: continue
    x, y = stopxy[i]
    ax0, ay0 = ax.transData.transform((x, y)) / PTPX              # 앵커의 화면 좌표(pt)
    dx, dy = x - cx, y - cy; mm = math.hypot(dx, dy) or 1
    base = (dx / mm * 54, dy / mm * 54)
    half = len(r['정류소명'][:14]) * 4.6 + 6                        # 라벨 반폭(pt) 근사
    best = None
    for k in range(14):                                           # 기본 위치에서 점점 벌려가며 빈자리를 찾는다
        for sgn in (1, -1):
            ox, oy = base[0], base[1] + sgn * k * 24
            lx, ly = ax0 + ox, ay0 + oy
            bad = sum(1 for qx, qy, qh in placed
                      if abs(lx - qx) < half + qh and abs(ly - qy) < 23)
            if best is None or bad < best[0]: best = (bad, ox, oy, lx, ly)
            if bad == 0: break
        if best[0] == 0: break
    _, ox, oy, lx, ly = best
    placed.append((lx, ly, half))
    ax.annotate(r['정류소명'][:14], (x, y), textcoords='offset points', xytext=(ox, oy), fontsize=8.8,
                ha='center', va='center', color='#1F2933', weight='bold', zorder=5,
                bbox=dict(boxstyle='round,pad=0.26', fc='white', ec='#CBD2D9', alpha=0.93, lw=0.8),
                arrowprops=dict(arrowstyle='-', color='#9AA5B1', lw=0.9, shrinkA=0, shrinkB=4))
ax.set_title(f'{TITLE.get(name, name)}\n급행 정차역 (원 크기 = 일평균 이용)', fontsize=12, weight='bold', pad=16)
ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_color('#E4E7EB')
ax.legend(handles=[Line2D([], [], marker='o', ls='', mfc=C_STOP, mec=C_STOP, ms=9, label='급행 정차 (거점·환승)'),
                   Line2D([], [], marker='o', ls='', mfc=C_UNI, mec=C_UNI, ms=9, label='급행 정차 (대학)'),
                   Line2D([], [], marker='o', ls='', mfc=C_P20, mec=C_P20, ms=9, label='급행 정차 (20대 거점)'),
                   Line2D([], [], marker='o', ls='', mfc='none', mec=C_PASS, ms=7, label='급행 통과')],
          loc='lower center', frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.11), ncol=4)

# ── (우상) 전후 비교
ax2 = fig.add_subplot(gs[0, 1]); n = len(seq)
for k, s in enumerate(seq):
    r = info.get(s['정류장명'])
    ax2.scatter(k, 1, s=22, c='#52606D', zorder=2)
    if r and r['급행정차'] == '정차':
        ax2.scatter(k, 0, s=38, c=(C_UNI if r['사유'] == '대학' else (C_P20 if r['사유'] == '20대거점' else C_STOP)), zorder=2)
ax2.plot([0, n - 1], [1, 1], color='#CBD2D9', lw=1.4, zorder=1)
ax2.plot([0, n - 1], [0, 0], color='#CBD2D9', lw=1.4, zorder=1)
ns = sum(1 for s in seq if info.get(s['정류장명'], {}).get('급행정차') == '정차')
ax2.set_yticks([1, 0]); ax2.set_yticklabels([f'기존 (모두 정차)\n{n}회', f'급행\n{ns}회'], fontsize=10)
ax2.set_xlim(-1, n); ax2.set_ylim(-0.6, 1.6); ax2.set_xticks([])
ax2.set_title(f'왕복 1회 정차 횟수:  {n}회 → {ns}회  (통과 {n-ns}회)', fontsize=11.5, weight='bold', pad=9)
for sp in ax2.spines.values(): sp.set_visible(False)

# ── (우하) 순서별 수요
ax3 = fig.add_subplot(gs[1, 1]); vals, cols = [], []
for s in seq:
    r = info.get(s['정류장명'])
    k = len(r['정류소ID'].split()) if r else 1
    vals.append(float(r['왕복일평균']) / k if r else 0)
    cols.append((C_UNI if r and r['사유'] == '대학' else (C_P20 if r and r['사유'] == '20대거점' else C_STOP)) if r and r['급행정차'] == '정차' else C_PASS)
ax3.bar(range(n), vals, color=cols, width=0.82)
ax3.set_title('정류소 순서별 일평균 이용 — 색칠이 급행 정차', fontsize=11.5, weight='bold', pad=9)
ax3.set_xlabel('노선 진행 순서 →', fontsize=9.5); ax3.set_ylabel('일평균 이용(건)', fontsize=9.5)
ax3.set_xlim(-1, n); ax3.set_xticks([])
ax3.grid(axis='y', color='#F0F2F5', lw=0.9); ax3.set_axisbelow(True)
for sp in ('top', 'right'): ax3.spines[sp].set_visible(False)
for sp in ('left', 'bottom'): ax3.spines[sp].set_color('#CBD2D9')

T = sum(float(r['왕복일평균']) for r in rows)
cov = sum(float(r['왕복일평균']) for r in rows if r['급행정차'] == '정차') / T * 100
fig.text(0.985, 0.015, f'평일 최소배차 {alloc}분 · 급행이 담는 기록 {cov:.0f}%  |  '
         f'자료: 경기도 정류소별 승하차(2026.6), 경기버스정보 노선·정류소, 행정안전부 주민등록(2026.8)',
         ha='right', fontsize=8.5, color='#7B8794')
out = f'figures/급행_{name}_노선도.png'
fig.savefig(out, dpi=170, bbox_inches='tight', facecolor='white')
print(f'-> {out}  (정차 {ns}/{n}, 지점 {len([r for r in rows if r["급행정차"]=="정차"])}, 기록 {cov:.0f}%)')
