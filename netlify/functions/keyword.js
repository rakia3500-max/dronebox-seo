const crypto = require("crypto");

function makeSignature(timestamp, method, path, secretKey) {
  const message = `${timestamp}.${method}.${path}`;
  return crypto.createHmac("sha256", secretKey).update(message).digest("base64");
}

exports.handler = async function (event) {
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Content-Type": "application/json",
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers, body: "" };
  }

  const keyword = event.queryStringParameters?.keyword;
  if (!keyword) {
    return { statusCode: 400, headers, body: JSON.stringify({ error: "keyword is required" }) };
  }

  const CUSTOMER_ID = process.env.NAVER_CUSTOMER_ID;
  const ACCESS_KEY  = process.env.NAVER_ACCESS_KEY;
  const SECRET_KEY  = process.env.NAVER_SECRET_KEY;

  const timestamp = Date.now().toString();
  const signature = makeSignature(timestamp, "GET", "/keywordstool", SECRET_KEY);

  // 띄어쓰기 그대로 유지 (네이버 API가 실제로 띄어쓰기 지원함)
  const cleanKeyword = keyword.trim();

  const params = new URLSearchParams();
  params.append("hintKeywords", cleanKeyword);
  params.append("showDetail", "1");

  const url = `https://api.searchad.naver.com/keywordstool?${params.toString()}`;

  try {
    const response = await fetch(url, {
      headers: {
        "X-Timestamp": timestamp,
        "X-API-KEY": ACCESS_KEY,
        "X-Customer": CUSTOMER_ID,
        "X-Signature": signature,
      },
    });

    const responseText = await response.text();
    console.log("Naver API status:", response.status);
    console.log("Naver API response:", responseText.slice(0, 300));

    if (!response.ok) {
      return { statusCode: response.status, headers, body: JSON.stringify({ error: responseText }) };
    }

    const data = JSON.parse(responseText);
    const keywords = (data.keywordList || []).map((k) => {
      const pc = k.monthlyPcQcCnt === "< 10" ? 5 : Number(k.monthlyPcQcCnt) || 0;
      const mobile = k.monthlyMobileQcCnt === "< 10" ? 5 : Number(k.monthlyMobileQcCnt) || 0;
      return {
        keyword: k.relKeyword,
        pcMonthly: pc,
        mobileMonthly: mobile,
        totalMonthly: pc + mobile,
        competition: k.compIdx,
      };
    });

    return { statusCode: 200, headers, body: JSON.stringify({ keywords }) };
  } catch (err) {
    console.error("Error:", err.message);
    return { statusCode: 500, headers, body: JSON.stringify({ error: err.message }) };
  }
};
