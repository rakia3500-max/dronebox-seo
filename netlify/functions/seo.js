exports.handler = async function (event) {
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Content-Type": "application/json",
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers, body: "" };
  }

  if (event.httpMethod !== "POST") {
    return { statusCode: 405, headers, body: JSON.stringify({ error: "Method not allowed" }) };
  }

  try {
    const { keyword, keywordData } = JSON.parse(event.body);
    const top10 = [...keywordData].sort((a, b) => b.totalMonthly - a.totalMonthly).slice(0, 10);
    const kwSummary = top10.map(k => `${k.keyword}(월${k.totalMonthly.toLocaleString()}회)`).join(", ");

    const prompt = `당신은 네이버 쇼핑 SEO 전문가입니다. 드론 쇼핑몰 "드론박스"의 "${keyword}" 관련 제품의 SEO 설정을 생성해주세요.

실제 네이버 검색량 상위 키워드: ${kwSummary}

반드시 아래 JSON 형식으로만 응답하세요. 설명이나 마크다운 없이 JSON만:
{"title":"60자이내 타이틀(검색량 높은 키워드 앞배치, 드론박스 포함)","description":"160자이내 메타설명(구매유도+핵심스펙)","keywords":"콤마구분 키워드 15개(검색량 높은 순)","naverTags":"파이프구분 10개 태그","attributes":"속성정보 500자이하"}`;

    const GEMINI_API_KEY = process.env.GEMINI_API_KEY;
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`;

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0.7,
          maxOutputTokens: 1500,
          responseMimeType: "application/json"
        }
      }),
    });

    const data = await response.json();
    console.log("Gemini response:", JSON.stringify(data).slice(0, 500));

    if (!response.ok) {
      console.error("Gemini API error:", JSON.stringify(data));
      return { statusCode: 500, headers, body: JSON.stringify({ error: "Gemini API error: " + JSON.stringify(data) }) };
    }

    let text = data.candidates?.[0]?.content?.parts?.[0]?.text || "";
    console.log("Raw text:", text.slice(0, 300));
    text = text.replace(/```json|```/g, "").trim();
    const seo = JSON.parse(text);

    return { statusCode: 200, headers, body: JSON.stringify(seo) };
  } catch (err) {
    console.error("Handler error:", err.message);
    return { statusCode: 500, headers, body: JSON.stringify({ error: err.message }) };
  }
};
