import streamlit as st
import google.generativeai as genai
import base64
import os

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="우리 가족 사랑방 🏠",
    page_icon="👨‍👩‍👦‍👦",
    layout="centered"
)

# ==========================================
# 2. API 키 설정 (가장 먼저!)
# ==========================================
if "MY_API_KEY" in st.secrets:
    MY_API_KEY = st.secrets["MY_API_KEY"]
else:
    st.error("🚨 API 키가 없습니다! Secrets 설정을 확인해주세요.")
    st.stop()

genai.configure(api_key=MY_API_KEY)

# ==========================================
# 3. [핵심] 서버에 있는 모델 직접 조회하기
# ==========================================
def find_best_model():
    try:
        # 서버야, 너가 가진 모델 다 내놔봐.
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # 목록 중에서 'gemini' 들어간 거 아무거나 잡기 (최신순 선호)
        # 1.5-flash -> 1.5-pro -> 1.0-pro 순서로 찾아봅니다.
        preferred_order = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro",
            "models/gemini-1.0-pro",
            "models/gemini-pro"
        ]
        
        for p in preferred_order:
            if p in available_models:
                return p # 찾았다! 이거 쓰자.
        
        # 선호하는 게 없으면 목록에 있는 'gemini' 아무거나 잡음
        for m in available_models:
            if "gemini" in m:
                return m
                
        return None # 진짜 아무것도 없음
    except Exception as e:
        st.error(f"모델 목록 조회 실패: {e}")
        return None

# ==========================================
# 4. 배경 이미지 설정
# ==========================================
def set_bg(image_file):
    if not os.path.exists(image_file):
        return 

    with open(image_file, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    
    page_bg_img = f'''
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url("data:image/jpeg;base64,{b64}");
        background-size: 50%;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_bg('family.jpg') 

# ==========================================
# 5. 사이드바 (가족 선택)
# ==========================================
with st.sidebar:
    st.title("👨‍👩‍👦‍👦 가족 선택")
    selected_user = st.radio(
        "누구랑 대화하시겠어요?",
        ("아버지 (손기혁)", "어머니 (김영숙)", "막내 (손준호)"),
        index=0
    )
    
    # [진단용] 실제 잡힌 모델 보여주기 (성공하면 나중에 지우세요)
    st.divider()
    best_model_name = find_best_model()
    if best_model_name:
        st.success(f"연결된 모델:\n{best_model_name}")
    else:
        st.error("사용 가능한 모델을 못 찾았습니다.")
        st.write("전체 목록 확인 필요")

user_name = selected_user.split('(')[1].replace(')', '')

# ==========================================
# 6. 사용자 변경 시 리셋
# ==========================================
if "current_user" not in st.session_state:
    st.session_state.current_user = selected_user

if st.session_state.current_user != selected_user:
    st.session_state.messages = [] 
    st.session_state.chat_session = None 
    st.session_state.current_user = selected_user
    st.rerun() 

# ==========================================
# 7. AI 설정 (자동으로 찾은 모델 사용)
# ==========================================
def get_system_instruction(user):
    base = "너는 이 가족을 끔찍이 아끼는 AI 비서야. 한국어로 따뜻하게 대답해."
    if "손기혁" in user:
        return base + " (대상: 손기혁님 - 71년생 부친, 국방과학연구소, 암투병, 시 문학, 존댓말, 감성적, 약간의 유머, 따뜻함)"
    elif "김영숙" in user:
        return base + " (대상: 김영숙님 - 71년생 모친, 어린이집 교사, 감수성, 요리/건강, 공감 대화, 고민을 잘 들어주는)"
    else:
        return base + " (대상: 손준호님 - 03년생 남동생, 보안전공, 재테크, 멘탈케어, 반존대, 고민을 잘 들어주는 )"

# 모델 로딩
if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    if best_model_name:
        try:
            # 찾은 모델 이름 그대로 넣기
            model = genai.GenerativeModel(best_model_name, system_instruction=get_system_instruction(selected_user))
            st.session_state.chat_session = model.start_chat(history=[])
            
            greeting = f"{user_name}님! 오늘도 행복한 하루 보내세요 🍀"
            st.session_state.messages = [{"role": "assistant", "content": greeting}]
        except Exception as e:
            st.error(f"모델 연결 실패: {e}")
    else:
        st.error("사용 가능한 Gemini 모델을 찾을 수 없습니다. API 키나 라이브러리 버전을 확인하세요.")

# ==========================================
# 8. 채팅 화면
# ==========================================
st.title(f"{user_name}님 전용 상담소 💬")

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
        except Exception as e:
            st.error(f"응답 오류: {e}")