import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

import os
import google.generativeai as genai
import streamlit as st

# Streamlit Secrets 또는 환경 변수에서 키를 읽어옴
api_key = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)
APP_PASSWORD = "1234"

st.set_page_config(page_title="주문서 자동 변환", layout="wide")

st.title("주문서 자동 변환")# ---------------------------------------------------------
# [추가] 비밀번호 인증 세션 로직
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

st.title("🔒 사내 주문서 자동 변환 시스템")

# 비밀번호 미인증 시 화면 차단
if not st.session_state.authenticated:
    st.subheader("접근 권한 확인")
    input_pwd = st.text_input("사내 접속 비밀번호를 입력하세요", type="password")
    
    if st.button("로그인", type="primary"):
        if input_pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
            
    st.caption("※ 본 시스템은 허가된 사내 임직원만 이용할 수 있습니다.")
    st.stop()  # 인증 전까지 아래 메인 기능 실행 중단

# 인증 성공 시 표시 및 로그아웃 버튼
st.success("인증 완료! 주문서 변환 기능을 사용하실 수 있습니다.")

col1, col2 = st.columns([8, 2])
with col2:
    if st.button("🔒 로그아웃"):
        st.session_state.authenticated = False
        st.rerun()
st.caption("오타, 쉼표(0,7), s/d 구분, OAA 고유 코드 매핑까지 완벽히 파싱합니다.")

# 사용자 입력
user_input = st.text_area("카톡 주문 메시지 전체 복사/붙여넣기", height=200, placeholder="여기에 카톡 메시지를 복사해서 넣으세요...")

if st.button("주문 값 자동 추출하기", type="primary"):
    if not user_input.strip():
        st.warning("카톡 메시지를 입력해 주세요.")
    else:
        prompt = f"""
        당신은 카카오톡 주문 메시지를 분석하여 정확한 자사 품목 코드와 정형화된 데이터를 추출하는 전문 AI입니다.
        제시된 주문 메시지를 분석하여 지정된 품목 매핑 표에 맞게 주문 정보를 추출하세요.

        [품목 고유 코드 1:1 매핑 표 - 반드시 아래 지정된 문자열 코드로만 변환하세요]
        1. 니들/팁 (1박스 = 20개 환산)
           - 니들_0.7 -> "교체용니들 0.7 / OAA-2112(1)"
           - 니들_0.8 -> "교체용니들 0.8 / OAA-2109(1)"
           - 니들_0.9 -> "교체용니들 0.9 / OAA-2113(1)"
           - 니들_1.0 -> "교체용니들 1.0 / OAA-2110(1)"
           - 니들_1.1 -> "교체용니들 1.1 / OAA-2196(1)"
           - 니들_1.2 -> "교체용니들 1.2 / OAA-2111(1)"
           * 알파벳 s / single / 싱글 표기 -> 0.8mm 니들 적용 ("교체용니들 0.8 / OAA-2109(1)")
           * 알파벳 d / double / 더블 표기 -> 1.0mm 니들 적용 ("교체용니들 1.0 / OAA-2110(1)")

        2. 식모기/본체/장치 (1박스 = 5개 환산)
           - 식모기_0.6 -> "모발이식장치 0.6 / OAA-2202(1)"
           - 식모기_0.7 -> "모발이식장치 0.7 / OAA-2193(1)"
           - 식모기_0.8 -> "모발이식장치 0.8 / OAA-2190(1)"
           - 식모기_0.9 -> "모발이식장치 0.9 / OAA-2194(1)"
           - 식모기_1.0 -> "모발이식장치 1.0 / OAA-2191(1)"
           - 식모기_1.1 -> "모발이식장치 1.1 / OAA-2195(1)"
           - 식모기_1.2 -> "모발이식장치 1.2 / OAA-2192(1)"

        3. 펀치류 (1박스 = 10개 환산)
           - ss100 / ss-100 / SS100 / SS-100 / SS 펀치 -> "HFUE-SS-100"
           - 라운드 -> "HFUE-RL-[규격숫자 두자리]" (예: 1.0mm -> HFUE-RL-10, 0.8mm -> HFUE-RL-08)
           - 크라운/세레티드 -> "HFUE-SL-[규격숫자 두자리]" (예: 0.8mm -> HFUE-SL-08)
           - 모디헤어 병원 -> "HFUE-TS-[규격숫자 두자리]"
           - 일반/트럼펫 -> "HFUE-TL-[규격숫자 두자리]"

        [주의사항]
        - '0,7'과 같이 쉼표가 들어간 소수점은 '0.7'로 자동 교정하세요.
        - 한 줄에 여러 품목이 언급된 경우(예: '0.7니들 2박스 1.0니들 2박스') 각각 독립된 항목으로 분리하세요.
        - '식모기팁'처럼 '팁'이나 '니들'이 포함된 경우 식모기 장치가 아니라 '니들'로 판단하세요.
        - 단일 알파벳 's'는 '교체용니들 0.8'로, 'ss100'이나 'ss-100'은 펀치류인 'HFUE-SS-100'으로 엄격히 구분하여 파싱하세요.
        - 병원명은 메시지 내에서 '의원/피부과/성형외과/병원' 등을 포함한 정확한 지점명을 찾으세요.

        [응답 형식]
        반드시 JSON Array 형태로만 응답하세요. 다른 설명 텍스트나 마크다운(```json)은 절대 포함하지 마세요.
        [
          {{
            "hospital": "병원명",
            "original": "원문 텍스트 조각",
            "code": "변환된 품목코드",
            "qty": "최종 환산 수량 (예: 40개 (2박스 × 20개))"
          }}
        ]

        분석할 카톡 메시지:
        \"\"\"{user_input}\"\"\"
        """

        with st.spinner("Gemini AI가 문맥을 분석하여 파싱 중입니다..."):
            try:
                # gemini-3.6-flash 사용
                model = genai.GenerativeModel("gemini-3.6-flash")
                response = model.generate_content(prompt)
                
                raw_result = response.text.strip()
                
                # Markdown JSON 태그 제거
                if raw_result.startswith("```json"):
                    raw_result = raw_result.replace("```json", "").replace("```", "").strip()
                elif raw_result.startswith("```"):
                    raw_result = raw_result.replace("```", "").strip()
                
                parsed_data = json.loads(raw_result)
                
                if parsed_data:
                    df = pd.DataFrame(parsed_data)
                    df.columns = ["주문처(병원)", "원문 텍스트", "변환 품목코드", "수량 환산"]
                    
                    st.subheader("추출 결과")
                    st.dataframe(df, use_container_width=True)
                    
                    # 엑셀 다운로드 버튼
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 엑셀(CSV) 다운로드",
                        data=csv,
                        file_name="order_result.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("추출된 주문 데이터가 없습니다.")

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")