const crypto = require("crypto");

function makeSignature(timestamp, method, path, secretKey) {
  const message = `${timestamp}.${method}.${path}`;
  return crypto.createHmac("sha256", secretKey).update(message).digest("base64");
}

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  if (req.method === "OPTIONS") return res.status(200).end();

  const { keyword } = req.query;
  if (!keyword) return res.status(400).json({ error: "keyword is required" });

  const CUSTOMER_ID = process.env.NAVER_CUSTOMER_ID;
  const ACCESS_KEY  = process.env.NAVER_ACCESS_KEY;
  const SECRET_KEY  = process.env.NAVER_SECRET_KEY;

  const timestamp = Date.now().toString();
  const method = "GET";
  const path = "/keywordstool";
  const signature = makeSignature(timestamp, method, path, SECRET_KEY);

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
      return res.status(response.status).json({ error: errText });
    }

    const data = await response.json();

    // 필요한 필드만 정제해서 반환
    const keywords = (data.keywordList || []).map((k) => ({
      keyword: k.relKeyword,
      pcMonthly: k.monthlyPcQcCnt === "< 10" ? 5 : Number(k.monthlyPcQcCnt) || 0,
      mobileMonthly: k.monthlyMobileQcCnt === "< 10" ? 5 : Number(k.monthlyMobileQcCnt) || 0,
      totalMonthly: 0,
      competition: k.compIdx, // low / mid / high
    })).map((k) => ({
      ...k,
      totalMonthly: k.pcMonthly + k.mobileMonthly,
    }));

    return res.status(200).json({ keywords });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
