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
# 2. 배경 이미지 설정 (안전한 Overlay 방식)
# ==========================================
def set_bg(image_file):
    if not os.path.exists(image_file):
        st.error(f"⚠️ '{image_file}' 파일이 없습니다. GitHub에 올렸는지 확인해주세요.")
        return 

    with open(image_file, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    
    # [핵심 변경] ::before 같은 거 안 씁니다. 가장 직관적인 CSS 사용.
    # linear-gradient: 이미지 위에 50% 투명한 흰색을 덧칠해서 연하게 만듭니다.
    page_bg_img = f'''
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url("data:image/jpeg;base64,{b64}");
        background-size: 50%; /* [요청] 크기 절반 */
        background-position: center center; /* [요청] 정가운데 */
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* 채팅창 스타일 */
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

# [실행]
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
    if user == "아버지 (손기혁)":
        return base + " (대상: 71년생 부친, 국방과학연구소, 암투병, 시 문학, 존댓말)"
    elif user == "어머니 (김영숙)":
        return base + " (대상: 71년생 모친, 어린이집 교사, 감수성, 요리/건강, 공감 대화)"
    else:
        return base + " (대상: 03년생 남동생, 보안전공, 재테크, 멘탈케어, 반존대)"

# 모델 로딩
if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=get_system_instruction(selected_user))
    st.session_state.chat_session = model.start_chat(history=[])
    
    greeting = f"{selected_user.split('(')[0]}님! 오늘도 행복하세요 🍀"
    st.session_state.messages = [{"role": "assistant", "content": greeting}]

# ==========================================
# 6. 채팅 화면
# ==========================================
st.title(f"{selected_user.split('(')[0]} 전용 상담소 💬")

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
            st.error(f"Error: {e}")