import "dotenv/config";
import axios from "axios";

const ODSAY_KEY = process.env.ODSAY_API_KEY!;

const stops = [
  "도농역",
  "가운휴먼시아",
  "연다산동종점",
  "연다산32통",
  "다산자이폴라리스",
];

const destinations = ["잠실역", "강남역", "여의도역", "서울역", "종로3가역"];

async function searchStation(name: string) {
  const url = "https://api.odsay.com/v1/api/searchStation";
  try {
    const res = await axios.get(url, {
      params: { apiKey: ODSAY_KEY, stationName: name },
    });
    const list = res.data?.result?.station;
    if (!list || list.length === 0) {
      console.log(`"${name}" -> 검색결과 없음 (raw: ${JSON.stringify(res.data).slice(0, 200)})`);
      return;
    }
    list.slice(0, 3).forEach((s: any) => {
      console.log(
        `"${name}" -> ${s.stationName} | x=${s.x}, y=${s.y} | type=${s.stationClass} | id=${s.stationID}`
      );
    });
  } catch (e: any) {
    console.log(`"${name}" -> 오류: ${e.response?.status} ${JSON.stringify(e.response?.data || e.message).slice(0, 300)}`);
  }
}

for (const s of [...stops, ...destinations]) {
  await searchStation(s);
}
