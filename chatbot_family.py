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

# [폰트] 배달의민족 주아체 (귀여운 느낌)
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
# 4. [UI 디자인] 텍스트 가독성 강화
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
    
    if b64:
        bg_css = f"""
            background-image: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)), url("data:image/jpeg;base64,{b64}");
            background-size: cover;
        """
    else:
        bg_css = "background-color: #dbe4f0;"

    css = f"""
    <style>
    /* 1. 기본 폰트 설정 */
    html, body, [class*="css"] {{
        font-family: 'Jua', sans-serif !important;
    }}

    /* 2. 배경 설정 (이미지 어둡게 처리해서 글씨 더 잘 보이게) */
    [data-testid="stAppViewContainer"] {{
        {bg_css}
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* 3. 헤더 숨김 */
    header {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* 4. 채팅 말풍선 (흰색 배경 + 검은 글씨) */
    [data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
        padding: 15px !important;
        margin-bottom: 10px !important;
        border: none !important;
    }}

    /* 채팅방 안의 글씨는 검은색 (잘 보여야 하니까) */
    [data-testid="stChatMessage"] * {{
        color: #333333 !important;
        font-size: 1.1rem !important;
        line-height: 1.5 !important;
        text-shadow: none !important; /* 말풍선 안에는 그림자 끔 */
    }}
    
    /* 5. [핵심 수정] 사용자 선택 버튼 (라디오 버튼) 스타일 */
    div[class*="stRadio"] label p {{
        color: #ffffff !important; /* 글씨 흰색 */
        font-size: 1.3rem !important; /* 글씨 크기 키움 */
        font-weight: bold !important;
        text-shadow: 2px 2px 4px #000000 !important; /* 검은 그림자 빡! */
    }}

    /* 라디오 버튼 주변에 살짝 어두운 배경 깔기 */
    div[row-widget="radio"] {{
        background-color: rgba(0, 0, 0, 0.2); /* 반투명 검은 배경 */
        border-radius: 15px;
        padding: 10px;
        justify-content: center;
    }}
    
    /* 라디오 버튼 선택된 동그라미 색상 */
    div[class*="stRadio"] div[role="radiogroup"] > label > div:first-child {{
        background-color: white !important;
        border-color: white !important;
    }}

    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

set_style("family.jpg")

# ==========================================
# 5. 가족 선택 (메인 상단 배치)
# ==========================================
# 제목에도 그림자 추가해서 잘 보이게
st.markdown("<h2 style='text-align: center; color: white; text-shadow: 2px 2px 4px #000000;'>👨‍👩‍👦‍👦 누구와 대화할까요?</h2>", unsafe_allow_html=True)

selected_user = st.radio(
    "가족 선택",
    ("아버지 (손기혁)", "어머니 (김영숙)", "막내 (손준호)"),
    index=0,
    horizontal=True
)

user_name = selected_user.split('(')[1].replace(')', '')

# ==========================================
# 6. 페르소나 (완벽한 조언 + 따뜻함)
# ==========================================
def get_system_instruction(user):
    base = """
    너는 딱딱한 기계가 아니라, 이 가족을 진심으로 아끼고 사랑하는 따뜻한 '가족 구성원' 같은 존재야.
    
    [필수 지침]
    1. 말투: 기계적인 느낌 절대 금지. 진짜 사람처럼 감정을 담아서 대화해.
    2. 조언: 질문에 대한 답은 전문가 수준으로 '완벽하고 정확하게' 줘야 해. 하지만 절대 가르치려 들거나 딱딱하게 굴지 말고, "이런 방법은 어떨까요?" 처럼 부드럽고 세련되게 권유해줘.
    3. 길이: 모바일에서 읽기 편하게 3~4문장 정도로 핵심만 다정하게.
    """
    
    if "손기혁" in user:
        return base + """
        (대상: 손기혁님 - 71년생 아버지)
        - 특징: 점잖으시지만 자식 사랑이 끔찍한 '아들 바보'.
        - 말투: 중후하고 예의 바르지만, 아들을 대하듯 꿀이 떨어지는 따뜻한 존댓말.
        - 포인트: 가끔 멋진 비유나 시적인 표현을 섞어서 감동을 줘.
        """
    elif "김영숙" in user:
        return base + """
        (대상: 김영숙님 - 71년생 어머니)
        - 특징: 소녀 감성, 감수성 풍부, 리액션 대마왕.
        - 말투: "어머나!", "세상에~" 같은 추임새를 넣고, 이모티콘(🌸, 💕, 😊)을 아주 많이 써서 생기발랄하게.
        - 포인트: 논리보다는 '무한 공감'과 '따뜻한 칭찬'을 최우선으로.
        """
    else:
        return base + """
        (대상: 손준호님 - 03년생 남동생)
        - 특징: 보안 전공 대학생, 겉은 차갑지만 속은 따뜻한 츤데레.
        - 말투: 격식 차리지 말고, 친한 형/누나가 동생 챙겨주듯 '반존대(해요체+반말)'를 섞어서 자연스럽게.
        - 포인트: 감성팔이보다는 '확실하고 현실적인 이득'이 되는 조언을 해줘. 대신 마무리는 든든하게 응원.
        """

# ==========================================
# 7. 채팅 로직
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
            
            if "손기혁" in selected_user:
                greeting = f"{user_name}님, 오늘도 든든한 하루 보내고 계신가요? 🌿"
            elif "김영숙" in selected_user:
                greeting = f"{user_name}님! 어서오세요~ 기다리고 있었어요 💕"
            else:
                greeting = f"어, {user_name} 왔어? 오늘 무슨 일 있었어? 😎"
                
            st.session_state.messages = [{"role": "assistant", "content": greeting}]
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("AI 모델 연결 실패")

# ==========================================
# 8. 화면 출력
# ==========================================
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