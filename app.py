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

# 3. Gemini 3.1 Flash  설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

# --- 세션 상태 초기화 (데이터 기억용) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_report" not in st.session_state:
    st.session_state.last_report = None

# 4. 사이드바 구성
st.sidebar.header("⚙️ 브리핑 설정")

# 브리핑 언어 선택 (베트남어 제외, 중국어 추가)
user_lang = st.sidebar.selectbox(
    "브리핑을 받을 언어",
    ["한국어", "English", "日本語", "中國語"],
    index=0
)

category = st.sidebar.selectbox(
    "뉴스 카테고리",
    ["general", "business", "technology", "sports", "entertainment", "science", "health"],
    format_func=lambda x: {
        "general": "전체", "business": "경제/경영", "technology": "IT/기술",
        "sports": "스포츠", "entertainment": "엔터", "science": "과학", "health": "건강"
    }.get(x)
)

# 검색어 입력 (입력 언어에 상관없이 AI가 번역 처리)
search_query = st.sidebar.text_input("상세 검색어 (어떤 언어든 가능)", "")

# 5. 메인 화면: 뉴스 브리핑 생성
st.title("🌐 AI 글로벌 뉴스 브리핑")

if st.sidebar.button("브리핑 생성 시작"):
    with st.spinner('AI가 검색어를 최적화하고 글로벌 뉴스를 분석 중입니다...'):
        
        # --- [핵심 기능] 다국어 검색어 자동 번역 매커니즘 ---
        search_target = search_query
        if search_query:
    # 카테고리가 'sports'면 게임 제외, 'entertainment'나 'technology'면 게임 포함 등 전략 수립
    context_instruction = ""
        if category == "sports":
            context_instruction = "Focus on real-world sports matches, scores, and athletes. EXCLUDE video games or e-sports."
        elif category == "technology" or category == "business":
            context_instruction = "Focus on the industry, business deals, and technological trends, including gaming if relevant."
        else:
            context_instruction = "Provide general news coverage for this topic."

    trans_prompt = f"""
    Translate '{search_query}' into an English keyword for a News API.
    
    [Instruction]
    {context_instruction}
    
    Output ONLY the final optimized search string.
    """
    
    trans_res = model.generate_content(trans_prompt)
    search_target = trans_res.text.strip()
    st.toast(f"🔍 {category} 맞춤형 최적화: {search_target}")
                # 브리핑 리포트 생성 (선택한 user_lang 반영)
                report_prompt = f"다음 뉴스 데이터를 분석하여 {user_lang}로 리포트를 작성해줘. 이슈별 그룹화와 전문가적 분석을 포함할 것.\n데이터: {context}"
                result = model.generate_content(report_prompt)
                
                # 결과 저장 및 초기화
                st.session_state.last_report = result.text 
                st.session_state.messages = [] 
            else:
                st.warning("관련 뉴스를 찾을 수 없습니다. 검색어를 변경해 보세요.")
        except Exception as e:
            st.error(f"데이터 수집 중 오류 발생: {e}")

# 리포트 출력
if st.session_state.last_report:
    st.markdown("---")
    st.subheader(f"📊 {user_lang} 글로벌 브리핑 결과")
    st.markdown(st.session_state.last_report)

# 6. 사이드바 챗봇 (데이터 기억 및 공유)
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI 뉴스 분석가")

if st.session_state.last_report:
    chat_container = st.sidebar.container(height=350)
    
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if chat_input := st.sidebar.chat_input("이 뉴스에 대해 질문하세요"):
        st.session_state.messages.append({"role": "user", "content": chat_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(chat_input)

            with st.chat_message("assistant"):
                # 생성된 리포트 내용을 바탕으로 답변 (Context Awareness)
                chat_prompt = f"리포트: {st.session_state.last_report}\n질문: {chat_input}\n전문가로서 리포트 기반의 답변을 해줘."
                chat_res = model.generate_content(chat_prompt)
                st.markdown(chat_res.text)
                st.session_state.messages.append({"role": "assistant", "content": chat_res.text})
else:
    st.sidebar.info("브리핑을 생성하면 AI와 대화할 수 있습니다.")
