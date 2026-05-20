import streamlit as st
import pandas as pd

st.set_page_config(page_title="TOPS AI PoC", layout="wide")
st.title("TOPS 직매입 운영 분석 대시보드")

st.sidebar.header("데이터 업로드")

inventory_file = st.sidebar.file_uploader("재고 파일", type=["xlsx"])
summary_file = st.sidebar.file_uploader("총괄장", type=["xlsx"])
sales_file = st.sidebar.file_uploader("판매리스트", type=["xlsx"])


# ======================
# 유틸 함수
# ======================

def make_unique_columns(df):
    cols = []
    seen = {}
    for col in df.columns:
        col = str(col).strip()
        if col in seen:
            seen[col] += 1
            new_col = f"{col}_{seen[col]}"
        else:
            seen[col] = 0
            new_col = col
        cols.append(new_col)
    df.columns = cols
    return df


def find_col(df, candidates):
    for candidate in candidates:
        for col in df.columns:
            if candidate == col:
                return col
    for candidate in candidates:
        for col in df.columns:
            if candidate in col:
                return col
    return None


def to_number(series):
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .replace(["", "nan", "None"], "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


# ======================
# 실행
# ======================

if inventory_file and summary_file and sales_file:

    inventory = pd.read_excel(inventory_file, engine="openpyxl")
    summary = pd.read_excel(summary_file, engine="openpyxl")
    sales = pd.read_excel(sales_file, engine="openpyxl")

    inventory = make_unique_columns(inventory)
    summary = make_unique_columns(summary)
    sales = make_unique_columns(sales)

    st.success("파일 업로드 완료")

    # ======================
    # 컬럼 자동 매핑
    # ======================

    stock_col = find_col(inventory, ["재고", "수량", "현재고"])
    sales_col = find_col(summary, ["누계판매", "판매수량"])
    total_stock_col = find_col(summary, ["누계총재고", "현재고"])
    category_col = find_col(summary, ["아이템", "카테고리"])
    style_col = find_col(summary, ["스타일코드"])
    style_name_col = find_col(summary, ["스타일명"])
    brand_col = find_col(summary, ["서브브랜드명"])
    season_col = find_col(summary, ["시즌"])

    # ======================
    # 숫자 변환
    # ======================

    inventory[stock_col] = to_number(inventory[stock_col])
    summary[sales_col] = to_number(summary[sales_col])
    summary[total_stock_col] = to_number(summary[total_stock_col])

    # ======================
    # KPI
    # ======================

    total_sales = summary[sales_col].sum()
    total_stock = summary[total_stock_col].sum()

    sell_through = (
        total_sales / (total_sales + total_stock) * 100
        if (total_sales + total_stock) > 0 else 0
    )

    st.subheader("핵심 KPI")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("실제 판매율", f"{sell_through:.1f}%")
    c2.metric("총 판매수량", f"{int(total_sales):,}")
    c3.metric("총 재고", f"{int(total_stock):,}")
    c4.metric("상품 수", f"{summary.shape[0]}")

    st.divider()

    # ======================
    # 카테고리 총판매율
    # ======================

    st.subheader("카테고리별 총판매율")

    if category_col:
        cat = summary.groupby(category_col).agg({
            sales_col: "sum",
            total_stock_col: "sum"
        }).reset_index()

        cat["총판매율"] = cat.apply(
            lambda x: x[sales_col] / (x[sales_col] + x[total_stock_col]) * 100
            if (x[sales_col] + x[total_stock_col]) > 0 else 0,
            axis=1
        ).round(1)

        st.dataframe(cat, use_container_width=True)
        st.bar_chart(cat.set_index(category_col)["총판매율"])

    st.divider()

    # ======================
    # 진도율 + 액션 추천
    # ======================

    st.subheader("문제 상품 + 액션 추천")

    df = summary.copy()

    df["판매"] = summary[sales_col]
    df["재고"] = summary[total_stock_col]

    # 🔥 기준값 (변경 가능)
    category_target = {
        "잡화": 60,
        "의류": 60,
        "슈즈": 50
    }

    SEASON_TOTAL = 7
    WARNING_THRESHOLD = 0.8
    CLEARANCE_THRESHOLD = 80

    # 임시 경과개월 (나중에 자동화)
    df["경과개월"] = 2

    # 목표 매핑
    if category_col:
        df["목표판매율"] = df[category_col].map(category_target).fillna(60)
    else:
        df["목표판매율"] = 60

    # 집계
    group_dict = {"판매": "sum", "재고": "sum"}

    if style_name_col:
        group_dict[style_name_col] = "first"
    if category_col:
        group_dict[category_col] = "first"
    if brand_col:
        group_dict[brand_col] = "first"

    agg = df.groupby(style_col).agg(group_dict).reset_index()

    # 판매율
    agg["총판매율"] = agg.apply(
        lambda x: x["판매"] / (x["판매"] + x["재고"]) * 100
        if (x["판매"] + x["재고"]) > 0 else 0,
        axis=1
    ).round(1)

    # 기대 판매율
    agg["목표판매율"] = agg[category_col].map(category_target).fillna(60)
    agg["경과개월"] = 2
    agg["기대판매율"] = agg["목표판매율"] * (agg["경과개월"] / SEASON_TOTAL)

    # 상태 + 액션
    def classify(row):
        actual = row["총판매율"]
        expected = row["기대판매율"]

        if row["경과개월"] <= SEASON_TOTAL:
            if actual < expected * WARNING_THRESHOLD:
                return "🔴 시즌부진", "점출"
            elif actual < expected:
                return "🟡 주의", "관찰"
            else:
                return "🔵 정상", "유지"
        else:
            if actual < CLEARANCE_THRESHOLD:
                return "🔴 체화위험", "할인"
            elif actual < 90:
                return "🟡 잔여재고", "관찰"
            else:
                return "🔵 정상", "유지"

    agg[["상태", "추천액션"]] = agg.apply(lambda x: pd.Series(classify(x)), axis=1)

    result = agg.sort_values("총판매율").head(20)

    st.dataframe(result, use_container_width=True)

    st.divider()

    # ======================
    # 상품 테이블
    # ======================

    st.subheader("상품 분석")

    preferred_cols = [
        "서브브랜드명",
        "스타일코드",
        "스타일명",
        "색상",
        "사이즈",
        "현재고",
        "누계판매",
        "누계총재고"
    ]

    visible_cols = [c for c in preferred_cols if c in summary.columns]

    st.dataframe(summary[visible_cols].head(100), use_container_width=True)

else:
    st.info("좌측에서 3개 파일을 업로드해주세요")