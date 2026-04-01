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

<<<<<<< HEAD
# 3. Gemini 설정 (모델명은 사용 가능한 최신 버전으로 유지)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 세션 상태 초기화 (데이터 유지용) ---
=======
# 3. Gemini 3.1 Flash Lite 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

# --- 세션 상태 초기화 ---
>>>>>>> db8b73b51417e8210fb5f3fb55f6d6b5e1ed0703
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

<<<<<<< HEAD
# [기능 추가] 분석 모드 선택
app_mode = st.sidebar.radio("📊 분석 모드 선택", ["일반 브리핑", "비교 분석 (VS Mode)"])

=======
>>>>>>> db8b73b51417e8210fb5f3fb55f6d6b5e1ed0703
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

# [기능 추가] VS 모드 관점 선택 리스트
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

# 5. 메인 화면 구성
st.title(f"🌐 AI 글로벌 뉴스 브리핑 {'[VS Mode]' if app_mode == '비교 분석 (VS Mode)' else ''}")

if st.sidebar.button("브리핑 생성 시작"):
<<<<<<< HEAD
    with st.spinner('AI가 글로벌 뉴스를 분석 중입니다...'):
        
        # 검색어 최적화 (다국어 대응)
        search_target = search_query
        if search_query:
            trans_prompt = f"Translate the search term '{search_query}' into a professional English keyword. Output ONLY the keyword."
            trans_res = model.generate_content(trans_prompt)
            search_target = trans_res.text.strip()
            st.toast(f"🔍 검색어 최적화 완료: {search_target}")

        # NewsAPI 데이터 수집
        base_url = "https://newsapi.org/v2/everything" if search_query else "https://newsapi.org/v2/top-headlines"
        params = {"q": search_target, "language": "en", "pageSize": 10, "apiKey": NEWS_API_KEY}
        if not search_query: params["category"] = category
=======
    with st.spinner('AI가 카테고리와 검색어를 분석하여 최적화 중입니다...'):
        
        # --- 검색어 최적화 로직 ---
        search_target = search_query
        if search_query:
            context_instruction = ""
            if category == "sports":
                context_instruction = "Focus on real-world sports matches, scores, and athletes. EXCLUDE video games or e-sports."
            elif category in ["technology", "business"]:
                context_instruction = "Focus on the industry, business deals, and technological trends, including gaming if relevant."
            else:
                context_instruction = "Provide general news coverage for this topic."

            trans_prompt = f"""
            Translate '{search_query}' into an English keyword for a News API.
            [Instruction]: {context_instruction}
            Output ONLY the final optimized search string.
            """
            
            try:
                trans_res = model.generate_content(trans_prompt)
                search_target = trans_res.text.strip()
                st.toast(f"🔍 {category} 맞춤형 최적화: {search_target}")
            except Exception as e:
                st.error(f"검색어 최적화 중 오류: {e}")
                search_target = search_query

        # --- NewsAPI 데이터 수집 로직 ---
        base_url = "https://newsapi.org/v2/everything" if search_query else "https://newsapi.org/v2/top-headlines"
        params = {
            "q": search_target,
            "language": "en", 
            "pageSize": 12,
            "apiKey": NEWS_API_KEY
        }
        if not search_query: 
            params["category"] = category
>>>>>>> db8b73b51417e8210fb5f3fb55f6d6b5e1ed0703

        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if data.get("status") == "ok" and data.get("articles"):
                articles = data["articles"]
                context = ""
                for i, art in enumerate(articles):
                    title = art.get('title', 'No Title')
                    desc = art.get('description', 'No Description')
                    context += f"기사 {i+1}: {title}\n내용: {desc}\n\n"

