import streamlit as st
import pandas as pd

st.set_page_config(page_title="TOPS AI PoC", layout="wide")
st.title("TOPS 직매입 운영 분석 대시보드")

# ======================
# 파일 업로드
# ======================

st.sidebar.header("데이터 업로드")

inventory_file = st.sidebar.file_uploader("재고 파일", type=["xlsx"])
summary_file = st.sidebar.file_uploader("총괄장", type=["xlsx"])
sales_file = st.sidebar.file_uploader("판매리스트", type=["xlsx"])

if inventory_file and summary_file and sales_file:

    inventory = pd.read_excel(inventory_file, engine="openpyxl")
    summary = pd.read_excel(summary_file, engine="openpyxl")
    sales = pd.read_excel(sales_file, engine="openpyxl")

    # 컬럼 공백 제거
    inventory.columns = inventory.columns.astype(str).str.strip()
    summary.columns = summary.columns.astype(str).str.strip()
    sales.columns = sales.columns.astype(str).str.strip()

    st.success("파일 업로드 완료")

    # ======================
    # 컬럼 선택 (핵심🔥)
    # ======================

    st.subheader("컬럼 매핑 (처음 한 번만 설정)")

    stock_col = st.selectbox(
        "재고 수량 컬럼 선택",
        options=list(inventory.columns)
    )

    sales_col = st.selectbox(
        "총괄장 판매 수량 컬럼 선택",
        options=list(summary.columns)
    )

    # ======================
    # KPI 계산
    # ======================

    total_stock = inventory[stock_col].sum()
    total_sales = summary[sales_col].sum()

    sell_through = (
        total_sales / (total_sales + total_stock) * 100
        if (total_sales + total_stock) > 0
        else 0
    )

    season_progress = 42
    expected_rate = 25

    # ======================
    # KPI 카드
    # ======================

    st.subheader("핵심 KPI")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("시즌 진행률", f"{season_progress}%")
    col2.metric("실제 판매율", f"{sell_through:.1f}%")
    col3.metric("기대 판매율", f"{expected_rate}%")
    col4.metric("총 재고", f"{int(total_stock):,}")

    st.divider()

    # ======================
    # 카테고리 분석
    # ======================

    st.subheader("카테고리별 판매")

    if "카테고리" in summary.columns:
        category_sales = summary.groupby("카테고리")[sales_col].sum()
        st.bar_chart(category_sales)
    else:
        st.warning("카테고리 컬럼이 없습니다")

    st.divider()

    # ======================
    # 상품 분석
    # ======================

    st.subheader("상품 분석")

    display_cols = [
        "스타일코드",
        "스타일명",
        "카테고리",
        "브랜드",
        "시즌",
        sales_col
    ]

    display_cols = [c for c in display_cols if c in summary.columns]

    if display_cols:
        st.dataframe(summary[display_cols].head(100), use_container_width=True)
    else:
        st.dataframe(summary.head(100), use_container_width=True)

    st.divider()

    # ======================
    # 원본 데이터 확인
    # ======================

    with st.expander("데이터 컬럼 확인 (문제 있을 때만 확인)"):
        st.write("재고 컬럼")
        st.write(list(inventory.columns))

        st.write("총괄장 컬럼")
        st.write(list(summary.columns))

        st.write("판매리스트 컬럼")
        st.write(list(sales.columns))

else:
    st.info("좌측에서 3개 파일을 업로드해주세요")