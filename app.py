import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from typing import Optional

# ── 페이지 설정 ─────────────────────────
st.set_page_config(
    page_title="단품 관리 간소화 툴",
    page_icon="📦",
    layout="wide",
)

# ── 샘플 데이터 ─────────────────────────
@st.cache_data
def generate_sample_data():
    np.random.seed(42)
    brands = ["Nike", "Adidas", "New Balance", "Puma", "Reebok"]
    cats = ["상의", "하의", "아우터", "신발", "악세서리"]
    stores = ["강남점", "홍대점", "잠실점", "신촌점", "명동점"]

    rows = []
    for i in range(50):
        stock = np.random.randint(10, 120)
        sold = np.random.randint(1, 60)

        rows.append({
            "상품코드": f"SKU-{i}",
            "상품명": f"{np.random.choice(brands)} 상품{i}",
            "브랜드": np.random.choice(brands),
            "카테고리": np.random.choice(cats),
            "매장": np.random.choice(stores),
            "재고수량": stock,
            "판매수량": sold,
            "판매율": round(sold / stock * 100, 1),
            "원가회수율": round(np.random.uniform(40, 120), 1),
        })

    return pd.DataFrame(rows)

# ── 파일 파싱 함수 ─────────────────────
def parse_uploaded_file(uploaded_file, kind: str) -> Optional[pd.DataFrame]:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"{kind} 파일 오류: {e}")
        return None

# ── 상태 초기화 ────────────────────────
if "df" not in st.session_state:
    st.session_state["df"] = None

# ── 사이드바 ─────────────────────────
st.sidebar.title("📦 단품 관리 툴")

use_sample = st.sidebar.toggle("샘플 데이터 사용")

if use_sample:
    st.session_state["df"] = generate_sample_data()

page = st.sidebar.radio(
    "메뉴",
    ["업로드", "대시보드", "문제상품", "액션추천"]
)

# ─────────────────────────────────────
# 1. 업로드
# ─────────────────────────────────────
if page == "업로드":
    st.title("📂 데이터 업로드")

    file = st.file_uploader("엑셀 업로드", type=["xlsx", "csv"])

    if file:
        df = parse_uploaded_file(file, "데이터")
        if df is not None:
            st.session_state["df"] = df
            st.success("업로드 완료")
            st.dataframe(df.head())

# 데이터 없으면 stop
if st.session_state["df"] is None:
    st.info("데이터를 업로드하거나 샘플 데이터를 사용하세요")
    st.stop()

df = st.session_state["df"]

# ─────────────────────────────────────
# 2. 대시보드
# ─────────────────────────────────────
if page == "대시보드":
    st.title("📊 대시보드")

    col1, col2, col3 = st.columns(3)

    col1.metric("총 상품 수", len(df))
    col2.metric("총 재고", int(df["재고수량"].sum()))
    col3.metric("평균 판매율", f"{df['판매율'].mean():.1f}%")

    st.subheader("카테고리 판매율")

    cat = df.groupby("카테고리")["판매율"].mean()
    st.bar_chart(cat)

# ─────────────────────────────────────
# 3. 문제 상품
# ─────────────────────────────────────
if page == "문제상품":
    st.title("⚠ 문제 상품")

    threshold = st.slider("판매율 기준", 0, 100, 30)

    problem = df[df["판매율"] < threshold]

    st.write(f"{len(problem)}개 상품")

    st.dataframe(problem)

# ─────────────────────────────────────
# 4. 액션 추천
# ─────────────────────────────────────
if page == "액션추천":
    st.title("🔥 액션 추천")

    def action(row):
        if row["판매율"] < 20:
            return "🔥 할인"
        elif row["판매율"] < 40:
            return "📦 점출"
        else:
            return "✅ 정상"

    df["추천액션"] = df.apply(action, axis=1)

    st.dataframe(df[["상품명", "판매율", "재고수량", "추천액션"]])
