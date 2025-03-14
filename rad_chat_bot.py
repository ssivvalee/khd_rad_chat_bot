import google.generativeai as genai
import streamlit as st
import os
import io
import json
from gtts import gTTS

# 모바일 뷰포트 설정 (HTML 헤더에 추가)
st.set_page_config(
    page_title="영상의학과 안내 챗봇",
    layout="centered",
    initial_sidebar_state="collapsed"
)
st.markdown(
    """
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        /* 모바일 최적화 CSS */
        @media (max-width: 768px) {
            .stApp {
                max-width: 100%;
                margin: 0;
                padding: 10px;
            }
            .stButton>button {
                width: 100%;
                padding: 10px;
                font-size: 16px;
                margin-bottom: 10px;
            }
            .stChatMessage {
                font-size: 16px;
                padding: 10px;
            }
            .stTextInput>div>input {
                font-size: 16px;
                padding: 10px;
            }
            [data-testid="stSidebar"] {
                width: 80% !important;
                padding: 10px;
            }
            .stExpander {
                margin-bottom: 10px;
            }
            .stExpander > div > div {
                padding: 10px;
            }
        }
        /* 데스크톱에서도 기본 스타일 유지 */
        .stButton>button {
            padding: 8px;
            font-size: 14px;
        }
        .stChatMessage {
            font-size: 14px;
            padding: 8px;
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

# 언어 옵션 설정
language_options = {
    "한국어": "ko",
    "English": "en",
    "日本語": "ja",
    "中文 (简体)": "zh-CN",
    "Español": "es"
}
selected_language = st.selectbox("언어를 선택하세요", list(language_options.keys()), index=0, key="language_select")
lang_code = language_options[selected_language]

# 제목 다국어 처리
titles = {
    "한국어": "영상의학과 안내 챗봇 (개인정보 넣지 마세요)",
    "English": "Radiology Guidance Chatbot (Do Not Enter Personal Information)",
    "日本語": "放射線科案内チャットボット（個人情報は入力しないでください）",
    "中文 (简体)": "放射科指导聊天机器人（请勿输入个人信息）",
    "Español": "Chatbot de Guía de Radiología (No Ingrese Información Personal)"
}

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

# 모델 로드 (가장 먼저 실행)
@st.cache_resource
def load_model():
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("model loaded...")
    return model

# 모델을 먼저 정의
model = load_model()

# 초기 메시지 및 계절별 주의 문구 정의
initial_messages = {
    "한국어": "알겠습니다! 검사 유형(초음파, MRI, CT)을 말씀해 주세요. 금식이나 당뇨약에 대해 궁금하면 물어보세요.",
    "English": "Understood! Please tell me the type of examination (ultrasound, MRI, CT). Feel free to ask about fasting or diabetes medication.",
    "日本語": "了解しました！検査の種類（超音波、MRI、CT）を教えてください。絶食や糖尿病薬について質問があればどうぞ。",
    "中文 (简体)": "明白了！请告诉我检查类型（超声波、MRI、CT）。如果对禁食或糖尿病药物有疑问，请随时问我。",
    "Español": "¡Entendido! Por favor, dime el tipo de examen (ultrasonido, MRI, CT). Si tienes preguntas sobre ayuno o medicamentos para la diabetes, no dudes en preguntar."
}

seasonal_notice = {
    "한국어": "2025년 3월에는 독감과 알레르기에 유의하세요. 손씻기와 마스크 착용을 권장합니다.",
    "English": "Notice about the most common diseases this season: In March 2025, please be cautious of flu and allergies. Hand washing and mask-wearing are recommended.",
    "日本語": "その時期に流行している病気に関する注意事項: 2025年3月はインフルエンザとアレルギーに注意してください。手洗いとマスク着用を推奨します。",
    "中文 (简体)": "关于本季最流行疾病的注意事项：2025年3月请注意流感和过敏症。建议勤洗手并佩戴口罩。",
    "Español": "Aviso sobre las enfermedades más comunes esta temporada: En marzo de 2025, tenga cuidado con la gripe y las alergias. Se recomienda lavarse las manos y usar mascarilla."
}

# 세션 초기화 (model 정의 후 실행)
if "chat_session" not in st.session_state:
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": initial_messages[selected_language]}]},
        {"role": "model", "parts": [{"text": seasonal_notice[selected_language]}]}
    ])

# 상단 레이아웃: 제목, 햄버거 메뉴, 집 모양 아이콘
col1, col2, col3 = st.columns([1, 8, 1])
with col1:
    if st.button("☰", key="menu_button"):
        st.session_state["show_sidebar"] = not st.session_state["show_sidebar"]
with col2:
    st.title(titles[selected_language])
with col3:
    if st.button("🏠", key="reset_button"):
        # 대화 리셋 로직
        st.session_state["chat_session"] = model.start_chat(history=[
            {"role": "user", "parts": [{"text": system_prompt}]},
            {"role": "model", "parts": [{"text": initial_messages[selected_language]}]},
            {"role": "model", "parts": [{"text": seasonal_notice[selected_language]}]}
        ])
        st.session_state.pop("chat_input", None)  # 입력값 초기화
        st.session_state.pop("response", None)    # 응답 초기화
        st.success("대화가 리셋되었습니다." if selected_language == "한국어" else "Chat has been reset.")
        st.rerun()  # 화면 새로고침 (experimental_rerun 대신 rerun 사용)

# 햄버거 메뉴 토글 상태 관리
if "show_sidebar" not in st.session_state:
    st.session_state["show_sidebar"] = False

# 사이드바에 FAQ 버튼 표시
if st.session_state["show_sidebar"]:
    with st.sidebar:
        st.header("서울아산병원 챗봇")
        st.markdown("아래 카테고리를 누르시면 카테고리 매뉴 한눈에 알아볼 수 있습니다.")

        # 건강검진 카테고리
        with st.expander("건강검진"):
            for btn in ["건강검사", "건강보험/검소", "검사예약/방사/검소", "내진", "진료관련"]:
                if st.button(btn, key=f"faq_{btn}"):
                    st.session_state["chat_input"] = btn

        # 업무 카테고리
        with st.expander("업무"):
            for btn in ["마스크 착용해 주세요.", "입원/퇴원", "기타 문진"]:
                if st.button(btn, key=f"faq_{btn}"):
                    st.session_state["chat_input"] = btn

        # 안내문내 카테고리
        with st.expander("안내문내"):
            for btn in ["증명서", "증명서 (출판/자격)", "의무기록", "동의서/위임장", "기타"]:
                if st.button(btn, key=f"faq_{btn}"):
                    st.session_state["chat_input"] = btn

        # 병실이용 안내 카테고리
        with st.expander("병실이용 안내"):
            for btn in ["오시는길", "주차", "편의시설", "전화번호안내", "출입", "참관코너"]:
                if st.button(btn, key=f"faq_{btn}"):
                    st.session_state["chat_input"] = btn

        # 웹페이지 이용 카테고리
        with st.expander("웹페이지 이용"):
            for btn in ["회원", "진료예약", "본인인증", "내사처비스", "고객서비스"]:
                if st.button(btn, key=f"faq_{btn}"):
                    st.session_state["chat_input"] = btn

        # 건강검사 카테고리
        with st.expander("건강검사"):
            for btn in ["영상의 소게"]:
                if st.button(btn, key=f"faq_{btn}"):
                    st.session_state["chat_input"] = btn

# 메인 화면 레이아웃
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
        st.error("음성 기능(gTTS)이 설치되지 않았습니다. 관리자에게 문의하세요." if selected_language == "한국어" else "Voice function (gTTS) is not installed. Contact the administrator.")
    except Exception as e:
        st.error(f"음성 변환 중 오류 발생: {str(e)}" if selected_language == "한국어" else f"Error during voice conversion: {str(e)}")
