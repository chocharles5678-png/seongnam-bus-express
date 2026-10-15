"""붙임2 양식 구조의 인쇄용 보고서 HTML 생성 — 350번 무증차 급행 재편 (축약판)
사용: python scripts/seongnam/x_build_report350.py
출력: output/분석보고서_350번.html  (브라우저에서 Ctrl+P → PDF로 저장, 배경 그래픽 켜기)

분량 기준(본문 5장 내외)에 맞추려고 본문을 약 40% 들어낸 판이다.
들어내기 전 상세판은 scripts/seongnam/.x_build_report350_full.py.bak 에 있다.
x_build_report.py(55번판)는 건드리지 않는다.
"""
import base64, io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

FIGS = [
    ('figures/급행_350_노선도.png', '그림 1',
     '350번 급행 재편 — 급행 정차 17지점 / 왕복 정차 90회 → 21회',
     '왼쪽은 노선도(원 크기 = 지점 왕복 일평균 승하차), 오른쪽 위는 정차 횟수 비교, '
     '오른쪽 아래는 정류소 순서별 이용량이며 색칠한 막대가 급행 정차 지점이다.'),
    ('figures/배차역설_4개노선.png', '그림 2',
     '배차 역설 — 나눌 수 있는 노선은 이미 배차가 촘촘한 노선뿐이다',
     '네 노선을 같은 틀로 실측해 비교했다. 급행 간격 30분 이하(음영)와 평균 순효과 0 이상을 '
     '동시에 만족하는 배정은 55번과 350번에만 있고, 배차가 가장 촘촘한 350번이 가장 크다.'),
    ('figures/무증차_350.png', '그림 3',
     '350번 무증차 재편 — 급행이 아낀 23분을 회차 여유로 두면 탄소가 줄고 효과는 3.6초만 깎인다',
     '왼쪽은 급행 배정 대수별 순효과와 급행 간격(운영 방식 B 기준), 오른쪽은 아낀 23분을 '
     '더 도는 데 쓸 때(A)와 회차 여유로 둘 때(B)의 효과·탄소 비교다. 막대의 단위가 서로 다르다.'),
]

ROWS = []


def row(label, html, cls=''):
    ROWS.append((label, html, cls))


row('이름 / 팀명', '<p class="blank">[ 기재 필요 ]</p>')

row('주제', """
<p class="lead">나눌 수 있는 버스는 이미 편한 버스였다<br>
— 버스위치 API 실측으로 찾은 성남 350번 무증차 급행 재편</p>
<p>마을버스가 주거지와 거점을 잇고 시내버스 일부 차량을 급행으로 돌리는 안을 <b>차량을 늘리지 않고</b>
검토했다. 성남 네 노선(88-1·380·55·350)의 <b>운행 대수와 왕복 소요시간을 공개 API로 직접 실측</b>해
같은 틀로 비교하고, 그중 350번을 제안 대상으로 선정했다.</p>
<p class="note"><b>증차(차량 증편)는 제안에서 제외했다.</b> 전수 계산 결과 증차는 효과가 크지만
정차 횟수가 줄지 않은 채 주행거리만 26.7% 늘어 공모전 주제인 탄소중립과 상충하기 때문이다(§7-7).<br>
<b>제안한 무증차 재편은 정차를 20.2% 줄여 일일 탄소를 3.7% 감축한다</b>(§7-6).</p>
""")

row('분석 배경<br>및 목적', """
<p>성남의 주거 생활권에서 판교 업무지역과 야탑·모란 생활거점으로 가는 통행은 정차가 많은 시내버스에
묶여 있다. 급행을 새로 만들려면 차량·기사·차고지가 필요하지만 <b>기존 차량의 배분만 바꾸는 재편</b>은
추가 투입 없이 가능하다. 그 재편이 실제로 이득인지가 이 분석의 질문이다.</p>
<p>효과는 <b>왕복 소요시간</b>과 <b>운행 대수</b>에서 전부 결정되는데 두 값은 공개 자료에 없다.
초기에 구간 소요시간 중앙값×구간 수로 88-1번 왕복을 78분으로 추정했으나 실측은 <b>98분</b>,
회차·회복 시간이 빠져 <b>26% 과소평가</b>였다.</p>
<p class="big">경기도 버스위치정보 API 응답에 <b>차량번호(plateNo)</b>와 <b>정류소순번(stationSeq)</b>이
들어 있다. 이 둘을 추적하면 운행 대수와 왕복 소요시간을 <b>추정이 아니라 실측</b>할 수 있다.
이 분석의 모든 운행 수치는 여기서 나왔다.</p>
<p><b>목적</b> ① 네 노선의 운행 대수·왕복시간을 같은 방법으로 실측한다.
② 무증차 급행 재편이 <b>어떤 조건에서 성립하는지</b> 찾는다. ③ 성립하는 노선에 정차역을 설계하고
<b>이득과 손해를 함께</b> 제시한다.</p>
<p class="warn"><b>연령을 노선 선정 조건으로 쓰지 않았다.</b> 행정동 20대 인구는 정차역 선정의
보조 지표로만 썼고, 노선 선정은 전적으로 실측 배차와 운행 대수로 했다.</p>
""")

