import { readFileSync } from "fs";
import * as XLSX from "xlsx";

const data = JSON.parse(readFileSync("data/gyeonggi_seoul_movement_20260831.json", "utf-8"));

const wb = XLSX.utils.book_new();

// Sheet 1: 요약 (Top5)
const top5 = data.시단위.slice(0, 5).map((r: any, i: number) => ({
  순위: i + 1,
  지역: r.지역,
  서울행_이동인구_명_일: Math.round(r.이동인구).toLocaleString(),
}));
const wsTop5 = XLSX.utils.json_to_sheet(top5);
wsTop5["!cols"] = [{ wch: 6 }, { wch: 14 }, { wch: 20 }];
XLSX.utils.book_append_sheet(wb, wsTop5, "TOP5 요약");

// Sheet 2: 시 단위 전체 순위
const cityAll = data.시단위.map((r: any, i: number) => ({
  순위: i + 1,
  지역: r.지역,
  서울행_이동인구_명_일: Math.round(r.이동인구),
}));
const wsCity = XLSX.utils.json_to_sheet(cityAll);
wsCity["!cols"] = [{ wch: 6 }, { wch: 14 }, { wch: 20 }];
XLSX.utils.book_append_sheet(wb, wsCity, "시 단위 전체 순위");

// Sheet 3: 행정구 단위 상세
const gguAll = data.행정구단위.map((r: any, i: number) => ({
  순위: i + 1,
  지역: r.지역,
  서울행_이동인구_명_일: Math.round(r.이동인구),
}));
const wsGgu = XLSX.utils.json_to_sheet(gguAll);
wsGgu["!cols"] = [{ wch: 6 }, { wch: 20 }, { wch: 20 }];
XLSX.utils.book_append_sheet(wb, wsGgu, "행정구 단위 상세");

// Sheet 4: 출처 및 방법론
const noteRows = [
  { 항목: "출처", 내용: "서울 열린데이터광장(data.seoul.go.kr) - 수도권 생활이동 (출발-도착지 기준, 목적별) 데이터셋 [OA-22300]" },
  { 항목: "원자료 제공기관", 내용: "서울특별시 + KT (휴대폰 LTE/5G 시그널 데이터 기반 추정)" },
  { 항목: "기준일자", 내용: data.기준일자 + " — 해당 데이터셋에서 확인 가능한 가장 최근 일자 파일" },
  { 항목: "집계 방법", 내용: "출발지 코드가 경기도(41로 시작)이고 도착지 코드가 서울(11로 시작)인 모든 행(성별·연령·시간대·이동목적 무관)의 cnt(추정 이동인구)를 출발지별로 합산" },
  { 항목: "시 단위 vs 행정구 단위", 내용: "성남시(수정/중원/분당구), 고양시(덕양/일산동/일산서구), 부천시(원미/소사/오정구), 용인시(처인/기흥/수지구), 화성시(4개구), 수원시(4개구), 안양시(만안/동안구), 안산시(상록/단원구)는 원자료상 구 단위로 나뉘어 있어 별도로 시 전체 합산치를 계산함. '지역'을 시(市) 단위로 비교할 때는 '시 단위 전체 순위' 시트를 기준으로 보는 것이 정확함" },
  { 항목: "TOP5 해석 시 주의", 내용: "구가 없는 남양주시·하남시 등은 원자료에서 이미 시 전체 단위라 그대로 순위에 반영되지만, 구가 있는 대형 도시(고양·성남 등)는 구별로 쪼개져 있으면 개별 구 순위표에서는 낮게 보일 수 있음 → 반드시 '시 단위' 기준으로 판단할 것" },
  { 항목: "데이터 특성상 한계", 내용: "1) 단일 날짜(2026-08-31, 월요일) 스냅샷이므로 요일별/계절별 변동은 반영 안 됨 2) 통신 시그널 기반 추정치로 실측이 아닌 통계적 추정값 3) '이동'은 체류시간 30분 이상인 경우만 집계되어 단순 환승 등은 제외됨" },
  { 항목: "참고", 내용: "월별로 더 안정적인 수치를 원하면 동일 방식으로 한 달치 일별 파일을 모두 합산하는 것도 가능 (1일 ~72MB, 한 달이면 약 2GB 처리 필요)" },
];
const wsNote = XLSX.utils.json_to_sheet(noteRows);
wsNote["!cols"] = [{ wch: 18 }, { wch: 95 }];
XLSX.utils.book_append_sheet(wb, wsNote, "출처 및 방법론");

XLSX.writeFile(wb, "output/경기도_서울_생활이동_TOP5_20260831.xlsx");
console.log("저장 완료: output/경기도_서울_생활이동_TOP5_20260831.xlsx");
