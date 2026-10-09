"""성남 정류장별 평일 추정 운행횟수 (경기도_버스노선 조회 API)."""
import csv, io, json, os, sys, time, urllib.parse, urllib.request
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CACHE = os.path.join(PROJ, 'data', 'raw', 'gg_busroute')
os.makedirs(CACHE, exist_ok=True)
BASE = 'https://apis.data.go.kr/6410000/busrouteservice/v2'
KEY = next(l.split('=', 1)[1].strip().strip('"') for l in open(os.path.join(PROJ, '.env'), encoding='utf-8')
           if l.startswith('DATA_GO_KR_KEY='))
PEAK = [(7 * 60, 9 * 60), (17 * 60, 19 * 60)]   # 첨두 07-09, 17-19


def call(op, name, **params):
    path = os.path.join(CACHE, f'{op}_{name}.json')
    if os.path.exists(path):
        return json.load(open(path, encoding='utf-8'))
    q = '&'.join(f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items())
    url = f'{BASE}/{op}?serviceKey={KEY}&format=json&{q}'
    d = json.loads(urllib.request.urlopen(url, timeout=30).read().decode('utf-8'))
    code = d['response']['msgHeader']['resultCode']
    if code not in (0, 4):   # 4 = 결과 없음
        raise RuntimeError(f'{op} {params}: {d["response"]["msgHeader"]}')
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
    time.sleep(0.05)
    return d


def mins(t):
    if not t or ':' not in t:
        return None
    h, m = map(int, t.split(':'))
    return h * 60 + m


def trips(first, last, peak, npeak):
    """한 방향 하루 운행횟수 추정: 첨두는 peak 간격, 나머지는 npeak 간격."""
    f, l = mins(first), mins(last)
    if f is None or l is None:
        return None
    if l < f:
        l += 24 * 60                      # 자정 넘김
    peak = peak or npeak
    npeak = npeak or peak
    if not peak:
        return None
    pm = sum(max(0, min(l, b) - max(f, a)) for a, b in PEAK)
    return 1 + pm / peak + (l - f - pm) / npeak


# 1) 성남 경유 노선
routes = {}
for kw in '0123456789':
    body = call('getBusRouteListv2', f'kw{kw}', keyword=kw)['response']['msgBody'] or {}
    L = body.get('busRouteList', [])
    for r in (L if isinstance(L, list) else [L]):
        if '성남' in (r.get('regionName') or '') or '성남' in r['adminName']:
            routes[r['routeId']] = r
print('성남 경유 노선:', len(routes))

# 2) 노선별 상세 + 정류장 목록 → 3) 정류장별 합산
stop_trips = defaultdict(float)
stop_trips_in = defaultdict(float)     # 도내 노선만 (서울 경유·시외·공항 제외)
stop_routes = defaultdict(set)
no_info = []
for rid, r in routes.items():
    info = call('getBusRouteInfoItemv2', str(rid), routeId=rid)['response']['msgBody']['busRouteInfoItem']
    up = trips(info.get('upFirstTime'), info.get('upLastTime'), info.get('peekAlloc'), info.get('nPeekAlloc'))
    dn = trips(info.get('downFirstTime'), info.get('downLastTime'), info.get('peekAlloc'), info.get('nPeekAlloc'))
    if up is None and dn is None:
        no_info.append(f"{r['routeName']}({r['routeTypeName']})")
        continue
    up = up or dn; dn = dn or up
    body = call('getBusRouteStationListv2', str(rid), routeId=rid)['response']['msgBody'] or {}
    S = body.get('busRouteStationList', [])
    intra = ('서울' not in (info.get('regionName') or '')
             and not any(k in info['routeTypeName'] for k in ('시외', '공항')))
    for s in (S if isinstance(S, list) else [S]):
        t = up if s['stationSeq'] < s.get('turnSeq', 10 ** 9) else dn
        stop_trips[s['stationId']] += t
        if intra:
            stop_trips_in[s['stationId']] += t
        stop_routes[s['stationId']].add(str(r['routeName']))
print('배차정보 없는 노선:', len(no_info), no_info[:15])

# 4) 우리 1,405개 정류장과 매칭
src = os.path.join(PROJ, 'data', 'seongnam_bus_stops_2025.csv')
stops = list(csv.DictReader(open(src, encoding='utf-8-sig')))
out = []
for s in stops:
    sid = int(s['정류장번호'].replace('GGB', ''))
    out.append({**s, '미정차': 'Y' if '미정차' in s['정류장명'] else 'N',
                '평일추정운행횟수': round(stop_trips.get(sid, 0)),
                '도내노선_운행횟수': round(stop_trips_in.get(sid, 0)),
                '경유노선수': len(stop_routes.get(sid, ())),
                '경유노선': ' '.join(sorted(stop_routes.get(sid, ())))})
matched = sum(1 for o in out if o['경유노선수'] > 0)
print(f'매칭: {matched}/{len(out)} ({matched / len(out) * 100:.1f}%)')

dst = os.path.join(PROJ, 'data', 'seongnam_stop_frequency.csv')
with open(dst, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print('saved', dst)
