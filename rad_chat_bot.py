import google.generativeai as genai
import streamlit as st
import os
import io
import json
from gtts import gTTS
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(
    page_title="영상의학과 안내 챗봇",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS로 서울아산병원 스타일 적용
st.markdown(
    """
    <style>
        /* 전체 컨테이너 스타일 */
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            height: 80vh;
            display: flex;
            flex-direction: column;
            background-color: #fff;
        }
        /* 헤더 스타일 */
        .chat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            background-color: #f5f5f5;
            border-bottom: 1px solid #e0e0e0;
        }
        .chat-header h3 {
            margin: 0;
            font-size: 18px;
            font-weight: bold;
        }
        /* 채팅창 스타일 */
        .chat-body {
            flex-grow: 1;
            overflow-y: auto;
            padding: 20px;
            background-color: #fafafa;
        }
        .chat-box h4 {
            font-size: 16px;
            color: #666;
            margin-bottom: 20px;
        }
        .stChatMessage {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 5px;
            background-color: #fff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        /* 입력창 스타일 */
        .chat-footer {
            padding: 10px 20px;
            border-top: 1px solid #e0e0e0;
            background-color: #fff;
        }
        .stTextInput > div > input {
            width: 100%;
            padding: 10px;
            font-size: 14px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        /* 모바일 반응형 */
        @media (max-width: 768px) {
            .chat-container {
                height: 100vh;
                border: none;
            }
            .chat-header {
                padding: 10px;
            }
            .chat-header h3 {
                font-size: 16px;
            }
            .stButton > button {
                padding: 8px;
                font-size: 14px;
            }
            .stChatMessage {
                font-size: 14px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)

# API 키 설정
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("API 키가 설정되지 않았습니다. 관리자에게 문의하세요.")
    st.stop()
genai.configure(api_key=api_key)

# 언어 옵션
language_options = {
    "한국어": "ko",
    "English": "en",
    "日本語": "ja",
    "中文 (简体)": "zh-CN",
    "Español": "es"
}
selected_language = st.selectbox("Select your language", list(language_options.keys()), index=0, key="language_select")
lang_code = language_options[selected_language]

# 제목 다국어 처리
titles = {
    "한국어": "영상의학과 챗봇",
    "English": "Radiology Chatbot",
    "日本語": "放射線科チャットボット",
    "中文 (简体)": "放射科聊天机器人",
    "Español": "Chatbot de Radiología"
}

# 파일 로드 함수
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

system_prompt = system_prompt_template.format(
    inspection_guidelines=inspection_guidelines,
    metformin_drugs=', '.join(metformin_drugs)
)

# 모델 로드
@st.cache_resource
def load_model():
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model

model = load_model()

# 초기 메시지
initial_messages = {
    "한국어": "안녕하세요? 영상의학과 챗봇입니다.<br>문의 사항은 아래 카테고리를 선택하시거나, 키워드를 입력해 주세요.",
    "English": "Hello? This is the Radiology Chatbot.<br>Please select a category below or enter a keyword.",
    "日本語": "こんにちは、放射線科チャットボットです。<br>お問い合わせは以下のカテゴリを選択するか、キーワードを入力してください。",
    "中文 (简体)": "您好？这里是放射科聊天机器人。<br>请在下方选择类别或输入关键词。",
    "Español": "¿Hola? Este es el Chatbot de Radiología.<br>Seleccione una categoría a continuación o ingrese una palabra clave."
}

seasonal_notice = {
    "한국어": "2025년 3월에는 독감과 알레르기에 유의하세요. 손씻기와 마스크 착용을 권장합니다.",
    "English": "In March 2025, please be cautious of flu and allergies. Hand washing and mask-wearing are recommended.",
    "日本語": "2025年3月はインフルエンザとアレルギーに注意してください。手洗いとマスク着用を推奨します。",
    "中文 (简体)": "2025年3月请注意流感和过敏症。建议勤洗手并佩戴口罩。",
    "Español": "En marzo de 2025, tenga cuidado con la gripe y las alergias. Se recomienda lavarse las manos y usar mascarilla."
}

# 세션 초기화
if "chat_session" not in st.session_state:
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": initial_messages[selected_language]}]},
        {"role": "model", "parts": [{"text": seasonal_notice[selected_language]}]}
    ])

# 챗봇 UI
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# 헤더
st.markdown('<div class="chat-header">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 8, 1])
with col1:
    if st.button("☰", key="menu_button"):
        st.session_state["show_sidebar"] = not st.session_state["show_sidebar"]
with col2:
    st.markdown(f'<h3>{titles[selected_language]}</h3>', unsafe_allow_html=True)
with col3:
    if st.button("🏠", key="reset_button"):
        st.session_state["chat_session"] = model.start_chat(history=[
            {"role": "user", "parts": [{"text": system_prompt}]},
            {"role": "model", "parts": [{"text": initial_messages[selected_language]}]},
            {"role": "model", "parts": [{"text": seasonal_notice[selected_language]}]}
        ])
        st.session_state.pop("chat_input", None)
        st.success("대화가 리셋되었습니다." if selected_language == "한국어" else "Chat has been reset.")
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 사이드바 (LNB)
if "show_sidebar" not in st.session_state:
    st.session_state["show_sidebar"] = False

if st.session_state["show_sidebar"]:
    with st.sidebar:
        st.header(titles[selected_language])
        st.markdown("아래 카테고리를 누르시면 관련 정보를 볼 수 있습니다.")
        with st.expander("검사 안내", expanded=True):
            for btn in ["초음파", "MRI", "CT", "금식", "당뇨약"]:
                if st.button(btn, key=f"faq_{btn}"):
                    st.session_state["chat_input"] = btn

# 채팅창
st.markdown('<div class="chat-body"><div class="chat-box"><h4>무엇을 도와드릴까요?</h4>', unsafe_allow_html=True)
for content in st.session_state.chat_session.history[2:]:
    with st.chat_message("ai" if content.role == "model" else "user"):
        st.markdown(content.parts[0].text, unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

# 입력창
st.markdown('<div class="chat-footer">', unsafe_allow_html=True)
if prompt := st.chat_input("키워드를 입력해 주세요" if selected_language == "한국어" else "Enter a keyword"):
    st.session_state["chat_input"] = prompt

if "chat_input" in st.session_state and st.session_state["chat_input"]:
    with st.chat_message("user"):
        st.markdown(st.session_state["chat_input"])
    with st.chat_message("ai"):
        st.session_state["response"] = st.session_state.chat_session.send_message(st.session_state["chat_input"])
        st.markdown(st.session_state["response"].text, unsafe_allow_html=True)

# 음성 버튼
if st.button("음성으로 듣기" if selected_language == "한국어" else "Listen to Voice", key="audio_button"):
    try:
        tts = gTTS(text=st.session_state["response"].text, lang=lang_code)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        st.audio(audio_buffer, format="audio/mp3")
    except Exception as e:
        st.error(f"음성 변환 중 오류 발생: {str(e)}" if selected_language == "한국어" else f"Error during voice conversion: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)
