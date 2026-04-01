import streamlit as st
import requests
import google.generativeai as genai

# 1. 페이지 설정
st.set_page_config(page_title="AI 글로벌 뉴스 브리핑", page_icon="🌐", layout="wide")

# 2. 보안 관리 (Secrets)
try:
    NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("보안 오류: API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인하세요.")
    st.stop()

# 3. Gemini 설정 (최신 모델 유지)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

# --- 세션 상태 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_report" not in st.session_state:
    st.session_state.last_report = None
if "vs_report" not in st.session_state:
    st.session_state.vs_report = {"left": None, "right": None}
if "active_perspectives" not in st.session_state:
    st.session_state.active_perspectives = (None, None)

# 4. 사이드바 구성
st.sidebar.header("⚙️ 브리핑 설정")

# 분석 모드
app_mode = st.sidebar.radio("📊 분석 모드 선택", ["일반 브리핑", "비교 분석 (VS Mode)"])

user_lang = st.sidebar.selectbox(
    "브리핑 언어", ["한국어", "English", "日本語", "中國語"], index=0
)

category = st.sidebar.selectbox(
    "뉴스 카테고리",
    ["general", "business", "technology", "sports", "entertainment", "science", "health"],
    format_func=lambda x: {
        "general": "전체", "business": "경제/경영", "technology": "IT/기술",
        "sports": "스포츠", "entertainment": "엔터", "science": "과학", "health": "건강"
    }.get(x)
)

search_query = st.sidebar.text_input("상세 검색어 (어떤 언어든 가능)", "")

# VS 모드 설정
if app_mode == "비교 분석 (VS Mode)":
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚖️ 비교 관점 선택")
    
    perspectives_list = [
        "긍정적/낙관론", "비판적/신중론", 
        "민주당(진보) 입장", "국민의힘(보수) 입장", 
        "기술 혁신 중심", "사회적 규제 중심",
        "투자자 입장", "일반 소비자 입장",
        "직접 입력"
    ]
    
    choice_1 = st.sidebar.selectbox("왼쪽 관점", perspectives_list, index=0)
    if choice_1 == "직접 입력":
        choice_1 = st.sidebar.text_input("왼쪽 관점 직접 정의", value="사용자 정의 1")
        
    choice_2 = st.sidebar.selectbox("오른쪽 관점", perspectives_list, index=1)
    if choice_2 == "직접 입력":
        choice_2 = st.sidebar.text_input("오른쪽 관점 직접 정의", value="사용자 정의 2")
else:
    choice_1, choice_2 = None, None

# 5. 메인 화면
st.title(f"🌐 AI 글로벌 뉴스 브리핑 {'[VS Mode]' if app_mode == '비교 분석 (VS Mode)' else ''}")

if st.sidebar.button("브리핑 생성 시작"):
    with st.spinner('AI가 뉴스를 분석 중입니다...'):

        # 검색어 최적화
        search_target = search_query
        if search_query:
            context_instruction = ""
            if category == "sports":
                context_instruction = "Focus on real-world sports matches."
            elif category in ["technology", "business"]:
                context_instruction = "Focus on industry and trends."
            else:
                context_instruction = "General news."

            trans_prompt = f"""
            Translate '{search_query}' into an English keyword.
            {context_instruction}
            Output ONLY the keyword.
            """
            
            try:
                trans_res = model.generate_content(trans_prompt)
                search_target = trans_res.text.strip()
                st.toast(f"🔍 최적화 완료: {search_target}")
            except:
                search_target = search_query

        # 뉴스 API 호출
        base_url = "https://newsapi.org/v2/everything" if search_query else "https://newsapi.org/v2/top-headlines"
        params = {
            "q": search_target,
            "language": "en",
            "pageSize": 12,
            "apiKey": NEWS_API_KEY
        }
        if not search_query:
            params["category"] = category

        response = requests.get(base_url, params=params)
        data = response.json()

        if data.get("status") == "ok" and data.get("articles"):
            context = ""
            for i, art in enumerate(data["articles"]):
                title = art.get("title", "")
                desc = art.get("description", "")
                context += f"{i+1}. {title}\n{desc}\n\n"

            if app_mode == "일반 브리핑":
                prompt = f"{user_lang}로 뉴스 분석 리포트 작성:\n{context}"
                result = model.generate_content(prompt)
                st.session_state.last_report = result.text
                st.session_state.vs_report = {"left": None, "right": None}

            else:
                left = model.generate_content(f"{choice_1} 관점 분석:\n{context}")
                right = model.generate_content(f"{choice_2} 관점 분석:\n{context}")

                st.session_state.vs_report = {
                    "left": left.text,
                    "right": right.text
                }
                st.session_state.active_perspectives = (choice_1, choice_2)
                st.session_state.last_report = None

            st.session_state.messages = []

        else:
            st.warning("관련 뉴스를 찾을 수 없습니다.")

# 결과 출력
if app_mode == "일반 브리핑" and st.session_state.last_report:
    st.markdown("---")
    st.subheader(f"📊 {user_lang} 브리핑")
    st.markdown(st.session_state.last_report)

elif app_mode == "비교 분석 (VS Mode)" and st.session_state.vs_report["left"]:
    st.markdown("---")
    p1, p2 = st.session_state.active_perspectives
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"🚩 {p1}")
        st.markdown(st.session_state.vs_report["left"])

    with col2:
        st.subheader(f"🚩 {p2}")
        st.markdown(st.session_state.vs_report["right"])

# 챗봇
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI 뉴스 분석가")

if st.session_state.last_report or st.session_state.vs_report["left"]:
    chat_container = st.sidebar.container(height=350)

    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if chat_input := st.sidebar.chat_input("질문하세요"):
        st.session_state.messages.append({"role": "user", "content": chat_input})

        if app_mode == "일반 브리핑":
            context_data = st.session_state.last_report
        else:
            p1, p2 = st.session_state.active_perspectives
            context_data = f"{p1}:\n{st.session_state.vs_report['left']}\n\n{p2}:\n{st.session_state.vs_report['right']}"

        chat_prompt = f"{context_data}\n질문: {chat_input}"
        chat_res = model.generate_content(chat_prompt)

        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(chat_res.text)

        st.session_state.messages.append({"role": "assistant", "content": chat_res.text})

else:
    st.sidebar.info("브리핑을 생성하면 AI와 대화할 수 있습니다.")