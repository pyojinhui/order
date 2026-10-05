import json
import os
import re
import google.generativeai as genai
import pandas as pd
import streamlit as st

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

if api_key:
    genai.configure(api_key=api_key)

APP_PASSWORD = "1234"

st.set_page_config(page_title="주문서 자동 변환", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #f8f9fa; }

    div[data-testid="stColumn"] > div:has(.login-title) {
        background-color: #ffffff !important;
        border: 1px solid #e9ecef !important;
        border-radius: 12px !important;
        padding: 35px 20px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06) !important;
    }

    .login-title, .login-sub, .login-footer, div[data-testid="stTextInput"] > label {
        white-space: nowrap !important;
        text-align: center !important;
        display: block !important;
    }

    .login-title {
        font-size: clamp(22px, 4vw, 45px) !important;
        font-weight: 700 !important;
        color: #212529;
        margin-bottom: 4px !important;
    }

    .login-sub {
        font-size: clamp(15px, 2.5vw, 30px) !important;
        color: #6c757d;
        margin-bottom: 24px !important;
    }

    div[data-testid="stTextInput"] > label {
        font-size: clamp(14px, 2.2vw, 24px) !important;
        color: #495057 !important;
        margin-bottom: 8px !important;
    }

    .login-footer {
        font-size: clamp(10px, 1.8vw, 13px) !important;
        color: #adb5bd !important;
        margin-top: 50px !important;
    }

    div[data-testid="stTextInput"], div.stButton {
        max-width: 300px !important;
        width: 90% !important;
        margin: 0 auto !important;
    }

    div[data-baseweb="input"] {
        height: 42px !important;
        border-radius: 6px !important;
    }

    div[data-baseweb="input"] input {
        font-size: 15px !important;
        text-align: center !important;
    }

    div.stButton > button {
        height: 44px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        line-height: 1 !important;
    }

    [data-testid="stDataFrame"] div[role="columnheader"] {
        justify-content: center !important;
        text-align: center !important;
    }

    /* 단위 선택: 두 선택지를 정확히 동일한 크기로 좌우 분할 */
    [data-testid="stSegmentedControl"] {
        width: 100% !important;
    }

    [data-testid="stSegmentedControl"] [role="radiogroup"] {
        width: 100% !important;
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 0 !important;
        box-sizing: border-box !important;
    }

    [data-testid="stSegmentedControl"] [role="radiogroup"] > * {
        width: 100% !important;
        min-width: 0 !important;
        max-width: none !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }

    [data-testid="stSegmentedControl"] [role="radio"],
    [data-testid="stSegmentedControl"] button {
        width: 100% !important;
        min-width: 0 !important;
        max-width: none !important;
        min-height: 44px !important;
        height: 44px !important;
        box-sizing: border-box !important;
        justify-content: center !important;
        text-align: center !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }

    /* 결과표는 Streamlit 데이터그리드가 아닌 HTML 표로 렌더링하므로
       각 셀의 정렬을 실제 셀 내부까지 직접 지정 */
    .order-result-table {
        width: 100% !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        background: #ffffff !important;
        font-size: 14px !important;
    }

    .order-result-table th {
        height: 30px !important;
        padding: 6px 10px !important;
        background: #f8f9fa !important;
        border-bottom: 1px solid #dee2e6 !important;
        border-right: 1px solid #dee2e6 !important;
        text-align: center !important;
        vertical-align: middle !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
    }

    .order-result-table td {
        height: 30px !important;
        padding: 6px 10px !important;
        border-bottom: 1px solid #e9ecef !important;
        border-right: 1px solid #e9ecef !important;
        text-align: left !important;
        vertical-align: middle !important;
        white-space: nowrap !important;
    }

    .order-result-table th:first-child,
    .order-result-table td:first-child {
        text-align: center !important;
    }

    .order-result-table th:last-child,
    .order-result-table td:last-child {
        border-right: 0 !important;
    }

    .order-result-table tr:last-child td {
        border-bottom: 0 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state.get("authenticated", False):
    _, login_col, _ = st.columns([1, 2, 1])

    with login_col:
        st.markdown("<div class='login-title'>🔒 사내 주문서</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-sub'>접근 권한 확인</div>", unsafe_allow_html=True)

        input_pwd = st.text_input("사내 비밀번호 입력", type="password", key="login_password_input")

        if st.button("로그인", type="primary", use_container_width=True, key="login_btn"):
            if input_pwd == APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")

        st.markdown("<div class='login-footer'>※ 본 시스템은 허가된 사내 임직원 전용입니다.</div>", unsafe_allow_html=True)

    st.stop()

_, center_col, _ = st.columns([1.5, 7, 1.5])

with center_col:
    st.title("🔒 사내 주문서 자동 변환 시스템")

    col_title, col_logout = st.columns([8, 2])
    with col_title:
        st.success("인증 완료! 주문서 변환 기능을 사용하실 수 있습니다.")
    with col_logout:
        if st.button("🔒 로그아웃", use_container_width=True, key="logout_btn"):
            st.session_state["authenticated"] = False
            st.rerun()

    st.caption(
        "오타, 쉼표(0,7), s/d 구분, 병원별 전용 모델, OAA 고유 코드 매핑까지 완벽히 파싱합니다."
    )

    user_input = st.text_area(
        "카톡 주문 메시지 전체 복사/붙여넣기",
        height=300,
        placeholder="여기에 카톡 메시지를 복사해서 넣으세요...",
        key="kakao_order_input"
    )

    if st.button("주문 값 자동 추출하기", type="primary", use_container_width=True, key="extract_btn"):
        if not user_input.strip():
            st.warning("카톡 메시지를 입력해 주세요.")
        elif not api_key:
            st.error("GEMINI_API_KEY가 설정되지 않았습니다.")
        else:
            prompt = f"""
            당신은 카카오톡 주문 메시지를 분석하여 정확한 자사 품목 코드와 정형화된 데이터를 추출하는 전문 AI입니다.
            제시된 주문 메시지를 분석하여 지정된 품목 매핑 표에 맞게 주문 정보를 추출하세요.

            [거래처명 식별 규칙]
            - 병원/거래처명은 풀네임이 아니더라도 핵심 키워드만 포함되어 있으면 해당 거래처로 매핑하세요.
            - 예시: '한나이브성형외과', '한나이브외과', '한나이브' -> 모두 동일한 한나이브 거래처로 인식
            - 예시: '김문규경대숲', '김문규' -> 김문규경대숲의원 인식
            - 예시: '마이모' -> 마이모의원 인식
            - 예시: '모디헤어', '모디' -> 모디헤어플란트의원 인식
            - 예시: '이규호', '모아름' -> 이규호 모아름의원 인식
            - 예시: '젬마' -> 젬마의원 인식
            - 예시: '포헤어' -> 포헤어의원(서울) 인식

            [거래처별 전용 펀치류 모델 매핑 규칙 - 최우선 적용]
            카톡 메시지에 언급된 거래처가 아래 목록에 해당하는 경우, 펀치류 주문 건에 대해 최우선으로 전용 코드 형식 및 규격을 적용하세요.
            1. 김문규경대숲의원 (키워드: 김문규, 경대숲) -> 품목코드: "HFUE-TL-085K", 품목명: "트럼펫 펀치 0.85K"
            2. 마이모의원 (키워드: 마이모) -> 품목코드: "HFUE-SHT-090", 품목명: "SHT 펀치 0.90"
            3. 모디헤어플란트의원 (키워드: 모디헤어, 모디) -> 품목코드: "HFUE-TS-[규격숫자 세자리]" (예: HFUE-TS-070), 품목명: "모디 전용 펀치"
            4. 이규호 모아름의원 (키워드: 이규호, 모아름) -> 품목코드: "MHP-RS-090(이규호)", 품목명: "모아름 전용 펀치 0.90"
            5. 젬마의원 (키워드: 젬마) -> 품목코드: "HFUE-RS-075(젬마)", 품목명: "젬마 전용 펀치 0.75"
            6. 포헤어의원(서울) (키워드: 포헤어) -> 품목코드: "MHP-SL-100(F)", 품목명: "포헤어 전용 펀치 1.00"
            7. 한나이브성형 / 한나이브외과의원 (키워드: 한나이브) -> 품목코드: "MHP-TL-100(한나)", 품목명: "한나이브 전용 펀치 1.00"

            [일반 품목 고유 코드 1:1 매핑 표]
            1. 니들/팁 (1박스 = 20개 환산)
               - 니들_0.6 -> 품목코드: "OAA-2199(1)", 품목명: "교체용니들 0.6"
               - 니들_0.7 -> 품목코드: "OAA-2112(1)", 품목명: "교체용니들 0.7"
               - 니들_0.8 -> 품목코드: "OAA-2109(1)", 품목명: "교체용니들 0.8"
               - 니들_0.9 -> 품목코드: "OAA-2113(1)", 품목명: "교체용니들 0.9"
               - 니들_1.0 -> 품목코드: "OAA-2110(1)", 품목명: "교체용니들 1.0"
               - 니들_1.1 -> 품목코드: "OAA-2196(1)", 품목명: "교체용니들 1.1"
               - 니들_1.2 -> 품목코드: "OAA-2111(1)", 품목명: "교체용니들 1.2"
               * 알파벳 s / single / 싱글 표기 -> 0.8mm 니들 적용 (품목코드: "OAA-2109(1)", 품목명: "교체용니들 0.8")
               * 알파벳 d / double / 더블 표기 -> 1.0mm 니들 적용 (품목코드: "OAA-2110(1)", 품목명: "교체용니들 1.0")

            2. 식모기/본체/장치 (1박스 = 5개 환산)
               - 식모기_0.6 -> 품목코드: "OAA-2202(1)", 품목명: "모발이식장치 0.6"
               - 식모기_0.7 -> 품목코드: "OAA-2193(1)", 품목명: "모발이식장치 0.7"
               - 식모기_0.8 -> 품목코드: "OAA-2190(1)", 품목명: "모발이식장치 0.8"
               - 식모기_0.9 -> 품목코드: "OAA-2194(1)", 품목명: "모발이식장치 0.9"
               - 식모기_1.0 -> 품목코드: "OAA-2191(1)", 품목명: "모발이식장치 1.0"
               - 식모기_1.1 -> 품목코드: "OAA-2195(1)", 품목명: "모발이식장치 1.1"
               - 식모기_1.2 -> 품목코드: "OAA-2192(1)", 품목명: "모발이식장치 1.2"

            3. 일반 병원의 펀치류 (1박스 = 10개 환산) - 위 전용 거래처에 해당하지 않을 경우 적용
               - ss100 / ss-100 / SS100 / SS-100 / SS 펀치 -> 품목코드: "HFUE-SS-100", 품목명: "SS 펀치 1.00"
               - 일반 병원의 라운드 펀치 -> 품목코드: "HFUE-RL-[규격숫자 세자리]", 품목명: "라운드 펀치 [규격]"
               - 일반 병원의 크라운/세레티드 펀치 -> 품목코드: "HFUE-SL-[규격숫자 세자리]", 품목명: "세레티드 펀치 [규격]"
               - 일반 병원의 일반/트럼펫 펀치 -> 품목코드: "HFUE-TL-[규격숫자 세자리]", 품목명: "트럼펫 펀치 [규격]"

            [펀치류 규격 세 자릿수 변환 규칙 - 엄격 적용]
            - 규격 숫자는 소수점을 제거하고 반드시 3자리 정수 형태(OOO)로 채우세요.
              예시) 1.0mm -> 100 (예: HFUE-RL-100)
              예시) 0.8mm 또는 0.8 -> 080 (예: HFUE-RL-080)
              예시) 0.6mm 또는 6 -> 060 (예: HFUE-RL-060)
              예시) 0.85mm -> 085 (예: HFUE-RL-085)

            [주의사항]
            - '0,7'과 같이 쉼표가 들어간 소수점은 '0.7'로 자동 교정하세요.
            - 한 줄에 여러 품목이 언급된 경우 각각 독립된 항목으로 분리하세요.
            - '식모기팁'처럼 '팁'이나 '니들'이 포함된 경우 식모기 장치가 아니라 '니들'로 판단하세요.
            - 단일 알파벳 's'는 '교체용니들 0.8'로, 'ss100'은 'HFUE-SS-100'으로 엄격히 구분하여 파싱하세요.
            - 거래처명은 메시지 내에서 핵심 명칭만 언급되어도 식별 가능한 명칭으로 매핑하여 정제하세요.
            - 반드시 품목코드는 영문/숫자 코드로만, 품목명은 한글 항목명으로 정확히 구분하여 분리하세요.

            [응답 형식]
            반드시 마크다운이나 다른 설명 없이 아래 형태의 JSON Array로만 응답하세요.
            [
              {{
                "hospital": "병원명",
                "original": "원문 텍스트 조각",
                "item_code": "변환된 품목코드 (예: OAA-2199(1) 또는 HFUE-TL-085K)",
                "item_name": "변환된 한글 품목명 (예: 교체용니들 0.6)",
                "qty": "최종 환산 수량 (예: 40개 (2박스 × 20개))"
              }}
            ]

            분석할 카톡 메시지:
            \"\"\"{user_input}\"\"\"
            """

            with st.spinner("Gemini AI가 문맥을 분석하여 파싱 중입니다..."):
                try:
                    generation_config = {"temperature": 0.0}

                    model = genai.GenerativeModel(
                        "gemini-3.5-flash-lite", generation_config=generation_config
                    )
                    response = model.generate_content(prompt)

                    raw_result = response.text.strip()

                    if "```" in raw_result:
                        raw_result = raw_result.replace("```json", "").replace("```", "")

                    start_idx = raw_result.find("[")
                    end_idx = raw_result.rfind("]")

                    if start_idx != -1 and end_idx != -1:
                        clean_json = raw_result[start_idx : end_idx + 1]
                        st.session_state["raw_parsed_data"] = json.loads(clean_json)
                    else:
                        st.error("결과를 분석하는 데 실패했습니다.")

                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

    if "raw_parsed_data" in st.session_state and st.session_state["raw_parsed_data"]:
        parsed_data = st.session_state["raw_parsed_data"]

        col_header_left, col_header_right = st.columns([7, 3])
        with col_header_left:
            st.subheader(f"추출 결과 (총 {len(parsed_data)}개 품목)")

        # 우측 위치는 그대로 유지하고, 두 선택지를 하나의 반분된 버튼으로 표시
        with col_header_right:
            device_unit_mode = st.segmented_control(
                "장치 단위 선택",
                options=["5개 단위 (기본)", "10개 단위"],
                default="5개 단위 (기본)",
                key="device_unit_segmented",
                label_visibility="collapsed",
                width="stretch",
            )

        selected_mode = device_unit_mode if device_unit_mode else "5개 단위 (기본)"
        multiplier = 10 if "10개" in selected_mode else 5

        processed_rows = []
        for idx, item in enumerate(parsed_data, 1):
            item_name = str(item.get("item_name", ""))
            raw_qty = str(item.get("qty", ""))

            if "장치" in item_name:
                # "40개 (2박스 × 20개)"처럼 반환되어도 첫 숫자 40을
                # 박스 수로 오인하지 않고 "박스" 앞 숫자만 사용
                box_match = re.search(r"(\d+)\s*박스", raw_qty)
                box_count = int(box_match.group(1)) if box_match else 0
                calc_total = box_count * multiplier
                display_qty = f"{calc_total}개 ({box_count}박스 × {multiplier}개)"
            else:
                display_qty = raw_qty

            processed_rows.append({
                "No.": idx,
                "주문처(병원)": item.get("hospital", ""),
                "원문 텍스트": item.get("original", ""),
                "품목코드": item.get("item_code", ""),
                "품목명": item_name,
                "수량 환산": display_qty,
            })

        df = pd.DataFrame(processed_rows)

        # st.dataframe/st.table의 내부 정렬 CSS에 의존하지 않고
        # 실제 HTML 셀(th/td)에 직접 정렬을 지정한다.
        html_table = df.to_html(
            index=False,
            classes="order-result-table",
            border=0,
            escape=True,
        )
        st.markdown(html_table, unsafe_allow_html=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 엑셀(CSV) 다운로드",
            data=csv,
            file_name="order_result.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_csv_btn"
        )
