import google.generativeai as genai
import streamlit as st
import os
import io
import json
import base64
from gtts import gTTS

# kangdong_logo.svg를 base64로 변환
with open("kangdong_logo.svg", "rb") as svg_file:
    encoded_string = base64.b64encode(svg_file.read()).decode()
    base64_svg = f"data:image/svg+xml;base64,{encoded_string}"

# CSS 스타일 (워터마크를 별도 div로 처리)
st.markdown(f"""
<style>
/* 워터마크를 위한 div 스타일 */
.watermark {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url("{base64_svg}");
    background-size: 50%;          /* 초기 크기, 화면의 50%에서 시작 */
    background-repeat: no-repeat;
    background-position: center;   /* 가운데 정렬 */
    opacity: 0.2;                  /* 워터마크만 투명 */
    z-index: -1;                   /* 콘텐츠 뒤로 배치 */
    pointer-events: none;          /* 클릭 방지 */
}}
.chat-text {{
    font-size: 18px !important;
}}
.title-text {{
    font-size: 24px !important;
}}
</style>
<!-- 워터마크 div 추가 -->
<div class="watermark"></div>
""", unsafe_allow_html=True)

# API 키 설정
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
    st.stop()
genai.configure(api_key=api_key)

st.markdown('<p class="title-text">영상의학과 안내 챗봇 (개인정보는 넣지 마세요)</p>', unsafe_allow_html=True)

# 파일 읽기 함수
def load_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

inspection_guidelines = load_text_file("data/inspection_guidelines.txt")
metformin_drugs = load_json_file("data/metformin_drugs.json")
faq_questions = load_json_file("data/faq_questions.json")
system_prompt_template = load_text_file("data/system_prompt.txt")
system_prompt = system_prompt_template.format(
    inspection_guidelines=inspection_guidelines,
    metformin_drugs=', '.join(metformin_drugs)
)

@st.cache_resource
def load_model():
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

model = load_model()

if "chat_session" not in st.session_state:
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": "무엇이든물어보세요"}]}
    ])

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
            st.markdown(f'<p class="chat-text">{content.parts[0].text}</p>', unsafe_allow_html=True)

    if prompt := st.chat_input("무엇이든 물어보세요."):
        st.session_state["chat_input"] = prompt

    if "chat_input" in st.session_state and st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(f'<p class="chat-text">{st.session_state["chat_input"]}</p>', unsafe_allow_html=True)
        with st.chat_message("ai"):
            st.session_state["response"] = st.session_state.chat_session.send_message(st.session_state["chat_input"])
            st.markdown(f'<p class="chat-text">{st.session_state["response"].text}</p>', unsafe_allow_html=True)

if st.button("음성으로 듣기", key="audio_button"):
    try:
        tts = gTTS(text=st.session_state["response"].text, lang='ko')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        st.audio(audio_buffer, format="audio/mp3")
    except Exception as e:
        st.error(f"음성 변환 중 오류 발생: {str(e)}")
