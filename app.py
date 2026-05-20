import streamlit as st
import pandas as pd

st.set_page_config(page_title="TOPS AI PoC", layout="wide")
st.title("TOPS 직매입 운영 분석 대시보드")

st.sidebar.header("데이터 업로드")

inventory_file = st.sidebar.file_uploader("재고 파일", type=["xlsx"])
summary_file = st.sidebar.file_uploader("총괄장", type=["xlsx"])
sales_file = st.sidebar.file_uploader("판매리스트", type=["xlsx"])

# 컬럼 중복 제거 함수 (핵심🔥)
def make_unique_columns(df):
    cols = []
    for i, col in enumerate(df.columns):
        if col in cols:
            col = f"{col}_{i}"
        cols.append(col)
    df.columns = cols
    return df

if inventory_file and summary_file and sales_file:

    inventory = pd.read_excel(inventory_file, engine="openpyxl")
    summary = pd.read_excel(summary_file, engine="openpyxl")
    sales = pd.read_excel(sales_file, engine="openpyxl")

    # 컬럼 정리
    inventory.columns = inventory.columns.astype(str).str.strip()
    summary.columns = summary.columns.astype(str).str.strip()
    sales.columns = sales.columns.astype(str).str.strip()

    # 🔥 중복 컬럼 해결
    inventory = make_unique_columns(inventory)
    summary = make_unique_columns(summary)
    sales = make_unique_columns(sales)

    st.success("파일 업로드 완료")

    # ======================
    # 컬럼 선택
    # ======================

    st.subheader("컬럼 매핑")

    stock_col = st.selectbox(
        "재고 수량 컬럼 선택",
        options=list(inventory.columns)
    )

    sales_col = st.selectbox(
        "판매 수량 컬럼 선택",
        options=list(summary.columns)
    )

    # 숫자 변환
    inventory[stock_col] = pd.to_numeric(inventory[stock_col], errors='coerce').fillna(0)
    summary[sales_col] = pd.to_numeric(summary[sales_col], errors='coerce').fillna(0)

    # KPI
    total_stock = inventory[stock_col].sum()
    total_sales = summary[sales_col].sum()

    if (total_sales + total_stock) > 0:
        sell_through = (total_sales / (total_sales + total_stock)) * 100
    else:
        sell_through = 0

    # KPI 카드
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("시즌 진행률", "42%")
    col2.metric("실제 판매율", f"{sell_through:.1f}%")
    col3.metric("기대 판매율", "25%")
    col4.metric("총 재고", f"{int(total_stock):,}")

    st.divider()

    # 상품 분석 (이제 에러 안 남🔥)
    st.subheader("상품 분석")
    st.dataframe(summary.head(100), use_container_width=True)

else:
    st.info("좌측에서 3개 파일을 업로드해주세요")