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
    ('figures/배차역설_4개노선.png', '그림 1',
     '배차 역설 — 최선값의 순서가 현행 배차 순서와 정확히 일치한다. 네 노선 모두 음수다',
     '네 노선을 같은 틀로 실측하고 같은 탑승 규칙(§7-3)으로 비교했다. 각 노선에서 평균 순효과가 '
     '가장 높은 배정을 표시했고 −2.93 → −0.69 → −0.18 → −0.12분으로 현행 배차 24.5 → 18.7 → '
     '11.1 → 7.9분 순서와 같다. 병행 노선 보완은 350번에만 실측해 이 도면에는 넣지 않았다.'),
    ('figures/무증차_350.png', '그림 2',
     '350번 무증차 재편 — 평균은 0 근처이고, 이득과 손해가 집단별로 갈린다',
     '왼쪽은 급행 배정 대수별 집단 손익과 급행 간격(운영 방식 B · 병행 노선 반영). 급행을 늘릴수록 '
     '①의 이득과 ③의 손해가 함께 커지고 전체 평균은 0 근처에 머문다. 오른쪽은 아낀 23분을 '
     '더 도는 데 쓸 때(A)와 회차 여유로 둘 때(B)의 효과·탄소 비교이며 막대의 단위가 서로 다르다. '
     '집단 비중은 정류소 기록으로 가중한 모형 비중이지 실제 수혜·피해 인구 비율이 아니다.'),
]

ROWS = []


def row(label, html, cls=''):
    ROWS.append((label, html, cls))


row('이름 / 팀명', '<p class="lead" style="margin:0">중앙조~달</p>')

row('주제', """
<p class="lead">마을버스 연계를 고려한 시내버스 급행 재편의 운영 조건과 이용자 영향<br>
— 성남시 350번 무증차 재편 사례를 중심으로</p>
<p>주거지에서 마을버스로 거점에 접근한 뒤 급행 시내버스로 주요 업무·생활지역까지 이동하는 방안을
검토한다. 성남의 네 후보 노선을 비교하고 350번을 상세 사례로 삼아, 기존 차량의 일부를 급행으로 전환할
때의 <b>시간 편익과 일반서비스 부담, 배출량 변화의 조건</b>을 분석한다.</p>
<p class="big"><b>급행을 탈 수 있는 사람 중 실제로 타는 비중은 정차역 수가 아니라 배차 간격이 정한다.</b>
350번 기본안에서 급행 정차 지점 이용자의 <b>30.6%</b>만 급행을 탄다. 네 노선을 같은 규칙으로 비교하면
평균 순효과의 최대값이 <b>현행 배차 간격 순서와 정확히 일치</b>한다 — 24.5 → 18.7 → 11.1 → 7.9분이
−2.93 → −0.69 → −0.18 → −0.12분이다. <b>급행 설계는 정차역 선정이 아니라 배차 설계에서 시작해야 한다.</b></p>
""")

row('분석 배경<br>및 목적', """
<p>대중교통의 편의는 주거지에서 정류장까지의 접근성과 주요 목적지까지의 이동시간을 함께 고려해야 한다.
본 분석은 성남의 주거생활권에서 판교·야탑·모란 등 주요 업무·생활거점으로 이어지는 이동을 대상으로,
마을버스로 거점까지 접근하고 급행 시내버스로 거점 간을 이동하는 구상에서 출발했다. <b>승용차 이용에
제약이 있는 시민의 이동 선택지를 넓히는 것</b>이 이 구상의 목적이다.</p>
<p>검토 대상은 기존 시내버스의 일부 운행을 급행으로 전환하는 <b>무증차 재편</b>이다. 이 경우 급행
이용자의 차내시간이 줄어들 가능성과 함께, <b>통과 정류장을 이용하는 시민의 대기시간이 늘어날 수
있다.</b> 따라서 정차 수뿐 아니라 배차 간격, 목적지까지 이어지는 병행노선, 일반서비스의 유지 조건을
함께 살펴야 한다.</p>
<p>이에 노선·정류소 자료와 공개 버스위치정보의 관측값을 활용해 성남의 네 후보 노선을 비교하고,
350번을 상세 분석하였다. 급행 정차계획과 차량 배분에 따른 <b>집단별 시간 편익·부담</b>을 평가하고,
운행거리와 정차 변화에 따른 배출 영향을 가정별로 검토하였다. 이를 통해 마을버스 연계 구상 중 시내버스
급행 재편을 검토할 <b>운영 조건과 일반서비스 보호 과제</b>를 제시하고자 한다.</p>
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
</table>
<p><b>수집 방법</b> 활용신청 후 발급받은 인증키로 <b>공식 OpenAPI를 호출</b>했다. 크롤링·비공개 경로는
쓰지 않았고 개발계정 한도(일 1,000회) 안에서 호출 예산을 두었다. <b>인증키는 환경변수로 분리해 코드·
제출물에 포함하지 않았다.</b><br>
<b>수집 기간</b> 버스위치 <b>2026-10-05 ~ 10-14</b>(평일 6일, 폴링 30~45초) — 10-07 88-1·55·380(992회),
10-12 55(600회), 10-13 350(352회), <b>10-14 350 첨두 480회</b>·357(274회). 승하차 2026-06-30 /
인구 2026-08-31 / 노선·정류소 제원 2026-10 조회분.<br>
<b>주요 변수</b> 위치 API <code>ts, route, plateNo, stationId, stationSeq</code> · 노선 API 경유 순서,
기·종점, <code>peekAlloc</code>(평일 최소 배차) · 승하차 정류소ID, 승차합계, 초승, 환승, 하차합계.
승하차 자료는 상업적 이용 및 변경 허용, OpenAPI는 포털 이용약관에 따른다.</p>
<p class="s">승하차 집계로 급행 정차역을 선정했다(성남시 1,305개소, 총 24,860,507건). GBIS 명세는
배차 필드 정의 확인에 썼다 — <code>peekAlloc</code>을 "첨두 배차"로 오독했다가 명세 원문이
"평일 최소 배차시간"임을 확인하고 관련 주장 4건을 철회했다.</p>
""")

