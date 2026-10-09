"""탄소 보조 추정 — 급행 재편의 수단전환 효과 시나리오
(a) 본 틀은 '감축의 선행조건'이고, 이 스크립트는 (b) 보조 추정만 담당한다.
※ 아래 ASSUMP의 값은 전부 가정이다. 출처가 확정되기 전에는 결과를 단정하지 말 것.
"""
import csv,io,sys,json,glob,math
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
ASSUMP=dict(
  car_g_km   = None,   # 승용차 CO2 배출계수 g/km  ← 미검증. 환경부 자동차 온실가스 관리제도 등에서 확정할 것
  bus_g_pkm  = None,   # 버스 CO2 배출원단위 g/인km ← 미검증
  occupancy  = 1.2,    # 승용차 평균 재차인원(명) ← 미검증. 국가교통DB 확인 필요
  trip_share = 1/3,    # 전환 통행 1건의 평균 주행거리 = 노선 편도 길이의 이 비율 (가정)
  shift_rates= (0.02,0.05,0.10),   # 급행 이용자 중 승용차에서 전환한 비율 시나리오
  days       = 250,    # 연간 환산 일수(평일 기준, 가정)
)
ROUTE={'88-1':dict(csv='data/express_88_1.csv'),'32':dict(csv='data/express_32.csv')}
routes={}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    b=json.load(open(f,encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    if isinstance(b,list): b=b[0]
    routes[str(b['routeId'])]=(str(b.get('routeName')),b.get('routeTypeName',''))
def hav(a,b):
    R=6371000;p=math.pi/180
    h=math.sin((b[1]-a[1])*p/2)**2+math.cos(a[1]*p)*math.cos(b[1]*p)*math.sin((b[0]-a[0])*p/2)**2
    return 2*R*math.asin(math.sqrt(h))
print('■ 전제 — 아래는 전부 가정값이다')
for k,v in ASSUMP.items(): print(f'   {k:<12}{v}' + ('   ← 출처 확정 필요' if v is None else ''))
print()
for name,cf in ROUTE.items():
    rows=list(csv.DictReader(open(cf['csv'],encoding='utf-8-sig')))
    rid=[k for k,v in routes.items() if v==(name,'마을버스')][0]
    A=json.load(open(f'data/raw/gg_routestation/{rid}.json',encoding='utf-8'))['response']['msgBody']['busRouteStationList']
    pts=[(float(s['x']),float(s['y'])) for s in A]
    rt_km=sum(hav(pts[i],pts[i+1]) for i in range(len(pts)-1))/1000
    one_way=rt_km/2
    use=sum(float(r['왕복일평균']) for r in rows if r['급행정차']=='정차')   # 승차+하차 건수
    trips=use/2                                                            # 통행 수로 환산
    d_km=one_way*ASSUMP['trip_share']
    print(f'── {name}번  (왕복 {rt_km:.1f}km, 편도 {one_way:.1f}km / 급행 정차역 일평균 이용 {use:,.0f}건 = 통행 약 {trips:,.0f}건)')
    print(f'   전환 통행 1건의 승용차 주행거리 가정 {d_km:.1f}km')
    for s in ASSUMP['shift_rates']:
        shifted=trips*s
        veh_km=shifted*d_km/ASSUMP['occupancy']
        if ASSUMP['car_g_km'] is None:
            print(f'   전환율 {s*100:>4.0f}% → 전환 통행 {shifted:>7,.0f}건/일, 줄어드는 승용차 주행 {veh_km:>8,.0f} km/일 '
                  f'({veh_km*ASSUMP["days"]/1000:>7,.0f} 천km/년)  → tCO2 = 배출계수 확정 후 산출')
        else:
            t=veh_km*ASSUMP['car_g_km']/1e6*ASSUMP['days']
            print(f'   전환율 {s*100:>4.0f}% → {veh_km:>8,.0f} km/일 → 연 {t:>7,.0f} tCO2')
    print()
print('※ 이 추정은 급행 이용자 중 일부가 승용차에서 전환한다는 가정에 전적으로 의존한다.')
print('※ 반대 방향 효과(통과 정류장의 배차 감소 → 자동차 이탈)는 반영되지 않았다. 순효과는 알 수 없다.')
