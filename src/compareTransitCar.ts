import "dotenv/config";
import axios from "axios";
import { writeFileSync } from "fs";

const ODSAY_KEY = process.env.ODSAY_API_KEY!;
const KAKAO_KEY = process.env.KAKAO_REST_API_KEY!;

interface Point {
  name: string;
  x: number;
  y: number;
  group?: string;
}

const origins: Point[] = [
  { name: "도농역.동화중고교.다산플루리움(중)", x: 127.161298, y: 37.607883, group: "철도인접(양호)" },
  { name: "가운휴먼시아.다산효성해링턴타워.새마을금고다산본점(중)", x: 127.156252, y: 37.605396, group: "철도인접(양호)" },
  { name: "다산자이폴라리스.반도유보라", x: 127.15207, y: 37.629614, group: "외곽(취약)" },
  { name: "유승한내들골든뷰.다산메트로3단지", x: 127.146691, y: 37.62252, group: "외곽(취약)" },
  { name: "다산자이.다산롯데캐슬", x: 127.151991, y: 37.627604, group: "외곽(취약)" },
];

const destinations: Point[] = [
  { name: "잠실역", x: 127.096971, y: 37.512691 },
  { name: "강남역", x: 127.030099, y: 37.498519 },
  { name: "여의도역", x: 126.923335, y: 37.523267 },
  { name: "서울역", x: 126.972317, y: 37.555946 },
  { name: "종로3가역", x: 126.99319, y: 37.570682 },
];

interface ResultRow {
  출발정류소: string;
  출발유형: string;
  목적지: string;
  대중교통_총소요시간_분: number | string;
  환승횟수: number | string;
  도보시간_분: number | string;
  대중교통_경로: string;
  자동차_소요시간_분: number | string;
  자동차_거리_km: number | string;
  소요시간_비율_대중교통나누기자동차: number | string;
  비고: string;
}

async function getTransit(o: Point, d: Point) {
  const res = await axios.get("https://api.odsay.com/v1/api/searchPubTransPathT", {
    params: { SX: o.x, SY: o.y, EX: d.x, EY: d.y, apiKey: ODSAY_KEY },
  });
  if (res.data?.error) return { error: res.data.error.msg || "ODsay 오류" };
  const paths = res.data?.result?.path;
  if (!paths || paths.length === 0) return { error: "경로 없음" };
  // totalTime 기준 최단 경로 선택
  const best = paths.reduce((a: any, b: any) => (a.info.totalTime <= b.info.totalTime ? a : b));
  const transitCount = (best.info.busTransitCount || 0) + (best.info.subwayTransitCount || 0);
  const routeNames: string[] = [];
  for (const sp of best.subPath) {
    if (sp.trafficType === 1 && sp.lane) routeNames.push(sp.lane.map((l: any) => l.name).join("/"));
    if (sp.trafficType === 2 && sp.lane) routeNames.push(sp.lane.map((l: any) => l.busNo).join("/"));
  }
  return {
    totalTime: best.info.totalTime,
    transitCount,
    walkTime: Math.round((best.info.totalWalk || 0) / 67), // 대략 도보 분속 67m 기준 환산
    route: routeNames.join(" -> "),
  };
}

async function getCar(o: Point, d: Point) {
  try {
    const res = await axios.get("https://apis-navi.kakaomobility.com/v1/directions", {
      params: { origin: `${o.x},${o.y}`, destination: `${d.x},${d.y}` },
      headers: { Authorization: `KakaoAK ${KAKAO_KEY}` },
    });
    const route = res.data?.routes?.[0];
    if (!route || route.result_code !== 0) return { error: route?.result_msg || "카카오 경로 오류" };
    return {
      durationMin: Math.round(route.summary.duration / 60),
      distanceKm: Math.round((route.summary.distance / 1000) * 10) / 10,
    };
  } catch (e: any) {
    return { error: String(e.response?.data?.msg || e.message) };
  }
}

async function main() {
  const rows: ResultRow[] = [];
  for (const o of origins) {
    for (const d of destinations) {
      const [transit, car] = await Promise.all([getTransit(o, d), getCar(o, d)]);
      const note: string[] = [];
      if ((transit as any).error) note.push(`대중교통: ${(transit as any).error}`);
      if ((car as any).error) note.push(`자동차: ${(car as any).error}`);

      const tTime = (transit as any).totalTime ?? "N/A";
      const cTime = (car as any).durationMin ?? "N/A";
      const ratio =
        typeof tTime === "number" && typeof cTime === "number" && cTime > 0
          ? Math.round((tTime / cTime) * 100) / 100
          : "N/A";

      rows.push({
        출발정류소: o.name,
        출발유형: o.group || "",
        목적지: d.name,
        대중교통_총소요시간_분: tTime,
        환승횟수: (transit as any).transitCount ?? "N/A",
        도보시간_분: (transit as any).walkTime ?? "N/A",
        대중교통_경로: (transit as any).route ?? "N/A",
        자동차_소요시간_분: cTime,
        자동차_거리_km: (car as any).distanceKm ?? "N/A",
        소요시간_비율_대중교통나누기자동차: ratio,
        비고: note.join(" / "),
      });
      console.log(`완료: ${o.name} -> ${d.name} | 대중교통 ${tTime}분 vs 자동차 ${cTime}분 (비율 ${ratio})`);
      await new Promise((r) => setTimeout(r, 300));
    }
  }
  writeFileSync("data/transit_car_comparison.json", JSON.stringify(rows, null, 2));
  console.log("\n저장 완료: data/transit_car_comparison.json");
}

main();