row('분석과정<br>및 방법', """
<p class="s">노선·정류소 제원 수집 → 위치 API 폴링(30~45초) → 운행 대수·왕복시간 실측 →
급행 정차역 선정 → 무증차 재편 제한 탐색 → 주행거리·정차 변화 산출</p>
<h4>5-1. 운행 대수와 왕복 소요시간</h4>
<p class="big"><b>추정을 버리고 위치 API를 직접 폴링한 이유.</b> 효과는 왕복 소요시간과 운행 대수에서
전부 결정되는데 두 값은 공개 자료에 없다. 구간 소요시간 중앙값 × 구간 수로 88-1번 왕복을 추정하면
<b>78분</b>이지만 실측은 <b>98분</b>이었다 — 회차·회복 시간이 빠져 <b>26% 과소</b>다. 이 차이를 확인한
뒤 추정을 결론에 쓰지 않기로 하고, 버스위치정보 API 응답의 <b>차량번호(plateNo)</b>와
<b>정류소순번(stationSeq)</b>을 차량별로 추적해 두 값을 <b>직접 측정</b>했다. 이 분석의 모든 운행
수치는 여기서 나왔다.</p>
<p><b>운행 대수</b>는 10분 단위 고유 차량번호의 중앙값이다 — 1시간으로 세면 교대·투입 차량까지 누적돼
과대 집계된다(350번 1시간 23대 vs 10분 19대). <b>왕복 소요시간</b>은 정류소 순번이 단조 증가하는 가장 긴
구간에서 진행률 95% 이상인 <b>완주 차량</b>의 중앙값이다. 이 집합은 관측 종료 시각에 절단되어 빠른 차량
쪽으로 치우치므로(§7-1) <b>350번은 관측창을 왕복의 1.6배(240분)까지 늘렸다.</b> 380번은 관측창이
왕복보다 짧아 완주 차량이 없어 통과 속도 환산값을 썼다. 왕복(150분)이 첨두창(115분)보다 길어
첨두 안에서 완주가 나올 수 없어, 첨두 통과 속도는 <b>연속 관측쌍 중 양 끝 시각이 모두 같은 창 안인
것만</b> 모아 집계했다.</p>

<h4>5-2. 급행 정차역 선정 규칙 — 다음의 합집합</h4>
<div class="rule">
① 기·종점·회차점 &nbsp;|&nbsp; ② 거점: 지점 왕복 일평균 승하차 ≥ 3,000건 &nbsp;|&nbsp;
③ 대학: 정류소명에 대학/가천대/을지대/신구대 포함 AND ≥ 1,000건<br>
④ 환승거점: 마을버스 5개 이상 경유 &nbsp;|&nbsp; ⑤ 20대 거점: 행정동 20대 ≥ 2,500명 AND 지점 ≥ 1,500건
</div>
<p>교집합으로는 최대 거점이 탈락해 <b>합집합</b>으로 했다. 집계는 <b>정류소 고유ID 기준</b>이다 —
이름으로 묶으면 같은 이름이면서 경유 마을버스 수가 다른 102곳의 값이 뭉개진다.
<b>노선 선정은 전적으로 실측 배차와 운행 대수로 했고 연령은 조건으로 쓰지 않았다</b> — 위 ⑤는
정차역 선정의 보조 지표일 뿐이다. <b>이 기준은 55번에 적용한 것과 동일하며 350번에 맞춰 조정하지
않았다.</b> 기준을 2,000/1,500으로 낮추면 24지점·커버 75.9%, 4,000/3,500으로 높이면 14지점·59.3%이고, 본문은 더 유리한 기준을 쓰지 않았다.</p>

<h4>5-3. 시뮬레이션 모형</h4>
<p>완행 왕복 = 150분(실측), 급행 왕복 = 150 − (통과 69회 × T) = <b>127분</b>. 각 서비스는
<b>자기 왕복시간 ÷ 자기 대수</b> 간격으로 운행하고 평균 대기는 <b>E[gap²] / (2·E[gap])</b>이다.</p>
<p>출발·도착이 <b>모두</b> 급행 정차 지점인 통행은 완행 잔여대기와 (급행 잔여대기 − 차내단축) 중
<b>작은 쪽</b>을 택하고, 차내 단축은 <b>급행을 실제로 탄 경우에만</b> 생긴다(§7-3).
한쪽이라도 통과 지점이면 완행 또는 병행 노선을 탄다(§7-3).</p>
<p class="warn"><b>가정 다섯.</b> <b>① T(정차 1회당 손실) = 20초</b> — 30초 폴링으로는 정류소 정차와
신호 정체를 구분할 수 없어 실측 3방법이 모두 실패했다. <b>② 평균 통행 = 편도의 1/3</b> — 차내 단축폭을
<u>선형으로</u> 좌우한다. <b>③ 출발·도착 독립</b> — 급행 이용 가능 41.8%는 기록 구성비 64.7%의 제곱이다.
<b>④ 병행 노선 1개의 배차 20분</b> — 357번만 실측했다. <b>⑤ 병행 노선의 차내 시간이 350번과 같다</b> —
경로가 다르므로 통과 지점 손해는 본문 값보다 클 수 있다. ①④는 평균의 부호를 가른다(§7-3).</p>
""")