row('활용 데이터', """
<table class="d data">
<tr><th>활용 데이터(명)</th><th>제공기관(명)</th><th>출처 플랫폼(명)</th><th>URL</th></tr>
<tr><td>경기도 버스위치정보 조회 (Open API)</td><td>경기도 교통정보과</td><td>공공데이터포털</td>
    <td>https://www.data.go.kr/data/15080648</td></tr>
<tr><td>경기도 버스노선 조회 (Open API)</td><td>경기도 교통정보과</td><td>공공데이터포털</td>
    <td>https://www.data.go.kr/data/15080662</td></tr>
<tr><td>경기도 버스정류소 현황</td><td>경기도</td><td>공공데이터포털</td>
    <td>https://www.data.go.kr/data/15057894</td></tr>
<tr><td>경기도 정류소별 승하차 인원 집계 (2026.06)</td><td>경기도 버스관리과</td><td>경기데이터드림</td>
    <td>https://data.gg.go.kr <span class="s">(infId=MZCREO5CKHZM6PJEA55P37391662)</span></td></tr>
<tr><td>주민등록 인구통계 — 행정동별 연령별 인구현황 (2026.08)</td><td>행정안전부</td><td>주민등록 인구통계</td>
    <td>https://jumin.mois.go.kr</td></tr>
<tr><td>경기버스정보 노선정보 항목 명세</td><td>경기도</td><td>GBIS</td>
    <td>https://www.gbis.go.kr/gbis2014/publicService.action?cmd=mBusRouteInfo</td></tr>
</table>
<table class="d">
<tr><th>구분</th><th>내용</th></tr>
<tr><td>수집 방법</td><td><b>공공데이터포털 활용신청 후 발급받은 인증키로 공식 OpenAPI를 호출</b>했다.
  웹 크롤링이나 비공개 경로 접근은 사용하지 않았다. 개발계정 한도(일 1,000회) 안에서 호출 예산을 두었다.</td></tr>
<tr><td>수집 기간</td><td>버스위치 <b>2026-10-05 ~ 10-14</b>(평일 6일, 폴링 30~45초) — 10-07 88-1·55·380(992회),
  10-12 55(600회), 10-13 350(352회), <b>10-14 350 첨두 480회</b>·357(274회).<br>
  승하차 2026-06-30 / 인구 2026-08-31 / 노선·정류소 제원 2026-10 조회분.</td></tr>
<tr><td>주요 변수</td><td>위치 API — <code>ts, route, plateNo, stationId, stationSeq</code> ·
  노선 API — 경유 순서, 기·종점, <code>peekAlloc</code>(평일 최소 배차) ·
  승하차 — 정류소ID, 승차합계, 초승, 환승, 하차합계</td></tr>
<tr><td>이용 조건</td><td>승하차 자료는 상업적 이용 및 변경 허용. OpenAPI는 포털 이용약관에 따름.
  <b>인증키는 환경변수로 분리해 코드·제출물에 포함하지 않았다.</b></td></tr>
</table>
<p class="s">승하차 집계로 급행 정차역을 선정했고(성남시 1,305개소, 총 24,860,507건), GBIS 명세는
배차 필드 정의 확인에 썼다 — 초기에 <code>peekAlloc</code>을 "첨두 배차"로 오독한 것을 바로잡은 근거다(§9-4).</p>
""")

row('분석과정<br>및 방법', """
<div class="flow">
<b>1</b> 노선·정류소 제원 수집 &nbsp;→&nbsp; <b>2</b> 위치 API 폴링(30~45초) &nbsp;→&nbsp;
<b>3</b> 운행 대수·왕복시간 실측 &nbsp;→&nbsp; <b>4</b> 급행 정차역 선정 &nbsp;→&nbsp;
<b>5</b> 무증차 재편 전수 시뮬레이션 &nbsp;→&nbsp; <b>6</b> 총 주행거리 변화 산출
</div>

<h4>5-1. 운행 대수와 왕복 소요시간</h4>
<p><b>운행 대수</b>는 10분 단위 고유 차량번호의 중앙값이다. 1시간으로 세면 교대·투입 차량까지 누적돼
과대 집계된다(350번 1시간 23대 vs 10분 19대). <b>왕복 소요시간</b>은 정류소 순번이 단조 증가하는
가장 긴 구간을 찾아 진행률 95% 이상인 <b>완주 차량</b>의 중앙값을 쓴다.</p>
<p class="warn"><b>완주 집합은 관측 종료 시각에 절단되어 빠른 차량 쪽으로 치우친다.</b>
350번을 155분만 관측했을 때는 완주 2대에 136분이었으나, 240분을 관측하니 <b>완주 13대에 150분</b>이었다.
본문은 150분을 쓴다. 왕복(150분)이 첨두창(115분)보다 길어 첨두 안에서 완주가 구조적으로 나올 수 없으므로,
첨두 통과 속도는 <b>연속 관측쌍 중 양 끝 시각이 모두 같은 창 안인 것만</b> 모아 집계했다.</p>

<h4>5-2. 급행 정차역 선정 규칙 — 다음의 합집합</h4>
<div class="rule">
① 기·종점·회차점 &nbsp;|&nbsp; ② 거점: 지점 왕복 일평균 승하차 ≥ 3,000건 &nbsp;|&nbsp;
③ 대학: 정류소명에 대학/가천대/을지대/신구대 포함 AND ≥ 1,000건<br>
④ 환승거점: 마을버스 5개 이상 경유 &nbsp;|&nbsp; ⑤ 20대 거점: 행정동 20대 ≥ 2,500명 AND 지점 ≥ 1,500건
</div>
<p>교집합으로는 최대 거점이 탈락해 <b>합집합</b>으로 했다. 집계는 <b>정류소 고유ID 기준</b>이다 —
이름으로 묶으면 성남에서 <b>같은 이름이면서 경유 마을버스 수가 다른 102곳</b>의 값이 뭉개진다(예: 판교역서편은 세 ID가 각각 6개 / 1개 / 0개). <b>이 기준은 55번에 적용한 것과 동일하며
350번에 맞춰 조정하지 않았다</b>(§7-4 민감도).</p>

<h4>5-3. 시뮬레이션 모형</h4>
<div class="box">
완행 왕복 = 150분(실측) &nbsp;·&nbsp; 급행 왕복 = 150 − (통과 69회 × T) = <b>127분</b><br>
각 서비스는 <b>자기 왕복시간 ÷ 자기 대수</b> 간격으로 운행 &nbsp;·&nbsp;
평균 대기 = <b>E[gap²] / (2·E[gap])</b>
</div>
<p>출발·도착이 <b>모두</b> 급행 정차 지점인 통행은 급행·완행 중 먼저 오는 차를 타고,
한쪽이라도 통과 지점이면 완행만 탄다.</p>
<p class="warn"><b>가정 세 가지.</b> <b>① T(정차 1회당 손실) = 20초</b> — 실측 3방법 모두 실패(§9-3).
15·20·25·30초로 모두 돌렸고 권장 급행 대수는 5대로 동일했다.
<b>② 평균 통행 = 편도의 1/3</b> — 차내 단축폭을 <u>선형으로</u> 좌우한다(1/4이면 2.9분, 1/2이면 5.7분).
<b>③ 출발·도착 독립</b> — 급행 이용 가능 42%는 기록 구성비 64.7%의 제곱이다.</p>
""")

