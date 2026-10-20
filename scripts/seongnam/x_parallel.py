# -*- coding: utf-8 -*-
"""통과 지점의 손해를 병행 노선으로 가중한다 — 방향·구간이 맞는 병행만 센다
사용: python scripts/seongnam/x_parallel.py [--hp 20] [--minrun 3]

왜 필요한가
  급행이 건너뛴 지점의 승객이 완행 간격 확대를 그대로 뒤집어쓴다고 보면 손해가 과대평가된다.
  그 정류장에 다른 노선이 서면 그쪽을 탈 수 있다. 그러나 "같은 정류장에 선다"가
  "내 목적지로 간다"는 뜻은 아니다. 두 단계로 걸러낸다.

  1단계 방향·구간  기준 노선 순서상 연속 N정차 이상을 공유하고, 그 구간이 상대 노선에서도
                  연속인 노선만 병행으로 센다. 상·하행은 정류소ID가 달라 자동으로 분리된다.
  2단계 목적지     그래도 병행이 가는 곳은 공유 구간까지다. 그 지점에서 하류 목적지 중
                  병행이 닿는 비중을 q로 재고, (1-q)는 대체 수단이 없는 것으로 둔다.

  손해 = q × (완행+병행 합산 대기 증가) + (1-q) × (완행 단독 대기 증가)

  1단계만 하고 q를 빼면 "완행을 없앨수록 좋다"는 결론이 나온다. 병행을 완전 대체재로
  취급한 결과이고, 조건부 분해로 막는다.
"""
import csv, io, json, sys, argparse, collections, statistics
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument('--route', default='350')
ap.add_argument('--fleet', type=int, default=19)
ap.add_argument('--cycle', type=float, default=150.0)
ap.add_argument('--T', type=float, default=20, help='정차 1회당 손실시간(초) — 가정값')
ap.add_argument('--trip', type=float, default=1/3, help='평균 통행 길이 = 편도의 이 비율 (가정)')
ap.add_argument('--hp', type=float, default=20.0, help='병행 노선 1개의 배차 간격(분) — 가정값')
ap.add_argument('--minrun', type=int, default=3, help='병행으로 셀 최소 연속 공유 정차 수')
ap.add_argument('--turn', type=int, default=45,
                help='회차점 순서. 상행은 1..turn, 하행은 turn..끝이다. 회차점은 종점이자 '
                     '주요 목적지이므로 상행 승객의 목적지 집합에 포함해야 한다')
ap.add_argument('--maxlocal', type=float, default=2.0,
                help='완행 간격 상한 = 현행의 이 배수. 넘기면 모퉁이 해가 나온다')
ap.add_argument('--detail', type=int, default=0, help='통과 지점 상세를 상위 N개까지 출력한다')
ap.add_argument('--keep-trips', action='store_true',
                help='운영 방식 B — 급행이 아낀 시간을 회차 여유로 두고 왕복 횟수를 유지한다. '
                     '급행 간격이 cycle/E가 되어 넓어지는 대신 총 주행거리가 늘지 않는다. '
                     '본문 제안은 B다')
a = ap.parse_args()

RT = {r['노선ID']: r for r in csv.DictReader(open('express_bus/clean/노선.csv', encoding='utf-8-sig'))}
rs = collections.defaultdict(list)
for r in csv.DictReader(open('express_bus/clean/노선정류장.csv', encoding='utf-8-sig')):
    rs[r['노선ID']].append(r)
SEQ = {k: [s['정류장ID'] for s in sorted(v, key=lambda s: int(s['순서']))] for k, v in rs.items()}
base = next(k for k, v in RT.items() if v['노선명'] == a.route)
B = SEQ[base]
Bset = set(B)


def runs(mask):
    """True가 이어지는 구간 [(시작idx, 길이), ...]"""
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            out.append((i, j - i))
            i = j
        else:
            i += 1
    return out


def cont_in(stops, other):
    """공유 구간이 상대 노선에서도 연속인가 — 위치 간 최대 칸수"""
    pos = {}
    for i, s in enumerate(other):
        pos.setdefault(s, []).append(i)
    p = [pos[s][0] for s in stops if s in pos]
    return max(abs(p[i + 1] - p[i]) for i in range(len(p) - 1)) if len(p) >= 2 else 99


