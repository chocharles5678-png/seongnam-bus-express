"""급행 재편 설계 — 한 노선의 차량 일부만 주요 정류장에 세운다 (증차 없음)
사용: python scripts/seongnam/x_express.py 88-1 | 32
정차 규칙 = 기·종점 U 거점 U 2차기준(원도심=고령취약, 분당=환승거점)
"""
import csv,io,sys,json,glob,math,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
PLAN={
 # 노선: 짝노선(완행 보강), 거점 기준(왕복 일평균), 2차기준
 '88-1': dict(pair='88',  hub=2000, kind='고령취약', th=40,  minu=1200),  # 접근로의 법정경사 초과 비율 %
 '32'  : dict(pair=None,  hub=2000, kind='환승거점', th=5,   minu=0),     # 경유 마을버스 노선 수
}
name=sys.argv[1] if len(sys.argv)>1 else '88-1'
cfg=PLAN[name]
slope={r['정류장번호'][3:]:r for r in csv.DictReader(open('data/seongnam_stop_slope.csv',encoding='utf-8-sig'))}
ride={r['정류소ID']:r for r in csv.DictReader(open('data/seongnam_ride_202606.csv',encoding='utf-8-sig'))}
routes={}
for f in glob.glob('data/raw/gg_busroute/getBusRouteInfoItemv2_*.json'):
    b=json.load(open(f,encoding='utf-8'))['response']['msgBody']['busRouteInfoItem']
    if isinstance(b,list): b=b[0]
    routes[str(b['routeId'])]=dict(nm=str(b.get('routeName')),ty=b.get('routeTypeName',''),al=b.get('peekAlloc'))   # GBIS 명세: 평일 최소 배차시간(분). 첨두 배차가 아니다
def load(n):
    rid=[k for k,v in routes.items() if v['nm']==n and v['ty']=='마을버스'][0]
    lst=json.load(open(f'data/raw/gg_routestation/{rid}.json',encoding='utf-8'))['response']['msgBody']['busRouteStationList']
    return (lst if isinstance(lst,list) else [lst]), routes[rid]['al']
A,alloc=load(name)
shared,alloc_p=(set(),None)
if cfg['pair']:
    B,alloc_p=load(cfg['pair']); shared={str(s['stationId']) for s in B}
# '(경유)' 표기는 정차하지 않는 통과점이므로 정차 횟수에서 제외한다
via=[s for s in A if '(경유)' in s['stationName']]
A=[s for s in A if '(경유)' not in s['stationName']]
pt=collections.OrderedDict()
for s in A:
    i=str(s['stationId'])
    p=pt.setdefault(s['stationName'],dict(name=s['stationName'],seqs=[],ids=[],u=0.0,sc=0.0,mb=0,share=False,dong=''))
    p['seqs'].append(s['stationSeq']); p['ids'].append(i)
    if i in ride: p['u']+=float(ride[i]['일평균']); p['mb']=max(p['mb'],int(ride[i]['마을버스수'] or 0)); p['dong']=ride[i]['행정동']
    if i in slope: p['sc']=max(p['sc'],float(slope[i]['정류장까지_8.33초과_비율']))
    if i in shared: p['share']=True
term={A[0]['stationName'],A[-1]['stationName'],A[A[0]['turnSeq']-1]['stationName'] if A[0].get('turnSeq') else None}
for p in pt.values():
    second = p['sc']>=cfg['th'] if cfg['kind']=='고령취약' else p['mb']>=cfg['th']
    if p['name'] in term: p['why']='기종점'
    elif p['u']>=cfg['hub']: p['why']='거점'
    elif second and p['u']>=cfg['minu']: p['why']=cfg['kind']
    else: p['why']=''