row('AI 기술<br>활용', """
<table class="d">
<tr><th>구분</th><th>내용</th></tr>
<tr><td>활용 AI 서비스</td><td>Claude (Anthropic) — Claude Code</td></tr>
<tr><td>활용 범위</td><td>공식 수집처 확인, Python 수집·정제·검증 코드 작성, 시뮬레이션 구현, 도면 생성, 문서 구성</td></tr>
<tr><td>검증 방식</td><td>AI가 낸 수치는 <b>원본 재집계와 재실행으로 대조</b>한 뒤에만 사용했다.
  AI의 설명 자체를 실측 자료로 쓰지 않았다.</td></tr>
</table>
<h4>주요 프롬프트 — 분석 방향을 바꾼 다섯 지점</h4>
<p class="note">아래는 <b>대화 기록에 남은 실제 입력 문장을 그대로</b> 옮긴 것이다.
AI가 문장을 지어내면 이 항목 자체가 무의미해지므로 재구성하거나 다듬지 않았다.</p>
<table class="d">
<tr><th>시점</th><th>입력한 문장</th><th>바뀐 것</th></tr>
<tr><td>10-05</td><td>"경사 고령 취약 이건 이제 배제시켜도 돼, 새로운 방향으로 가고 있으니깐"</td>
    <td><b>선정 조건 정리.</b> 경사·고령을 정차역 선정에서 제외하고 이용량·환승 중심으로 단순화했다</td></tr>
<tr><td>10-06</td><td>"일단 그럼 20대 사람들이 사는 곳에서 어느 노선도를 해야 현명할까,
    우리의 공모전 취지는 차량이 없는 20대들을 위해 급행 노선도를 짜는거야"</td>
    <td><b>목적 확정.</b> 마을버스 단독에서 <b>마을버스 연계 + 시내버스 급행</b>으로 방향을 바꿨다</td></tr>
<tr><td>10-06</td><td>"88-1 첨두 지금 구하자"</td>
    <td><b>실측 착수.</b> 버스위치 API 폴링을 실제로 돌려 추정값(왕복 78분)을 실측(98분)으로 대체했다</td></tr>
<tr><td>10-08</td><td>"350·330·220 연속성 검증부터 하자"</td>
    <td><b>350번 검토 시작.</b> 병행 노선 중첩을 전수 검증해 350번의 독점 구간이 0임을 확인했다</td></tr>
<tr><td>10-15</td><td>"증차는 공모전 취지인 탄소중립과 맞지 않아서 빼자"</td>
    <td><b>증차 배제.</b> 총 주행거리 비율을 산출해 증차안을 기각 사유와 함께 제외했다(§7-5)</td></tr>
</table>

<h4>AI 활용에서 실제로 작동한 것</h4>
<ol class="key">
<li><b>실측으로 AI의 추정을 반증했다.</b> AI가 외삽으로 낸 88-1 왕복 78분은 실측 98분과 26% 차이였다.
  이후 외삽값은 결론에 쓰지 않는 규칙을 적용했다.</li>
<li><b>1차 명세로 AI의 필드 해석을 반증했다.</b> <code>peekAlloc</code>을 "첨두 배차"로 읽은 것이
  오독임을 GBIS 명세 원문에서 확인하고 관련 주장 4건을 철회했다.</li>
<li><b>전수 계산과 표본 확대로 코드·집계 결함을 잡았다.</b> 시뮬레이션이 급행 대수를
  <code>(3,5,6,8,10)</code>으로 하드코딩해 N=1·2를 건너뛰었고, 350번 왕복은 완주 2대 136분에서
  관측창 확대 후 <b>완주 13대 150분</b>으로 바뀌었다.</li>
</ol>
""")

