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

  const url = `https://api.searchad.naver.com/keywordstool?hintKeywords=${encodeURIComponent(keyword)}&showDetail=1`;

  try {
    const response = await fetch(url, {
      headers: {
        "X-Timestamp": timestamp,
        "X-API-KEY": ACCESS_KEY,
        "X-Customer": CUSTOMER_ID,
        "X-Signature": signature,
      },
    });

    if (!response.ok) {
      const errText = await response.text();
      return { statusCode: response.status, headers, body: JSON.stringify({ error: errText }) };
    }

    const data = await response.json();
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
    return { statusCode: 500, headers, body: JSON.stringify({ error: err.message }) };
  }
};