row('AI 기술<br>활용', """
<p><b>활용 서비스</b> Claude (Anthropic) — Claude Code. <b>활용 범위</b> 공식 수집처 확인, Python
수집·정제·검증 코드 작성, 시뮬레이션 구현, 도면 생성, 문서 구성. <b>검증 방식</b> AI가 낸 수치는
<b>원본 재집계와 재실행으로 대조</b>한 뒤에만 썼고 AI의 설명 자체를 실측 자료로 쓰지 않았다.</p>
<h4>주요 프롬프트 — 분석 방향을 바꾼 여섯 지점</h4>
<p class="s">아래는 분석의 방향을 바꾼 입력의 <b>요지</b>다. 구어체 원문을 기술 용어로 정리했으며
<b>지시 내용은 바꾸지 않았다.</b> 원문은 대화 기록에 남아 있다.</p>
<table class="d">
<tr><th>시점</th><th>입력 요지</th><th>분석에 반영된 결과</th></tr>
<tr><td>10-08</td><td>350번과 330·220번이 공유하는 정류소가 <b>노선 순서상 연속인지</b> 전수로 검증할 것</td>
    <td>공유 정류소를 단순 개수가 아니라 <b>연속 구간</b>으로 세는 기준을 세웠다. 350번 90정차 전부에
    병행 노선이 있어 <b>독점 구간이 0</b>임을 확인했고, 이 기준이 뒤의 목적지 커버 q로 이어졌다(§7-3)</td></tr>
<tr><td>10-15</td><td>본문 수치를 원자료와 전수 대조해 <b>출처가 불분명하거나 표류한 값</b>을 찾을 것</td>
    <td>내부 불일치 5건과 <b>적용 범위 혼용</b>을 발견했다. 탄소 산출의 적용 범위를 전일과 첨두 2시간으로
    분리해 각각 −3.7%·−0.53%로 다시 적고, 제안 범위와 일치하는 값을 쓰도록 바로잡았다(§7-4)</td></tr>
<tr><td>10-16</td><td>외부 검토 지적을 전면 수용하고, <b>같은 유형의 오류를 사전에 거르는 점검 절차</b>를
    만들 것</td>
    <td>대기와 차내 단축을 서로 다른 탑승 선택에 묶어 더한 <b>모형 구조 오류</b>를 인정해
    <b>+0.44분을 철회</b>했다. 분해한 항이 같은 선택에 묶여 있는지 확인하는 절차를 만들어 이후 분석에
    적용했다(§7-3)</td></tr>
<tr><td>10-17</td><td>차량 증편은 제안 범위에서 제외하고, <b>기존 19대의 배분 변경만으로</b> 성립
    가능성을 검토할 것</td>
    <td>증차 효과를 먼저 전수로 계산한 뒤, 주행거리가 <b>+24.9%</b> 늘어 탄소중립 취지와 상충한다는
    이유로 제안에서 제외했다. 이후 모든 산출은 <b>기존 19대 배분</b>만을 전제로 한다(§7-2·§8-3)</td></tr>
<tr><td>10-17</td><td>급행 탑승자의 차내 단축 외에 <b>다른 집단에 생기는 효과</b>를 분리해 제시할 것</td>
    <td>평균 하나로 보던 효과를 <b>급행 이용 가능(41.8%) · 통과·병행 대체 가능(50.0%) ·
    통과·대체 없음(8.2%)</b> 세 집단으로 분해했다. 평균이 −0.091분인데 ③은 −1.41분임이 여기서
    드러났다(§7-3)</td></tr>
<tr><td>10-17</td><td>완행 간격 확대로 생기는 <b>통과 지점의 대기 부담을 병행 노선으로 보완</b>할 수
    있는지 볼 것</td>
    <td>통과 지점 손해를 −1.41분으로 일괄 적용하던 것을 각 정류장의 병행 노선으로 가중했다.
    <b>목적지 커버 q = 0.860</b>을 도입해 실제 손해 집단을 통과 지점 전체에서 <b>대체 없는 8.2%</b>로
    좁혔다(§7-3)</td></tr>
</table>

<h4>AI 활용에서 실제로 작동한 것 — 반증 장치</h4>
<p><b>① 1차 명세로 필드 해석을 반증했다.</b> <code>peekAlloc</code>을 "첨두 배차"로 읽은 것이 오독임을
GBIS 명세 원문에서 확인하고 관련 주장 4건을 철회했다. <b>② 전수 계산과 표본 확대로 코드 결함을
잡았다.</b> 급행 대수를 <code>(3,5,6,8,10)</code>으로 하드코딩해 N=1·2를 건너뛰었고, 350번 왕복은
완주 2대 136분에서 관측창 확대 후 완주 13대 150분이 됐다. <b>③ 외부 검토자의 독립 구현이 모형 자체의
오류를 잡았다</b> — 전수 계산과 민감도로는 드러나지 않는 종류였다(§7-3).
<b>AI가 낸 수치는 어느 것도 이 세 장치를 통과하기 전에 결론으로 쓰지 않았다.</b></p>
""")

