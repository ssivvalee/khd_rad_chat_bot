import google.generativeai as genai
import streamlit as st
import os
import io
import json
from gtts import gTTS
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(
    page_title="영상의학과 안내 챗봇",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 모바일 및 기본 스타일 (가시성 개선 포함)
st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        @media (max-width: 768px) {
            .stApp { max-width: 100%; margin: 0; padding: 10px; }
            .stButton>button { width: 100%; padding: 10px; font-size: 16px; margin-bottom: 10px; }
            .stChatMessage { font-size: 16px; padding: 10px; }
            .stTextInput>div>input { font-size: 16px; padding: 10px; }
            [data-testid="stSidebar"] { width: 80% !important; padding: 10px; }
            .stExpander { margin-bottom: 10px; }
        }
        .chat-header { background: #f5f5f5; padding: 10px; text-align: center; font-size: 18px; }
        .chat-body { max-height: 400px; overflow-y: auto; padding: 10px; }
        .bot-message { background: #e9ecef; padding: 8px; margin: 5px 0; border-radius: 5px; }
        /* 메뉴 버튼 스타일 개선 */
        .menu-button button {
            background-color: #007bff;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 8px 16px;
            font-size: 16px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .menu-button button:hover {
            background-color: #0056b3;
        }
        /* 사이드바 열림 상태에서 화살표 숨기기 */
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# API 키 설정
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("API 키가 설정되지 않았습니다.")
    st.stop()
genai.configure(api_key=api_key)

# 언어 설정
language_options = {"한국어": "ko", "English": "en", "日本語": "ja", "中文 (简体)": "zh-CN", "Español": "es"}
selected_language = st.selectbox("언어 선택", list(language_options.keys()), index=0, key="language_select")
lang_code = language_options[selected_language]

# 다국어 제목 ("서울아산병원"을 "영상의학과"로 대체)
titles = {
    "한국어": "영상의학과 챗봇",
    "English": "Radiology Chatbot",
    "日本語": "放射線科チャットボット",
    "中文 (简体)": "放射科聊天机器人",
    "Español": "Chatbot de Radiología"
}

# 데이터 로드 (예시 파일 가정)
def load_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ""

inspection_guidelines = load_text_file("data/inspection_guidelines.txt")
# 시스템 프롬프트에서 "서울아산병원"을 "영상의학과"로 대체
system_prompt = f"당신은 영상의학과 챗봇입니다. 다음 가이드라인을 참고하세요:\n{inspection_guidelines}"

# 모델 로드
@st.cache_resource
def load_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = load_model()

# 초기 메시지 ("서울아산병원"을 "영상의학과"로 대체)
initial_messages = {
    "한국어": "안녕하세요? 영상의학과 챗봇입니다. 검사 유형(초음파, MRI, CT)을 말씀해 주세요.",
    "English": "Hello! This is the Radiology Chatbot. Please specify the exam type (ultrasound, MRI, CT).",
    "日本語": "こんにちは！放射線科チャットボットです。検査の種類（超音波、MRI、CT）を教えてください。",
    "中文 (简体)": "您好！我是放射科聊天机器人。请告诉我检查类型（超声波、MRI、CT）。",
    "Español": "¡Hola! Soy el chatbot de radiología. Por favor, dime el tipo de examen (ultrasonido, MRI, CT)."
}

notices = [
    {"title": "마스크 착용", "content": "병원 내에서는 마스크를 착용해 주세요.", "lang": "한국어"},
    {"title": "Mask Wearing", "content": "Please wear a mask in the hospital.", "lang": "English"}
]

# 세션 초기화
if "chat_session" not in st.session_state:
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": initial_messages[selected_language]}]},
        {"role": "model", "parts": [{"text": next(n["content"] for n in notices if n["lang"] == selected_language)}]}
    ])
if "last_activity" not in st.session_state:
    st.session_state["last_activity"] = datetime.now()
if "show_sidebar" not in st.session_state:
    st.session_state["show_sidebar"] = False

# 세션 타임아웃 (10분)
def check_session_timeout():
    if datetime.now() - st.session_state["last_activity"] > timedelta(minutes=10):
        st.session_state["chat_session"] = model.start_chat(history=[
            {"role": "user", "parts": [{"text": system_prompt}]},
            {"role": "model", "parts": [{"text": initial_messages[selected_language] + " (세션이 만료되어 재시작되었습니다.)"}]}
        ])
        st.warning("10분 동안 활동이 없어 세션이 재설정되었습니다.")

# 헤더
col1, col2, col3 = st.columns([1, 8, 1])
with col1:
    # 메뉴 버튼
    menu_label = "메뉴" if selected_language == "한국어" else "Menu"
    if st.button(menu_label, key="menu_button"):
        st.session_state["show_sidebar"] = True
        # JavaScript를 사용해 사이드바 강제 열기
        components.html(
            """
            <script>
                // Streamlit의 기본 사이드바 토글 버튼을 찾아 클릭
                const sidebarToggle = document.querySelector('[data-testid="stSidebarCollapsedControl"]');
                if (sidebarToggle) {
                    sidebarToggle.click();
                }
            </script>
            """,
            height=0
        )
with col2:
    st.markdown(f"<div class='chat-header'>{titles[selected_language]}</div>", unsafe_allow_html=True)
with col3:
    reset_label = "리셋" if selected_language == "한국어" else "Reset"
    if st.button(reset_label, key="reset_button"):
        st.session_state["chat_session"] = model.start_chat(history=[
            {"role": "user", "parts": [{"text": system_prompt}]},
            {"role": "model", "parts": [{"text": initial_messages[selected_language]}]},
            {"role": "model", "parts": [{"text": next(n["content"] for n in notices if n["lang"] == selected_language)}]}
        ])
        st.session_state["show_sidebar"] = False
        st.success("대화가 리셋되었습니다.")
        st.rerun()

# 사이드바 (즉시 표시)
if st.session_state["show_sidebar"]:
    with st.sidebar:
        st.header("카테고리")
        categories = {
            "진료/검사": ["진료예약", "검사예약/변경/취소", "내원"],
            "원무": ["수납", "입원/퇴원"],
            "발급안내": ["증명서", "의무기록"],
            "병원이용 안내": ["오시는길", "주차", "편의시설"]
        }
        for category, items in categories.items():
            with st.expander(category, expanded=True):
                for item in items:
                    if st.button(item, key=f"cat_{item}"):
                        st.session_state["chat_input"] = item

# 채팅 창
st.markdown("<div class='chat-body'>", unsafe_allow_html=True)
for content in st.session_state.chat_session.history[2:]:
    role = "ai" if content.role == "model" else "user"
    with st.chat_message(role):
        st.markdown(f"<div class='bot-message'>{content.parts[0].text}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# 입력창
if prompt := st.chat_input("키워드를 입력하세요"):
    prompt = ''.join(c for c in prompt if c.isalnum() or c.isspace())
    st.session_state["chat_input"] = prompt
    st.session_state["last_activity"] = datetime.now()

if "chat_input" in st.session_state and st.session_state["chat_input"]:
    check_session_timeout()
    with st.chat_message("user"):
        st.markdown(st.session_state["chat_input"])
    with st.chat_message("ai"):
        response = st.session_state.chat_session.send_message(st.session_state["chat_input"])
        st.markdown(f"<div class='bot-message'>{response.text}</div>", unsafe_allow_html=True)
        st.session_state["response"] = response

# 음성 출력
if st.button("음성으로 듣기", key="audio_button") and "response" in st.session_state:
    tts = gTTS(text=st.session_state["response"].text, lang=lang_code)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    st.audio(audio_buffer, format="audio/mp3")
