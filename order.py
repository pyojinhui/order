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
            - 단, 동일한 핵심 키워드를 공유하더라도 실제 거래처가 다른 경우에는 반드시 구분하여 매핑하세요.
            - 예시:
            - '한나이브성형외과', '한나이브성형외과의원' → 한나이브성형외과 거래처
            - '한나이브외과', '한나이브외과의원' → 한나이브외과 거래처
            - '한나이브'처럼 병원명이 불완전하여 어느 거래처인지 구분할 수 없는 경우에는 임의로 한 곳에 매핑하지 말고 문맥을 확인하세요.
            - 예시: '김문규경대숲', '김문규' -> 김문규경대숲의원 인식
            - 예시: '마이모' -> 마이모의원 인식
            - 예시: '모디헤어', '모디' -> 모디헤어플란트의원 인식
            - 예시: '이규호', '모아름' -> 이규호 모아름의원 인식
            - 예시: '젬마' -> 젬마의원 인식
            - 예시: '포헤어' -> 포헤어의원(서울) 인식

            [거래처별 전용 펀치류 모델 매핑 규칙 - 라인 및 규격 일치 시에만 적용]

카톡 메시지에 언급된 거래처가 아래 목록에 해당하는 경우, 펀치류 주문에 대해 거래처별 전용 모델 적용 가능 여부를 먼저 확인하세요.

**1. 전용 모델 적용 원칙**

- 거래처별 전용 모델은 주문 원문의 펀치 라인과 규격이 해당 전용 모델의 조건에 모두 일치하는 경우에만 적용합니다.
- 거래처명이 일치하더라도 주문한 펀치 라인 또는 규격이 전용 모델과 다르면 전용 모델을 적용하지 마세요.
- 전용 모델 적용 조건에 맞지 않으면 일반 병원과 동일하게 주문 원문에 명시된 펀치 라인과 규격을 기준으로 품목코드와 품목명을 매핑하세요.
- 전용 모델이 있다는 이유만으로 주문 원문의 펀치 라인이나 규격을 변경하지 마세요.
- 전용 모델의 규격이 주문 규격과 다르더라도 임의로 전용 모델의 규격에 맞춰 변환하지 마세요.
- 일반 펀치 라인이 명시되어 있지 않거나 규격이 확인되지 않으면 기존 일반 펀치류 파싱 규칙을 적용하여 임의로 라인이나 규격을 추론하지 마세요.
- 단, 거래처별 전용 모델의 적용 조건에 라인이 명시되어 있지 않거나 별도의 허용 조건이 정의되어 있다면, 해당 조건이 명확하게 충족되는 경우에만 전용 모델을 적용하세요.

**2. 거래처별 전용 모델 및 적용 조건**

1) 김문규경대숲의원
- 식별 키워드: 김문규
- 전용 모델: HFUE-TL-085K, HFUE-TL-080(M)
- 전용 모델 규격: 0.85K, 0.8
- 적용 조건: 주문 라인이 트럼펫(TL)이고 규격이 0.85K인 경우에만 적용합니다.
- 그 외 라인 또는 규격은 주문 원문에 따라 일반 펀치류 규칙을 적용합니다.

2) 마이모의원
- 식별 키워드: 마이모
- 전용 모델: HFUE-SHT-090
- 전용 모델 규격: SHT 0.90
- 적용 조건: 주문 라인이 SHT이고 규격이 0.90인 경우에만 적용합니다.
- 그 외 라인 또는 규격은 주문 원문에 따라 일반 펀치류 규칙을 적용합니다.

3) 모디헤어플란트의원
- 식별 키워드: 모디헤어, 모디
- 전용 모델 형식: HFUE-TS-[규격 숫자 세 자리]
- 적용 조건: 주문 원문의 규격을 그대로 사용하여 해당 전용 코드의 규격과 일치하는 경우에 적용합니다.
- 주문 라인이나 규격이 전용 모델의 조건과 일치하지 않으면 일반 펀치류 규칙을 적용합니다.

4) 이규호 모아름의원
- 식별 키워드: 이규호, 모아름
- 전용 모델: MHP-RS-090(이규호)
- 전용 모델 규격: RS 0.90
- 적용 조건: 주문 라인이 RS이고 규격이 0.90인 경우에만 적용합니다.
- 그 외 라인 또는 규격은 주문 원문에 따라 일반 펀치류 규칙을 적용합니다.

5) 젬마의원
- 식별 키워드: 젬마
- 전용 모델: HFUE-RS-075(젬마)
- 전용 모델 규격: RS 0.75
- 적용 조건: 주문 라인이 RS이고 규격이 0.75인 경우에만 적용합니다.
- 트럼펫 0.80, 트럼펫 1.00 등 다른 라인이나 규격의 주문에는 젬마 전용 모델을 적용하지 마세요.
- 예: "젬마 트럼펫 0.8 100개" → HFUE-TL-080 / 트럼펫 펀치 0.80
- 예: "젬마 RS 0.75 100개" → HFUE-RS-075(젬마) / 젬마 전용 펀치 0.75
- 그 외 라인 또는 규격은 주문 원문에 따라 일반 펀치류 규칙을 적용합니다.

