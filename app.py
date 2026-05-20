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


def risk_level(rate):
    if rate < 30:
        return "🔴 위험"
    elif rate < 60:
        return "🟡 주의"
    return "🔵 정상"


if inventory_file and summary_file and sales_file:

    inventory = pd.read_excel(inventory_file, engine="openpyxl")
    summary = pd.read_excel(summary_file, engine="openpyxl")
    sales = pd.read_excel(sales_file, engine="openpyxl")

    inventory = make_unique_columns(inventory)
    summary = make_unique_columns(summary)
    sales = make_unique_columns(sales)

    st.success("파일 업로드 완료")

    stock_col = find_col(inventory, ["현재고", "재고수량", "재고", "수량", "누계총재고", "총재고"])
    sales_col = find_col(summary, ["누계판매", "누계판매수량", "판매수량", "기간판매"])
    total_stock_col = find_col(summary, ["누계총재고", "총재고", "현재고", "재고"])
    category_col = find_col(summary, ["아이템", "카테고리", "품목", "세분류"])
    style_col = find_col(summary, ["스타일코드"])
    style_name_col = find_col(summary, ["스타일명", "상품명"])
    brand_col = find_col(summary, ["서브브랜드명", "브랜드명", "브랜드"])
    season_col = find_col(summary, ["시즌"])
    store_col = find_col(sales, ["점포명", "매장명", "점포"])
    sales_amt_col = find_col(sales, ["판매금액", "실판매금액", "매출금액", "총판매가"])

    with st.expander("컬럼 매핑 확인 / 수정", expanded=False):
        st.write("재고 수량:", stock_col)
        st.write("판매 수량:", sales_col)
        st.write("총재고:", total_stock_col)
        st.write("카테고리:", category_col)
        st.write("스타일코드:", style_col)
        st.write("브랜드:", brand_col)
        st.write("판매리스트 점포:", store_col)
        st.write("판매리스트 매출:", sales_amt_col)

        if stock_col is None:
            stock_col = st.selectbox("재고 수량 컬럼 선택", list(inventory.columns))
        if sales_col is None:
            sales_col = st.selectbox("판매 수량 컬럼 선택", list(summary.columns))
        if total_stock_col is None:
            total_stock_col = st.selectbox("총재고 컬럼 선택", list(summary.columns))
        if category_col is None:
            category_col = st.selectbox("카테고리 컬럼 선택", ["선택 안 함"] + list(summary.columns))
            if category_col == "선택 안 함":
                category_col = None

    inventory[stock_col] = to_number(inventory[stock_col])
    summary[sales_col] = to_number(summary[sales_col])
    summary[total_stock_col] = to_number(summary[total_stock_col])

    if sales_amt_col:
        sales[sales_amt_col] = to_number(sales[sales_amt_col])

    total_sales = summary[sales_col].sum()
    total_stock = summary[total_stock_col].sum()
    sell_through = total_sales / (total_sales + total_stock) * 100 if (total_sales + total_stock) > 0 else 0

    season_progress = 42
    expected_rate = 25

    st.subheader("핵심 KPI")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("시즌 진행률", f"{season_progress}%")
    c2.metric("실제 판매율", f"{sell_through:.1f}%")
    c3.metric("기대 판매율", f"{expected_rate}%")
    c4.metric("총 재고", f"{int(total_stock):,}")

    st.divider()

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
        )

        cat["총판매율"] = cat["총판매율"].round(1)
        cat["재고구성비"] = (cat[total_stock_col] / cat[total_stock_col].sum() * 100).round(1)
        cat["판매구성비"] = (cat[sales_col] / cat[sales_col].sum() * 100).round(1)

        st.dataframe(cat, use_container_width=True)
        st.bar_chart(cat.set_index(category_col)["총판매율"])
    else:
        st.warning("카테고리 컬럼을 인식하지 못했습니다.")

    st.divider()

    st.subheader("시즌 상태 구분")

    if season_col:
        def season_status(x):
            x = str(x)
            if "25" in x:
                return "시즌 상품"
            elif "24" in x:
                return "시즌 경과 상품"
            return "시즌 종료 상품"

        summary["시즌상태"] = summary[season_col].apply(season_status)

        season_table = summary.groupby("시즌상태").agg({
            sales_col: "sum",
            total_stock_col: "sum"
        }).reset_index()

        season_table["총판매율"] = season_table.apply(
            lambda x: x[sales_col] / (x[sales_col] + x[total_stock_col]) * 100
            if (x[sales_col] + x[total_stock_col]) > 0 else 0,
            axis=1
        ).round(1)

        st.dataframe(season_table, use_container_width=True)
    else:
        st.warning("시즌 컬럼을 인식하지 못했습니다.")

    st.divider()

    st.subheader("점포별 월평균 매출")

    if store_col and sales_amt_col:
        store_sales = sales.groupby(store_col)[sales_amt_col].sum().reset_index()
        store_sales["월평균매출"] = (store_sales[sales_amt_col] / 3).round(0)
        store_sales = store_sales.sort_values("월평균매출", ascending=False)
        st.dataframe(store_sales.head(20), use_container_width=True)
        st.bar_chart(store_sales.set_index(store_col)["월평균매출"].head(20))
    else:
        st.info("판매리스트에서 점포명 또는 매출 컬럼을 찾지 못했습니다.")

    st.divider()

    st.subheader("문제 상품 TOP 10")

    df = summary.copy()
    df["판매"] = to_number(df[sales_col])
    df["재고"] = to_number(df[total_stock_col])

    group_dict = {"판매": "sum", "재고": "sum"}

    if style_name_col:
        group_dict[style_name_col] = "first"
    if category_col:
        group_dict[category_col] = "first"
    if brand_col:
        group_dict[brand_col] = "first"
    if season_col:
        group_dict[season_col] = "first"

    top_df = df.groupby(style_col).agg(group_dict).reset_index()

    top_df["총판매율"] = top_df.apply(
        lambda x: x["판매"] / (x["판매"] + x["재고"]) * 100
        if (x["판매"] + x["재고"]) > 0 else 0,
        axis=1
    )

    top_df["총판매율"] = top_df["총판매율"].round(1)
    top_df["위험도"] = top_df["총판매율"].apply(risk_level)

    top10 = top_df.sort_values("총판매율").head(10)
    st.dataframe(top10, use_container_width=True)

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
        "기간판매",
        "누계판매",
        "누계총재고",
        "시즌상태"
    ]

    visible_cols = []
    for col in preferred_cols:
        matched = find_col(summary, [col])
        if matched and matched not in visible_cols:
            visible_cols.append(matched)

    if "시즌상태" in summary.columns and "시즌상태" not in visible_cols:
        visible_cols.append("시즌상태")

    st.dataframe(summary[visible_cols].head(100), use_container_width=True)

else:
    st.info("좌측에서 재고 파일, 총괄장, 판매리스트 3개 파일을 업로드해주세요.")