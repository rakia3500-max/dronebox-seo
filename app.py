# -*- coding: utf-8 -*-
"""
[웹 버전] BitDrone_Manager_Web_v1.0.py
- PC 설치 불필요 -> 웹 브라우저(PC/모바일)에서 바로 실행
- 네이버 쇼핑 크롤링 + Gemini AI 리포트 + 구글 시트/슬랙 자동화 통합
"""

import streamlit as st
import pandas as pd
import datetime as dt
import time
import base64
import hmac
import hashlib
import requests
import json
import io
import google.generativeai as genai
import xlsxwriter

# --- 페이지 설정 ---
st.set_page_config(page_title="쇼핑 통합 관제 (Web)", layout="wide")

# --- 기본 설정값 ---
DEFAULT_SELLERS = {
    "MY_BRAND_1": "드론박스, DroneBox, DRONEBOX, DJI 정품판매점 드론박스",
    "MY_BRAND_2": "빛드론, Bit-Drone, Bit Drone, BITDRONE, BIT-DRONE",
    "COMPETITORS": "다다사, dadasa, 효로로, Hyororo, 드론뷰, DroneView"
}

# --- 1. 사이드바 (설정 메뉴) ---
st.sidebar.title("⚙️ 시스템 설정")

with st.sidebar.expander("🔑 API 키 설정", expanded=True):
    gemini_key = st.text_input("Gemini API Key", type="password")
    naver_cid = st.text_input("네이버 검색 Client ID")
    naver_csec = st.text_input("네이버 검색 Client Secret", type="password")
    ad_api_key = st.text_input("광고 API Key")
    ad_sec_key = st.text_input("광고 Secret Key", type="password")
    ad_cus_id = st.text_input("광고 Customer ID")

with st.sidebar.expander("🔗 구글/슬랙 연동"):
    apps_script_url = st.text_input("Apps Script URL")
    apps_script_token = st.text_input("Apps Script Token")

with st.sidebar.expander("🎯 타겟 업체 설정"):
    my_brand_1 = st.text_area("내 브랜드 1 (DB)", DEFAULT_SELLERS["MY_BRAND_1"])
    my_brand_2 = st.text_area("내 브랜드 2 (BIT)", DEFAULT_SELLERS["MY_BRAND_2"])
    competitors = st.text_area("경쟁사 (콤마 구분)", DEFAULT_SELLERS["COMPETITORS"])


# --- 2. API 엔진 함수 ---
def get_vol(kw, ak, sk, cid):
    if not (ak and sk and cid): return 0, 0, 0
    try:
        ts = str(int(time.time() * 1000))
        sig = base64.b64encode(
            hmac.new(sk.encode(), f"{ts}.GET./keywordstool".encode(), hashlib.sha256).digest()).decode()
        headers = {"X-Timestamp": ts, "X-API-KEY": ak, "X-Customer": cid, "X-Signature": sig}
        res = requests.get(f"https://api.naver.com/keywordstool?hintKeywords={kw.replace(' ', '')}&showDetail=1",
                           headers=headers, timeout=5)
        for i in res.json().get('keywordList', []):
            if i['relKeyword'].replace(" ", "") == kw.replace(" ", ""):
                v = int(str(i['monthlyPcQcCnt']).replace("<", "")) + int(str(i['monthlyMobileQcCnt']).replace("<", ""))
                c = float(str(i['monthlyAvePcClkCnt']).replace("<", "")) + float(
                    str(i['monthlyAveMobileClkCnt']).replace("<", ""))
                return v, round(c, 1), round(c / v * 100, 2) if v else 0
    except:
        pass
    return 0, 0, 0