row('분석 내용<br>및 결과', """
<h4>7-1. 네 노선 실측 — 같은 방법, 같은 기간</h4>
<table class="d n">
<tr><th>노선</th><th>왕복<br>정차</th><th>공시 배차</th><th>왕복 소요<br>(실측)</th>
    <th>관측<br>대수</th><th>배차<br>(왕복÷대수)</th><th>공시 대비</th><th>급행 분리</th></tr>
<tr><td>88-1 <span class="s">마을</span></td><td>71회</td><td>15~25분</td><td><b>98분</b></td><td><b>4.0대</b></td>
    <td>24.5분</td><td class="no">최소값의 1.6배</td><td class="no">불가</td></tr>
<tr><td>380</td><td>106회</td><td>15~25분</td><td><b>187분</b><span class="s">*</span></td><td><b>10.0대</b></td>
    <td>18.7분</td><td>범위 안</td><td class="no">불가</td></tr>
<tr><td>55</td><td>127회</td><td>10~20분</td><td><b>200분</b></td><td><b>18.0대</b></td>
    <td>11.1분</td><td>범위 안</td><td class="ok">가능(+0.17분)</td></tr>
<tr class="hl"><td><b>350</b></td><td><b>90회</b></td><td><b>7~9분</b></td><td><b>150분</b></td>
    <td><b>19.0대</b></td><td class="hl2"><b>7.9분</b></td><td>범위 안</td>
    <td class="ok"><b>가능(+0.51분)</b></td></tr>
</table>
<p class="big"><b>갈림길은 배차 하나다.</b> 88-1번은 4대뿐이라 1대만 돌려도 급행이 98분에 한 대가 되고,
380번은 10대라 급행 간격을 30분 이하로 만들면 평균이 −5.7분이 된다. 공시 범위를 크게 벗어난 것은
마을버스 88-1번뿐이다 — <b>공시 배차를 실제 운행으로 간주하면 안 되지만, 배차가 촘촘한 시내버스에서는
공시가 대체로 지켜진다.</b></p>
<p class="s">* 380번은 관측창(115분)이 왕복보다 짧아 완주 차량이 없다. 187분은 통과 속도 환산값이다. 네 노선의 왕복·대수는 모두 같은 방법(<code>x_peak.py</code>)으로 재계산했다 — 88-1·380은 10-07, 55는 10-12, 350은 10-14 첨두 관측이다.</p>
<p class="note">위 표와 <b>그림 2</b>의 순효과는 급행이 아낀 시간만큼 더 도는 <b>운영 방식 A</b> 기준이다.
본 보고서가 제안하는 것은 아낀 시간을 회차 여유로 두는 <b>방식 B</b>이며(§7-4), B 기준으로는 <b>350번만 성립하고 55번은 탈락한다</b>(§7-8).</p>

<h4>7-2. 350번 첨두 실측 (2026-10-14 수 07:04~11:04, 480회 호출)</h4>
<p><b>첨두 운행 19.0대 · 완주 왕복 150분(완주 13대, 142~158분) · 배차 7.9분.</b>
통과 속도는 첨두 0.563 / 비첨두 0.608로 <b>첨두 지체 −7.4%</b>(55번 −14.3%)다.
첨두 배차는 완주 실측(150분)÷19.0대, 비첨두는 완주가 없어 환산(145분)÷18.0대로 계산했다 — 기준이 다르므로 소수점까지 비교하지 않는다. 완주 13대는 모두 첨두 출발(07:04~08:42)이다. <b>배차는 시간대에 둔감하다</b> — 왕복과 대수가
같이 움직여 상쇄된다(비첨두 8.0분, 55번도 첨두 11.1 / 비첨두 10.9분).</p>

<h4>7-3. 급행 정차역 — 17지점, 왕복 90회 → 21회, 기록 커버 64.7%</h4>
<p>축은 <b>상대원차고지 → 모란역 → 성남시청 → 야탑역 → 판교테크노밸리 → 운중동</b>이다.
이용 상위는 야탑역 전면 16,203 · 후면 15,124, 모란역2.3번출구 12,346 · 5번출구 8,444,
성남시청전면 5,391, 운중동행정복지센터 4,232, 유라코퍼레이션.SK케미칼 3,866,
판교유스센터 3,522건이다(왕복 일평균).</p>
<p class="warn"><b>64.7%의 분모.</b> 그 정류소에 서는 <b>모든 노선의 승하차 기록</b> 구성비다.
원본에 노선 구분 컬럼이 없어 "350번 승객의 64.7%"라고 말할 수 없고 인원으로도 환산할 수 없다.</p>
<p class="note"><b>급행이 상대원1동행정복지센터를 통과한다.</b> 왕복 일평균 2,945건으로 거점 기준
3,000건에 <b>55건 미달</b>이다. 상대원 주민을 위한 급행인데 상대원1동을 건너뛰는 모양이 된다.
기준을 2,900으로 낮추면 정차하지만 <b>기준을 결과에 맞춰 조정한 것이 되므로 그대로 두었다.</b>
기점인 상대원차고지에서는 급행을 탈 수 있다.</p>

<h4>7-4. 운영 방식의 선택 — 급행이 아낀 23분을 어디에 쓰는가</h4>
<p>급행은 왕복이 150분에서 <b>127분</b>으로 짧아진다. 이 <b>23분</b>을 어떻게 쓰느냐가
효과와 탄소를 동시에 가른다.</p>
<table class="d n">
<tr><th></th><th>A. 쉬지 않고 더 돈다</th><th class="hl2">B. 회차 여유로 둔다 <b>(제안)</b></th></tr>
<tr><td>급행 간격 (5대)</td><td>25.4분</td><td class="hl2"><b>30.0분</b></td></tr>
<tr><td>통행당 평균 순효과</td><td>+0.51분</td><td class="hl2"><b>+0.44분</b></td></tr>
<tr><td>일일 주행거리</td><td class="no">+4.8%</td><td class="ok"><b>0%</b></td></tr>
<tr><td>일일 정차 횟수</td><td>−19.1%</td><td><b>−20.2%</b></td></tr>
<tr><td><b>일일 탄소</b></td><td>±0% <span class="s">(−3.0 ~ +2.5)</span></td>
    <td class="ok"><b>−3.7%</b> <span class="s">(−6.6 ~ −1.9)</span></td></tr>
</table>
<p class="big"><b>B를 택했다.</b> 평균 순효과를 <b>0.07분(3.6초)</b> 내주고 탄소 감축과 운영 현실성을 얻는다.
A는 급행의 회차 여유시간을 0으로 두는 가정인데, 실제 운행에는 지연 흡수·기사 휴식을 위한
회복시간이 필요하다. <b>B의 23분 대기는 그 회복시간에 해당한다.</b></p>

<h4>7-5. 무증차 재편 결과 (운영 방식 B) — 급행 5대에서 평균 +0.44분</h4>
<table class="d n">
<tr><th>급행 대수</th><th>1</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th><th>9</th></tr>
<tr><td>급행 간격</td><td>150분</td><td>50.0분</td><td>37.5분</td><td><b>30.0분</b></td><td>25.0분</td>
    <td>21.4분</td><td>16.7분</td></tr>
<tr><td>평균 순효과</td><td>+1.37분</td><td>+0.97분</td><td>+0.74분</td><td><b>+0.44분</b></td><td>+0.16분</td>
    <td class="no">−0.15분</td><td class="no">−0.87분</td></tr>
</table>
<p>평균만 보면 급행 1대가 최선이지만 <b>150분에 한 대는 급행이 아니라 특별편</b>이다.
급행 간격 30분 이하를 만드는 최소 대수가 <b>5대</b>이고, 그때 간격이 <b>정확히 30.0분</b>이다.
기준선에 딱 걸친다는 점을 밝혀 둔다.</p>
<table class="d n">
<tr><th>급행 5대 / 완행 14대</th><th>현행</th><th>재편 후</th><th>순효과</th></tr>
<tr><td>완행 간격</td><td>7.9분</td><td>10.7분</td><td>—</td></tr>
<tr><td>급행 간격</td><td>—</td><td>30.0분</td><td>—</td></tr>
<tr><td>급행 이용 가능 (42%)</td><td>3.95분 대기</td><td>4.77분 대기</td><td class="ok">+3.01분</td></tr>
<tr><td>급행 이용 불가 (58%)</td><td>3.95분 대기</td><td>5.36분 대기</td><td class="no">−1.41분</td></tr>
<tr class="hl"><td><b>통행당 평균</b></td><td>—</td><td>—</td><td class="ok"><b>+0.44분</b></td></tr>
</table>
<p class="warn"><b>대기시간은 모든 지점에서 늘어난다.</b> 급행 정차 지점조차 3.95분에서 4.77분이 된다.
차량 수가 같은데 두 서비스로 나뉘며 도착이 불규칙해지기 때문이다. <b>이득은 전적으로 차내 시간에서 나온다.</b></p>
<p><b>민감도</b> — 정차 기준을 2,000/1,500으로 낮추면 24지점·커버 75.9%, 4,000/3,500으로 높이면
14지점·59.3%다. 세 기준 모두 평균이 양수이고 1분을 넘지 않는다.
<b>본문은 더 유리한 기준을 쓰지 않고 55번과 동일한 3,000/2,500을 유지했다.</b></p>
<p class="warn"><b>대기시간은 모든 지점에서 늘어난다.</b> 급행 정차 지점조차 3.9분에서 4.6분이 된다.
차량 수가 같은데 두 서비스로 나뉘며 도착이 불규칙해지기 때문이다. <b>이득은 전적으로 차내 시간에서 나온다.</b></p>
<p><b>민감도</b> — 정차 기준을 2,000/1,500으로 낮추면 24지점·커버 75.9%·평균 +0.9분,
4,000/3,500으로 높이면 14지점·59.3%·+0.3분이다. 세 기준 모두 양수이고 1분을 넘지 않는다.
<b>본문은 더 유리한 기준을 쓰지 않고 55번과 동일한 3,000/2,500을 유지했다.</b></p>

<h4>7-6. 탄소 — 정차가 20% 줄어 배출이 감소한다</h4>
<p>급행은 왕복 정차가 90회에서 <b>21회</b>로 준다. 버스 배출의 일부는 <b>감속으로 버린 운동에너지를
재가속으로 회복하는 연료</b>와 정차 중 공회전에서 나오므로, 정차가 줄면 배출이 줄어든다.</p>
<div class="box">
정차 1회 손실 = <b>½mv²</b> ÷ 구동효율 ÷ 연료발열량 × 배출계수 &nbsp;+&nbsp; 공회전연료 × 체류시간 × 배출계수
</div>
<table class="d n">
<tr><th></th><th>현행 (19대 전부 완행)</th><th>재편 후 (급행 5 / 완행 14)</th><th>변화</th></tr>
<tr><td>일일 주행거리</td><td>4,226 km</td><td>4,226 km</td><td><b>0%</b></td></tr>
<tr><td>일일 정차 횟수</td><td>9,508회</td><td>7,589회</td><td class="ok"><b>−20.2%</b></td></tr>
<tr class="hl"><td><b>일일 배출</b></td><td>4,648 kgCO₂</td><td>4,478 kgCO₂</td>
    <td class="ok"><b>−3.7%</b></td></tr>
</table>
<p><b>왕복 1회만 놓고 보면 급행이 완행보다 6.1 kgCO₂, 12~15% 적게 배출한다</b>(44.0 → 37.9 kgCO₂).
운영 방식 B는 왕복 횟수를 늘리지 않으므로 이 절감이 그대로 남는다.</p>
<table class="d n">
<tr><th>가정 (차량 질량 · 순항속도)</th><th>일일 배출 변화</th></tr>
<tr><td>11t · 25km/h (보수)</td><td class="ok">−1.9 ~ −2.5%</td></tr>
<tr class="hl"><td><b>13t · 30km/h (중간, 본문)</b></td><td class="ok"><b>−3.1 ~ −4.0%</b></td></tr>
<tr><td>16t · 35km/h (적극)</td><td class="ok">−5.1 ~ −6.6%</td></tr>
</table>
<p>총 배출계수를 1.0·1.1·1.3 kgCO₂/km로 바꿔가며 돌렸고, <b>아홉 조합 모두 감축</b>이다.</p>

<h4>7-7. 증차를 제외한 이유</h4>
<p>증차 4대면 통과 지점 손해 없이 평균 +1.7분이 가능하다. <b>그러나 완행 19대가 그대로 다 서므로
정차 횟수가 줄지 않는다.</b> 상쇄 요인 없이 주행거리만 늘어난다.</p>
<table class="d n">
<tr><th>급행을 도입하는 두 방법</th><th>주행거리</th><th>정차 횟수</th><th>탄소</th><th>평균 효과</th></tr>
<tr class="hl"><td><b>무증차 재편 (제안)</b></td><td><b>0%</b></td><td class="ok"><b>−20.2%</b></td>
    <td class="ok"><b>−3.7%</b></td><td>+0.44분</td></tr>
<tr><td>증차 4대</td><td class="no">+24.9%</td><td>0%</td><td class="no">약 +25%</td><td>+1.7분</td></tr>
</table>
<p class="big"><b>효과의 70%를 포기하는 대신 탄소를 25% 늘리지 않기로 했다.</b>
공모전 주제가 탄소중립이므로 이 교환을 택했다. 증차안은 전수 계산을 마친 뒤 이 이유로 기각했다.</p>

<h4>7-8. 운영 방식 B를 걸면 350번만 남는다</h4>
<p>회차 여유를 확보하는 운영 방식 B를 네 노선에 똑같이 적용하면, <b>급행 간격 30분 이하와
평균 순효과 0 이상을 동시에 만족하는 배정이 350번에만 있다.</b></p>
<table class="d n">
<tr><th>노선</th><th>A. 쉬지 않고 더 돈다</th><th>B. 회차 여유 확보 (제안 기준)</th></tr>
<tr><td>88-1</td><td class="no">없음</td><td class="no">없음</td></tr>
<tr><td>380</td><td class="no">없음</td><td class="no">없음</td></tr>
<tr><td>55</td><td>급행 6대 +0.17분</td><td class="no"><b>없음</b></td></tr>
<tr class="hl"><td><b>350</b></td><td>급행 5대 +0.51분</td><td class="ok"><b>급행 5대 +0.44분</b></td></tr>
</table>
<p class="big"><b>55번은 운영 방식 A에서만 성립한다.</b> 급행에 회차 여유를 주면 간격이 33.3분으로
벌어져 기준을 넘고, 기준 안에 들어오는 7대는 평균이 음수(−0.45분)가 된다.
<b>350번은 두 방식 모두에서 성립하는 유일한 노선이다.</b></p>
<p>350번이 이기는 것은 이득이 커서가 아니라 <b>손해가 작아서다.</b> 급행을 타는 개인의 이득은
55번이 더 크지만(+4.17 대 +3.01분), 통과 지점의 손해가 55번 −2.78분 대 350번 −1.41분으로 절반이다.
완행 간격 악화도 55번 11.1→16.7분, 350번 7.9→10.7분이다.</p>

<h4>7-9. 통과 지점의 손해는 균등하지 않다 — 공장지대 7정차</h4>
<p>350번은 <b>90정차 전부에 병행 노선이 있어 독점 구간이 0</b>이다(중앙값 11개, 야탑역 44개).
다만 <b>상대원 공장지대 7정차</b>만 병행이 <b>357번 하나</b>뿐이어서 357번도 실측했다 —
관측 8.5대, 왕복 환산 170분, <b>배차 20.0분</b>(공시 15~20분의 상한).
공장지대 대기는 현행 3.44분 → 재편 후 <b>4.42분</b>(완행 단독이면 5.35분이므로 357번이 0.93분 보완).</p>
<p>급행화해도 완행 14대는 그 7정차에 계속 서므로 공장지대가 350번을 잃는 것이 아니다. 다만 병행이
중앙값 11개인 다른 통과 지점은 보완이 더 크므로 <b>공장지대 7정차는 통과 지점 중에서도 상대적으로 불리하다.</b></p>
""")

