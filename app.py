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

# --- 관점별 상세 지침 정의 (프롬프트 엔진) ---
def get_analysis_prompt(perspective, context, lang):
    instructions = {
        "긍정적/낙관론": "당신은 미래지향적 낙관주의자입니다. 뉴스에서 성장 잠재력, 해결책, 새로운 기회를 찾아 희망적인 분석을 제공하세요.",
        "비판적/신중론": "당신은 냉철한 리스크 분석가입니다. 뉴스 이면의 위험 요소, 부작용, 숨겨진 비용 및 한계점을 날카롭게 지적하세요.",
        "민주당(진보) 입장": "당신은 사회적 평등과 공공성을 중시합니다. 취약 계층 보호, 분배의 정의, 인권 및 개혁적 가치를 기준으로 분석하세요.",
        "국민의힘(보수) 입장": "당신은 자유 시장과 효율성을 중시합니다. 기업 경쟁력, 규제 완화, 국가 안보 및 실용주의적 가치를 기준으로 분석하세요.",
        "청년층(MZ)": "당신은 실용주의와 공정성을 중시하는 2030 세대입니다. 자산 형성, 미래 세대의 기회, 디지털 혁신 관점에서 분석하세요.",
        "노년층(실버)": "당신은 경험이 풍부하고 안정을 중시하는 6070 세대입니다. 전통적 가치, 사회 안전망, 건강 및 장기적인 안정을 중시하세요.",
        "기술 혁신 중심": "당신은 기술 지상주의자입니다. 기술적 진보, 효율성, 산업 생태계 변화와 미래 기술력에 초점을 맞춰 분석하세요.",
        "사회적 규제 중심": "당신은 윤리적 책임과 법적 규제를 중시합니다. 기업의 사회적 책임, 법적 제한, 시민 사회에 미치는 영향에 집중하세요."
    }
    
    detail = instructions.get(perspective, "당신은 해당 분야의 전문 분석가입니다. 객관적이고 깊이 있는 통찰을 제공하세요.")
    
    return f"""
    [Role] {detail}
    [Task] 아래 제공된 뉴스 데이터를 바탕으로 전문가 리포트를 작성하세요. 
    단순한 내용 요약은 금지합니다. 당신의 '관점'이 명확하게 반영된 비평과 전망을 포함해야 합니다.
    [Language] 모든 내용은 {lang}로 작성하세요.
    
    [News Data]
    {context}
    """

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

search_query = st.sidebar.text_input("상세 검색어 (선택 사항)", "")

# VS 모드 설정
if app_mode == "비교 분석 (VS Mode)":
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚖️ 비교 관점 선택")
    
    perspectives_list = [
        "긍정적/낙관론", "비판적/신중론", 
        "민주당(진보) 입장", "국민의힘(보수) 입장", 
        "청년층(MZ)", "노년층(실버)",
        "기술 혁신 중심", "사회적 규제 중심",
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
    with st.spinner('AI가 글로벌 뉴스를 분석 중입니다...'):

        # 검색어 최적화
        search_target = search_query
        if search_query:
            trans_prompt = f"Translate '{search_query}' into an English keyword for News API. Output ONLY the keyword."
            try:
                trans_res = model.generate_content(trans_prompt)
                search_target = trans_res.text.strip()
                st.toast(f"🔍 검색어 최적화: {search_target}")
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
                context += f"{i+1}. {art.get('title')}\n{art.get('description')}\n\n"

            if app_mode == "일반 브리핑":
                prompt = f"다음 뉴스를 {user_lang}로 전문적인 리포트로 분석해줘:\n{context}"
                result = model.generate_content(prompt)
                st.session_state.last_report = result.text
                st.session_state.vs_report = {"left": None, "right": None}
            else:
                # VS 모드: 각각의 페르소나 주입 프롬프트 사용
                p_left = get_analysis_prompt(choice_1, context, user_lang)
                p_right = get_analysis_prompt(choice_2, context, user_lang)
                
                left_res = model.generate_content(p_left)
                right_res = model.generate_content(p_right)

                st.session_state.vs_report = {
                    "left": left_res.text,
                    "right": right_res.text
                }
                st.session_state.active_perspectives = (choice_1, choice_2)
                st.session_state.last_report = None

            st.session_state.messages = []
        else:
            st.warning("뉴스를 찾을 수 없습니다. 검색어를 조정해 보세요.")

# 결과 출력 레이아웃
if app_mode == "일반 브리핑" and st.session_state.last_report:
    st.markdown("---")
    st.subheader(f"📊 {user_lang} 종합 분석 리포트")
    st.markdown(st.session_state.last_report)

elif app_mode == "비교 분석 (VS Mode)" and st.session_state.vs_report["left"]:
    st.markdown("---")
    p1, p2 = st.session_state.active_perspectives
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"🚩 {p1}")
        st.info(f"{p1} 관점에서 바라본 분석입니다.")
        st.markdown(st.session_state.vs_report["left"])

    with col2:
        st.subheader(f"🚩 {p2}")
        st.warning(f"{p2} 관점에서 바라본 분석입니다.")
        st.markdown(st.session_state.vs_report["right"])

# 6. 사이드바 챗봇 (컨텍스트 통합)
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI 뉴스 분석가")

if st.session_state.last_report or st.session_state.vs_report["left"]:
    chat_container = st.sidebar.container(height=350)

    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if chat_input := st.sidebar.chat_input("이 이슈에 대해 더 궁금한 점은?"):
        st.session_state.messages.append({"role": "user", "content": chat_input})

        # 챗봇 답변용 문맥 데이터 구성
        if app_mode == "일반 브리핑":
            context_data = st.session_state.last_report
        else:
            p1, p2 = st.session_state.active_perspectives
            context_data = f"[{p1} 분석]:\n{st.session_state.vs_report['left']}\n\n[{p2} 분석]:\n{st.session_state.vs_report['right']}"

        chat_prompt = f"다음은 최근 뉴스에 대한 분석 리포트입니다.\n{context_data}\n\n사용자 질문: {chat_input}\n전문가로서 리포트 내용을 바탕으로 답변해 주세요."
        
        try:
            chat_res = model.generate_content(chat_prompt)
            with chat_container:
                with st.chat_message("assistant"):
                    st.markdown(chat_res.text)
            st.session_state.messages.append({"role": "assistant", "content": chat_res.text})
        except:
            st.error("답변 생성 중 오류가 발생했습니다.")
else:
    st.sidebar.info("뉴스 브리핑을 먼저 생성해 주세요.")