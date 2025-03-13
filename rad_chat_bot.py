import google.generativeai as genai 
import streamlit as st
import os

# API 키 설정 (환경 변수 사용)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
    st.stop()
genai.configure(api_key=api_key)

st.title("영상의학과 검사 안내 챗봇")

# 검사 관련 기본 정보
inspection_guidelines = """
- 초음파: 복부 초음파의 경우 6시간 전부터 금식하세요. 자세한 내용은 노란색 검사안내지를 참고하세요.
- MRI: 금속 물체(장신구, 열쇠 등)를 제거하고 검사실에 들어가세요. 간, 췌장, 담낭 검사는 금식6시간 필수입니다. 자세한 내용은 노란색 검사안내지를 참고하세요.
- CT: 조영제 사용검사의 경우 6시간금식, 검사 2일전 메트포르민 성분 당뇨약을 복용을 중단해야 합니다. 검사전날, 검사당일, 검사다음날까지 3일간 복용을 중단합니다. 자세한 내용은 노란색 검사안내지를 참고하세요.
"""

# 메트포르민 포함 약물 목록
metformin_drugs = [
    "glucophage", "glucophage xr", "metformin", "glycomet", "fortamet", 
    "riomet", "glumetza", "janumet", "다이아벡스"
]

@st.cache_resource
def load_model():
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("model loaded...")
    return model

model = load_model()

# 시스템 프롬프트
system_prompt = (
    "너는 병원 검사 안내 챗봇이야. 환자가 예약된 검사에 대해 질문하면, 개인정보 없이 일반적인 검사 유형(혈액검사, 초음파, MRI, CT 등)에 대한 준비사항, 절차, 주의사항을 친절하게 안내해줘. "
    f"다음은 참고할 기본 정보야:\n{inspection_guidelines}\n"
    "환자가 구체적인 검사 유형을 말하지 않으면, 질문을 명확히 하도록 유도해. "
    "또한, 환자가 당뇨약 이름을 물으면, 그 약이 메트포르민 성분인지 확인해줘. "
    f"메트포르민 포함 약물 목록: {', '.join(metformin_drugs)}. "
    "목록에 없는 약은 '정확한 성분은 의사나 약사에게 확인하세요'라고 답해."
)

if "chat_session" not in st.session_state:    
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": "알겠습니다! 검사나 약에 대해 궁금한 점을 말씀해 주세요."}]}
    ])

# FAQ 정의
faq_questions = [
    "초음파는 언제부터 금식하나요?",
    "MRI 준비사항이 뭐예요?",
    "CT 전에 당뇨약을 끊어야 하나요?",
    "다이아벡스는 메트포르민인가요?",
    "검사 전 물을 마셔도 되나요?"
]

# 화면을 3열로 나누기 (왼쪽 FAQ | 대화창 | 오른쪽 FAQ)
col1, col2, col3 = st.columns([1, 2, 1])  # 비율 조정: 좌 1, 중 2, 우 1

# 왼쪽 FAQ
with col1:
    st.subheader("자주 묻는 질문 (1)")
    for i in range(0, len(faq_questions)//2):  # FAQ 절반을 왼쪽에
        if st.button(faq_questions[i], key=f"faq_left_{i}"):
            st.session_state["chat_input"] = faq_questions[i]

# 오른쪽 FAQ
with col3:
    st.subheader("자주 묻는 질문 (2)")
    for i in range(len(faq_questions)//2, len(faq_questions)):  # 나머지 절반을 오른쪽에
        if st.button(faq_questions[i], key=f"faq_right_{i}"):
            st.session_state["chat_input"] = faq_questions[i]

# 중앙 대화창
with col2:
    # 대화 기록 출력
    for content in st.session_state.chat_session.history[2:]:  # 시스템 프롬프트 제외
        with st.chat_message("ai" if content.role == "model" else "user"):
            st.markdown(content.parts[0].text)

    # 사용자 질문 처리
    if prompt := st.chat_input("금식, 당뇨약에 대해 질문하세요 (예: 언제부터 금식인가요? 제가 먹는 당뇨약도 끊어야 하나요?):"):
        st.session_state["chat_input"] = prompt

    # FAQ 버튼이나 입력창에서 받은 질문 처리
    if "chat_input" in st.session_state and st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(st.session_state["chat_input"])
        with st.chat_message("ai"):
            response = st.session_state.chat_session.send_message(st.session_state["chat_input"])
            st.markdown(response.text)
        # 질문 처리 후 초기화
        st.session_state["chat_input"] = ""
