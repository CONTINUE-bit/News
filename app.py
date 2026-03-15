import streamlit as st
import requests
import google.generativeai as genai

# 페이지 설정
st.set_page_config(page_title="AI 글로벌 뉴스 브리핑", page_icon="🌐", layout="wide")

# 보안 관리: st.secrets에서 키 로드
try:
    NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("보안 오류: API 키가 설정되지 않았습니다. .streamlit/secrets.toml 파일을 확인하세요.")
    st.stop()

# Gemini 2.5 Flash 설정 (지난 프로젝트의 안정성 반영)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 사이드바 구성
st.sidebar.header("⚙️ 브리핑 설정")

user_lang = st.sidebar.selectbox(
    "브리핑 언어",
    ["한국어", "English", "日本語", "Tiếng Việt"],
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

search_query = st.sidebar.text_input("상세 검색어 (선택 사항)", "")

# 메인 화면
st.title("🌐 AI 글로벌 뉴스 브리핑")
st.info(f"현재 설정: **{category.upper()}** 뉴스 | **{user_lang}** 리포트")

if st.sidebar.button("브리핑 생성 시작"):
    with st.spinner('글로벌 데이터를 수집하고 분석 중입니다...'):
        
        # NewsAPI 호출 (글로벌 데이터 확보를 위해 영어로 수집)
        base_url = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": category,
            "q": search_query,
            "language": "en", 
            "pageSize": 10,
            "apiKey": NEWS_API_KEY
        }
        
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if data.get("status") == "ok" and data.get("articles"):
                articles = data["articles"]
                
                # Gemini에게 전달할 데이터 구성
                context = ""
                for i, art in enumerate(articles):
                    title = art.get('title', '제목 없음')
                    desc = art.get('description', '설명 없음')
                    context += f"기사 {i+1}: {title}\n요약문: {desc}\n\n"

                # 프롬프트 설계
                prompt = f"""
                당신은 전문 뉴스 분석가입니다. 제공된 뉴스 리스트를 바탕으로 요약 리포트를 작성하세요.
                
                지침:
                1. 반드시 **{user_lang}**로 작성할 것.
                2. 기사를 나열하지 말고, 비슷한 주제끼리 묶어 3~4개의 핵심 이슈로 구조화할 것.
                3. 각 이슈마다 객관적인 분석을 포함할 것.
                4. 마지막에 '전체적인 시장 흐름에 대한 한 줄 평'을 작성할 것.

                뉴스 데이터:
                {context}
                """

                # Gemini 2.5 Flash 생성 결과
                result = model.generate_content(prompt)
                
                st.markdown("---")
                st.subheader(f"📊 실시간 {category} 이슈 브리핑")
                st.markdown(result.text)
                
                # 출처 링크
                with st.expander("🔗 수집된 뉴스 원문 링크 리스트"):
                    for art in articles:
                        st.write(f"- [{art['title']}]({art['url']})")
                        
            else:
                st.warning("관련 뉴스를 가져올 수 없습니다. 카테고리나 검색어를 확인해 주세요.")
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
else:
    st.write("왼쪽 설정 후 버튼을 누르면 AI가 리포트를 생성합니다.")