def get_rank(kw, cid, sec):
    if not (cid and sec): return []
    try:
        headers = {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": sec}
        res = requests.get("https://openapi.naver.com/v1/search/shop.json", headers=headers,
                           params={"query": kw, "display": 100, "sort": "sim"})
        return res.json().get('items', [])
    except:
        return []


def get_ai_report(text, api_key):
    if not api_key: return "API 키가 없습니다."
    try:
        genai.configure(api_key=api_key)
        prompt = f"""
        당신은 '드론박스(DroneBox)'와 '빛드론(BitDrone)'의 수석 SEO 컨설턴트입니다.
        아래 데이터를 분석하여 '일일 SEO 전략 보고서'를 작성하십시오.

        [데이터]
        {text}

        [작성 가이드]
        1. 🚨 긴급 점검 (10위 밖): 경쟁사(다다사 등) 언급 및 액션 플랜 제시
        2. 🏆 상위권 유지 (1~3위): 성과 칭찬 및 방어 전략
        3. 💡 액션 플랜: 4~9위권 집중 공략법
        """
        # 모델 자동 우회
        models = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
        for m in models:
            try:
                model = genai.GenerativeModel(m)
                response = model.generate_content(prompt)
                if response.text: return response.text
            except:
                continue
        return "AI 분석 실패 (모든 모델 응답 없음)"
    except Exception as e:
        return f"에러 발생: {e}"


# --- 3. 메인 화면 ---
st.title("🚀 쇼핑 통합 관제 시스템 (Web Ver)")
st.markdown("네이버 쇼핑 순위 추적 및 AI 분석 리포트 자동화")

# 키워드 입력
input_method = st.radio("키워드 입력 방식", ["직접 입력", "파일 업로드 (.txt)"], horizontal=True)
keywords = []

if input_method == "직접 입력":
    kws_text = st.text_area("키워드를 콤마(,) 또는 줄바꿈으로 구분해 입력하세요")
    if kws_text:
        keywords = [k.strip() for k in kws_text.replace(',', '\n').split('\n') if k.strip()]
else:
    uploaded_file = st.file_uploader("키워드 파일 업로드", type="txt")
    if uploaded_file:
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        keywords = [k.strip() for k in stringio.readlines() if k.strip()]

# 실행 버튼
if st.button("분석 시작", type="primary"):
    if not keywords:
        st.warning("키워드를 입력해주세요.")
    else:
        status_log = st.empty()
        progress_bar = st.progress(0)

        results = []
        ai_raw_text = ""
        today = dt.date.today().isoformat()

        t_db = [x.strip() for x in my_brand_1.split(',')]
        t_bit = [x.strip() for x in my_brand_2.split(',')]
        t_comp = [x.strip() for x in competitors.split(',')]

        for idx, kw in enumerate(keywords):
            status_log.info(f"🔍 분석 중... ({idx + 1}/{len(keywords)}): {kw}")
            progress_bar.progress((idx + 1) / len(keywords))

            vol, clk, ctr = get_vol(kw, ad_api_key, ad_sec_key, ad_cus_id)
            items = get_rank(kw, naver_cid, naver_csec)

            r_db = r_bit = r_da = r_hr = r_dv = 999
            top_mall = items[0]['mallName'] if items else "-"

            if items:
                for r, item in enumerate(items, 1):
                    mn = item['mallName'].replace(" ", "")
                    # 순위 체크
                    if any(x.replace(" ", "") in mn for x in t_db): r_db = min(r_db, r)
                    if any(x.replace(" ", "") in mn for x in t_bit): r_bit = min(r_bit, r)
                    if "다다사" in mn: r_da = min(r_da, r)
                    if "효로로" in mn: r_hr = min(r_hr, r)
                    if "드론뷰" in mn: r_dv = min(r_dv, r)

                    # 데이터 저장 조건 (3위 이내 or 자사 or 경쟁사)
                    is_mine = any(x.replace(" ", "") in mn for x in t_db + t_bit)
                    is_comp = any(x.replace(" ", "") in mn for x in t_comp) or "다다사" in mn

                    if r <= 3 or is_mine or is_comp:
                        results.append({
                            "date": today, "keyword": kw, "vol": vol, "click": clk, "ctr": ctr,
                            "rank": r, "mall": item['mallName'],
                            "title": item['title'].replace("<b>", "").replace("</b>", ""),
                            "price": item['lprice'], "link": item['link'],
                            "is_db": any(x.replace(" ", "") in mn for x in t_db),
                            "is_bit": any(x.replace(" ", "") in mn for x in t_bit),
                            "is_da": "다다사" in mn, "is_hr": "효로로" in mn, "is_dv": "드론뷰" in mn
                        })

            best = min(r_db, r_bit)
            rank_str = str(best) if best < 999 else "순위밖"
            ai_raw_text += f"{kw},{rank_str},{top_mall}\n"
            time.sleep(0.1)  # 딜레이

        status_log.success("✅ 분석 완료!")

        # --- 결과 처리 ---
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df)  # 화면에 표 출력

            # 1. 엑셀 다운로드
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Results')
            processed_data = output.getvalue()

            st.download_button(label="💾 엑셀 다운로드", data=processed_data, file_name=f"Rank_{today}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # 2. 구글 시트/슬랙 전송
            if apps_script_url:
                try:
                    # CSV 변환 (BOM 제거 utf-8)
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue().encode('utf-8')

                    # 현재 웹페이지 URL 보내기 (Streamlit은 URL 자동 감지 불가하므로 안내 메시지 전송)
                    requests.post(apps_script_url,
                                  params={"token": apps_script_token, "dash_url": "https://share.streamlit.io"},
                                  data=csv_data)
                    st.toast("✅ 구글 시트 및 슬랙 전송 완료", icon="🚀")
                except Exception as e:
                    st.error(f"전송 실패: {e}")

            # 3. AI 리포트 생성
            with st.spinner("🤖 AI가 리포트를 작성 중입니다..."):
                report = get_ai_report(ai_raw_text, gemini_key)
                st.subheader("📝 AI SEO 전략 리포트")
                st.markdown(report)

                # 리포트 다운로드
                st.download_button("📜 리포트 다운로드 (TXT)", report, file_name=f"Report_{today}.txt")
        else:
            st.warning("검색 결과가 없습니다.")