<<<<<<< HEAD
                if app_mode == "일반 브리핑":
                    # 일반 모드: 단일 리포트 생성
                    report_prompt = f"다음 뉴스 데이터를 분석하여 {user_lang}로 리포트를 작성해줘. 전문가적 분석을 포함할 것.\n데이터: {context}"
                    result = model.generate_content(report_prompt)
                    st.session_state.last_report = result.text
                    st.session_state.vs_report = {"left": None, "right": None}
                
                else:
                    # VS 모드: 두 가지 관점으로 각각 생성
                    st.session_state.last_report = None
                    
                    prompt_left = f"너는 {choice_1}의 시각을 가진 전문가야. 다음 뉴스 데이터를 {user_lang}로 분석해줘.\n데이터: {context}"
                    prompt_right = f"너는 {choice_2}의 시각을 가진 전문가야. 다음 뉴스 데이터를 {user_lang}로 분석해줘.\n데이터: {context}"
                    
                    res_left = model.generate_content(prompt_left)
                    res_right = model.generate_content(prompt_right)
                    
                    st.session_state.vs_report = {"left": res_left.text, "right": res_right.text}
                    st.session_state.active_perspectives = (choice_1, choice_2)
                
                st.session_state.messages = [] # 대화 내역 초기화
            else:
                st.warning("관련 뉴스를 찾을 수 없습니다.")
=======
                # 브리핑 리포트 생성
                report_prompt = f"다음 뉴스 데이터를 분석하여 {user_lang}로 리포트를 작성해줘. 이슈별 그룹화와 전문가적 분석을 포함할 것.\n데이터: {context}"
                result = model.generate_content(report_prompt)
                
                st.session_state.last_report = result.text 
                st.session_state.messages = [] 
            else:
                st.warning("관련 뉴스를 찾을 수 없습니다. 검색어나 카테고리를 변경해 보세요.")
>>>>>>> db8b73b51417e8210fb5f3fb55f6d6b5e1ed0703
        except Exception as e:
            st.error(f"데이터 수집 중 오류 발생: {e}")

# --- 결과 출력 레이아웃 ---
if app_mode == "일반 브리핑" and st.session_state.last_report:
    st.markdown("---")
    st.subheader(f"📊 {user_lang} 글로벌 브리핑 결과")
    st.markdown(st.session_state.last_report)

<<<<<<< HEAD
elif app_mode == "비교 분석 (VS Mode)" and st.session_state.vs_report["left"]:
    st.markdown("---")
    p1, p2 = st.session_state.active_perspectives
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"🚩 {p1}")
        st.info(f"{p1} 관점에서의 분석입니다.")
        st.markdown(st.session_state.vs_report["left"])
        
    with col2:
        st.subheader(f"🚩 {p2}")
        st.warning(f"{p2} 관점에서의 분석입니다.")
        st.markdown(st.session_state.vs_report["right"])

=======
>>>>>>> db8b73b51417e8210fb5f3fb55f6d6b5e1ed0703
# 6. 사이드바 챗봇
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI 뉴스 분석가")

if st.session_state.last_report or st.session_state.vs_report["left"]:
    chat_container = st.sidebar.container(height=350)
    
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if chat_input := st.sidebar.chat_input("뉴스 분석에 대해 질문하세요"):
        st.session_state.messages.append({"role": "user", "content": chat_input})
        
        # 챗봇 컨텍스트 설정
        if app_mode == "일반 브리핑":
            context_data = st.session_state.last_report
        else:
            context_data = f"[{p1} 분석]: {st.session_state.vs_report['left']}\n\n[{p2} 분석]: {st.session_state.vs_report['right']}"

<<<<<<< HEAD
        chat_prompt = f"리포트 내용: {context_data}\n질문: {chat_input}\n위 내용을 바탕으로 전문가로서 답변해줘."
        chat_res = model.generate_content(chat_prompt)
        
        with chat_container:
            with st.chat_message("user"): st.markdown(chat_input)
            with st.chat_message("assistant"): st.markdown(chat_res.text)
        
        st.session_state.messages.append({"role": "assistant", "content": chat_res.text})
=======
            with st.chat_message("assistant"):
                chat_prompt = f"리포트: {st.session_state.last_report}\n질문: {chat_input}\n전문가로서 리포트 기반의 답변을 해줘."
                chat_res = model.generate_content(chat_prompt)
                st.markdown(chat_res.text)
                st.session_state.messages.append({"role": "assistant", "content": chat_res.text})
>>>>>>> db8b73b51417e8210fb5f3fb55f6d6b5e1ed0703
else:
    st.sidebar.info("브리핑을 생성하면 AI와 대화할 수 있습니다.")