6) 포헤어의원(서울)
- 식별 키워드: 포헤어
- 전용 모델: MHP-SL-100(F)
- 전용 모델 규격: SL 1.00
- 적용 조건: 주문 라인이 SL이고 규격이 1.00인 경우에만 적용합니다.
- 그 외 라인 또는 규격은 주문 원문에 따라 일반 펀치류 규칙을 적용합니다.

7) 한나이브성형외과
- 식별 키워드: 한나이브성형, 한나이브성형외과
- 전용 모델: MHP-TL-100(W)
- 전용 모델 규격: TL 1.00(W)
- 적용 조건: 주문 라인이 TL이고 규격이 1.00이며, 전용 모델의 특수모델 조건까지 일치하는 경우에만 적용합니다.
- 그 외 라인 또는 규격은 주문 원문에 따라 일반 펀치류 규칙을 적용합니다.

8) 한나이브외과의원
- 식별 키워드: 한나이브외과
- 전용 모델: MHP-TL-100(W)
- 전용 모델 규격: TL 1.00(W)
- 적용 조건: 주문 라인이 TL이고 규격이 1.00이며, 전용 모델의 특수모델 조건까지 일치하는 경우에만 적용합니다.
- 그 외 라인 또는 규격은 주문 원문에 따라 일반 펀치류 규칙을 적용합니다.
- 한나이브성형외과와 한나이브외과의원은 서로 다른 거래처이므로 반드시 구분합니다.

9) 모래내의원, 센텀모빅스피부과의원, 더모헤어플란트피부과의원
- 식별 키워드: 모래내, 센텀모빅스, 더모헤어플란트
- 등록된 전용 모델: HFUE-TL-085K, HFUE-TL-080(M)
- 각 모델은 주문 라인과 규격이 해당 모델의 조건에 일치하는 경우에만 적용합니다.
- TL 0.85K 주문은 HFUE-TL-085K를 적용합니다.
- TL 0.80 주문은 HFUE-TL-080(M)을 적용합니다.
- 그 외 라인 또는 규격은 주문 원문에 따라 일반 펀치류 규칙을 적용합니다.

**3. 전용 모델 적용 후 일반 모델 처리**

전용 모델 적용 여부를 확인한 뒤, 전용 모델 조건에 일치하지 않는 주문은 반드시 기존 일반 펀치류 규칙으로 처리합니다.

예시:

- "젬마 트럼펫 0.8 100개"
  → HFUE-TL-080 / 트럼펫 펀치 0.80

- "젬마 크라운 1.0 100개"
  → HFUE-SL-100 / 세레티드 펀치 1.00

- "젬마 RS 0.75 100개"
  → HFUE-RS-075(젬마) / 젬마 전용 펀치 0.75

- "마이모 RL 0.8 100개"
  → HFUE-RL-080 / 라운드 펀치 0.80

- "마이모 SHT 0.9 100개"
  → HFUE-SHT-090 / 트럼펫타입 사이드홀 0.90

- "포헤어 트럼펫 0.8 100개"
  → HFUE-TL-080 / 트럼펫 펀치 0.80

- "포헤어 SL 1.0 100개"
  → MHP-SL-100(F) / 포헤어 전용 펀치 1.00

- "김문규 트럼펫 0.8 100개"
  → HFUE-TL-080 / 트럼펫 펀치 0.80

- "김문규 트럼펫 0.85 100개"
  → HFUE-TL-085K / 트럼펫 펀치 0.85K

**4. 최종 적용 우선순위**

1. 거래처명 식별
2. 주문 원문의 펀치 라인, 규격 및 특수모델 확인
3. 거래처별 전용 모델의 라인·규격·특수모델 조건 일치 여부 확인
4. 조건이 모두 일치하면 전용 모델 적용
5. 조건이 일치하지 않으면 기존 일반 펀치류 코드 매핑 규칙 적용
6. 일반 펀치 라인 또는 규격이 확인되지 않으면 임의로 코드를 생성하지 않고 미확정 상태로 출력

