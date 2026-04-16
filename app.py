import streamlit as st
import pandas as pd

st.set_page_config(page_title="단품 데이터 관리 툴", layout="wide")

st.title("📊 단품 데이터 통합 분석 툴")

# -------------------------------
# 1. 파일 업로드
# -------------------------------
st.header("1. 데이터 업로드")

col1, col2 = st.columns(2)

with col1:
    stock_file = st.file_uploader("📦 재고 데이터 업로드", type=["xlsx"])

with col2:
    sales_file = st.file_uploader("💰 매출 데이터 업로드", type=["xlsx"])

if stock_file and sales_file:
    stock_df = pd.read_excel(stock_file)
    sales_df = pd.read_excel(sales_file)

    st.success("데이터 업로드 완료")

    # -------------------------------
    # 2. 데이터 처리
    # -------------------------------
    merged = pd.merge(
        stock_df,
        sales_df,
        on=["상품코드", "매장코드"],
        how="left"
    )

    merged["판매수량"] = merged["판매수량"].fillna(0)

    summary = merged.groupby(
        ["상품코드", "상품명", "브랜드", "카테고리"],
        as_index=False
    ).agg({
        "판매수량": "sum",
        "재고수량": "sum"
    })

    # -------------------------------
    # 3. KPI 계산
    # -------------------------------
    summary["판매율"] = summary["판매수량"] / (
        summary["판매수량"] + summary["재고수량"]
    )

    # 간단 원가회수율 (추정)
    summary["원가회수율"] = summary["판매율"] * 1.5

    # -------------------------------
    # 4. KPI 표시
    # -------------------------------
    st.header("2. KPI")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("총 상품 수", len(summary))
    col2.metric("총 재고", int(summary["재고수량"].sum()))
    col3.metric("평균 판매율", f"{summary['판매율'].mean():.2%}")
    col4.metric("평균 회수율", f"{summary['원가회수율'].mean():.2%}")

    # -------------------------------
    # 5. 문제 상품 필터링
    # -------------------------------
    st.header("3. 문제 상품")

    problem = summary[summary["판매율"] < 0.4].copy()

    st.write(f"⚠ 문제 상품 수: {len(problem)}")
    st.dataframe(problem, use_container_width=True)

    # -------------------------------
    # 6. 액션 추천
    # -------------------------------
    st.header("4. 액션 추천")

    def recommend(row):
        if row["판매율"] < 0.3 and row["재고수량"] > 50:
            return "🔥 할인 필요 (30%)"
        elif row["판매율"] < 0.4:
            return "📦 점출 필요"
        elif row["판매율"] > 0.7:
            return "📥 점입 필요"
        else:
            return "✅ 정상"

    summary["추천액션"] = summary.apply(recommend, axis=1)

    st.dataframe(
        summary[["상품명", "판매율", "재고수량", "추천액션"]],
        use_container_width=True
    )

    # -------------------------------
    # 7. 카테고리 분석
    # -------------------------------
    st.header("5. 카테고리 분석")

    category = summary.groupby("카테고리", as_index=False).agg({
        "판매율": "mean",
        "재고수량": "sum"
    })

    st.bar_chart(category.set_index("카테고리")["판매율"])

    # -------------------------------
    # 8. 매장 이동 추천 기초 데이터
    # -------------------------------
    st.header("6. 점출/점입 추천")

    store_summary = merged.groupby(["상품코드", "매장코드"], as_index=False).agg({
        "판매수량": "sum",
        "재고수량": "sum"
    })

    store_summary["일판매량"] = store_summary["판매수량"] / 7
    store_summary["재고일수"] = store_summary["재고수량"] / (
        store_summary["일판매량"] + 0.01
    )

    st.dataframe(store_summary, use_container_width=True)

else:
    st.info("재고 데이터와 매출 데이터를 업로드해주세요.")