row('분석 내용<br>및 결과', """
<h4>7-1. 네 노선 실측 — 갈림길은 배차 하나다</h4>
<table class="d n">
<tr><th>노선</th><th>왕복<br>정차</th><th>공시 배차</th><th>왕복 소요<br>(실측)</th>
    <th>관측<br>대수</th><th>배차<br>(왕복÷대수)</th><th>공시 대비</th><th>급행 분리<br>(최선 배정)</th></tr>
<tr><td>88-1 <span class="s">마을</span></td><td>71회</td><td>15~25분</td><td><b>98분</b></td><td><b>4.0대</b></td>
    <td>24.5분</td><td class="no">최소값의 1.6배</td><td class="no">−2.93분</td></tr>
<tr><td>380</td><td>106회</td><td>15~25분</td><td><b>187분</b><span class="s">*</span></td><td><b>10.0대</b></td>
    <td>18.7분</td><td>범위 안</td><td class="no">−0.69분</td></tr>
<tr><td>55</td><td>127회</td><td>10~20분</td><td><b>200분</b></td><td><b>18.0대</b></td>
    <td>11.1분</td><td>범위 안</td><td class="no">−0.18분</td></tr>
<tr class="hl"><td><b>350</b></td><td><b>90회</b></td><td><b>7~9분</b></td><td><b>150분</b></td>
    <td><b>19.0대</b></td><td class="hl2"><b>7.9분</b></td><td>범위 안</td>
    <td class="hl2"><b>−0.12분</b></td></tr>
</table>
<p class="big"><b>마지막 열의 순서가 배차 순서와 정확히 일치한다</b> — 24.5 → 18.7 → 11.1 → 7.9분이
−2.93 → −0.69 → −0.18 → −0.12분이다. <b>네 노선 모두 음수이고 350번이 가장 덜 나쁘다.</b>
이 순서는 간격 산술에서 나오므로 아래 가정들과 무관하다. 350번만 상세 분석 대상으로 골랐다.</p>
<p class="s">* 380번은 관측창이 왕복보다 짧아 완주 차량이 없다. 187분은 통과 속도 환산값이다. 네 노선 모두
같은 방법(<code>x_peak.py</code>)으로 계산했다 — 88-1·380은 10-07, 55는 10-12, 350은 10-14 첨두.
350번은 관측 240분·완주 13대로 왕복 중앙값 150분이다(155분만 관측했을 때는 완주 2대·136분 — 절단 편향).</p>

<h4>7-2. 급행 정차역 17지점과 운영 방식</h4>
<p>정차역은 §5-2의 다섯 규칙으로 <b>17지점 / 왕복 정차 90회 → 21회(통과 69회) / 기록 커버 64.7%</b>다.
급행은 왕복이 150분에서 <b>127분</b>으로 짧아지는데, 이 <b>23분</b>을 더 도는 데 쓰면(A) 간격 25.4분·
평균 +0.03분이지만 <b>주행거리가 4.8% 늘어</b> 탄소가 상쇄되고, 회차 여유로 두면(B) 간격 30.0분·
평균 −0.091분이지만 <b>주행거리 0%·정차 −20.2%</b>다. <b>B를 택했다</b> — 평균을 0.12분 내주고 탄소
감축과 운영 현실성(지연 흡수·기사 휴식)을 얻는다. <b>두 방식 모두 평균이 0 근처다 — 운영 방식 선택이
부호를 가를 만큼 효과가 작다.</b> 아래는 전부 B 기준이다.</p>

<h4>7-3. 재편 결과 — 평균은 0 근처, 이득과 손해가 집단별로 갈린다</h4>
<div class="box">
<b>탑승 규칙</b> &nbsp; 승객은 완행과 급행 중 <b>자기 총시간이 짧은 쪽</b>을 탄다.
급행의 차내 단축은 <b>급행을 실제로 탄 사람에게만</b> 생긴다.
</div>
<p>2026-10-16까지 우리는 대기를 "먼저 오는 차를 탄다"로 계산하면서 차내 단축은 급행 정차 지점 이용자
전원에게 더했다. <b>한 식에 서로 다른 두 사람이 들어가 있었다.</b> 일관된 규칙으로 고치면 아래와 같고
이전 판의 <b>+0.44분은 철회한다</b>. 완행 간격 a·급행 간격 b·차내 단축 S에 대해 <b>a + S ≤ b</b>이면
급행 탑승 확률은 <b>P = (a/2 + S)/b</b>이고, 조건이 깨지면 적분이 포화되어 일반식을 쓴다
(350번은 급행 9대부터 깨진다).</p>
<table class="d n">
<tr><th>급행 대수</th><th>1</th><th>3</th><th>5 <span class="s">(제안)</span></th><th>7</th><th>9</th></tr>
<tr><td>급행 / 완행 간격</td><td>150 / 8.3분</td><td>50.0 / 9.4분</td><td><b>30.0 / 10.7분</b></td>
    <td>21.4 / 12.5분</td><td>16.7 / 15.0분</td></tr>
<tr><td>급행 탑승 비중</td><td>5.3%</td><td>17.0%</td><td><b>30.6%</b></td><td>47.1%</td><td>67.1%</td></tr>
<tr><td>① 급행 이용 가능 (41.8%)</td><td>+0.01분</td><td>+0.06분</td><td class="ok"><b>+0.16분</b></td>
    <td class="ok">+0.37분</td><td class="ok">+0.86분</td></tr>
<tr><td>② 통과 · 병행 대체 가능 (50.0%)</td><td>−0.03분</td><td>−0.05분</td><td><b>−0.08분</b></td>
    <td>−0.13분</td><td>−0.19분</td></tr>
<tr><td>③ 통과 · <b>대체 없음</b> (8.2%)</td><td class="no">−0.22분</td><td class="no">−0.74분</td>
    <td class="no"><b>−1.41분</b></td><td class="no">−2.30분</td><td class="no">−3.55분</td></tr>
<tr class="hl"><td><b>통행당 평균</b></td><td class="no">−0.026분</td><td class="no">−0.060분</td>
    <td class="no"><b>−0.091분</b></td><td class="no">−0.095분</td><td class="no">−0.025분</td></tr>
</table>
<p class="s">급행 정차 지점 이용자 41.8% 중 30.6%, 즉 <b>전체 통행의 12.8%</b>만 급행을 탄다. 집단 비중은
<b>정류소 기록으로 가중한 모형 비중</b>이며 실제 수혜·피해 인구 비율이 아니다.</p>
<p><b>통과 지점을 ②와 ③으로 나눈 기준.</b> 급행이 건너뛴 정류장에도 다른 노선이 선다. 350번 순서상
<b>연속 3정차 이상</b>을 공유하고 그 구간이 상대 노선에서도 연속인 노선만 병행으로 세면 지점당 중앙값
8개이고 <b>독점 구간은 0개</b>다. 다만 병행이 데려다 주는 곳은 공유 구간까지이므로, 각 지점에서 하류
목적지 중 병행이 닿는 비중을 q로 재면 기록 가중 <b>q = 0.860</b>이다. 즉 통과 지점 기록의 <b>86.0%는
병행으로 대체되고(②), 14.0%는 대체 수단이 없다(③).</b> 손해 = q × (완행+병행 합산 대기 증가) +
(1−q) × (완행 단독 증가)로 쓴다. 병행을 완전 대체재로 취급해 이 분해를 빼면 "완행을 없앨수록 좋다"는
모퉁이 해가 나온다.</p>
<p class="warn"><b>q는 357·330·220 세 노선이 사실상 결정한다.</b> 연속 공유 하한을 2에서 20정차까지
올려도 q가 움직이지 않다가, 25정차로 올려 330·220을 빼면 <b>0.860 → 0.533</b>으로 떨어진다.
<b>이 셋 중 하나가 감축·변경되면 이 분석의 토대가 사라진다.</b> 357번만 실측했고(배차 20.0분)
330·220은 미측정이다. 또한 <b>정차손실 20초는 실측에 실패한 가정값</b>이고 15~30초 × 병행 15~30분의
12조건에서 평균은 <b>−0.241 ~ +0.196분</b>으로 부호가 바뀐다. <b>−0.091분을 실측 효과로 쓰지 않는다.</b></p>
<p class="s"><b>검증</b> — 해석식·격자적분(3,000×3,000)·몬테카를로(200만 명)가 소수 셋째 자리까지
일치했고, 급행 간격을 무한대로 보내면 완행 단독값(−1.4098분)으로 수렴한다. 외부 검토자가 공개 코드를
독립 구현해 기본값 <b>−0.0927454</b>를 재현했고 우리 값과 2.6×10<sup>−7</sup>분 차이였다.</p>

<h4>7-4. 탄소 — 적용 범위를 섞지 않는다</h4>
<p>버스 배출의 일부는 <b>감속으로 버린 운동에너지를 재가속으로 회복하는 연료</b>와 정차 중 공회전에서
나온다. 정차 1회 손실 = ½mv² ÷ 구동효율 ÷ 연료발열량 × 배출계수 + 공회전연료 × 체류시간 × 배출계수로
쓰고 총배출계수를 주행분과 정차분으로 분해했다. 운영 방식 B는 왕복 횟수를 유지하므로 <b>주행거리가 0%</b>이고
정차만 준다 — <b>전일 전면 시행이면 정차 −20.2% / 탄소 −3.7%</b>이고, 첨두 2시간만 적용하면
전일 운행의 14.4%에 해당해 <b>정차 −2.9% / 탄소 −0.53%</b>다.</p>
<p class="warn"><b>본문은 제안 범위와 같은 전일 기준 −3.7%를 쓴다.</b> 적용 범위를 섞으면 같은 제안의
탄소 효과가 7배까지 달라진다. 환산 근거 — 222.4 km ÷ 왕복 40 km = 일 5.56 왕복, 첨두 2시간은
120 ÷ 150 = 0.80 왕복이므로 전일 운행의 <b>14.4%</b>다.</p>
""")