row('정책제안<br>및 기대효과', """
<div class="box">
급행 <b>5대</b> · 간격 <b>30.0분</b> &nbsp;|&nbsp; 완행 <b>14대</b> · 간격 <b>10.7분</b><br>
급행 정차 <b>17지점</b> · 왕복 정차 <b>90회 → 21회</b>(통과 69회)<br>
급행이 아낀 23분은 <b>회차 여유</b>로 둔다 — 왕복 횟수를 현행과 같게 유지<br>
<b>차량 증편 없음 · 노선 신설 없음 · 총 주행거리 0% · 일일 탄소 −3.7%</b>
</div>
<h4>급행을 타는 사람은 얼마나 빨라지나</h4>
<p>급행은 편도 44구간 중 <b>12곳에만 선다.</b> 건너뛴 정류소 하나당 20초(가정)가 줄어들므로
<b>멀리 갈수록 이득이 커진다.</b> 실제 구간으로 계산하면 이렇다.</p>
<table class="d n">
<tr><th>구간</th><th>중간 정류소</th><th>급행이 통과</th><th>차내 단축</th><th>대기 증가</th><th class="hl2">순이득</th></tr>
<tr class="hl"><td style="text-align:left"><b>상대원차고지 → 한국학중앙연구원</b> <span class="s">(전 구간)</span></td>
    <td>43곳</td><td>33곳</td><td><b>11.0분</b></td><td>−0.8분</td><td class="ok"><b>+10.2분</b></td></tr>
<tr class="hl"><td style="text-align:left"><b>상대원차고지 → 이노밸리.포스코DX</b> <span class="s">(판교테크노밸리)</span></td>
    <td>27곳</td><td>20곳</td><td><b>6.7분</b></td><td>−0.8분</td><td class="ok"><b>+5.9분</b></td></tr>
<tr><td style="text-align:left">상대원차고지 → 야탑역</td><td>19곳</td><td>15곳</td><td>5.0분</td>
    <td>−0.8분</td><td class="ok">+4.2분</td></tr>
<tr><td style="text-align:left">성남시청 → 운중동행정복지센터</td><td>19곳</td><td>13곳</td><td>4.3분</td>
    <td>−0.8분</td><td class="ok">+3.5분</td></tr>
<tr><td style="text-align:left">모란역5번출구 → 판교유스센터</td><td>17곳</td><td>11곳</td><td>3.7분</td>
    <td>−0.8분</td><td class="ok">+2.9분</td></tr>
<tr><td style="text-align:left">야탑역 → 이노밸리.포스코DX</td><td>7곳</td><td>5곳</td><td>1.7분</td>
    <td>−0.8분</td><td>+0.9분</td></tr>
</table>
<p class="big"><b>이 노선의 핵심 통행인 상대원 주거·공장지대 → 판교테크노밸리는 편도 5.9분,
전 구간 이용자는 10.2분 빨라진다.</b> 왕복으로 출퇴근하면 상대원–판교 이용자는 하루 <b>12분</b>,
주 5일이면 <b>한 시간</b>을 돌려받는다. 350번은 상대원차고지에서 출발해 모란·야탑을 거쳐
판교테크노밸리 다섯 곳과 운중동까지 가는 축이라, 이 구간이 노선의 중심이다.</p>
<p class="note"><b>본문의 "+3.2분"과 위 표의 차이.</b> +3.2분은 <b>평균 통행 길이를 편도의 1/3로
가정</b>했을 때의 값이다. 실제로는 구간 길이에 비례해 0.9분부터 10.2분까지 벌어진다.
<b>짧게 타는 사람은 거의 이득이 없고, 멀리 가는 사람일수록 크게 얻는다</b> — 이것이 급행의 성격이다.</p>

<h4>전체로 보면</h4>
<p>통행당 평균 <b>+0.44분</b>이다. 급행을 탈 수 있는 42%가 평균 +3.01분을 얻고,
<b>탈 수 없는 58%가 −1.41분을 잃는</b> 합이다. 비용은 차량 증편 없이
급행 표시체계·정류소 안내·운행계획 변경·인가 검토·기사 교육이다.</p>

<h4>단계적 도입 — 효과가 통행당 31초이기 때문이다</h4>
<p class="big">이 크기의 개선에 노선 전체를 한 번에 바꾸는 것은 위험 대비 이득이 맞지 않는다.
<b>①</b> 출근 방향 첨두(07~09시)에만 급행 5대를 시범 운행하며 통과 지점의 실제 대기·혼잡·승차 거절과 <b>실제 연료 소모</b>를 계측하고,
<b>②</b> 악화가 모형(−1.4분)을 넘으면 중단한다. <b>③</b> 공장지대 7정차는 357번(20.0분)이 유일한
보완이므로 따로 계측한다.</p>

<h4>기대효과</h4>
<ul>
<li><b>차량 추가 없이</b> 주거지–판교 접근성을 개선하면서 <b>일일 탄소를 3.7% 줄인다</b> — 주행거리는 늘지 않고 정차만 20.2% 감소한다(증차안은 주행거리 +24.9%).</li>
<li><b>급행 재편의 적용 조건을 수치로 제시</b>한다 — 배차 10분 이하, 관측 대수 18대 이상.
  다른 노선·다른 도시에 그대로 적용할 수 있다.</li>
</ul>
<p class="warn"><b>제시하지 않는 것.</b> 수혜 인원, 승용차 전환 수요, 탄소 감축량은 산출하지 않았다.
노선별 OD와 배출계수를 확보하지 못했기 때문이다. <b>추정값을 제시하지 않는 것이 이 보고서의 원칙이다.</b></p>
""")

