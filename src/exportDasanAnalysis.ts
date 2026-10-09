import { readFileSync } from "fs";
import * as XLSX from "xlsx";

const busData = JSON.parse(readFileSync("data/dasan_bus_analysis.json", "utf-8"));
const carData = JSON.parse(readFileSync("data/gyeonggi_car_registration_2024.json", "utf-8"));
const carData2022 = JSON.parse(readFileSync("data/gyeonggi_car_registration_2022.json", "utf-8"));

const nyj2024 = carData.find((c: any) => c.시군 === "남양주시");
const nyj2022 = carData2022.find((c: any) => c.시군 === "남양주시");

const wb = XLSX.utils.book_new();

// Sheet 1: 요약
const summaryRows = [
  { 항목: "분석 대상", 값: "다산신도시(남양주) 경유 광역버스 정류소" },
  { 항목: "데이터 기간", 값: "2025년 6월 (평일 21일 / 주말 9일)" },
  { 항목: "평일 일평균 승하차", 값: busData.요약.평일일평균.toLocaleString() + "명" },
  { 항목: "주말 일평균 승하차", 값: busData.요약.주말일평균.toLocaleString() + "명" },
  { 항목: "평일 최고혼잡 3개 시간대", 값: busData.요약.상위3시간대.map((h: string) => h + "시").join(", ") },
  { 항목: "위 3개 시간대가 하루 전체에서 차지하는 비중", 값: busData.요약.상위3시간대비중 + "%" },
  { 항목: "남양주시 자가용 승용차 등록대수 (2024)", 값: carData.find((c: any) => c.시군 === "남양주시").자가용승용차.toLocaleString() + "대" },
  { 항목: "남양주시 전체 자동차 등록대수 (2024)", 값: carData.find((c: any) => c.시군 === "남양주시").전체합계.toLocaleString() + "대" },
];
const wsSummary = XLSX.utils.json_to_sheet(summaryRows);
wsSummary["!cols"] = [{ wch: 40 }, { wch: 40 }];
XLSX.utils.book_append_sheet(wb, wsSummary, "요약");

// Sheet 2: 시간대별 승하차
const wsHour = XLSX.utils.json_to_sheet(
  busData.시간대별.map((h: any) => ({ 시간대: h.hour + "시", 승차: h.boarding, 하차: h.alighting, 합계: h.total }))
);
wsHour["!cols"] = [{ wch: 10 }, { wch: 12 }, { wch: 12 }, { wch: 12 }];
XLSX.utils.book_append_sheet(wb, wsHour, "평일 시간대별 승하차");

// Sheet 3: 정류소별 상위
const wsStop = XLSX.utils.json_to_sheet(
  busData.정류소별상위20.map((s: any, i: number) => ({ 순위: i + 1, 정류소명: s.name, 평일총승하차: s.total }))
);
wsStop["!cols"] = [{ wch: 6 }, { wch: 45 }, { wch: 14 }];
XLSX.utils.book_append_sheet(wb, wsStop, "정류소별 이용량 상위20");

// Sheet 4: 노선별 상위
const wsRoute = XLSX.utils.json_to_sheet(
  busData.노선별상위20.map((s: any, i: number) => ({ 순위: i + 1, 노선번호: s.route, 평일총승하차: s.total }))
);
wsRoute["!cols"] = [{ wch: 6 }, { wch: 14 }, { wch: 14 }];
XLSX.utils.book_append_sheet(wb, wsRoute, "노선별 이용량 상위20");

// Sheet 5: 경기도 시군별 자동차등록 (2024)
const wsCar = XLSX.utils.json_to_sheet(carData);
wsCar["!cols"] = [{ wch: 10 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }];
XLSX.utils.book_append_sheet(wb, wsCar, "경기도 시군별 자동차등록(2024)");

