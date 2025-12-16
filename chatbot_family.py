import streamlit as st
import google.generativeai as genai
import base64
import os

# ==========================================
# 1. 페이지 설정 & 폰트 로딩
# ==========================================
st.set_page_config(
    page_title="우리 가족 사랑방 🏠",
    page_icon="👨‍👩‍👦‍👦",
    layout="centered"
)

# [핵심] 귀여운 폰트(Jua) 웹에서 가져오기
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Jua&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# ==========================================
# 2. API 키 설정
# ==========================================
if "MY_API_KEY" in st.secrets:
    MY_API_KEY = st.secrets["MY_API_KEY"]
else:
    st.error("🚨 API 키가 없습니다! Secrets 설정을 확인해주세요.")
    st.stop()

genai.configure(api_key=MY_API_KEY)

# ==========================================
# 3. 모델 찾기 (캐싱)
# ==========================================
@st.cache_resource
def find_best_model():
    try:
        available_models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                available_models.append(m.name)
        
        preferred_order = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        for p in preferred_order:
            if p in available_models: return p
        for m in available_models:
            if "gemini" in m: return m
        return None
    except:
        return None

# ==========================================
# 4. [UI 디자인] 파스텔톤 & 귀여운 폰트 적용
# ==========================================
@st.cache_data
def get_base64_image(image_file):
    if not os.path.exists(image_file):
        return None
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_style(image_file):
    b64 = get_base64_image(image_file)
    
    # 이미지가 있으면 배경으로 깔고, 없으면 '파스텔 블루' 색상 사용
    if b64:
        bg_css = f"""
            background-image: linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.2)), url("data:image/jpeg;base64,{b64}");
            background-size: cover;
        """
    else:
        bg_css = "background-color: #b2c7d9;" # 카톡 기본 배경색 느낌

    css = f"""
    <style>
    /* 1. 폰트 전체 적용 (주아체) */
    html, body, [class*="css"] {{
        font-family: 'Jua', sans-serif !important;
        color: #333333 !important;
    }}

    /* 2. 전체 배경 설정 */
    [data-testid="stAppViewContainer"] {{
        {bg_css}
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* 3. 헤더 숨기기 (깔끔하게) */
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* 4. 채팅 말풍선 디자인 (둥글고 하얀 카드) */
    [data-testid="stChatMessage"] {{
        background-color: #ffffff !important;
        border-radius: 20px !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important; /* 그림자 효과 */
        padding: 15px !important;
        margin-bottom: 15px !important;
    }}

    /* 5. 말풍선 안의 글씨 */
    [data-testid="stChatMessage"] * {{
        color: #4a4a4a !important; /* 진한 회색 (눈 편안) */
        font-size: 1.1rem !important; /* 글씨 조금 키움 */
        line-height: 1.6 !important;
    }}

    /* 6. 사용자 아이콘 배경색 변경 */
    [data-testid="stChatMessageAvatarUser"] {{
        background-color: #fef01b !important; /* 카톡 노란색 */
    }}
    
    /* 7. 입력창 디자인 */
    .stChatInput textarea {{
        border-radius: 20px !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# 배경 이미지 적용
set_style("family.jpg")

# ==========================================
# 5. 사이드바 (가족 선택)
# ==========================================
with st.sidebar:
    st.title("👨‍👩‍👦‍👦 대화 상대")
    st.markdown("---")
    selected_user = st.radio(
        "누구에게 말을 걸까요?",
        ("아버지 (손기혁)", "어머니 (김영숙)", "막내 (손준호)"),
        index=0
    )
    st.info("💡 팁: 편하게 반말로 대화해보세요!")

user_name = selected_user.split('(')[1].replace(')', '')

def get_system_instruction(user):
    base = "너는 이 가족을 끔찍이 아끼는 AI 비서야. 답변은 3문장 이내로 짧고 다정하게 해줘."
    if "손기혁" in user:
        return base + " (대상: 손기혁님 - 71년생 부친, 점잖지만 아들바보, 시적인 표현 사용)"
    elif "김영숙" in user:
        return base + " (대상: 김영숙님 - 71년생 모친, 감수성 풍부, 리액션 대마왕, 이모티콘 많이 씀)"
    else:
        return base + " (대상: 손준호님 - 03년생 남동생, 츤데레, 현실적인 조언, 반존대)"

# ==========================================
# 6. 채팅 로직
# ==========================================
if "current_user" not in st.session_state:
    st.session_state.current_user = selected_user

if st.session_state.current_user != selected_user:
    st.session_state.messages = [] 
    st.session_state.chat_session = None 
    st.session_state.current_user = selected_user
    st.rerun()

if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    best_model_name = find_best_model()
    if best_model_name:
        try:
            model = genai.GenerativeModel(best_model_name, system_instruction=get_system_instruction(selected_user))
            st.session_state.chat_session = model.start_chat(history=[])
            greeting = f"{user_name}님! 어서오세요~ 오늘 기분은 어떠세요? 😊"
            st.session_state.messages = [{"role": "assistant", "content": greeting}]
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("모델 연결 실패")

# ==========================================
# 7. 화면 출력
# ==========================================
# 제목 스타일링
st.markdown(f"<h1 style='text-align: center; color: white; text-shadow: 2px 2px 4px #000000;'>{user_name}님 상담소 💬</h1>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if st.session_state.chat_session:
        try:
            response = st.session_state.chat_session.send_message(prompt)
            with st.chat_message("assistant"):
                st.write(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except:
            st.error("응답 오류")