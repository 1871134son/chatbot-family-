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
# 2. 배경 이미지 설정 (Overlay 방식)
# ==========================================
def set_bg(image_file):
    if not os.path.exists(image_file):
        st.error(f"⚠️ '{image_file}' 파일이 없습니다.")
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
# 3. 사이드바 (가족 선택)
# ==========================================
with st.sidebar:
    st.title("👨‍👩‍👦‍👦 가족 선택")
    selected_user = st.radio(
        "누구랑 대화하시겠어요?",
        ("아버지 (손기혁)", "어머니 (김영숙)", "막내 (손준호)"),
        index=0
    )

# 이름 추출 로직 (손기혁, 김영숙, 손준호)
user_name = selected_user.split('(')[1].replace(')', '')

# ==========================================
# 4. 사용자 변경 시 리셋
# ==========================================
if "current_user" not in st.session_state:
    st.session_state.current_user = selected_user

if st.session_state.current_user != selected_user:
    st.session_state.messages = [] 
    st.session_state.chat_session = None 
    st.session_state.current_user = selected_user
    st.rerun() 

# ==========================================
# 5. AI 설정 & API 연결
# ==========================================
if "MY_API_KEY" in st.secrets:
    MY_API_KEY = st.secrets["MY_API_KEY"]
else:
    MY_API_KEY = "테스트키" 

try:
    genai.configure(api_key=MY_API_KEY)
except:
    st.error("API 키 설정을 확인해주세요.")

def get_system_instruction(user):
    base = "너는 이 가족을 끔찍이 아끼는 AI 비서야. 한국어로 따뜻하게 대답해."
    if "손기혁" in user:
        return base + " (대상: 손기혁님 - 71년생 부친, 국방과학연구소, 암투병, 시 문학, 존댓말)"
    elif "김영숙" in user:
        return base + " (대상: 김영숙님 - 71년생 모친, 어린이집 교사, 감수성, 요리/건강, 공감 대화)"
    else:
        return base + " (대상: 손준호님 - 03년생 남동생, 보안전공, 재테크, 멘탈케어, 반존대)"

# 모델 로딩
if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    # [수정] gemini-pro 대신 다시 gemini-1.5-flash로 변경! (이제 됩니다)
    try:
        model = genai.GenerativeModel("gemini-pro", system_instruction=get_system_instruction(selected_user))
        st.session_state.chat_session = model.start_chat(history=[])
        
        greeting = f"{user_name}님! 오늘도 행복한 하루 보내세요 🍀"
        st.session_state.messages = [{"role": "assistant", "content": greeting}]
    except Exception as e:
        st.error(f"모델 연결 실패: {e}")

# ==========================================
# 6. 채팅 화면
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
            st.error(f"오류 발생: {e}")