row('분석의 한계<br><span class="add">(추가 항목)</span>', """
<h4>9-1. 19대는 관측 차량 수이지 인가·배정 대수가 아니다</h4>
<p>공개 자료에 인가 대수가 없다. 실제로 몇 대를 급행으로 떼어낼 수 있는지는 인가·기사 배치·차고지
운영 조건에 달렸고 그 자료는 확보하지 못했다.</p>

<h4>9-2. 세 가지 가정 위에 있다</h4>
<table class="d">
<tr><th>가정</th><th>값</th><th>영향</th></tr>
<tr><td>정차 1회당 손실 T</td><td>20초</td><td>차내 단축폭을 좌우. 15~30초로 모두 돌렸고 <b>권장 5대로 동일</b></td></tr>
<tr><td>평균 통행 길이</td><td>편도의 1/3</td><td><b>차내 단축폭을 선형으로 좌우</b>. 1/4이면 2.9분, 1/2이면 5.7분</td></tr>
<tr><td>출발·도착 독립</td><td>42% = 64.7%²</td><td>급행 이용 가능 비중. 실제 통행 분포를 모른다</td></tr>
</table>

<h4>9-3. 정차 1회당 손실시간(T)은 실측에 실패했다</h4>
<p>세 방법 모두 실패했다. <b>문헌</b>은 국내 논문이 서울 간선·중앙차로 기준이라 부적합,
<b>첫차 시각 역산</b>은 기점·종점 시각차가 편도거리와 음의 상관(−0.51)이라 소요시간이 아니었으며,
<b>회귀</b>는 R²가 0.11→0.08로 떨어지고 환산 주행속도가 61~113km/h로 비현실적이었다.</p>

<h4>9-4. 분석 과정에서 자체 발견하고 정정한 오류</h4>
<table class="d">
<tr><th>오류</th><th>정정</th></tr>
<tr><td>구간 중앙값×구간수로 88-1 왕복 78분 추정</td><td>실측 98분. <b>26% 과소</b>. 외삽값 사용 금지 규칙 도입</td></tr>
<tr><td><code>peekAlloc</code>을 "첨두 배차"로 오독</td><td>명세상 "평일 최소 배차". 관련 주장 4건 철회</td></tr>
<tr><td>급행 대수를 <code>(3,5,6,8,10)</code>으로 하드코딩</td>
    <td>전수로 교체. "380번 무증차 전부 마이너스"가 틀렸음이 드러남(1대 +1.2분)</td></tr>
<tr><td>350번 왕복을 완주 2대로 136분이라 함</td><td>관측창 확대 후 <b>완주 13대 150분</b>. 절단 편향</td></tr>
<tr><td>첨두를 구간 중간시각으로 분류 / 공장지대가 350번을 잃는다고 서술</td>
    <td>연속 관측쌍 기준으로 교체 / 완행은 계속 정차한다(손해 +0.98분)</td></tr>
</table>

<h4>9-5. 비교 노선의 왕복시간은 재계산한 값이다</h4>
<p>88-1·380·55번의 왕복시간은 초기 분석의 값이 아니라 <b>이 보고서의 방법으로 다시 계산한 값</b>이다.
55번은 초기 195분에서 <b>200분</b>으로, 380번은 200분에서 <b>187분</b>으로 바뀌었다.
초기 값은 완주 차량 표본이 얇아 빠른 차량 쪽으로 치우쳐 있었다(§9-4의 절단 편향과 같은 원인).
<b>이 보정으로 네 노선 비교의 결론은 바뀌지 않았다</b> — 55번은 방식 A에서만, 350번은 A·B 모두에서 성립한다.</p>

<h4>9-6. 확보하지 못한 자료</h4>
<ul>
<li><b>온실가스 배출계수</b> — 국토해양부 고시 제2010-592호가 1차 출처이나 수치가 첨부파일로만 공개되어 직접 인용하지 못했다. 총 배출계수를 <b>1.0·1.1·1.3 kgCO₂/km로 바꿔가며</b> 돌렸고 아홉 조합 모두 감축이었다. 절대 감축량(tCO₂)은 제시하지 않는다.</li>
<li><b>탄소 추정은 상한이다</b> — 정차 절감을 ½mv²로 계산했으나 신호·정체로 어차피 멈추는 경우를 빼지 않았다. 또 350번의 실제 연료를 확인하지 않아 경기 사업형 승합 CNG 통계를 대리값으로 썼다. 제동 회생이 있는 차량이면 절감폭이 줄어든다.</li>
<li><b>수단 전환은 산출하지 않았다</b> — 급행 후에도 상대원→판교는 승용차가 더 빠르므로 승용차에서 버스로의 전환 규모를 가정하지 않았다. 본문의 탄소 감축은 <b>운행 구조 변화만</b>으로 계산한 값이다.</li>
<li><b>노선별 OD</b> — 수혜·불편 인원을 사람 수로 환산할 수 없다. 64.7%는 기록 구성비다.</li>
<li><b>357번 완주 왕복</b> — 관측 128분이 왕복(170분)보다 짧아 완주가 없다. 170분은 환산값이며
  두 환산 방법이 168·170분으로 수렴한 것에 근거한다.</li>
<li><b>동일 출발·도착지의 기존 대안</b> — 같은 구간을 잇는 다른 노선·철도와의 총 이동시간 비교는
  범위 밖이다. <b>최종 타당성 판단에는 이 비교가 필요하다.</b></li>
</ul>
""")

