import "dotenv/config";
import axios from "axios";

const ODSAY_KEY = process.env.ODSAY_API_KEY!;
const KAKAO_KEY = process.env.KAKAO_REST_API_KEY!;

// 서울역 -> 강남역 테스트
const SX = 126.972317, SY = 37.554648; // 서울역
const EX = 127.027583, EY = 37.497925; // 강남역

async function testOdsay() {
  const url = "https://api.odsay.com/v1/api/searchPubTransPathT";
  try {
    const res = await axios.get(url, {
      params: { SX, SY, EX, EY, apiKey: ODSAY_KEY },
    });
    console.log("=== ODsay 응답 ===");
    console.log(JSON.stringify(res.data, null, 2).slice(0, 1500));
  } catch (e: any) {
    console.log("=== ODsay 오류 ===");
    console.log(e.response?.status, JSON.stringify(e.response?.data || e.message));
  }
}

async function testKakao() {
  const url = "https://apis-navi.kakaomobility.com/v1/directions";
  try {
    const res = await axios.get(url, {
      params: { origin: `${SX},${SY}`, destination: `${EX},${EY}` },
      headers: { Authorization: `KakaoAK ${KAKAO_KEY}` },
    });
    console.log("=== 카카오모빌리티 응답 ===");
    console.log(JSON.stringify(res.data, null, 2).slice(0, 1500));
  } catch (e: any) {
    console.log("=== 카카오모빌리티 오류 ===");
    console.log(e.response?.status, JSON.stringify(e.response?.data || e.message));
  }
}

await testOdsay();
await testKakao();
