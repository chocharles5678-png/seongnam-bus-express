"""기준 노선과 공유 구간이 연속인가 — 정류소ID 기준 전수 비교
사용: python scripts/seongnam/x_corridor.py 350 [--detail 357,330,220] [--min 10]
연속 = 기준 노선 순서상 끊기지 않고 이어지는 공유 정류소. 상대 노선에서도 연속인지 따로 본다.
데이터: express_bus/clean/{노선,노선정류장}.csv
"""
import csv, io, sys, argparse, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument('route', nargs='?', default='350')
ap.add_argument('--detail', default='357,330,220')
ap.add_argument('--min', type=int, default=10, help='최장 연속이 이 값 이상인 노선만 표에 싣는다')
a = ap.parse_args()

rt = {r['노선ID']: r for r in csv.DictReader(open('express_bus/clean/노선.csv', encoding='utf-8-sig'))}
rs = collections.defaultdict(list)
for r in csv.DictReader(open('express_bus/clean/노선정류장.csv', encoding='utf-8-sig')):
    rs[r['노선ID']].append(r)
seq = {k: [s['정류장ID'] for s in sorted(v, key=lambda s: int(s['순서']))] for k, v in rs.items()}
name = {k: v['노선명'] for k, v in rt.items()}

ids = [k for k, v in rt.items() if v['노선명'] == a.route]
if not ids: sys.exit(f'{a.route}번을 찾지 못했다')
base = ids[0]
B = seq[base]
Bset = set(B)
m = rt[base]
print(f"■ 기준 {a.route}번 ({base}) {m['노선유형']} / {m['기점']} ~ {m['종점']} / 정류소 {len(B)}개"
      f" (고유 {len(Bset)}개) / 배차 최소 {m['첨두배차_분']}분 최대 {m['비첨두배차_분']}분\n")


def runs(mask):
    """True가 이어지는 구간 [(시작idx, 길이), ...]"""
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]: j += 1
            out.append((i, j - i)); i = j
        else: i += 1
    return out


def gap_in_other(stops, other):
    """기준 노선의 연속 공유 구간이 상대 노선에서도 연속인가 — 위치 간 최대 칸수"""
    pos = {}
    for i, s in enumerate(other):
        pos.setdefault(s, []).append(i)
    p = [pos[s][0] for s in stops if s in pos]
    if len(p) < 2: return None
    return max(abs(p[i + 1] - p[i]) for i in range(len(p) - 1))


rows = []
for rid, S in seq.items():
    if rid == base: continue
    shared = Bset & set(S)
    if not shared: continue
    rr = runs([s in shared for s in B])
    top = max(rr, key=lambda x: x[1])
    rows.append((top[1], len(shared), len(S), rid, rr))
rows.sort(reverse=True)

print(f'■ {a.route}번과 공유 구간이 연속 {a.min}정차 이상인 노선')
print(f"{'노선':>6} {'유형':<10} {'최장연속':>7} {'공유':>5} {'연속덩어리':>10} {'상대정류소':>7}  기점~종점")
hit = [r for r in rows if r[0] >= a.min]
for top, nsh, nst, rid, rr in hit:
    v = rt[rid]
    chunks = sum(1 for _, L in rr if L >= 3)
    print(f"{v['노선명']:>6} {v['노선유형'].replace('시내버스',''):<10} {top:>7} {nsh:>5} {chunks:>10} {nst:>7}  "
          f"{v['기점'][:10]}~{v['종점'][:10]}")
if not hit: print('  없음')
print(f'\n  공유 정류소가 1개 이상인 노선 {len(rows)}개 중 {len(hit)}개가 연속 {a.min}정차 이상')

for t in [x.strip() for x in a.detail.split(',') if x.strip()]:
    tid = next((k for k, v in rt.items() if v['노선명'] == t), None)
    if tid is None or tid not in seq:
        print(f'\n■ {t}번 — 자료 없음'); continue
    S = seq[tid]; v = rt[tid]
    shared = Bset & set(S)
    mask = [s in shared for s in B]
    rr = runs(mask)
    print(f"\n■ {a.route} × {t}  ({v['노선유형']} / {v['기점']}~{v['종점']} / 정류소 {len(S)}개"
          f" / 배차 최소 {v['첨두배차_분']}분)")
    print(f"  기점 동일: {'예' if rt[base]['기점'] == v['기점'] else '아니오'}"
          f"  / 종점 동일: {'예' if rt[base]['종점'] == v['종점'] else '아니오'}")
    print(f'  공유 정류소 {len(shared)}개 ({len(shared)/len(Bset)*100:.0f}% of {a.route} 고유 {len(Bset)})')
    if not rr:
        print('  연속 구간 없음'); continue
    print(f'  연속 덩어리 {len(rr)}개 — 길이 {sorted((L for _,L in rr), reverse=True)}')
    bar = ''.join('#' if x else '.' for x in mask)
    for i in range(0, len(bar), 60): print('  ' + bar[i:i + 60])
    print(f'  (# = {t}번과 공유, 왼쪽부터 {a.route}번 순서 1~{len(B)})')
    for st, L in sorted(rr, key=lambda x: -x[1])[:3]:
        if L < 3: continue
        stops = B[st:st + L]
        g = gap_in_other(stops, S)
        nmS = {s['정류장ID']: s['정류장명'] for s in rs[base]}
        print(f'    순서 {st+1}~{st+L} ({L}정차) {nmS.get(stops[0],"?")} → {nmS.get(stops[-1],"?")}'
              f' / {t}번에서의 위치 최대간격 {g}칸' + ('  ← 상대 노선에서도 연속' if g == 1 else ''))
