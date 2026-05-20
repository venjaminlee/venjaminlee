import streamlit as st
import pandas as pd

st.set_page_config(page_title="TOPS AI PoC", layout="wide")
st.title("TOPS 직매입 운영 분석 대시보드")

st.sidebar.header("데이터 업로드")

inventory_file = st.sidebar.file_uploader("재고 파일", type=["xlsx"])
summary_file = st.sidebar.file_uploader("총괄장", type=["xlsx"])
sales_file = st.sidebar.file_uploader("판매리스트", type=["xlsx"])


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


if inventory_file and summary_file and sales_file:

    inventory = pd.read_excel(inventory_file, engine="openpyxl")
    summary = pd.read_excel(summary_file, engine="openpyxl")
    sales = pd.read_excel(sales_file, engine="openpyxl")

    inventory = make_unique_columns(inventory)
    summary = make_unique_columns(summary)
    sales = make_unique_columns(sales)

    st.success("파일 업로드 완료")

    stock_col = find_col(
        inventory,
        ["현재고", "재고수량", "재고", "수량", "누계총재고", "총재고", "stock_qty"]
    )

    sales_col = find_col(
        summary,
        ["누계판매", "누계판매수량", "판매수량", "기간판매", "cum_sales_qty"]
    )

    category_col = find_col(
        summary,
        ["카테고리", "아이템", "품목", "세분류"]
    )

    style_col = find_col(
        summary,
        ["스타일코드"]
    )

    style_name_col = find_col(
        summary,
        ["스타일명", "상품명"]
    )

    with st.expander("컬럼 매핑 확인 / 수정", expanded=False):
        st.write("자동 인식된 재고 수량 컬럼:", stock_col if stock_col else "인식 실패")
        st.write("자동 인식된 판매 수량 컬럼:", sales_col if sales_col else "인식 실패")
        st.write("자동 인식된 카테고리 컬럼:", category_col if category_col else "인식 실패")
        st.write("자동 인식된 스타일코드 컬럼:", style_col if style_col else "인식 실패")

        if stock_col is None:
            stock_col = st.selectbox("재고 수량 컬럼 선택", options=list(inventory.columns))

        if sales_col is None:
            sales_col = st.selectbox("판매 수량 컬럼 선택", options=list(summary.columns))

        if category_col is None:
            category_col = st.selectbox("카테고리 컬럼 선택", options=["선택 안 함"] + list(summary.columns))
            if category_col == "선택 안 함":
                category_col = None

        if style_col is None:
            style_col = st.selectbox("스타일코드 컬럼 선택", options=list(summary.columns))

    inventory[stock_col] = to_number(inventory[stock_col])
    summary[sales_col] = to_number(summary[sales_col])

    total_stock = inventory[stock_col].sum()
    total_sales = summary[sales_col].sum()

    sell_through = (
        total_sales / (total_sales + total_stock) * 100
        if (total_sales + total_stock) > 0
        else 0
    )

    season_progress = 42
    expected_rate = 25

    st.subheader("핵심 KPI")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("시즌 진행률", f"{season_progress}%")
    col2.metric("실제 판매율", f"{sell_through:.1f}%")
    col3.metric("기대 판매율", f"{expected_rate}%")
    col4.metric("총 재고", f"{int(total_stock):,}")

    st.divider()

    st.subheader("카테고리별 판매")

    if category_col:
        category_sales = summary.groupby(category_col)[sales_col].sum().sort_values(ascending=False)
        st.bar_chart(category_sales)
    else:
        st.warning("카테고리 컬럼을 인식하지 못했습니다.")

    st.divider()

    st.subheader("문제 상품 TOP 10")

    if style_col:
        df = summary.copy()

        df["판매"] = to_number(df[sales_col])

        stock_in_summary_col = find_col(
            summary,
            ["현재고", "누계총재고", "총재고", "재고수량", "재고"]
        )

        if stock_in_summary_col:
            df["재고"] = to_number(df[stock_in_summary_col])
        else:
            df["재고"] = 0

        group_dict = {
            "판매": "sum",
            "재고": "sum"
        }

        if style_name_col:
            group_dict[style_name_col] = "first"

        if category_col:
            group_dict[category_col] = "first"

        top_df = df.groupby(style_col).agg(group_dict).reset_index()

        top_df["판매율"] = top_df.apply(
            lambda x: x["판매"] / (x["판매"] + x["재고"]) * 100
            if (x["판매"] + x["재고"]) > 0 else 0,
            axis=1
        )

        def risk_level(rate):
            if rate < 30:
                return "🔴 상"
            elif rate < 60:
                return "🟡 중"
            else:
                return "🔵 하"

        top_df["위험도"] = top_df["판매율"].apply(risk_level)
        top_df["판매율"] = top_df["판매율"].round(1)

        top10 = top_df.sort_values("판매율").head(10)

        st.dataframe(top10, use_container_width=True)
    else:
        st.warning("스타일코드 컬럼을 찾지 못했습니다.")

    st.divider()

    st.subheader("상품 분석")

    preferred_cols = [
        "브랜드코드",
        "서브브랜드명",
        "스타일코드",
        "스타일명",
        "색상",
        "사이즈",
        "PLU",
        "현판가",
        "현재고",
        "누계판매",
        "기간판매",
        "누계총재고",
    ]

    visible_cols = []
    for col in preferred_cols:
        matched_col = find_col(summary, [col])
        if matched_col and matched_col not in visible_cols:
            visible_cols.append(matched_col)

    if sales_col not in visible_cols:
        visible_cols.append(sales_col)

    if visible_cols:
        st.dataframe(summary[visible_cols].head(100), use_container_width=True)
    else:
        st.dataframe(summary.head(100), use_container_width=True)

    st.divider()

    with st.expander("원본 데이터 컬럼 확인"):
        st.write("재고 파일 컬럼")
        st.write(list(inventory.columns))

        st.write("총괄장 컬럼")
        st.write(list(summary.columns))

        st.write("판매리스트 컬럼")
        st.write(list(sales.columns))

else:
    st.info("좌측에서 재고 파일, 총괄장, 판매리스트 3개 파일을 업로드해주세요.")