cov = collections.defaultdict(list)          # 기준 노선 순서 i -> [(노선명, 구간시작, 길이)]
for rid, S in SEQ.items():
    if rid == base:
        continue
    sh = Bset & set(S)
    if not sh:
        continue
    for st, L in runs([s in sh for s in B]):
        if L >= a.minrun and cont_in(B[st:st + L], S) <= 1:
            for i in range(st, st + L):
                cov[i].append((RT[rid]['노선명'], st, L))

R = list(csv.DictReader(open(f'data/express_{a.route}.csv', encoding='utf-8-sig')))
w, nm = {}, {}
for r in R:
    for o in r['순서'].split(','):
        w[int(o) - 1] = float(r['왕복일평균'])
        nm[int(o) - 1] = r['정류소명']


def down(i):
    """i 이후의 같은 방향 목적지 순서"""
    return list(range(i + 1, a.turn)) if i < a.turn else list(range(i + 1, len(B)))


PT = []
for r in R:
    ords = [int(x) - 1 for x in r['순서'].split(',')]
    qs, nsx = [], []
    for i in ords:
        d = down(i)
        tot = sum(w[j] for j in d if j in w)
        if not d or tot <= 0:
            continue
        ok = set()
        for _, st, L in cov[i]:
            ok |= {j for j in d if st <= j < st + L}
        qs.append(sum(w[j] for j in ok if j in w) / tot)
        nsx.append(len(cov[i]))
    PT.append(dict(name=r['정류소명'], k=len(ords), vol=float(r['왕복일평균']),
                   base=(r['급행정차'] == '정차'),
                   q=statistics.mean(qs) if qs else 1.0,
                   n=statistics.mean(nsx) if nsx else 0))

NA = sum(x['k'] for x in PT)
TOT = sum(x['vol'] for x in PT)
H0 = a.cycle / a.fleet