**중요: 거래처별 전용 모델은 일반 펀치류 규칙보다 무조건 우선 적용되는 규칙이 아닙니다. 전용 모델의 라인과 규격 등 적용 조건이 주문 원문과 일치하는 경우에만 우선 적용합니다.**


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

               [INNER BODY와 모발이식장치 구분 규칙]

              - INNER BODY와 모발이식장치는 규격 숫자(0.6~1.2)가 동일하더라도 서로 완전히 다른 품목입니다.
              - 숫자만 보고 품목을 판단하거나 매핑하지 마세요.
              - 주문 원문에 "INNER BODY", "INNERBODY", "이너바디"가 명시되어 있으면 반드시 INNER_BODY_MAP을 사용하세요.
              - 주문 원문에 "식모기", "모발이식장치", "장치", "본체"가 명시되어 있으면 반드시 DEVICE_MAP을 사용하세요.
              - 예:
              - "INNER BODY 0.8" → OHA-2065A / INNER BODY(0.8)
              - "이너바디 0.8" → OHA-2065A / INNER BODY(0.8)
              - "식모기 0.8" → OAA-2190(1) / 모발이식장치 0.8
              - "모발이식장치 0.8" → OAA-2190(1) / 모발이식장치 0.8
              - "0.8"처럼 규격 숫자만 단독으로 있는 경우에는 임의로 INNER BODY 또는 모발이식장치로 판단하지 마세요.

            2. 식모기/본체/장치 (1박스 = 5개 환산)
               - 식모기_0.6 -> 품목코드: "OAA-2202(1)", 품목명: "모발이식장치 0.6"
               - 식모기_0.7 -> 품목코드: "OAA-2193(1)", 품목명: "모발이식장치 0.7"
               - 식모기_0.8 -> 품목코드: "OAA-2190(1)", 품목명: "모발이식장치 0.8"
               - 식모기_0.9 -> 품목코드: "OAA-2194(1)", 품목명: "모발이식장치 0.9"
               - 식모기_1.0 -> 품목코드: "OAA-2191(1)", 품목명: "모발이식장치 1.0"
               - 식모기_1.1 -> 품목코드: "OAA-2195(1)", 품목명: "모발이식장치 1.1"
               - 식모기_1.2 -> 품목코드: "OAA-2192(1)", 품목명: "모발이식장치 1.2"

                            [교체용니들 / 모발이식장치 특수모델 규칙]

             - 교체용니들과 모발이식장치에는 기본 모델 외에 특수모델이 있습니다.
             - 특수모델은 품목코드 뒤에 아래 suffix를 추가하여 구분합니다.
               - D = dull
               - W = wide
               - T = thin

             - 특수모델이 명시되지 않은 경우에는 기본 품목코드를 사용합니다.
             - 특수모델이 명시된 경우에는 해당 특수모델의 suffix를 기본 품목코드 뒤에 추가합니다.

             [특수모델 허용 규격]
             - dull(D): 모든 규격에서 사용 가능
             - wide(W): 0.7, 0.8, 0.9, 1.0에서만 사용 가능
             - thin(T): 0.8, 1.0에서만 사용 가능

             - 허용되지 않는 규격에 특수모델이 입력된 경우에는 임의로 품목코드를 생성하지 마세요.
             - 예:
               "0.8 thin" -> 기본 품목코드 뒤에 T 추가
               "1.0 thin" -> 기본 품목코드 뒤에 T 추가
               "0.7 wide" -> 기본 품목코드 뒤에 W 추가
               "0.9 wide" -> 기본 품목코드 뒤에 W 추가
               "1.2 wide" -> wide는 1.2에 존재하지 않으므로 임의로 W를 붙이지 않음
               "0.6 thin" -> thin은 0.6에 존재하지 않으므로 임의로 T를 붙이지 않음

             [교체용니들 예시]
             - 교체용니들 0.8 기본 -> "OAA-2109(1)"
             - 교체용니들 0.8 thin -> "OAA-2109T(1)"
             - 교체용니들 0.8 wide -> "OAA-2109W(1)"
             - 교체용니들 0.8 dull -> "OAA-2109D(1)"

             - 교체용니들 1.0 기본 -> "OAA-2110(1)"
             - 교체용니들 1.0 thin -> "OAA-2110T(1)"
             - 교체용니들 1.0 wide -> "OAA-2110W(1)"
             - 교체용니들 1.0 dull -> "OAA-2110D(1)"

             [중요]
             - "thin", "wide", "dull"은 규격과 별개의 특수모델 정보입니다.
             - "0.8 thin"은 "0.8"이라는 규격과 "thin"이라는 특수모델을 모두 인식해야 합니다.
             - "thin"이 포함되어 있다고 해서 다른 규격으로 변경하지 마세요.
             - 주문 원문에 여러 품목이 있는 경우 각 품목별로 규격과 특수모델을 독립적으로 판단하세요.


                          [연속 줄 주문 파싱 규칙]

             - 주문 원문에서 품목명이 한 번만 표시되고 그 아래에 여러 줄로 규격과 수량이 나열된 경우,
               해당 품목명은 다음 품목명이 새로 등장하기 전까지 이어지는 모든 줄에 적용합니다.

             - 예:
               "식모기니들
                0.7 10박스
                0.9 10박스
                1.0 10박스
                1.1 10박스
                펀치니들 1.1 200개"

               위 주문은 다음과 같이 각각 독립된 품목으로 파싱합니다.

               1. 식모기니들 0.7 10박스
               2. 식모기니들 0.9 10박스
               3. 식모기니들 1.0 10박스
               4. 식모기니들 1.1 10박스
               5. 펀치니들 1.1 200개

             - "식모기니들"은 반드시 교체용니들 품목으로 인식합니다.
             - "식모기" 또는 "모발이식장치"는 모발이식장치 품목으로 인식합니다.
             - "식모기니들"과 "식모기"는 서로 다른 품목이므로 혼동하지 마세요.
             - 새로운 품목명이 등장하면 그 이후부터는 새 품목의 규칙을 적용합니다.

             [수량 환산 규칙]

             - 교체용니들: 1박스 = 20개
             - 펀치니들: 1박스 = 10개
             - 모발이식장치: 기본 1박스 = 5개
             - 모발이식장치의 1박스 환산 단위는 사용자가 선택한 장치 단위 설정을 따릅니다.
             - 장치 단위가 "5개 단위"이면 1박스 = 5개
             - 장치 단위가 "10개 단위"이면 1박스 = 10개
             - 장치 외의 품목은 장치 단위 설정의 영향을 받지 않습니다.
             - 주문 수량이 "개"로 명시된 경우에는 별도 환산 없이 입력된 수량 그대로 사용합니다.

             - 예:
               "식모기니들 0.7 10박스" → 교체용니들 0.7 / 10박스 × 20 = 200개
               "식모기니들 0.9 10박스" → 교체용니들 0.9 / 10박스 × 20 = 200개
               "식모기니들 1.0 10박스" → 교체용니들 1.0 / 10박스 × 20 = 200개
               "식모기니들 1.1 10박스" → 교체용니들 1.1 / 10박스 × 20 = 200개
               "펀치니들 1.1 200개" → 펀치니들 1.1 / 200개 그대로

            3. 이너바디
             - 이너바디_0.6 -> 품목코드: "OHA-2065D", 품목명: "INNER BODY(0.6)"
             - 이너바디_0.7 -> 품목코드: "OHA-2065E", 품목명: "INNER BODY(0.7)"
             - 이너바디_0.8 -> 품목코드: "OHA-2065A", 품목명: "INNER BODY(0.8)"
             - 이너바디_0.9 -> 품목코드: "OHA-2065F", 품목명: "INNER BODY(0.9)"
             - 이너바디_1.0 -> 품목코드: "OHA-2065B", 품목명: "INNER BODY(1.0)"
             - 이너바디_1.1 -> 품목코드: "OHA-2065G", 품목명: "INNER BODY(1.1)"
             - 이너바디_1.2 -> 품목코드: "OHA-2065C", 품목명: "INNER BODY(1.2)"

              [교체용니들 + 이너바디 규격 연동 규칙]

             - "1.0니들 35박스 / 이너바디 10개"처럼 니들 규격이 먼저 명시되고 이후 "이너바디"에 규격이 생략된 경우,
               이너바디는 앞에서 명시된 니들의 규격을 그대로 따라갑니다.
             - 예:
               "1.0니들 35박스 / 이너바디 10개"
               -> 교체용니들 1.0 / INNER BODY 1.0
               
               "0.8니들 20박스 / 이너바디 5개"
               -> 교체용니들 0.8 / INNER BODY 0.8
               
               "1.2니들 10박스 / 이너바디 3개"
               -> 교체용니들 1.2 / INNER BODY 1.2

             - 이너바디에 별도의 규격이 명시되어 있으면 앞의 니들 규격보다 이너바디에 직접 표시된 규격을 우선합니다.
             - 예:
               "1.0니들 35박스 / 이너바디 0.8 10개"
               -> 교체용니들 1.0 / INNER BODY 0.8
             
             - 따라서 "이너바디" 뒤에 규격이 없는 경우에는 바로 앞에서 명시된 니들 규격을 이너바디 규격으로 사용합니다.
               

            4. 일반 병원의 펀치류 (1박스 = 10개 환산)

             [펀치 라인 종류 및 코드]

             - NHT(뉴하이브리드 토네이도):
               nht / NHT / 뉴하이브리드 토네이도
               -> 품목코드: "HFUE-NHT-[규격숫자 세자리]"
               -> 품목명: "뉴하이브리드 토네이도 [규격]"

             - HT(하이브리드 토네이도):
               ht / HT / 하이브리드 토네이도
               -> 품목코드: "HFUE-HT-[규격숫자 세자리]"
               -> 품목명: "하이브리드 토네이도 [규격]"

             - SH(라운드타입 사이드홀):
               sh / SH / 라운드타입 사이드홀
               -> 품목코드: "HFUE-SH-[규격숫자 세자리]"
               -> 품목명: "라운드타입 사이드홀 [규격]"

             - SHS(크라운타입 사이드홀):
               shs / SHS / 크라운타입 사이드홀
               -> 품목코드: "HFUE-SHS-[규격숫자 세자리]"
               -> 품목명: "크라운타입 사이드홀 [규격]"

             - SHT(트럼펫타입 사이드홀):
               sht / SHT / 트럼펫타입 사이드홀
               -> 품목코드: "HFUE-SHT-[규격숫자 세자리]"
               -> 품목명: "트럼펫타입 사이드홀 [규격]"

             - FT(Flared 타입):
               ft / FT / flared / Flared
               -> 품목코드: "HFUE-FT-[규격숫자 세자리]"
               -> 품목명: "Flared 타입 [규격]"


             [사이드홀 슬릿 특수모델]

             - 사이드홀에는 "슬릿(Slit)" 특수모델이 있습니다.
             - 슬릿이 명시된 경우 해당 사이드홀 기본 코드 뒤에 반드시 "S" suffix를 붙입니다.
             - 슬릿은 규격과 별개의 특수모델 정보입니다.
             - SH / SHS / SHT 중 어떤 사이드홀 라인인지 먼저 판단한 후 슬릿 여부를 적용합니다.

             예:
             - "SH 0.8" -> HFUE-SH-080
             - "SH 0.8 슬릿" -> HFUE-SH-080S
             - "SH-080S" -> HFUE-SH-080S
             - "SHS 0.8" -> HFUE-SHS-080
             - "SHS 0.8 슬릿" -> HFUE-SHS-080S
             - "SHT 0.8" -> HFUE-SHT-080
             - "SHT 0.8 슬릿" -> HFUE-SHT-080S

             - 코드 끝의 "S"는 슬릿 특수모델을 의미합니다.
             - "S"가 포함되어 있다고 해서 SL 펀치로 판단하지 마세요.
             - SH / SHS / SHT 라인이 먼저 확정된 경우에만 슬릿 suffix를 적용하세요.


             [기존 일반 펀치 라인]

             - SS 펀치:
               ss100 / ss-100 / SS100 / SS-100 / SS 펀치
               -> 품목코드: "HFUE-SS-100"
               -> 품목명: "SS 펀치 1.00"

             - RL(라운드):
               라운드 / round / RL이 주문 원문에 명시된 경우에만 적용
               -> 품목코드: "HFUE-RL-[규격숫자 세자리]"
               -> 품목명: "라운드 펀치 [규격]"

             - SL(세레티드/크라운):
               세레티드 / serrated / 크라운 / crown / SL이 주문 원문에 명시된 경우에만 적용
               -> 품목코드: "HFUE-SL-[규격숫자 세자리]"
               -> 품목명: "세레티드 펀치 [규격]"

             - TL(트럼펫):
               트럼펫 / trumpet / TL이 주문 원문에 명시된 경우에만 적용
               -> 품목코드: "HFUE-TL-[규격숫자 세자리]"
               -> 품목명: "트럼펫 펀치 [규격]"


                [모모의원 전용 매핑 - 최우선 적용]

             - 주문 원문에 "모모"가 포함되어 있으면 모모의원으로 인식합니다.
             - "모모 수원", "모모 강남", "모모 부산", "모모 대구", "모모(수원)", "모모(강남)"처럼
               "모모 + 지점명" 형태로 작성된 경우에도 반드시 모모의원으로 인식합니다.
             - 지점명은 모모의원 거래처를 구분하기 위한 정보일 뿐, 별도의 거래처로 판단하지 않습니다.

             - 모모의원에서 "트럼펫 100" 또는 "트럼펫 1.0" 또는 "TL 100" 또는 "TL 1.0" 주문:
               -> 품목코드: "HFUE-TL-100(M)"
               -> 품목명: "트럼펫 펀치 1.00(M)"

             - 모모의원에서 "크라운 100" 또는 "크라운 1.0" 또는 "SL 100" 또는 "SL 1.0" 주문:
               -> 품목코드: "HFUE-SL-100"
               -> 품목명: "세레티드 펀치 1.00"

             - 모모의원이라고 해서 모든 펀치를 M타입으로 변경하지 마세요.
             - M타입은 모모의원의 트럼펫 1.00에만 적용합니다.
             - 모모의원 크라운 1.00은 일반 HFUE-SL-100을 사용합니다.
             - 모모의원에서 1.00 이외의 트럼펫 규격은 별도 M타입으로 변경하지 않습니다.
             - 모모의원에서 다른 규격 또는 다른 펀치 라인이 주문된 경우에는 별도 전용 규칙이 없는 한 일반 펀치 매핑을 적용합니다.


             [펀치 라인 판별 핵심 규칙]

             - 펀치니들은 "펀치니들"이라는 단어만으로 RL / SL / TL을 판단하지 않습니다.
             - 규격 숫자만으로 RL / SL / TL을 판단하지 않습니다.
             - "일반 병원", "일반 펀치", "일반 거래처"라는 표현은 TL을 의미하지 않습니다.
             - "펀치니들 1.1 200개"처럼 라인이 없는 경우 절대로 TL-110으로 변환하지 않습니다.
             - 라인이 없는 경우 RL / SL / TL 중 어느 하나도 임의로 선택하지 않습니다.
             - 동일 주문의 앞선 줄에서 라인이 명시된 경우에는 새로운 라인이 나오기 전까지 해당 라인을 계속 적용합니다.
             - 새로운 펀치 라인이 나오면 그 시점부터 새로운 라인으로 변경합니다.
             - NHT / HT / SH / SHS / SHT / FT 역시 각각 독립된 펀치 라인으로 판단합니다.
             - 펀치 라인이 명확하게 확인된 경우에만 해당 라인의 품목코드를 생성합니다.
             - 크라운, 세레티드, SL 등 펀치 라인이 확인되더라도 규격 숫자가 없으면 규격을 임의로 추론하지 않습니다.
             - "크라운 펀치팁 50개"처럼 라인은 확인되지만 규격이 없는 경우:
               -> 품목코드: ""
               -> 품목명: "펀치니들 (SL 라인 / 규격 미확정)"
               -> 수량: "50개"
             - 규격이 명시되지 않은 경우 SL-100 등 특정 규격의 품목코드를 생성하지 않습니다.
             - 단, 거래처별 전용 매핑 규칙으로 규격까지 명확하게 확정되는 경우에는 해당 규칙을 적용합니다.


             [예시]

             - "NHT 0.8 100개"
               -> HFUE-NHT-080

             - "HT 1.0 100개"
               -> HFUE-HT-100

             - "SH 0.8 100개"
               -> HFUE-SH-080

             - "SH 0.8 슬릿 100개"
               -> HFUE-SH-080S

             - "SH-080S 100개"
               -> HFUE-SH-080S

             - "SHS 0.8 100개"
               -> HFUE-SHS-080

             - "SHT 0.8 100개"
               -> HFUE-SHT-080

             - "SHT 0.8 슬릿 100개"
               -> HFUE-SHT-080S

             - "FT 0.9 100개"
               -> HFUE-FT-090

             - "모모(강남)
                트럼펫 100 100개"
               -> HFUE-TL-100(M)

             - "모모(강남)
                크라운 100 100개"
               -> HFUE-SL-100

             - "펀치니들 1.1 200개"
               -> 라인 미확정
               -> 품목코드: ""
               -> 품목명: "펀치니들 1.1 (라인 미확정)"
               -> 수량: "200개"


             [펀치류 규격 변환]

             - 라인이 확정된 경우에만 규격을 코드로 변환합니다.
             - 0.6 -> 060
             - 0.7 -> 070
             - 0.8 -> 080
             - 0.9 -> 090
             - 1.0 -> 100
             - 1.1 -> 110
             - 1.2 -> 120
             - 0.85 -> 085
             - 규격 숫자만으로 펀치 라인을 결정하지 않습니다.

           5.
             - 핸드피스_2세대 -> 품목코드: "MTP-H175", 품목명: "핸드피스A (Graft2 전용)"
             - 핸드피스_헤드 -> 품목코드: "META-007B", 품목명: "hand piece head(상품) (Graft1 전용)"
             - 헤드 -> 품목코드: "META-007B", 품목명: "hand piece head(상품) (Graft1 전용)"
             - 핸드피스 -> 품목코드: "META-007A", 품목명: "hand piece assy (Graft1 전용)"
             - 천공기 -> 품목코드: "MTP-HF10", 품목명: "FUE 모낭채취장치"
             - 모낭채취기기_버젼1 -> 품목코드: "MTP-HF10", 품목명: "FUE 모낭채취장치"
             - 모낭채취기기_FUE -> 품목코드: "MTP-HF10", 품목명: "FUE 모낭채취장치"
             - FUE_모낭채취장치 -> 품목코드: "MTP-HF10", 품목명: "FUE 모낭채취장치"
             - needle_controller -> 품목코드: "OHA-2064A", 품목명: "NEEDLE CONTROLLER"
             - 아우터바디 -> 품목코드: "OHA-2170A", 품목명: "OUTER BODY"
             - outer_body -> 품목코드: "OHA-2170A", 품목명: "OUTER BODY"
             - spindle -> 품목코드: "META-013", 품목명: "Spindle"
             - 스핀들 -> 품목코드: "META-013", 품목명: "Spindle"
             - spring -> 품목코드: "SPR-101-001", 품목명: "spring"
             - 스프링 -> 품목코드: "SPR-101-001", 품목명: "spring"
             - 볼빅트랜스폼세트 -> 품목코드: "MTP-BV-TR1", 품목명: "볼빅트랜스폼세트"
             - 오일스프레이 -> 품목코드: "MTP-SP", 품목명: "오일스프레이"
             - 캡 -> 품목코드: "OHA-2063A", 품목명: "CAP"
             

            [주의사항]
            - '0,7'과 같이 쉼표가 들어간 소수점은 '0.7'로 자동 교정하세요.
            - 한 줄에 여러 품목이 언급된 경우 각각 독립된 항목으로 분리하세요.
            - '식모기팁'처럼 '팁'이나 '니들'이 포함된 경우 식모기 장치가 아니라 '니들'로 판단하세요.
           * 단일 알파벳 `'s'`는 반드시 **교체용니들 0.8**로 파싱하세요.
           * `'ss100'`, `'ss-100'`은 반드시 **HFUE-SS-100**으로 파싱하세요.
           * `'s-100'`, `'s100'`처럼 `'s' + 숫자 규격`으로 입력된 경우에는 **SL 계열로 우선 해석하여 `HFUE-SL-100`으로 파싱하세요.**
           * `'sl100'`, `'sl-100'`은 **HFUE-SL-100**으로 파싱하세요.
           * `'s'`와 `'s + 숫자'`는 완전히 다른 입력으로 취급하세요.
           * 단, 병원/거래처별 전용 품목코드가 있는 경우에는 해당 거래처의 전용 매핑 규칙을 최우선으로 적용하세요.
           * 파싱 우선순위는 다음과 같습니다.

        1. 거래처별 전용 품목 매핑
        2. `ss` + 숫자 → SS 계열
        3. `sl` + 숫자 → SL 계열
        4. `s` + 숫자 → SL 계열
        5. 단일 `s` → 교체용니들 0.8

            - 거래처명은 메시지 내에서 핵심 명칭만 언급되어도 식별 가능한 명칭으로 매핑하여 정제하세요.
            - 반드시 품목코드는 영문/숫자 코드로만, 품목명은 한글 항목명으로 정확히 구분하여 분리하세요.

            [응답 형식]
            반드시 마크다운이나 다른 설명 없이 아래 형태의 JSON Array로만 응답하세요.
            [
              {{
                "hospital": "병원명",
                "original": "원문 텍스트 조각",
                "item_code": "변환된 품목코드 (예: OAA-2199(1) 또는 HFUE-TL-085K)",
                "item_name": "변환된 한글 품목명 (예: 교체용니들 0.8)",
                "qty": "최종 환산 수량 (예: 40개 (2박스 × 20개))"
              }}
            ]

            분석할 카톡 메시지:
            \"\"\"{user_input}\"\"\"
            """
            if not api_key:
                st.error("Gemini API 키를 찾을 수 없습니다. 배포 환경의 Secrets 설정을 확인해 주세요.")
                st.stop()
            with st.spinner("Gemini AI가 문맥을 분석하여 파싱 중입니다..."):
                try:
                    generation_config = {"temperature": 0.0}

                    model = genai.GenerativeModel(
                        "gemini-3.5-flash-lite", generation_config=generation_config
                    )
                    response = model.generate_content(
                       prompt,
                       request_options={"timeout": 30}
                    )

                    raw_result = response.text.strip()

                    if "```" in raw_result:
                        raw_result = raw_result.replace("```json", "").replace("```", "")

                    start_idx = raw_result.find("[")
                    end_idx = raw_result.rfind("]")

                    if start_idx != -1 and end_idx != -1:
                        clean_json = raw_result[start_idx : end_idx + 1]

                        parsed_result = json.loads(clean_json)
                                               # ====================================================
                       # 교체용니들 품목코드 강제 매핑
                       # ====================================================
                        NEEDLE_CODE_MAP = {
                           "0.6": "OAA-2199(1)",
                           "0.7": "OAA-2112(1)",
                           "0.8": "OAA-2109(1)",
                           "0.9": "OAA-2113(1)",
                           "1.0": "OAA-2110(1)",
                           "1.1": "OAA-2196(1)",
                           "1.2": "OAA-2111(1)",
                       }

                        for row in parsed_result:
                           item_name = str(row.get("item_name", "")).strip()
                           original_text = str(row.get("original", "")).strip()

                           # 교체용니들 품목에만 적용
                           if "교체용니들" not in item_name:
                               continue

                           # 품목명에서 규격 추출
                           size_match = re.search(
                               r"교체용니들\s*([01][.,]\d{1,2})",
                               item_name
                           )

                           if not size_match:
                               continue

                           size = size_match.group(1).replace(",", ".")
                           base_code = NEEDLE_CODE_MAP.get(size)

                           if not base_code:
                               continue

                           # 특수 모델 확인
                           original_lower = original_text.lower()
                           suffix = ""

                           if re.search(r"thin|씬|띤", original_lower):
                               suffix = "T"
                           elif re.search(r"wide|와이드", original_lower):
                               suffix = "W"
                           elif re.search(r"dull|덜", original_lower):
                               suffix = "D"

                           # 특수 모델 적용 가능 규격 제한
                           if suffix == "T" and size not in ("0.8", "1.0"):
                               suffix = ""
                           elif suffix == "W" and size not in (
                               "0.7", "0.8", "0.9", "1.0"
                           ):
                               suffix = ""

                           # 최종 품목코드 적용
                           row["item_code"] = base_code.replace(
                               "(1)", f"{suffix}(1)"
                           )

                        
                        # ====================================================
                        # 수량 누락 보완: 주문 원문에서 규격별 수량 추출
                        # ====================================================
                        for row in parsed_result:
                            current_qty = str(row.get("qty", "")).strip()

                            # 이미 수량이 있으면 기존 값 유지
                            if current_qty:
                                continue

                            original_text = str(row.get("original", ""))
                            item_code = str(row.get("item_code", "")).upper()

                            # 품목코드에서 규격 추출 (예: 080, 085K, 100(M))
                            code_size_match = re.search(
                                r"-(\d{3})(?:[A-Z]|\([A-Z]\))?$",
                                item_code
                            )

                            if not code_size_match:
                                continue

                            code_size = code_size_match.group(1)

                            # 주문 원문에서 규격과 수량이 함께 있는 줄 검색
                            for line in user_input.splitlines():
                                size_match = re.search(
                                    r"(?<!\d)(0[.,]\d{1,2}|1[.,]\d{1,2}|0\d{2}|1\d{2})(?!\d)",
                                    line
                                )
                                qty_match = re.search(
                                    r"(?<![\d.,])(\d[\d,]*)\s*(개|ea|박스|box)\b?",
                                    line,
                                    re.IGNORECASE
                                )

                                if not size_match or not qty_match:
                                    continue

                                size_text = size_match.group(1).replace(",", ".")

                                try:
                                    size_value = float(size_text)
                                    line_size = f"{int(round(size_value * 100)):03d}"
                                except ValueError:
                                    continue

                                if line_size == code_size:
                                    row["qty"] = (
                                        f"{qty_match.group(1)}{qty_match.group(2)}"
                                    )
                                    break

                        # ====================================================
                        # 펀치류 규격 검증: 규격 없는 크라운은 SL-100 생성 금지
                        # ====================================================
                        for row in parsed_result:
                            original_text = str(row.get("original", ""))
                            lower_text = original_text.lower()

                            is_sl_line = (
                                "크라운" in original_text
                                or "crown" in lower_text
                                or "세레티드" in original_text
                                or re.search(
                                    r"(?<![a-z])sl\s*[-_]?\s*\d",
                                    lower_text
                                ) is not None
                            )

                            if is_sl_line:
                                text_without_qty = re.sub(
                                    r"\d+\s*(개|ea|박스|box)",
                                    "",
                                    lower_text,
                                    flags=re.IGNORECASE,
                                )

                                size_match = re.search(
                                    r"(?<!\d)(?:0[.,](?:85|[6789])|1[.,][012]|"
                                    r"060|070|080|085|090|100|110|120)(?!\d)",
                                    text_without_qty,
                                )

                                if not size_match:
                                    row["item_code"] = ""
                                    row["item_name"] = (
                                        "펀치니들 (SL 라인 / 규격 미확정)"
                                    )

                        # ====================================================
                        # 모모의원 전용 후처리
                        # 원문에 "모모"가 있으면 지점명과 관계없이 모모의원으로 인식
                        # ====================================================
                        for row in parsed_result:
                            original_text = str(row.get("original", ""))
                            hospital_text = str(row.get("hospital", ""))
                        

                        # ====================================================
                        # 모모의원 전용 후처리
                        # 원문에 "모모"가 있으면 지점명과 관계없이 모모의원으로 인식
                        # ====================================================
                        for row in parsed_result:
                            original_text = str(row.get("original", ""))
                            hospital_text = str(row.get("hospital", ""))

                            if "모모" in user_input or "모모" in original_text or "모모" in hospital_text:
                                row["hospital"] = "모모의원"

                                punch_text = (original_text + " " + hospital_text).lower()

                                                                # 모모의원 트럼펫 → 규격에 관계없이 M타입
                                if (
                                    "트럼펫" in punch_text
                                    or "trumpet" in punch_text
                                ):
                                    size_match = re.search(
                                        r"(?<!\d)(0[.,]\d{1,2}|1[.,]\d{1,2}|0\d{2}|1\d{2})(?!\d)",
                                        punch_text
                                    )

                                    if size_match:
                                        size_text = size_match.group(1).replace(",", ".")
                                        size_value = float(size_text)

                                        code_size = f"{int(round(size_value * 100)):03d}"

                                        row["item_code"] = f"HFUE-TL-{code_size}(M)"
                                        row["item_name"] = f"트럼펫 펀치 {size_value:.2f}(M)"

                                # 모모의원 크라운 1.0 → 일반 SL
                                elif (
                                    ("크라운" in punch_text or "crown" in punch_text)
                                    and re.search(r"(?<!\d)(1[,.]0|100)(?!\d)", punch_text)
                                ):
                                    row["item_code"] = "HFUE-SL-100"
                                    row["item_name"] = "세레티드 펀치 1.00"

                        st.session_state["raw_parsed_data"] = parsed_result

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
                options=["5개 단위", "10개 단위"],
                default="5개 단위",
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
                # Gemini가 반환한 qty에서 실제 개수와 박스 수 확인
                ea_match = re.search(r"(\d+)\s*개", raw_qty)
                box_match = re.search(r"(\d+)\s*박스", raw_qty)

                if ea_match:
                    # 실제 주문 수량이 개수로 표시된 경우
                    actual_qty = int(ea_match.group(1))

                    if actual_qty % multiplier == 0:
                        box_count = actual_qty // multiplier
                        display_qty = f"{actual_qty}개 ({box_count}박스 × {multiplier}개)"
                    else:
                        display_qty = f"{actual_qty}개"

                elif box_match:
                    # 박스로 주문한 경우에만 선택 단위에 따라 계산
                    box_count = int(box_match.group(1))
                    calc_total = box_count * multiplier
                    display_qty = f"{calc_total}개 ({box_count}박스 × {multiplier}개)"

                else:
                    display_qty = raw_qty

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
