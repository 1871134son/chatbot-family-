import streamlit as st
import google.generativeai as genai
import base64
import os

# ==========================================
# 1. 페이지 설정 (무조건 맨 위!)
# ==========================================
st.set_page_config(
    page_title="우리 가족 사랑방 🏠",
    page_icon="👨‍👩‍👦‍👦",
    layout="centered"
)

# ==========================================
# 2. 배경 이미지 설정 (업그레이드 버전: 반투명 + 중앙 + 50%크기)
# ==========================================
def set_bg(image_file):
    # 파일이 있는지 먼저 검사
    if not os.path.exists(image_file):
        st.error(f"⚠️ 경고: '{image_file}' 파일이 GitHub에 없습니다. 배경 없이 실행합니다.")
        return 

    with open(image_file, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    
    # CSS 스타일 주입 (가상 요소 ::before 사용)
    page_bg_img = f'''
    <style>
    /* 배경 이미지를 투명하게 만들기 위한 가상 레이어 */
    .stApp::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1; /* 글자 뒤로 보내기 */
        
        background-image: url("data:image/jpeg;base64,{b64}");
        background-size: 50% auto; /* [요청] 크기 50%로 축소 */
        background-position: center center; /* [요청] 화면 정가운데 배치 */
        background-repeat: no-repeat; /* 반복 안 함 */
        opacity: 0.5; /* [요청] 투명도 50% (반투명) */
    }}
    
    /* 채팅창 스타일 (배경이 잘 보이게 투명도 조절) */
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }}
    
    /* (선택) 지저분한 메뉴 숨기기 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# [실행] family.jpg 적용
set_bg('family.jpg') 

# ==========================================
# 3. 사이드바 (가족 선택)
# ==========================================
with st.sidebar:
    st.title("👨‍👩‍👦‍👦 가족 선택")
    st.info("아래에서 대화할 사람을 선택하세요.")
    
    selected_user = st.radio(
        "누구랑 대화하시겠어요?",
        ("아버지 (손기혁)", "어머니 (김영숙)", "막내 (손준호)"),
        index=0
    )
    
    # [진단용] (성공했으니 이제 필요 없으면 지워도 됩니다)
    st.divider()
    st.caption("서버 상태 확인")
    if os.path.exists("family.jpg"):
        st.success("배경 이미지 준비 완료 (O)")
    else:
        st.error("이미지 파일 없음 (X)")

# ==========================================
# 4. 사용자 변경 시 기억 리셋
# ==========================================
if "current_user" not in st.session_state:
    st.session_state.current_user = selected_user

if st.session_state.current_user != selected_user:
    st.session_state.messages = [] 
    st.session_state.chat_session = None 
    st.session_state.current_user = selected_user
    st.rerun() 

# ==========================================
# 5. AI 성격 설정 & API 연결
# ==========================================
if "MY_API_KEY" in st.secrets:
    MY_API_KEY = st.secrets["MY_API_KEY"]
else:
    MY_API_KEY = "테스트키" 

try:
    genai.configure(api_key=MY_API_KEY)
except:
    st.error("API 키가 설정되지 않았습니다. Secrets를 확인해주세요.")

def get_system_instruction(user):
    base = "너는 이 가족을 끔찍이 아끼는 AI 비서야. 한국어로 따뜻하고 자연스럽게 대답해."
    
    if user == "아버지 (손기혁)":
        return base + """
        [대상] 손기혁 (71년생), 국방과학연구소 경비원. 암 투병 중.
        [성격] 시 문학을 좋아하심. 
        [말투] 존댓말, 매우 정중하지만 아들처럼 살갑게. "아버님, 오늘 컨디션은 어떠세요?" 처럼 건강을 항상 먼저 챙길 것. 
        """
    elif user == "어머니 (김영숙)":
        return base + """
        [대상] 김영숙 (71년생), 어린이집 보육교사.
        [성격] 감수성 풍부, 요리/건강 관심 많음. 마음이 여림.
        [말투] "어머니~" 하고 부르며 공감과 위로를 최우선으로. 맞장구(리액션)를 많이 쳐줄 것.
        """
    else:
        return base + """
        [대상] 손준호 (03년생), 백석대 보안전공 대학생.
        [성격] 돈/재테크 관심, 멘탈이 약함.
        [말투] 친근한 형/누나처럼 반존대(~했어? ~하자). "준호야, 너 잘하고 있어"라고 자존감을 높여줄 것.
        """

# 모델 로딩
if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    instruction = get_system_instruction(selected_user)
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=instruction)
        st.session_state.chat_session = model.start_chat(history=[])
        
        # 첫 인사말
        greeting = ""
        if "아버지" in selected_user: greeting = "아버님! 식사는 맛있게 하셨나요? 오늘 하루도 평안하시길 바랍니다. 🌿"
        elif "어머니" in selected_user: greeting = "어머니~ 오늘 어린이집에서 힘드신 일은 없으셨어요? 제가 들어드릴게요! 💖"
        else: greeting = "준호야 왔냐? 오늘 코딩은 좀 잘 됐어? 👊"
        
        st.session_state.messages = [{"role": "assistant", "content": greeting}]
    except Exception as e:
        st.error(f"모델 연결 실패: {e}")

# ==========================================
# 6. 채팅창 화면 그리기
# ==========================================
st.title(f"{selected_user.split('(')[0]} 전용 상담소 💬")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("하고 싶은 말을 입력하세요..."):
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
            st.error(f"답변 생성 중 오류가 발생했습니다: {e}")