row('분석도구<br>및 참고문헌', """
<table class="d">
<tr><th>구분</th><th>내용</th></tr>
<tr><td>도구</td><td>Python 3.14 (numpy, matplotlib) · Git · Claude (Anthropic) — Claude Code</td></tr>
<tr><td>주요 산출</td><td>차량별 순번 추적, 10분 단위 고유차량 계수, 단조증가 완주 판정,
  연속 관측쌍 기준 첨두 분리, 대기시간 분포 E[gap²]/(2·E[gap]), 급행 대수 전수 계산, 민감도 분석</td></tr>
<tr><td><b>코드</b></td><td><b>https://github.com/chocharles5678-png/seongnam-bus-express</b><br>
  <span class="s">수집·분석·시뮬레이션·도면·보고서 생성 코드와 원시 관측 자료 전체를 공개했다.
  인증키는 포함되지 않으며 <code>.env.example</code>에 필요한 변수명만 두었다.</span></td></tr>
</table>
<pre>python scripts/seongnam/x_collect_location.py 350 --interval 30 --minutes 240 --budget 500
python scripts/seongnam/x_peak.py 20261014 --route 350
python scripts/seongnam/x_express_trunk.py 350
python scripts/seongnam/x_sim_fleet.py 350 --fleet 19 --cycle 150 --T 20 --keep-trips
python scripts/seongnam/x_carbon.py --route 350 --fleet 19 --express 5</pre>
<p class="s">원시 관측은 <code>data/raw/bus_location/*.jsonl</code>에 날짜별로 쌓인다.
인증키는 <code>.env</code>에서 읽으며 코드에 포함되지 않는다.</p>

<h4>참고문헌</h4>
<ul>
<li>경기버스정보(GBIS) 노선정보 항목조회 명세. https://www.gbis.go.kr/gbis2014/publicService.action?cmd=mBusRouteInfo</li>
<li>공공데이터포털, 경기도 버스위치정보 조회. https://www.data.go.kr/data/15080648</li>
<li>공공데이터포털, 경기도 버스노선 조회. https://www.data.go.kr/data/15080662</li>
<li>경기데이터드림, 경기도 정류소별 승하차 인원 집계(2026.06). https://data.gg.go.kr</li>
<li>행정안전부, 주민등록 인구통계 — 행정동별 연령별 인구현황(2026.08). https://jumin.mois.go.kr</li>
<li>한국교통안전공단, 용도별 차종별 연료별 일평균 자동차주행거리(2022) — 탄소 산정의 주행거리 기준. https://www.data.go.kr/data/15088454</li>
<li>국토해양부 고시 제2010-592호, 교통수단별 온실가스 배출계수 — 지속가능교통물류발전법 제16조제2항 근거. <span class="s">수치가 첨부파일로만 공개되어 본문에서 직접 인용하지 못했다(§9-6).</span></li>
<li class="blank">[ 정차시간(dwell time) 문헌 — 국내 간선 기준 자료만 확인되어 본문에서 사용하지 않음 ]</li>
</ul>
""")