row('정책제안<br>및 기대효과', """
<div class="box">
급행 <b>5대</b> · 간격 <b>30.0분</b> &nbsp;|&nbsp; 완행 <b>14대</b> · 간격 <b>10.7분</b><br>
급행 정차 <b>17지점</b> · 왕복 정차 <b>90회 → 21회</b>(통과 69회) · 아낀 23분은 <b>회차 여유</b><br>
<b>차량 증편 없음 · 노선 신설 없음 · 총 주행거리 0% · 일일 탄소 −3.7%</b>
</div>
<h4>8-1. 누가 얼마나 빨라지나 — 멀리 가는 사람</h4>
<p>급행은 편도 44구간 중 <b>12곳에만 선다.</b> 건너뛴 정류소 하나당 20초(가정)가 줄어드니
<b>멀리 갈수록 이득이 커진다</b> — 전체 111개 구간의 차내 단축 중앙값 2.7분, 최대 12.0분이다.</p>
<table class="d n">
<tr><th>구간</th><th>급행이 통과</th><th>차내 단축</th>
    <th class="hl2">급행 시각을<br>알고 나오면</th><th>무작위로<br>나오면</th></tr>
<tr class="hl"><td style="text-align:left"><b>한국학중앙연구원 → 상대원차고지</b>
    <span class="s">(전 구간)</span></td><td>36곳</td><td><b>12.0분</b></td>
    <td class="ok"><b>+12.0분</b></td><td class="ok">+3.76분</td></tr>
<tr class="hl"><td style="text-align:left"><b>상대원차고지 → 이노밸리.포스코DX</b>
    <span class="s">(판교테크노밸리)</span></td><td>20곳</td><td><b>6.7분</b></td>
    <td class="ok"><b>+6.7분</b></td><td class="ok">+1.15분</td></tr>
<tr><td style="text-align:left">야탑역 → 이노밸리.포스코DX <span class="s">(짧은 구간)</span></td>
    <td>5곳</td><td>1.7분</td><td class="ok">+1.7분</td><td class="no">−0.43분</td></tr>
</table>
<p class="big"><b>급행 간격이 30분이므로 운행시각을 공시하면 출발 시각을 맞출 수 있고, 그만큼 대기
증가가 줄고 차내 단축이 남는다. 상대원 ↔ 판교 장거리 통근이 최대 수혜자이며 편도 11~12분이 그 상한이다.</b></p>

<h4>8-2. 전체로 보면 — 평균을 숨기지 않는다</h4>
<p>같은 도착시각으로 재편 전후를 모형 안에서 1건씩 비교하면(몬테카를로 200만, 평균 통행 = 편도 1/3)
<b>모형 통행의 21.4%</b>에서 시간이 줄어든다 — 급행을 타서 9.1%(+4.88분), 완행 14대가 균등 재배치되어
12.3%(+3.19분)다. 두 번째는 급행의 효과가 아니다. <b>관측이 아니라 모형 출력이며 수혜 인원 비율이
아니다.</b> 급행 17지점이 노선 기록량의 64.7%를 담는다(야탑역 왕복 일평균 기록 31,327, 모란역 20,790).</p>
<p class="warn">그러나 <b>통행당 평균은 −0.091분</b>이다 — 41.8%가 +0.16분을 얻고 통과 지점 중 병행으로
대체되는 50.0%가 −0.08분, <b>대체 수단이 없는 8.2%가 −1.41분을 잃는</b> 합이다.</p>
<p class="big"><b>그래서 이 제안의 근거는 평균이 아니다.</b> 평균은 정차손실 가정만으로 부호가 바뀌어
(§7-3) 지지도 기각도 하지 못한다. 근거는 <b>상대원 ↔ 판교 장거리 통근의 편도 11~12분</b>과 그 비용이
<b>차량 0대</b>라는 것이고, <b>통과 지점의 대기 부담이 실재하며 8.2%는 대체 수단이 없다</b>는 것도 같은
무게로 놓는다. <b>평균 하나로 결론을 내릴 수 있는 사안이 아니다.</b></p>

<h4>8-3. 도입 방안과 기대효과</h4>
<p class="big"><b>①</b> 관측 19대 중 5대를 <b>전일 급행으로 전환</b>하고 급행 운행시각을
<b>정류소·앱에 공시한다</b>(8-1 두 열의 차이가 전부 여기서 온다). <b>②</b> 시행과 함께 통과 지점의 실제 대기·혼잡·
승차 거절과 <b>실제 연료 소모</b>를 계측해 모형값과 대조한다. <b>③</b> 357·330·220의 실제 배차를 측정한다 —
대체 가능성이 이 셋에 걸려 있고, (1−q)×기록이 큰 판교원마을1·2단지·아튼빌후문은 정차 추가 후보로 둔다.</p>
<ul>
<li><b>차량 추가 없이</b> 상대원–판교 장거리 통근의 편도 <b>11~12분</b>을 단축한다. 주행거리는 늘지 않고
  정차만 <b>20.2%</b> 줄어 <b>일일 탄소를 3.7% 감축</b>한다(증차안은 주행거리 +24.9%).</li>
<li><b>급행 분할의 전제조건을 수치로 제시</b>한다 — 네 노선의 결과 순서가 현행 배차 순서와 정확히
  일치했다. <b>배차가 촘촘한 노선만 분할 여지가 있다.</b></li>
<li><b>급행 탑승 비중은 정차역이 아니라 배차가 정한다</b>는 것을 공식으로, <b>병행 노선은 개수가 아니라
  행선지로 세어야 한다</b>는 것을 q로 보였다. 병행 1개인 공장지대(q 0.75~1.00)가 병행 2~5개인
  운중동·낙생(q 0.56~0.64)보다 안전했다.</li>
</ul>
<p class="warn"><b>제시하지 않는 것.</b> 수혜 인원, 승용차 전환 수요, 탄소 절대 감축량(tCO₂)은 산출하지
않았다. 노선별 OD와 배출계수를 확보하지 못했기 때문이다. <b>추정값을 제시하지 않는 것이 이 보고서의
원칙이다.</b></p>
""")

