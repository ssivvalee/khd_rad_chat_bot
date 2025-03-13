import google.generativeai as genai
import streamlit as st
import os
import io
from gtts import gTTS

# API 키 설정
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
    st.stop()
genai.configure(api_key=api_key)

st.title("영상의학과 검사 안내 챗봇 (개인정보 미포함)")

# 검사 관련 기본 정보
inspection_guidelines = """
- 초음파: 복부 초음파의 경우 6시간 전부터 금식하세요. 자세한 내용은 노란색 검사안내지 또는 스티커를 참고하세요.
- MRI: 금속 물체(장신구, 열쇠 등)를 제거하고 검사실에 들어가세요. 간, 췌장, 담낭 검사는 금식 6시간 필수입니다. 자세한 내용은 노란색 검사안내지 또는 스티커를 참고하세요.
- CT: 조영제 사용검사의 경우 6시간 금식, 검사 2일 전 메트포르민 성분 당뇨약 복용 중단(검사 전날, 당일, 다음날까지 3일간). 자세한 내용은 노란색 검사안내지 또는 스티커를 참고하세요.
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
    "너는 병원 검사 안내 챗봇이야. 환자가 예약된 검사에 대해 질문하면, 개인정보(이름, 등록번호 등)를 묻지 않고 일반적인 검사 유형(초음파, MRI, CT 등)에 대한 준비사항, 절차, 주의사항을 친절하게 안내해줘. "
    f"참고 정보:\n{inspection_guidelines}\n"
    "질문이 모호하면 '어떤 검사를 말씀하신 건가요? (초음파, MRI, CT 중 선택)'이라고 유도. "
    "외래 협조 요청 시 '외래에서 금식/당뇨약 안내를 병원에 문의하세요'라고 응답. "
    "스티커 연동: '노란색 검사안내지 또는 스티커를 확인하세요: 금식 6시간, 당뇨약 중단 필요' 추가. "
    "당뇨약 물음 시, 메트포르민 성분 여부 확인: {', '.join(metformin_drugs)}. 목록 외 약은 '정확한 성분은 의사나 약사에게 확인하세요'라고 답해."
)

if "chat_session" not in st.session_state:
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": "알겠습니다! 검사 유형(초음파, MRI, CT)을 말씀해 주세요. 금식이나 당뇨약에 대해 궁금하면 물어보세요."}]}
    ])

# FAQ 정의
faq_questions = [
    "초음파는 언제부터 금식하나요?",
    "MRI 준비사항이 뭐예요?",
    "CT 전에 당뇨약을 끊어야 하나요?",
    "다이아벡스는 메트포르민인가요?",
    "검사 전 물을 마셔도 되나요?"
]

# 화면 레이아웃
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("자주 묻는 질문 (1)")
    for i in range(0, len(faq_questions)//2):
        if st.button(faq_questions[i], key=f"faq_left_{i}"):
            st.session_state["chat_input"] = faq_questions[i]

with col3:
    st.subheader("자주 묻는 질문 (2)")
    for i in range(len(faq_questions)//2, len(faq_questions)):
        if st.button(faq_questions[i], key=f"faq_right_{i}"):
            st.session_state["chat_input"] = faq_questions[i]

with col2:
    # 대화 기록 출력
    for content in st.session_state.chat_session.history[2:]:
        with st.chat_message("ai" if content.role == "model" else "user"):
            st.markdown(content.parts[0].text)

    # 사용자 질문 처리
    if prompt := st.chat_input("검사 유형(초음파, MRI, CT)을 말씀해 주세요. 금식이나 당뇨약 질문도 가능합니다:"):
        st.session_state["chat_input"] = prompt

    # FAQ 버튼이나 입력창에서 받은 질문 처리
    if "chat_input" in st.session_state and st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(st.session_state["chat_input"])
        with st.chat_message("ai"):
            st.session_state["response"] = st.session_state.chat_session.send_message(st.session_state["chat_input"])
            st.markdown(st.session_state["response"].text)
            # 음성 안내 버튼
            if st.button("음성으로 듣기", key="audio_button"):
                try:
                    tts = gTTS(text=st.session_state["response"].text, lang='ko')
                    # 파일 저장 대신 메모리에서 처리
                    audio_buffer = io.BytesIO()
                    tts.write_to_fp(audio_buffer)
                    audio_buffer.seek(0)
                    st.audio(audio_buffer, format="audio/mp3")
                except ImportError:
                    st.error("음성 기능(gTTS)이 설치되지 않았습니다. 관리자에게 문의하세요.")
                except Exception as e:
                    st.error(f"음성 변환 중 오류 발생: {str(e)}")
        # 익명 피드백
        feedback = st.radio("도움이 되었나요?", ["Yes", "No"], key="feedback")
        if feedback == "No":
            st.text_input("피드백을 남겨주세요 (익명):", key="feedback_input")
        st.session_state["chat_input"] = ""