P=list(pt.values()); tot=sum(p['u'] for p in P)
sel=[p for p in P if p['why']]; stop_cnt=sum(len(p['seqs']) for p in sel)
cov=sum(p['u'] for p in sel)/tot*100
print(f"■ {name}번 급행 설계  (평일 최소배차 {alloc}분" + (f", 짝노선 {cfg['pair']} {alloc_p}분" if cfg['pair'] else ", 짝노선 없음") + ")")
print(f"  지점 {len(P)}곳 / 정차 {len(A)}회 (왕복)" + (f" / 경유통과점 {len(via)}개 제외" if via else ""))
print(f"  급행 정차 {len(sel)}지점 {stop_cnt}회  →  통과 {len(A)-stop_cnt}회")
print(f"  급행이 담는 수요 {sum(p['u'] for p in sel):,.0f} / {tot:,.0f} = {cov:.0f}%")
print(f"  2차기준: {cfg['kind']} (" + (f"경사초과>={cfg['th']}% & 이용>={cfg['minu']}건" if cfg['kind']=='고령취약' else f"마을버스>={cfg['th']}개") + ")\n")
hdr='경사초과' if cfg['kind']=='고령취약' else '마을버스'
print(f"{'순서':<12}{'정류소명':<30}{'왕복일평균':>9}{hdr:>8}{'행정동':>9}  사유")
for p in P:
    if not p['why']: continue
    v=f"{p['sc']:.0f}%" if cfg['kind']=='고령취약' else f"{p['mb']}개"
    print(f"{','.join(map(str,p['seqs'])):<12}{p['name'][:28]:<30}{p['u']:>9,.0f}{v:>8}{p['dong']:>9}  {p['why']}")
print(f"\n■ 통과하는 지점 상위 8 (완행이 계속 담당)")
for p in sorted([x for x in P if not x['why']],key=lambda x:-x['u'])[:8]:
    print(f"  {p['name'][:30]:<32}{p['u']:>8,.0f}{'  ('+cfg['pair']+' 공유)' if p['share'] else ''}")
# 배차 설계
un=[p for p in P if not p['share']]; sel_un=[p for p in sel if not p['share']]
un_pass=sum(p['u'] for p in un)-sum(p['u'] for p in sel_un)
print('\n'+'─'*70)
print('■ 배차 설계 — 운행 대수가 공개되지 않아 비율로 설계한다')
for k in (2,3):
    exp=alloc*k; loc=alloc*k/(k-1)
    print(f"\n  [{k}회 중 1회 급행]  급행 {exp:.0f}분 간격 / 완행 {loc:.0f}분 간격")
    if cfg['pair']:
        sh=[p for p in P if p['share']]
        print(f"    {cfg['pair']} 공유 {len(sh)}지점: 완행 {1/(1/loc+1/alloc_p):.0f}분 간격 유지")
    print(f"    급행 정차 지점: 급행{exp:.0f}분 + 완행{loc:.0f}분 → 약 {1/(1/exp+1/loc):.0f}분 간격 유지")
    print(f"    통과 지점: {alloc}분 → {loc:.0f}분 (영향 수요 {un_pass:,.0f}건 = 전체의 {un_pass/tot*100:.0f}%)")
print('\n■ 단축 효과 추정')
print(f'  왕복 {len(A)}회 중 {stop_cnt}회만 정차 → {len(A)-stop_cnt}회 통과')
print('  정차 1회당 손실시간은 가정값이다. 문헌 확인 전까지 단정하지 않는다.')
for dw in (15,20,25,30):
    s=(len(A)-stop_cnt)*dw
    print(f'    {dw}초 가정 → 왕복 {s/60:.0f}분 단축 (편도 약 {s/120:.0f}분)')
out=f'data/express_{name.replace("-","_")}.csv'
with open(out,'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(['순서','정류소명','정류소ID','행정동','왕복일평균','경사초과비율','마을버스수','짝노선공유','급행정차','사유'])
    for p in P:
        w.writerow([','.join(map(str,p['seqs'])),p['name'],' '.join(p['ids']),p['dong'],round(p['u']),round(p['sc'],1),
                    p['mb'],'o' if p['share'] else '','정차' if p['why'] else '통과',p['why']])
print(f'\n-> {out}')