imgs = []
for path, no, cap, desc in FIGS:
    if not os.path.exists(path):
        imgs.append(f'<p class="blank">[ {no} 파일 없음: {path} ]</p>'); continue
    b64 = base64.b64encode(open(path, 'rb').read()).decode()
    imgs.append(f'<figure><img src="data:image/png;base64,{b64}" alt="{cap}">'
                f'<figcaption><b>{no}.</b> {cap}<br><span class="s">{desc}</span></figcaption></figure>')
row('분석결과<br>이미지<br><span class="add">(필수)</span>', '\n'.join(imgs), 'figs')


CSS = """
@page { size: A4; margin: 15mm 13mm; }
* { box-sizing: border-box; }
body { font-family: "Malgun Gothic","맑은 고딕",sans-serif; color:#111; margin:0;
       font-size:9.4pt; line-height:1.62; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.wrap { max-width: 184mm; margin: 0 auto; padding: 8mm 0; }
.head { text-align:center; border-bottom:2.2px solid #111; padding-bottom:7px; margin-bottom:12px; }
.head .ev { font-size:9pt; color:#52514e; letter-spacing:.02em; }
.head h1 { font-size:19pt; margin:5px 0 0; letter-spacing:.22em; }
table.form { width:100%; border-collapse:collapse; }
table.form > tbody > tr > th { width:26mm; background:#f4f5f7; border:1px solid #9aa0a6;
       font-size:9.6pt; font-weight:700; vertical-align:middle; text-align:center; padding:9px 4px; line-height:1.45; }
table.form > tbody > tr > td { border:1px solid #9aa0a6; padding:10px 11px; vertical-align:top; }
tr { page-break-inside: avoid; }
tr.figs { page-break-inside: auto; }
h4 { font-size:10.2pt; margin:13px 0 5px; padding-left:7px; border-left:3.4px solid #2a78d6; }
td > h4:first-child { margin-top:2px; }
p { margin:5px 0; }
p.lead { font-size:11pt; font-weight:700; margin:2px 0 7px; line-height:1.5; }
p.big { background:#f2f5fa; border-left:3.4px solid #2a78d6; padding:8px 11px; margin:9px 0; font-size:9.9pt; }
p.note { background:#fff8e6; border:1px solid #e8d9a8; padding:7px 10px; margin:7px 0; font-size:8.9pt; }
p.warn { background:#fdeeea; border-left:3.4px solid #eb6834; padding:7px 10px; margin:8px 0; font-size:8.9pt; }
p.arrow { color:#444; font-size:8.9pt; margin:3px 0 9px 10px; }
p.eq, div.rule, div.flow, div.box, pre { background:#f6f7f9; border:1px solid #e0e2e6;
       padding:8px 11px; margin:7px 0; font-size:8.9pt; line-height:1.78; }
div.box { text-align:center; font-size:10pt; }
div.flow { line-height:1.95; text-align:center; }
pre { font-family:Consolas,"D2Coding",monospace; font-size:8.1pt; white-space:pre-wrap; line-height:1.6; }
code { font-family:Consolas,"D2Coding",monospace; font-size:8.5pt; background:#f0f1f3; padding:0 3px; border-radius:2px; }
blockquote { margin:4px 0 2px 10px; padding:6px 11px; border-left:3px solid #9aa0a6;
       background:#fafafa; font-size:9.3pt; }
ul, ol { margin:5px 0; padding-left:19px; } li { margin:2.5px 0; }
ol.key { counter-reset:k; list-style:none; padding-left:0; }
ol.key li { counter-increment:k; position:relative; padding-left:21px; margin:5px 0; }
ol.key li::before { content:counter(k); position:absolute; left:0; top:1px; width:15px; height:15px;
       background:#2a78d6; color:#fff; border-radius:50%; font-size:8pt; text-align:center; line-height:15px; font-weight:700; }
table.d { width:100%; border-collapse:collapse; margin:7px 0; font-size:8.7pt; }
table.d th { background:#eef0f3; border:1px solid #c3c7cc; padding:5px 6px; text-align:center; line-height:1.4; }
table.d td { border:1px solid #c3c7cc; padding:5px 6px; vertical-align:middle; }
table.d.n td { text-align:center; } table.d.n td:first-child { text-align:left; }
table.d.data td { font-size:8.2pt; word-break:break-all; }
tr.hl td { background:#f2f5fa; } td.hl2 { background:#e6f0fb; }
td.ok { color:#1d6b2c; font-weight:700; } td.no { color:#b4341a; font-weight:700; }
.s { color:#52514e; font-size:8.2pt; }
.blank { color:#b4341a; font-weight:700; }
.add { font-weight:400; font-size:8pt; color:#52514e; }
figure { margin:0 0 13px; page-break-inside:avoid; }
figure img { width:100%; border:1px solid #d8dade; display:block; }
figcaption { font-size:8.5pt; color:#333; padding-top:5px; line-height:1.55; }
"""

body = '\n'.join(
    f'<tr class="{cls}"><th>{lab}</th><td>{html}</td></tr>' for lab, html, cls in ROWS)

HTML = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>분석보고서 — 성남 시내버스 350번 무증차 급행 재편</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<div class="head">
  <div class="ev">- AI와 함께하는 교통문제 해결을 위한 데이터 분석 공모전 -</div>
  <h1>분석보고서</h1>
</div>
<table class="form"><tbody>
{body}
</tbody></table>
</div></body></html>"""

os.makedirs('output', exist_ok=True)
out = 'output/분석보고서_350번.html'
open(out, 'w', encoding='utf-8').write(HTML)
print(f'-> {out}  ({len(HTML)/1024/1024:.2f} MB, 그림 {len(FIGS)}장 포함)')
print('   브라우저에서 열고 Ctrl+P → 대상 "PDF로 저장" → 배경 그래픽 켜기')
