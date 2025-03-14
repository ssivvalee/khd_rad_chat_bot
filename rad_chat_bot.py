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

# 사이드바 (항상 노출되도록 설정)
st.sidebar.subheader("언급 언급하세요" if selected_language == "한국어" else "Mention Mention")
st.sidebar.markdown("로고 이미지를 축소할 수 없습니다." if selected_language == "한국어" else "Cannot shrink logo image.")
menu_options = ["검사날짜 찾기", "언론날짜 찾기", "자궁 문진표", "상담 전화내역", "문의하기"]
selected_menu = st.sidebar.radio("", menu_options)

# 제목 다국어 처리
titles = {
    "한국어": "영상의학과 안내 챗봇 서비스",
    "English": "Radiology Guidance Chatbot Service",
    "日本語": "放射線科案内チャットボットサービス",
    "中文 (简体)": "放射科指导聊天机器人服务",
    "Español": "Servicio de Chatbot de Guía de Radiología"
}
st.title(titles[selected_language])

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
        "한국어": "안녕하세요! 검사 유형(초음파, MRI, CT)을 말씀해 주세요. 금식이나 당뇨약에 대해 궁금하면 물어보세요.",
        "English": "Hello! Please tell me the type of examination (ultrasound, MRI, CT). Feel free to ask about fasting or diabetes medication.",
        "日本語": "こんにちは！検査の種類（超音波、MRI、CT）を教えてください。絶食や糖尿病薬について質問があればどうぞ。",
        "中文 (简体)": "你好！请告诉我检查类型（超声波、MRI、CT）。如果对禁食或糖尿病药物有疑问，请随时问我。",
        "Español": "¡Hola! Por favor, dime el tipo de examen (ultrasonido, MRI, CT). Si tienes preguntas sobre ayuno o medicamentos para la diabetes, no dudes en preguntar."
    }
    st.session_state["chat_session"] = model.start_chat(history=[
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": initial_messages[selected_language]}]}
    ])

# FAQ 섹션 (이미지 스타일 반영)
faq_data = [
    {
        "question": "CT 검사의 금식 시간 조정과 사전 예약 여부에 대해 알려주세요.",
        "answer": "조영제를 사용하는 CT 검사의 경우, 6시간 금식이 필요합니다. 조영제를 사용하지 않는 검사라면 금식이 필요 없을 수도 있습니다. 가정 정확한 정보는 노관석 검사 안내자 스티커를 확인하세요. 만약 입원이나 스티커를 찾을 수 없다면 예약한 의학에서 확인하는 것을 추천합니다."
    },
    {
        "question": "써야 금식은 몇시?",
        "answer": "써야 금식은 몇시? (질문을 클릭하면 답변을 확인할 수 있습니다.)"
    },
    {
        "question": "CT 검사의 금식 시간 조정과 사전 예약 여부에 대해 알려주세요.",
        "answer": "조영제를 사용하는 CT 검사의 경우, 6시간 금식이 필요합니다. 조영제를 사용하지 않는 검사라면 금식이 필요 없을 수도 있습니다. 가정 정확한 정보는 노관석 검사 안내자 스티커를 확인하세요. 만약 입원이나 스티커를 찾을 수 없다면 예약한 의학에서 확인하는 것을 추천합니다."
    }
]

for i, faq in enumerate(faq_data):
    with st.expander(faq["question"], expanded=False):
        st.markdown(faq["answer"])
        # 써야 금식은 몇시? 버튼 (이미지와 동일한 스타일)
        if st.button("써야 금식은 몇시?" if selected_language == "한국어" else "What time is fasting required?", key=f"faq_button_{i}"):
            st.session_state["chat_input"] = faq["question"]

# 경고 메시지 (노란색 배경)
st.warning("환자 본인이 직접 문의하셔야 합니다. 건강 상담은 의료진과 상의하세요.")

# 대화 창
for content in st.session_state.chat_session.history[2:]:
    with st.chat_message("ai" if content.role == "model" else "user"):
        st.markdown(content.parts[0].text)

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