// Sheet 5-2: 남양주시 2022 vs 2024 전후비교 (8호선 별내선 다산역 개통: 2023.12)
const pct = (a: number, b: number) => (((b - a) / a) * 100).toFixed(2) + "%";
const compareRows = [
  { 항목: "전체 자동차 등록대수", "2022년(개통 전)": nyj2022.전체합계, "2024년(개통 후)": nyj2024.전체합계, 증감: nyj2024.전체합계 - nyj2022.전체합계, 증감률: pct(nyj2022.전체합계, nyj2024.전체합계) },
  { 항목: "자가용 승용차", "2022년(개통 전)": nyj2022.자가용승용차, "2024년(개통 후)": nyj2024.자가용승용차, 증감: nyj2024.자가용승용차 - nyj2022.자가용승용차, 증감률: pct(nyj2022.자가용승용차, nyj2024.자가용승용차) },
  { 항목: "전체 승용차(자가용+영업용 등)", "2022년(개통 전)": nyj2022.전체승용차, "2024년(개통 후)": nyj2024.전체승용차, 증감: nyj2024.전체승용차 - nyj2022.전체승용차, 증감률: pct(nyj2022.전체승용차, nyj2024.전체승용차) },
  { 항목: "화물차", "2022년(개통 전)": nyj2022.화물차, "2024년(개통 후)": nyj2024.화물차, 증감: nyj2024.화물차 - nyj2022.화물차, 증감률: pct(nyj2022.화물차, nyj2024.화물차) },
];
const wsCompare = XLSX.utils.json_to_sheet(compareRows);
wsCompare["!cols"] = [{ wch: 30 }, { wch: 16 }, { wch: 16 }, { wch: 12 }, { wch: 10 }];
XLSX.utils.book_append_sheet(wb, wsCompare, "남양주시 2022vs2024 비교");

// Sheet 6: 참고사항
const noteRows = [
  { 항목: "출처1", 내용: "경기데이터드림 - 경기도 광역버스 버스노선별 정류장별 시간대별 일자별 승하차 인원 (2025년 6월)" },
  { 항목: "출처2", 내용: "경기데이터드림 - 경기통계연보 2025(65회, 2024년 기준) + 2023(63회, 2022년 기준), ⅩⅠ.교통 관광 챕터" },
  { 항목: "필터링 방법", 내용: "정류소명에 '다산'이 포함된 행만 추출 (오탐 1건 '㈜다다산업' 제외)" },
  { 항목: "8호선 별내선(다산역) 개통일", 내용: "2023년 12월 30일 — 따라서 2022년 데이터는 개통 전, 2024년 데이터는 개통 후 첫 완전한 1년치" },
  { 항목: "핵심 시사점 1", 내용: "평일 출퇴근 시간대(7,8,19시)에 하루 이용량의 25.1%가 집중 — 대체 교통수단이 부족해 특정 시간대 광역버스에 의존하는 패턴으로 해석 가능" },
  { 항목: "핵심 시사점 2 (반전)", 내용: "지하철 개통에도 불구하고 남양주시 자가용 승용차 등록대수는 2022년 264,014대 → 2024년 270,194대로 오히려 증가(+2.34%). 다만 같은 기간 다산신도시 입주가 계속 진행되어 인구 자체가 늘고 있으므로(2024년 남양주시 전체 인구 약 73만명, 다산1동만 약 10만명), 총량이 아니라 '1인당/세대당' 자가용 보유율로 정규화해야 정확한 해석이 가능합니다." },
  { 항목: "추가로 필요한 데이터", 내용: "남양주시(또는 다산동) 2022년, 2024년 정확한 인구·세대수 — 통계청 KOSIS 또는 남양주시청 통계연보에서 확인 필요 (이번 검색에서는 2024년 수치만 확인됨: 약 732,810명)" },
];
const wsNote = XLSX.utils.json_to_sheet(noteRows);
wsNote["!cols"] = [{ wch: 14 }, { wch: 90 }];
XLSX.utils.book_append_sheet(wb, wsNote, "출처 및 참고사항");

XLSX.writeFile(wb, "output/다산신도시_교통분석_2025_06.xlsx");
console.log("저장 완료");
