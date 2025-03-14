import streamlit as st
import os
import io
from gtts import gTTS
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(
    page_title="서울아산병원 챗봇",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS 스타일링
st.markdown("""
    <style>
        .chat-container { max-width: 100%; margin: 0 auto; padding: 10px; border: 1px solid #e0e0e0; border-radius: 5px; background-color: #f9f9f9; height: 90vh; display: flex; flex-direction: column; }
        .chat-header { display: flex; justify-content: space-between; align-items: center; padding: 10px; background-color: #005566; color: white; border-radius: 5px 5px 0 0; }
        .chat-header h3 { margin: 0; font-size: 18px; }
        .chat-body { flex: 1; overflow-y: auto; padding: 10px; background-color: #fff; }
        .chat-box h4 { font-size: 16px; color: #333; margin-bottom: 10px; }
        .bot-message { background-color: #f1f1f1; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .chat-footer { padding: 10px; background-color: #f9f9f9; border-top: 1px solid #e0e0e0; }
        .user-input input { width: 100%; padding: 8px; font-size: 14px; border: 1px solid #ccc; border-radius: 5px; }
        @media (max-width: 768px) { .chat-container { padding: 5px; height: 95vh; } .chat-header h3 { font-size: 16px; } .chat-box h4 { font-size: 14px; } .bot-message { font-size: 14px; } }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {"role": "bot", "content": "안녕하세요? 서울아산병원 챗봇입니다.<br>문의 사항은 아래 카테고리를 선택하시거나, 키워드를 입력해 주세요."},
        {"role": "bot", "content": "<div class='bot-message'><div class='ment'><p>공지사항</p><div class='disease_wrap'><div class='title'>마스크를 착용해 주세요.</div><div class='info'><dl>인플루엔자 유행 시기입니다. 병원 내에서는 마스크를 착용해 주시기 바랍니다.</dl></div></div></div></div>"}
    ]
if "show_lnb" not in st.session_state:
    st.session_state["show_lnb"] = False

# LNB 토글 함수
def toggle_lnb():
    st.session_state["show_lnb"] = not st.session_state["show_lnb"]

# 채팅 컨테이너 시작
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# 헤더
with st.container():
    st.markdown("""
        <div class="chat-header">
            <div id="lnb_menu"><a href="#"><img src="https://via.placeholder.com/24" alt="LNB-OPEN"></a></div>
            <h3>서울아산병원 챗봇</h3>
            <div class="loghome"><a href="#"><img src="https://via.placeholder.com/24" alt="home"></a></div>
        </div>
    """, unsafe_allow_html=True)
    # LNB 열기 버튼 (on_click 사용)
    st.button("LNB 열기", key="show_lnb", help="메뉴 열기", type="primary", on_click=toggle_lnb)

# LNB 메뉴 (사이드바)
if st.session_state["show_lnb"]:
    with st.sidebar:
        st.markdown('<div class="allSearchWrap window">', unsafe_allow_html=True)
        st.markdown('<div class="lnb_close"><a href="#"><img src="https://via.placeholder.com/24" alt="LNB-CLOSE"></a></div>', unsafe_allow_html=True)
        st.markdown('<p class="txt">아래 키워드를 누르시면 키워드 메인 화면으로 이동합니다.</p>', unsafe_allow_html=True)
        
        categories = {
            "진료/검사": ["진료예약", "진료변경/취소", "검사예약/변경/취소", "내원", "진료관련", "약제"],
            "원무": ["수납", "입원/퇴원", "기타 문의"],
            "발급안내": ["증명서", "증명서 (홈페이지)", "의무기록", "동의서/위임장", "기타"],
            "병원이용 안내": ["오시는길", "주차", "편의시설", "전화번호안내", "출입", "칭찬코너", "고객의소리", "기타"],
            "홈페이지 이용": ["회원", "진료예약", "본인인증", "나의차트", "고객서비스"],
            "암병원": ["진료/검사", "암병원 소개"],
            "건강검진": ["문진 작성", "예약 관련", "검사 관련", "결과 관련", "기타"],
            "서울아산병원 앱": ["앱 관련", "회원서비스", "진료예약/취소", "앱 메뉴"]
        }
        
        for category, subcategories in categories.items():
            with st.expander(category, expanded=False):
                for subcategory in subcategories:
                    if st.button(subcategory, key=f"lnb_{subcategory}"):
                        st.session_state["chat_history"].append({"role": "user", "content": subcategory})
                        st.session_state["chat_history"].append({"role": "bot", "content": f"{subcategory}에 대한 정보를 준비 중입니다."})
                        st.session_state["show_lnb"] = False
        st.markdown('</div>', unsafe_allow_html=True)
        st.button("LNB 닫기", key="hide_lnb", on_click=toggle_lnb)

# 채팅 본문
with st.container():
    st.markdown('<div class="chat-body"><div class="chat-box" id="chatBox"><h4>무엇을 도와드릴까요?</h4><div id="notinoti">', unsafe_allow_html=True)
    for message in st.session_state["chat_history"]:
        if message["role"] == "bot":
            st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div>{message["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div></div></div>', unsafe_allow_html=True)

# 푸터
with st.container():
    st.markdown('<div class="chat-footer"><div class="user-input">', unsafe_allow_html=True)
    user_input = st.text_input("키워드 입력 후 자동 완성 목록에서 선택해 주세요.", max_chars=30, key="user_input")
    if user_input:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        st.session_state["chat_history"].append({"role": "bot", "content": f"'{user_input}'에 대한 답변을 준비 중입니다."})
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 스크롤 맨 아래로
st.markdown("""
    <script>
        var chatBox = document.getElementById("chatBox");
        chatBox.scrollTop = chatBox.scrollHeight;
    </script>
""", unsafe_allow_html=True)
