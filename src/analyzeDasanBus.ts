import { readFileSync, writeFileSync } from "fs";

interface Row {
  date: string;
  hour: string;
  company: string;
  route: string;
  stopId: string;
  region: string;
  stopNo: string;
  stopName: string;
  boarding: number;
  alighting: number;
  routeCount: number;
}

const raw = readFileSync("data/raw/dasan_rows_clean.csv", "utf-8").trim().split("\n");
const rows: Row[] = raw.map((line) => {
  const [date, hour, company, route, stopId, region, stopNo, stopName, boarding, alighting, routeCount] = line.split("|");
  return {
    date,
    hour,
    company,
    route,
    stopId,
    region,
    stopNo,
    stopName,
    boarding: Number(boarding) || 0,
    alighting: Number(alighting) || 0,
    routeCount: Number(routeCount) || 0,
  };
});

console.log("총 행 수:", rows.length);

// 요일 계산 (YYYYMMDD -> 요일)
function dow(dateStr: string): number {
  const y = Number(dateStr.slice(0, 4));
  const m = Number(dateStr.slice(4, 6));
  const d = Number(dateStr.slice(6, 8));
  return new Date(y, m - 1, d).getDay(); // 0=일 ... 6=토
}

const weekdayRows = rows.filter((r) => {
  const w = dow(r.date);
  return w >= 1 && w <= 5;
});
const weekendRows = rows.filter((r) => {
  const w = dow(r.date);
  return w === 0 || w === 6;
});

function sumTotal(rs: Row[]) {
  return rs.reduce((a, r) => a + r.boarding + r.alighting, 0);
}

const weekdayDays = new Set(weekdayRows.map((r) => r.date)).size;
const weekendDays = new Set(weekendRows.map((r) => r.date)).size;

const weekdayTotal = sumTotal(weekdayRows);
const weekendTotal = sumTotal(weekendRows);

console.log(`평일(${weekdayDays}일) 총 승하차: ${weekdayTotal.toLocaleString()} / 일평균 ${Math.round(weekdayTotal / weekdayDays).toLocaleString()}`);
console.log(`주말(${weekendDays}일) 총 승하차: ${weekendTotal.toLocaleString()} / 일평균 ${Math.round(weekendTotal / weekendDays).toLocaleString()}`);

// 시간대별 집계 (평일 기준, 출퇴근 혼잡 확인용)
const hourMap = new Map<string, { boarding: number; alighting: number }>();
for (const r of weekdayRows) {
  const cur = hourMap.get(r.hour) || { boarding: 0, alighting: 0 };
  cur.boarding += r.boarding;
  cur.alighting += r.alighting;
  hourMap.set(r.hour, cur);
}
const hourStats = Array.from(hourMap.entries())
  .map(([hour, v]) => ({ hour, boarding: v.boarding, alighting: v.alighting, total: v.boarding + v.alighting }))
  .sort((a, b) => a.hour.localeCompare(b.hour));

console.log("\n[평일 시간대별 승하차 합계]");
hourStats.forEach((h) => console.log(`${h.hour}시: 승차 ${h.boarding.toLocaleString()} / 하차 ${h.alighting.toLocaleString()} / 합계 ${h.total.toLocaleString()}`));

const weekdayGrandTotal = hourStats.reduce((a, h) => a + h.total, 0);
const top3Hours = [...hourStats].sort((a, b) => b.total - a.total).slice(0, 3);
const top3Sum = top3Hours.reduce((a, h) => a + h.total, 0);
console.log(`\n상위 3개 시간대(${top3Hours.map((h) => h.hour + "시").join(", ")}) 비중: ${((top3Sum / weekdayGrandTotal) * 100).toFixed(1)}%`);

// 정류소별 총 이용량 순위 (평일 기준)
const stopMap = new Map<string, number>();
for (const r of weekdayRows) {
  stopMap.set(r.stopName, (stopMap.get(r.stopName) || 0) + r.boarding + r.alighting);
}
const stopRanking = Array.from(stopMap.entries())
  .map(([name, total]) => ({ name, total }))
  .sort((a, b) => b.total - a.total);

console.log("\n[평일 정류소별 이용량 상위 10]");
stopRanking.slice(0, 10).forEach((s, i) => console.log(`${i + 1}. ${s.name}: ${s.total.toLocaleString()}`));

// 노선별 집계
const routeMap = new Map<string, number>();
for (const r of weekdayRows) {
  routeMap.set(r.route, (routeMap.get(r.route) || 0) + r.boarding + r.alighting);
}
const routeRanking = Array.from(routeMap.entries())
  .map(([route, total]) => ({ route, total }))
  .sort((a, b) => b.total - a.total);

console.log("\n[평일 노선별 이용량 상위 10]");
routeRanking.slice(0, 10).forEach((s, i) => console.log(`${i + 1}. ${s.route}번: ${s.total.toLocaleString()}`));

// 저장 (엑셀용 JSON)
writeFileSync(
  "data/dasan_bus_analysis.json",
  JSON.stringify(
    {
      요약: {
        평일일수: weekdayDays,
        평일총승하차: weekdayTotal,
        평일일평균: Math.round(weekdayTotal / weekdayDays),
        주말일수: weekendDays,
        주말총승하차: weekendTotal,
        주말일평균: Math.round(weekendTotal / weekendDays),
        상위3시간대: top3Hours.map((h) => h.hour),
        상위3시간대비중: Number(((top3Sum / weekdayGrandTotal) * 100).toFixed(1)),
      },
      시간대별: hourStats,
      정류소별상위20: stopRanking.slice(0, 20),
      노선별상위20: routeRanking.slice(0, 20),
    },
    null,
    2
  )
);
console.log("\n저장 완료: data/dasan_bus_analysis.json");
