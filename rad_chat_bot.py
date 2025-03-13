import google.generativeai as genai
import streamlit as st
import os
import io
import json
from gtts import gTTS

# API 키 설정
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
    st.stop()
genai.configure(api_key=api_key)

st.title("영상의학과 검사 안내 챗봇 (개인정보 미포함)")

# 파일 읽기 함수
def load_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 데이터 로드
inspection_guidelines = load_text_file("data/inspection_guidelines.txt")
metformin_drugs = load_json_file("data/metformin_drugs.json")
faq_questions = load_json_file("data/faq_questions.json")
system_prompt_template = load_text_file("data/system_prompt.txt")

# system_prompt에 데이터 삽입
system_prompt = system_prompt_template.format(
    inspection_guidelines=inspection_guidelines,
    metformin_drugs=', '.join(metformin_drugs)
)

@st.cache_resource
def load_model():
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("model loaded...")
    return model

model = load_model()

# 세션 초기화
if "chat_session" not in st.session_state:
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": "알겠습니다! 검사 유형(초음파, MRI, CT)을 말씀해 주세요. 금식이나 당뇨약에 대해 궁금하면 물어보세요."}]}
    ])

# 화면 레이아웃 (FAQ 및 대화 부분은 그대로 유지)
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
    for content in st.session_state.chat_session.history[2:]:
        with st.chat_message("ai" if content.role == "model" else "user"):
            st.markdown(content.parts[0].text)

    if prompt := st.chat_input("검사 유형(초음파, MRI, CT)을 말씀해 주세요. 금식이나 당뇨약 질문도 가능합니다:"):
        st.session_state["chat_input"] = prompt

    if "chat_input" in st.session_state and st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(st.session_state["chat_input"])
        with st.chat_message("ai"):
            st.session_state["response"] = st.session_state.chat_session.send_message(st.session_state["chat_input"])
            st.markdown(st.session_state["response"].text)

if st.button("음성으로 듣기", key="audio_button"):
    try:
        tts = gTTS(text=st.session_state["response"].text, lang='ko')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        st.audio(audio_buffer, format="audio/mp3")
    except ImportError:
        st.error("음성 기능(gTTS)이 설치되지 않았습니다. 관리자에게 문의하세요.")
    except Exception as e:
        st.error(f"음성 변환 중 오류 발생: {str(e)}")
