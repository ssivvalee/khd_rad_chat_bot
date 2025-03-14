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

# 언어 옵션 설정
language_options = {
    "한국어": "ko",
    "English": "en",
    "日本語": "ja",
    "中文 (简体)": "zh-CN",
    "Español": "es"
}
selected_language = st.sidebar.selectbox("언어를 선택하세요", list(language_options.keys()), index=0)
lang_code = language_options[selected_language]

# 제목 다국어 처리
titles = {
    "한국어": "영상의학과 안내 챗봇 (개인정보 넣지 마세요)",
    "English": "Radiology Guidance Chatbot (Do Not Enter Personal Information)",
    "日本語": "放射線科案内チャットボット（個人情報は入力しないでください）",
    "中文 (简体)": "放射科指导聊天机器人（请勿输入个人信息）",
    "Español": "Chatbot de Guía de Radiología (No Ingrese Información Personal)"
}
st.title(titles[selected_language])

# 파일 읽기 함수
def load_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 데이터 로드 (언어별 파일을 준비할 경우 파일 경로를 동적으로 변경 가능)
inspection_guidelines = load_text_file("data/inspection_guidelines.txt")  # 언어별 파일 추가 가능
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

# 세션 초기화 (언어에 따라 초기 메시지 변경 가능)
if "chat_session" not in st.session_state:
    initial_messages = {
        "한국어": "알겠습니다! 검사 유형(초음파, MRI, CT)을 말씀해 주세요. 금식이나 당뇨약에 대해 궁금하면 물어보세요.",
        "English": "Understood! Please tell me the type of examination (ultrasound, MRI, CT). Feel free to ask about fasting or diabetes medication.",
        "日本語": "了解しました！検査の種類（超音波、MRI、CT）を教えてください。絶食や糖尿病薬について質問があればどうぞ。",
        "中文 (简体)": "明白了！请告诉我检查类型（超声波、MRI、CT）。如果对禁食或糖尿病药物有疑问，请随时问我。",
        "Español": "¡Entendido! Por favor, dime el tipo de examen (ultrasonido, MRI, CT). Si tienes preguntas sobre ayuno o medicamentos para la diabetes, no dudes en preguntar."
    }
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": initial_messages[selected_language]}]}
    ])

# 화면 레이아웃
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("자주 묻는 질문 (1)" if selected_language == "한국어" else "Frequently Asked Questions (1)")
    for i in range(0, len(faq_questions)//2):
        if st.button(faq_questions[i], key=f"faq_left_{i}"):
            st.session_state["chat_input"] = faq_questions[i]

with col3:
    st.subheader("자주 묻는 질문 (2)" if selected_language == "한국어" else "Frequently Asked Questions (2)")
    for i in range(len(faq_questions)//2, len(faq_questions)):
        if st.button(faq_questions[i], key=f"faq_right_{i}"):
            st.session_state["chat_input"] = faq_questions[i]

with col2:
    for content in st.session_state.chat_session.history[2:]:
        with st.chat_message("ai" if content.role == "model" else "user"):
            st.markdown(content.parts[0].text)

    if prompt := st.chat_input("무엇이든 물어보세요" if selected_language == "한국어" else "Ask anything"):
        st.session_state["chat_input"] = prompt

    if "chat_input" in st.session_state and st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(st.session_state["chat_input"])
        with st.chat_message("ai"):
            st.session_state["response"] = st.session_state.chat_session.send_message(st.session_state["chat_input"])
            st.markdown(st.session_state["response"].text)

# 음성 버튼
if st.button("음성으로 듣기" if selected_language == "한국어" else "Listen to Voice", key="audio_button"):
    try:
        tts = gTTS(text=st.session_state["response"].text, lang=lang_code)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        st.audio(audio_buffer, format="audio/mp3")
    except ImportError:
        st.error("음성 기능(gTTS)이 설치되지 않았습니다. 관리자에게 문의하세요。" if selected_language == "한국어" else "Voice function (gTTS) is not installed. Contact the administrator.")
    except Exception as e:
        st.error(f"음성 변환 중 오류 발생: {str(e)}" if selected_language == "한국어" else f"Error during voice conversion: {str(e)}")
