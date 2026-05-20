import streamlit as st
import pandas as pd

st.set_page_config(page_title="TOPS AI PoC", layout="wide")
st.title("TOPS 직매입 운영 분석 대시보드")

st.sidebar.header("데이터 업로드")

inventory_file = st.sidebar.file_uploader("재고 파일", type=["xlsx"])
summary_file = st.sidebar.file_uploader("총괄장", type=["xlsx"])
sales_file = st.sidebar.file_uploader("판매리스트", type=["xlsx"])

def find_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

if inventory_file and summary_file and sales_file:
    inventory = pd.read_excel(inventory_file, engine="openpyxl")
    summary = pd.read_excel(summary_file, engine="openpyxl")
    sales = pd.read_excel(sales_file, engine="openpyxl")

    inventory.columns = inventory.columns.astype(str).str.strip()
    summary.columns = summary.columns.astype(str).str.strip()
    sales.columns = sales.columns.astype(str).str.strip()

    st.success("파일 업로드 완료")

    stock_col = find_col(inventory, ["재고", "현재고", "재고수량", "수량", "stock_qty", "누계총재고"])
    sales_col = find_col(summary, ["누계판매", "판매수량", "누계판매수량", "cum_sales_qty"])

    total_stock = inventory[stock_col].sum() if stock_col else 0
    total_sales = summary[sales_col].sum() if sales_col else 0

    sell_through = (
        total_sales / (total_sales + total_stock) * 100
        if (total_sales + total_stock) > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("시즌 진행률", "42%")
    col2.metric("실제 판매율", f"{sell_through:.1f}%")
    col3.metric("기대 판매율", "25%")
    col4.metric("총 재고", f"{int(total_stock):,}")

    st.divider()

    st.subheader("인식된 컬럼")
    st.write("재고 수량 컬럼:", stock_col if stock_col else "인식 실패")
    st.write("판매 수량 컬럼:", sales_col if sales_col else "인식 실패")

    st.divider()

    st.subheader("상품 분석")

    display_cols = [
        "스타일코드",
        "스타일명",
        "카테고리",
        "브랜드",
        "시즌",
        "누계판매",
        "누계총재고",
        "현재고",
        "재고수량",
    ]
    display_cols = [c for c in display_cols if c in summary.columns]

    if display_cols:
        st.dataframe(summary[display_cols].head(100), use_container_width=True)
    else:
        st.dataframe(summary.head(100), use_container_width=True)

    st.divider()

    with st.expander("업로드 데이터 컬럼 확인"):
        st.write("재고 파일 컬럼")
        st.write(list(inventory.columns))

        st.write("총괄장 컬럼")
        st.write(list(summary.columns))

        st.write("판매리스트 컬럼")
        st.write(list(sales.columns))

else:
    st.info("좌측에서 재고 파일, 총괄장, 판매리스트 3개 파일을 업로드해주세요.")