# 도면 생성기(x_report_fig350.py)가 같은 q를 쓰도록 내보낸다. 계산을 두 벌 두지 않는다.
QOUT = f'data/par_q_{a.route}.json'
json.dump(dict(route=a.route, turn=a.turn, minrun=a.minrun, hp=a.hp,
               stops=[{k: x[k] for k in ('name', 'k', 'vol', 'base', 'q', 'n')} for x in PT]),
          io.open(QOUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def p_express(a_loc, b_exp, S):
    """P(급행 선택) = P(급행 잔여대기 − S < 완행 잔여대기), 둘 다 균등분포

    간편식 (a/2 + S)/b 는 a+S <= b 에서만 맞는다. 급행 간격이 좁아져 그 조건이
    깨지면 적분이 포화되므로 일반식을 쓴다. 350번은 급행 9대부터 깨진다.
    """
    if S >= b_exp:
        return 1.0
    if a_loc + S <= b_exp:
        return (a_loc / 2 + S) / b_exp
    c = b_exp - S
    return ((c * c / 2 + S * c) / b_exp + (a_loc - c)) / a_loc


def wait(hs, H=1800):
    arr = np.sort(np.concatenate([np.arange(0, H, h) for h in hs if h and h > 0]))
    g = np.diff(arr)
    g = g[g > 1e-9]
    return (g ** 2).sum() / (2 * g.sum())


_G = (np.arange(1500) + 0.5) / 1500.0
W0 = wait([H0])


def evaluate(stopset, E):
    """세 집단의 1통행당 효과와 전체 평균. 대기는 선택한 경로의 것 하나만 센다"""
    NS = sum(x['k'] for x in PT if x['name'] in stopset)
    SKIP = NA - NS
    p = sum(x['vol'] for x in PT if x['name'] in stopset) / TOT
    P_USE = p * p                                # 출발·도착 모두 급행 정차 (독립 가정)
    GAIN = SKIP / 2 * a.T / 60 * a.trip
    hl = a.cycle / (a.fleet - E)
    # 차내 단축(GAIN)은 실제 주행이 빨라진 결과라 어느 방식이든 같다.
    # 급행 간격만 달라진다 — B는 아낀 시간을 회차 여유로 쓰므로 완행과 같은 주기로 돈다.
    he = (a.cycle if a.keep_trips else a.cycle - SKIP * a.T / 60) / E
    # 1. 급행 이용 가능 — 완행 대기와 (급행 대기 - 차내단축) 중 작은 쪽
    g1 = W0 - float(np.minimum((_G * hl)[:, None], (_G * he)[None, :] - GAIN).mean())
    sq = s1 = wq = w1 = 0.0
    for x in PT:
        if x['name'] in stopset:
            continue
        hp = a.hp / x['n'] if x['n'] > 0 else None
        aa = -((wait([hl, hp]) if hp else wait([hl])) - (wait([H0, hp]) if hp else wait([H0])))
        bb = -(wait([hl]) - wait([H0]))
        sq += x['vol'] * x['q'] * aa
        wq += x['vol'] * x['q']
        s1 += x['vol'] * (1 - x['q']) * bb
        w1 += x['vol'] * (1 - x['q'])
    VT = wq + w1
    return dict(E=E, nstop=len(stopset), ncall=NS, cover=p, GAIN=GAIN, he=he, hl=hl,
                g1=g1, g2=(sq / wq if wq > 1e-9 else 0.0),
                g3=(s1 / w1 if w1 > 1e-9 else 0.0),
                sh3=((1 - P_USE) * w1 / VT if VT > 0 else 0.0),
                tot=(P_USE * g1 + (1 - P_USE) * (sq + s1) / VT if VT > 0 else P_USE * g1),
                pch=p_express(hl, he, GAIN))


BASE = {x['name'] for x in PT if x['base']}
pas = [x for x in PT if not x['base']]
qw = sum(x['vol'] * x['q'] for x in pas) / sum(x['vol'] for x in pas)
print(f'■ {a.route}번 — 통과 지점 {len(pas)}개 / 병행 기준: 연속 {a.minrun}정차 이상 +'
      f' 상대 노선에서도 연속')
print(f'  병행 노선 수   중앙값 {statistics.median([x["n"] for x in pas]):.0f}'
      f'  최소 {min(x["n"] for x in pas):.0f}  최대 {max(x["n"] for x in pas):.0f}'
      f'  0개 지점 {sum(1 for x in pas if x["n"] == 0)}개')
print(f'  목적지 대체 비중 q   이용량 가중 {qw:.3f}'
      f'  중앙값 {statistics.median([x["q"] for x in pas]):.3f}'
      f'  최소 {min(x["q"] for x in pas):.3f}')
print(f'  → 통과 지점 이용의 {(1 - qw) * 100:.1f}%는 병행으로 대체되지 않는다')

if a.detail:
    t1q = sum(x['vol'] * (1 - x['q']) for x in pas)
    print(f'\n■ 대체 없는 이용량이 큰 통과 지점 상위 {a.detail}개 (합계의 몫)')
    print(f"{'정류소':28}{'병행수':>7}{'q':>7}{'일평균':>9}{'(1-q)×이용':>12}{'몫':>7}")
    for x in sorted(pas, key=lambda x: -x['vol'] * (1 - x['q']))[:a.detail]:
        print(f'{x["name"][:26]:28}{x["n"]:>7.0f}{x["q"]:>7.2f}{x["vol"]:>9.0f}'
              f'{x["vol"] * (1 - x["q"]):>12.0f}{x["vol"] * (1 - x["q"]) / t1q * 100:>6.1f}%')
    print(f'\n■ q 가 가장 낮은 통과 지점 상위 {a.detail}개 — 병행이 가는 곳이 가장 좁다')
    print(f"{'정류소':28}{'병행수':>7}{'q':>7}{'일평균':>9}")
    for x in sorted(pas, key=lambda x: x['q'])[:a.detail]:
        print(f'{x["name"][:26]:28}{x["n"]:>7.0f}{x["q"]:>7.2f}{x["vol"]:>9.0f}')
    print(f'\n■ 병행이 1개뿐인 통과 지점')
    print(f"{'정류소':28}{'병행수':>7}{'q':>7}{'일평균':>9}")
    for x in sorted([y for y in pas if y['n'] <= 1], key=lambda x: -x['vol']):
        print(f'{x["name"][:26]:28}{x["n"]:>7.0f}{x["q"]:>7.2f}{x["vol"]:>9.0f}')

print(f'\n■ 집단별 손익 (병행 1개 {a.hp:.0f}분 가정 · 현행 대기 {W0:.2f}분 ·'
      f' 기본 정차표 {len(BASE)}지점)')
print(f"{'급행':>4}{'완행간격':>9}{'급행간격':>9}{'급행탑승':>9}"
      f"{'①이용가능':>11}{'②통과·대체':>12}{'③통과·대체없음':>15}{'③비중':>8}{'평균':>9}")
for E in range(1, a.fleet):
    r = evaluate(BASE, E)
    print(f'{E:>4}{r["hl"]:>8.1f}분{r["he"]:>8.1f}분{r["pch"] * 100:>8.0f}%'
          f'{r["g1"]:>+10.2f}분{r["g2"]:>+11.2f}분{r["g3"]:>+14.2f}분'
          f'{r["sh3"] * 100:>7.1f}%{r["tot"]:>+8.3f}분')

LIM = a.maxlocal * H0
EMAX = a.fleet - int(np.ceil(a.cycle / LIM))
ORD = {'대체없는 이용량': lambda x: -x['vol'] * (1 - x['q']) / x['k'],
       'q 낮은 순': lambda x: (x['q'], -x['vol']),
       '이용량 많은 순': lambda x: -x['vol'] / x['k'],
       '병행 적은 순': lambda x: (x['n'], -x['vol'])}
print(f'\n■ 제한 탐색 — 급행 1~{EMAX}대 × 정차 추가 0~{len(pas)} × 정렬 {len(ORD)}종')
print(f'  유효범위: 완행 간격 ≤ {LIM:.1f}분 (현행의 {a.maxlocal:g}배). 넘기면 병행을 완전'
      f' 대체재로 취급한 모퉁이 해가 나온다')
allr, uniq, tabs = [], set(), set()
for lab, key in ORD.items():
    cand = sorted(pas, key=key)
    for E in range(1, EMAX + 1):
        for k in range(len(cand) + 1):
            ss = BASE | {x['name'] for x in cand[:k]}
            r = evaluate(ss, E)
            r['ord'] = lab
            allr.append(r)
            uniq.add((E, frozenset(ss)))
            tabs.add(frozenset(ss))
good = [r for r in allr if min(r['g1'], r['g2'], r['g3']) >= -1e-9]
print(f'  조건 {len(allr):,}개 = 고유 설계 {len(uniq):,}개 + 중복 {len(allr)-len(uniq):,}개'
      f'  (고유 정차표 {len(tabs)}개)')
print(f'  모든 집단이 손해를 안 보는 설계: {len(good)}개')
print(f'  ※ 가능한 정차표 조합은 2^{len(pas)} ≈ {2.0**len(pas):.2g}개다. 네 정렬 기준을 따라간')
print(f'    {len(tabs)}개({len(tabs)/2.0**len(pas)*100:.1g}%)만 본 제한 탐색이므로 불가능성 증명이 아니다.')

print('\n■ 3번 집단(대체 없음)의 손해를 묶었을 때 얻을 수 있는 평균')
print(f"{'③ 손해 상한':>12}{'급행':>5}{'지점':>5}{'커버':>7}{'③비중':>7}"
      f"{'①':>8}{'②':>8}{'③':>8}{'평균':>9}")
for cap in (0.0, -0.25, -0.5, -1.0, -1.5, -2.0, None):
    f = allr if cap is None else [r for r in allr if r['g3'] >= cap - 1e-9]
    if not f:
        continue
    b = max(f, key=lambda r: r['tot'])
    lab = '제약 없음' if cap is None else f'{cap:.2f}분'
    print(f"{lab:>12}{b['E']:>5}{b['nstop']:>5}{b['cover'] * 100:>6.1f}%"
          f"{b['sh3'] * 100:>6.1f}%{b['g1']:>+7.2f}분{b['g2']:>+7.2f}분"
          f"{b['g3']:>+7.2f}분{b['tot']:>+8.3f}분")

print(f'\n※ 가정: 정차손실 {a.T:.0f}초 · 평균 통행 = 편도의 {a.trip * 100:.0f}% ·'
      f' 출발·도착 독립 · 병행 1개 {a.hp:.0f}분')
print('※ 병행 노선의 차내 시간은 기준 노선과 같다고 두었다. 경로가 다르므로 실제로는 더'
      ' 걸릴 수 있어 손해는 여기 값보다 크다.')
