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

    st.success("파일 업로드 완료")

    # ======================
    # KPI 계산
    # ======================

    total_stock = inventory["재고"].sum()
    total_sales = summary["누계판매"].sum()

    sell_through = (total_sales / (total_sales + total_stock)) * 100 if (total_sales + total_stock) > 0 else 0

    season_progress = 42
    expected_rate = 25

    # ======================
    # KPI 카드
    # ======================

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("시즌 진행률", f"{season_progress}%")
    col2.metric("실제 판매율", f"{sell_through:.1f}%")
    col3.metric("기대 판매율", f"{expected_rate}%")
    col4.metric("총 재고", f"{int(total_stock):,}")

    st.divider()

    # ======================
    # 카테고리별 판매
    # ======================

    st.subheader("카테고리별 판매")

    if "카테고리" in summary.columns and "누계판매" in summary.columns:
        category_sales = summary.groupby("카테고리")["누계판매"].sum()
        st.bar_chart(category_sales)
    else:
        st.warning("총괄장에 '카테고리' 또는 '누계판매' 컬럼이 없습니다.")

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
        "누계판매",
        "누계총재고",
    ]

    display_cols = [col for col in display_cols if col in summary.columns]

    if display_cols:
        st.dataframe(summary[display_cols].head(100), use_container_width=True)
    else:
        st.warning("표시할 수 있는 상품 분석 컬럼이 없습니다.")

    st.divider()

    # ======================
    # 원본 데이터 확인
    # ======================

    with st.expander("업로드 데이터 미리보기"):
        st.write("재고 파일")
        st.dataframe(inventory.head(), use_container_width=True)

        st.write("총괄장")
        st.dataframe(summary.head(), use_container_width=True)

        st.write("판매리스트")
        st.dataframe(sales.head(), use_container_width=True)

else:
    st.info("좌측에서 재고 파일, 총괄장, 판매리스트 3개 파일을 업로드해주세요.")