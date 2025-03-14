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

# 사이드바 메뉴 (이미지 로드 오류 처리 추가)
st.sidebar.subheader("메뉴")
try:
    logo_path = "path_to_logo.png"  # 실제 로고 파일 경로로 변경
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)  # use_column_width 대신 use_container_width 사용
    else:
        st.sidebar.warning("로고 이미지를 찾을 수 없습니다. 파일 경로를 확인하세요.")
except Exception as e:
    st.sidebar.error(f"이미지 로드 중 오류 발생: {str(e)}")

menu_options = ["검사날짜 찾기", "언론날짜 찾기", "자궁 문진표", "상담 전화내역", "문의하기"]
selected_menu = st.sidebar.radio("", menu_options)

# 제목 다국어 처리
titles = {
    "한국어": "소아청소년 상담 챗봇 서비스",
    "English": "Pediatric Counseling Chatbot Service",
    "日本語": "小児青少年相談チャットボットサービス",
    "中文 (简体)": "儿科咨询聊天机器人服务",
    "Español": "Servicio de Chatbot de Consejería Pediátrica"
}
st.title(titles[selected_language])

# 챗봇 버튼 (파란색 스타일)
if st.button("소아청소년 상담 챗봇 서비스" if selected_language == "한국어" else "Pediatric Counseling Chatbot Service", 
             key="chatbot_button", 
             help="운영 발신키 플랫폼에 탑재된 답변으로", 
             use_container_width=True, 
             type="primary"):
    st.session_state["chat_input"] = "start"

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
    initial_messages = {
        "한국어": "안녕하세요! 아이와 관련된 고민이 있으시다면 편하게 이야기해주세요.",
        "English": "Hello! If you have any concerns about your child, feel free to talk.",
        "日本語": "こんにちは！お子様に関する悩みがあれば気軽にお話しください。",
        "中文 (简体)": "你好！如果有关于孩子的烦恼，请随时告诉我。",
        "Español": "¡Hola! Si tienes alguna preocupación sobre tu hijo, no dudes en hablar."
    }
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": initial_messages[selected_language]}]}
    ])

# 대화 창
for content in st.session_state.chat_session.history[2:]:
    with st.chat_message("ai" if content.role == "model" else "user"):
        st.markdown(content.parts[0].text)

# 경고 메시지 (주황색 배경)
st.warning("아이 부모님이 직접 문의하셔야 합니다. 아이 본인은 건강 상담을 통해 예약이 많습니다.")

# 입력 창
if prompt := st.chat_input("대화를 종료하시겠습니까?" if selected_language == "한국어" else "Would you like to end the conversation?"):
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
        st.error("음성 기능(gTTS)이 설치되지 않았습니다. 관리자에게 문의하세요." if selected_language == "한국어" else "Voice function (gTTS) is not installed. Contact the administrator.")
    except Exception as e:
        st.error(f"음성 변환 중 오류 발생: {str(e)}" if selected_language == "한국어" else f"Error during voice conversion: {str(e)}")
