import { readFileSync } from "fs";
import * as XLSX from "xlsx";

const rows = JSON.parse(readFileSync("data/transit_car_comparison.json", "utf-8"));

const wb = XLSX.utils.book_new();

const wsData = XLSX.utils.json_to_sheet(rows);
wsData["!cols"] = [
  { wch: 45 }, { wch: 14 }, { wch: 12 }, { wch: 16 }, { wch: 10 },
  { wch: 12 }, { wch: 30 }, { wch: 16 }, { wch: 14 }, { wch: 18 }, { wch: 30 },
];
XLSX.utils.book_append_sheet(wb, wsData, "대중교통vs자동차 비교");

const validRows = rows.filter((r: any) => typeof r.소요시간_비율_대중교통나누기자동차 === "number");
const byGroup: Record<string, number[]> = {};
for (const r of validRows) {
  byGroup[r.출발유형] = byGroup[r.출발유형] || [];
  byGroup[r.출발유형].push(r.소요시간_비율_대중교통나누기자동차);
}
const avg = (arr: number[]) => (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2);

const summaryRows = [
  { 항목: "분석 대상 구간 수", 값: `${rows.length}개 (성공 ${validRows.length}개 / 할당량 초과로 미수집 ${rows.length - validRows.length}개)` },
  ...Object.entries(byGroup).map(([g, arr]) => ({
    항목: `${g} 평균 소요시간 비율 (대중교통/자동차)`,
    값: `${avg(arr)}배 (${arr.length}개 구간 평균)`,
  })),
];
const wsSummary = XLSX.utils.json_to_sheet(summaryRows);
wsSummary["!cols"] = [{ wch: 45 }, { wch: 40 }];
XLSX.utils.book_append_sheet(wb, wsSummary, "요약");

const noteRows = [
  { 항목: "출처1", 내용: "ODsay 대중교통 길찾기 API (lab.odsay.com) - 총소요시간/환승횟수/도보시간" },
  { 항목: "출처2", 내용: "카카오모빌리티 자동차 길찾기 API (developers.kakaomobility.com) - 실시간 교통정보 반영 자동차 소요시간" },
  { 항목: "출발정류소 분류", 내용: "철도인접(양호): 도농역/다산역 인근 상위 이용 정류소 2곳. 외곽(취약): 신도시 외곽부 저이용 정류소 3곳 (버스 이용량 하위권)" },
  { 항목: "목적지", 내용: "서울 주요 업무·환승 거점 5곳: 잠실역, 강남역, 여의도역, 서울역, 종로3가역" },
  { 항목: "소요시간 비율 해석", 내용: "1.0에 가까울수록 대중교통이 자동차와 경쟁력 있음. 2.0 이상이면 대중교통이 자동차보다 2배 이상 오래 걸려 사실상 자동차 의존이 불가피한 구간으로 해석 가능" },
  { 항목: "미수집 데이터", 내용: "유승한내들골든뷰.다산메트로3단지 -> 여의도역/서울역/종로3가역, 다산자이.다산롯데캐슬 -> 전체 5개 목적지: ODsay API 일일 할당량 초과(HTTP 429)로 조회 실패. 할당량 초기화 후 재수집 필요" },
  { 항목: "데이터 수집 시점", 내용: "2026-09-15 기준 실시간 교통상황 반영값 (시간대에 따라 변동 가능)" },
  { 항목: "주의사항", 내용: "ODsay는 대중교통 경로 중 totalTime이 가장 짧은 경로 1개만 선택해 비교함. 실제 배차간격 대기시간은 포함되지 않을 수 있음" },
];
const wsNote = XLSX.utils.json_to_sheet(noteRows);
wsNote["!cols"] = [{ wch: 16 }, { wch: 90 }];
XLSX.utils.book_append_sheet(wb, wsNote, "출처 및 주의사항");

XLSX.writeFile(wb, "output/다산_대중교통vs자동차_비교.xlsx");
console.log("저장 완료: output/다산_대중교통vs자동차_비교.xlsx");
