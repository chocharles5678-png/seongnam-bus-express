import "dotenv/config";
import axios from "axios";

const ODSAY_KEY = process.env.ODSAY_API_KEY!;
const names = ["유승한내들골든뷰", "다산자이.다산롯데캐슬"];

async function searchStation(name: string) {
  const res = await axios.get("https://api.odsay.com/v1/api/searchStation", {
    params: { apiKey: ODSAY_KEY, stationName: name },
  });
  const list = res.data?.result?.station || [];
  list.slice(0, 3).forEach((s: any) => {
    console.log(`"${name}" -> ${s.stationName} | x=${s.x}, y=${s.y} | id=${s.stationID}`);
  });
}
for (const n of names) await searchStation(n);