row('분석도구<br>및 참고문헌', """
<p><b>도구</b> Python 3.14 (numpy, matplotlib) · Git · Claude (Anthropic) — Claude Code.
<b>주요 산출</b> 차량별 순번 추적, 10분 단위 고유차량 계수, 단조증가 완주 판정, 연속 관측쌍 기준 첨두
분리, 대기시간 분포 E[gap²]/(2·E[gap]), 급행 대수·정차표 제한 탐색, 12조건 민감도.</p>
<p class="big"><b>코드 https://github.com/chocharles5678-png/seongnam-bus-express</b><br>
<span class="s">수집·분석·시뮬레이션·도면·보고서 생성 코드와 원시 관측 자료를 공개했다. 차량번호는 노선별
가명(350-01 …)으로 치환했다 — 차량 식별 키로만 쓰므로 분석 결과는 동일하다. 인증키는 포함되지 않으며
<code>.env.example</code>에 변수명만 두었다.</span></p>
<pre>python scripts/seongnam/x_peak.py 20261014 --route 350
python scripts/seongnam/x_parallel.py --keep-trips
python scripts/seongnam/x_carbon.py --route 350 --fleet 19 --express 5</pre>

<h4>참고문헌</h4>
<ul>
<li>경기버스정보(GBIS) 노선정보 항목조회 명세. https://www.gbis.go.kr/gbis2014/publicService.action?cmd=mBusRouteInfo</li>
<li>공공데이터포털, 경기도 버스위치정보 조회. https://www.data.go.kr/data/15080648</li>
<li>공공데이터포털, 경기도 버스노선 조회. https://www.data.go.kr/data/15080662</li>
<li>경기데이터드림, 경기도 정류소별 승하차 인원 집계(2026.06). https://data.gg.go.kr</li>
<li>행정안전부, 주민등록 인구통계 — 행정동별 연령별 인구현황(2026.08). https://jumin.mois.go.kr</li>
<li>한국교통안전공단, 용도별 차종별 연료별 일평균 자동차주행거리(2022) — 탄소 산정의 주행거리 기준. https://www.data.go.kr/data/15088454</li>
<li>국토해양부 고시 제2010-592호, 교통수단별 온실가스 배출계수 — 지속가능교통물류발전법 제16조제2항 근거. <span class="s">수치가 첨부파일로만 공개되어 본문에서 직접 인용하지 못했다. 총 배출계수를 1.0·1.1·1.3 kgCO₂/km로 바꿔가며 돌렸고 절대 감축량(tCO₂)은 제시하지 않는다.</span></li>
<li><span class="s">정차시간(dwell time) 문헌은 국내 간선 기준 자료만 확인되어 본문에서 사용하지 않았다.
  정차 1회당 손실 20초는 가정값이며 15~30초 범위의 결과를 §7-3에 적었다.</span></li>
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
@page { size: A4; margin: 12mm 11mm; }
* { box-sizing: border-box; }
body { font-family: "Malgun Gothic","맑은 고딕",sans-serif; color:#111; margin:0;
       font-size:8.8pt; line-height:1.48; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.wrap { max-width: 188mm; margin: 0 auto; padding: 3mm 0; }
.head { text-align:center; border-bottom:2px solid #111; padding-bottom:4px; margin-bottom:7px; }
.head .ev { font-size:8.4pt; color:#52514e; letter-spacing:.02em; }
.head h1 { font-size:15pt; margin:3px 0 0; letter-spacing:.2em; }
table.form { width:100%; border-collapse:collapse; }
table.form > tbody > tr > th { width:26mm; background:#f4f5f7; border:1px solid #9aa0a6;
       font-size:8.9pt; font-weight:700; vertical-align:middle; text-align:center; padding:5px 3px; line-height:1.35; }
table.form > tbody > tr > td { border:1px solid #9aa0a6; padding:6px 8px; vertical-align:top; }
/* 서식 행이 한 쪽보다 길어 avoid 를 걸면 통째로 밀려 빈 공간이 생긴다. 쪼개 흘린다. */
tr { page-break-inside: auto; }
table.d { page-break-inside: avoid; }   /* 자료 표는 쪼개지 않는다 */
h4 { font-size:9.4pt; margin:8px 0 3px; padding-left:6px; border-left:3px solid #2a78d6; }
td > h4:first-child { margin-top:1px; }
p { margin:3px 0; }
p.lead { font-size:10.2pt; font-weight:700; margin:1px 0 4px; line-height:1.4; }
p.big { background:#f2f5fa; border-left:3px solid #2a78d6; padding:5px 8px; margin:5px 0; font-size:9.1pt; }
p.note { background:#fff8e6; border:1px solid #e8d9a8; padding:4px 7px; margin:4px 0; font-size:8.3pt; }
p.warn { background:#fdeeea; border-left:3px solid #eb6834; padding:4px 7px; margin:5px 0; font-size:8.3pt; }
p.arrow { color:#444; font-size:8.9pt; margin:3px 0 9px 10px; }
p.eq, div.rule, div.flow, div.box, pre { background:#f6f7f9; border:1px solid #e0e2e6;
       padding:5px 8px; margin:4px 0; font-size:8.3pt; line-height:1.55; }
div.box { text-align:center; font-size:9pt; }
div.flow { line-height:1.95; text-align:center; }
pre { font-family:Consolas,"D2Coding",monospace; font-size:8.1pt; white-space:pre-wrap; line-height:1.6; }
code { font-family:Consolas,"D2Coding",monospace; font-size:8.5pt; background:#f0f1f3; padding:0 3px; border-radius:2px; }
blockquote { margin:4px 0 2px 10px; padding:6px 11px; border-left:3px solid #9aa0a6;
       background:#fafafa; font-size:9.3pt; }
ul, ol { margin:3px 0; padding-left:17px; } li { margin:1.5px 0; }
ol.key { counter-reset:k; list-style:none; padding-left:0; }
ol.key li { counter-increment:k; position:relative; padding-left:21px; margin:5px 0; }
ol.key li::before { content:counter(k); position:absolute; left:0; top:1px; width:15px; height:15px;
       background:#2a78d6; color:#fff; border-radius:50%; font-size:8pt; text-align:center; line-height:15px; font-weight:700; }
table.d { width:100%; border-collapse:collapse; margin:4px 0; font-size:8.1pt; }
table.d th { background:#eef0f3; border:1px solid #c3c7cc; padding:3px 4px; text-align:center; line-height:1.3; }
table.d td { border:1px solid #c3c7cc; padding:3px 4px; vertical-align:middle; }
table.d.n td { text-align:center; } table.d.n td:first-child { text-align:left; }
table.d.data td { font-size:8.2pt; word-break:break-all; }
tr.hl td { background:#f2f5fa; } td.hl2 { background:#e6f0fb; }
td.ok { color:#1d6b2c; font-weight:700; } td.no { color:#b4341a; font-weight:700; }
.s { color:#52514e; font-size:7.7pt; }
.blank { color:#b4341a; font-weight:700; }
.add { font-weight:400; font-size:8pt; color:#52514e; }
figure { margin:0 0 7px; page-break-inside:avoid; }
figure img { width:100%; border:1px solid #d8dade; display:block; }
figcaption { font-size:7.9pt; color:#333; padding-top:3px; line-height:1.42; }
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
