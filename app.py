import plotly.express as px
import streamlit as st
import pandas as pd

st.set_page_config(page_title="TOPS AI PoC", layout="wide")

st.markdown("""
<style>
.block-container {
    padding-top: 0.8rem;
    padding-bottom: 0.8rem;
    max-width: 100% !important;
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
}
h1 { font-size: 18px !important; margin-bottom: 0.3rem !important; }
h2, h3 { font-size: 13px !important; margin-top: 0.5rem !important; }
div[data-testid="stMetricValue"] { font-size: 14px !important; }
div[data-testid="stMetricLabel"] { font-size: 9px !important; }
section[data-testid="stSidebar"] { width: 140px !important; }
section[data-testid="stSidebar"] * { font-size: 9px !important; }
div[data-testid="stDataFrame"] { font-size: 8px !important; }
hr { margin: 0.7rem 0 !important; }
.small-note {
    font-size: 10px;
    color: #6b7280;
    margin-top: -4px;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="padding: 8px 0 14px 0;">
    <h1 style="font-size:18px; margin-bottom:4px;">
        TOPS AI 재고 운영 의사결정 시스템
    </h1>
    <div style="font-size:10px; color:#4b5563;">
        판매율과 재고를 기반으로 우선 조치가 필요한 상품과 점포 액션을 자동 추천합니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("### 📂 데이터 업로드")

with st.expander("재고 / 총괄장 / 판매리스트 파일 업로드", expanded=True):
    upload_col1, upload_col2, upload_col3 = st.columns(3)

    with upload_col1:
        inventory_file = st.file_uploader("재고 파일", type=["xlsx"])

    with upload_col2:
        summary_file = st.file_uploader("총괄장", type=["xlsx"])

    with upload_col3:
        sales_file = st.file_uploader("판매리스트", type=["xlsx"])

with st.sidebar:
    st.markdown("## TOPS AI")
    selected_menu = st.radio(
        "메뉴",
        [
            "대시보드",
            "AI 우선 조치",
            "점출/점입 추천",
            "창고 출고배분",
            "상품 전체 진단"
        ],
        label_visibility="collapsed"
    )


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


def classify_action(row):
    actual = row["총판매율"]

    if actual < 40:
        return "🔴 판매부진", "점출/배분 검토"
    elif actual < 60:
        return "🟡 주의", "관찰"
    else:
        return "🔵 정상", "유지"


def diagnose_reason(row):
    if row["GAP"] < -10 and row["재고"] > row["판매"] * 2:
        return "목표 미달 + 재고 과다"
    elif row["GAP"] < -10:
        return "목표 대비 판매 부진"
    elif row["재고"] > row["판매"] * 3:
        return "재고 과다"
    elif row["총판매율"] < 30:
        return "판매 저조"
    elif row["경과개월"] > 7 and row["총판매율"] < 80:
        return "시즌 경과 체화 우려"
    else:
        return "정상 범위"


def format_number_cols(df):
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            if "율" in col or "비" in col or "GAP" in col:
                out[col] = out[col].round(0).astype(int)
            else:
                out[col] = out[col].round(0).astype(int)
    return out


if inventory_file and summary_file and sales_file:

    inventory = make_unique_columns(pd.read_excel(inventory_file, engine="openpyxl"))
    summary = make_unique_columns(pd.read_excel(summary_file, engine="openpyxl"))
    sales = make_unique_columns(pd.read_excel(sales_file, engine="openpyxl"))

    st.success("파일 업로드 완료")

    inv_style_col = find_col(inventory, ["스타일코드"])
    inv_store_col = find_col(inventory, ["점포명", "매장명", "점포"])
    inv_stock_col = find_col(inventory, ["현재고수량", "재고수량", "현재고", "재고", "수량"])
    inv_type_col = find_col(inventory, ["재고구분", "구분"])

    sales_style_col = find_col(sales, ["스타일코드"])
    sales_store_col = find_col(sales, ["점포명", "매장명", "점포"])
    sales_qty_col = find_col(sales, ["판매수량", "판매수량_1", "수량"])
    sales_amt_col = find_col(sales, ["실판매금액", "판매금액", "매출금액", "총판매"])

    sum_sales_col = find_col(summary, ["누계판매수량", "누계판매", "판매수량"])
    sum_stock_col = find_col(summary, ["누계총재고수량", "누계총재고", "현재고", "재고"])
    category_col = find_col(summary, ["아이템", "카테고리", "품목"])
    style_col = find_col(summary, ["스타일코드"])
    style_name_col = find_col(summary, ["스타일명", "상품명"])
    brand_col = find_col(summary, ["서브브랜드명", "브랜드명"])
    season_col = find_col(summary, ["시즌"])

    with st.expander("컬럼 매핑 확인 / 수정", expanded=False):
        st.write("재고 스타일코드:", inv_style_col)
        st.write("재고 점포명:", inv_store_col)
        st.write("재고 수량:", inv_stock_col)
        st.write("재고 구분:", inv_type_col)
        st.write("판매 스타일코드:", sales_style_col)
        st.write("판매 점포명:", sales_store_col)
        st.write("판매 수량:", sales_qty_col)
        st.write("판매 금액:", sales_amt_col)
        st.write("총괄 판매:", sum_sales_col)
        st.write("총괄 재고:", sum_stock_col)
        st.write("카테고리:", category_col)
        st.write("스타일코드:", style_col)

    inventory[inv_stock_col] = to_number(inventory[inv_stock_col])
    summary[sum_sales_col] = to_number(summary[sum_sales_col])
    summary[sum_stock_col] = to_number(summary[sum_stock_col])

    if sales_qty_col:
        sales[sales_qty_col] = to_number(sales[sales_qty_col])
    if sales_amt_col:
        sales[sales_amt_col] = to_number(sales[sales_amt_col])

    total_sales = summary[sum_sales_col].sum()
    total_stock = summary[sum_stock_col].sum()
    product_count = summary[style_col].nunique() if style_col else summary.shape[0]

    sell_through = (
        total_sales / (total_sales + total_stock) * 100
        if (total_sales + total_stock) > 0 else 0
    )

    category_target = {
        "잡화": 60,
        "의류": 60,
        "슈즈": 50
    }

    df = summary.copy()
    df["판매"] = to_number(df[sum_sales_col])
    df["재고"] = to_number(df[sum_stock_col])

    group_dict = {"판매": "sum", "재고": "sum"}

    if style_name_col:
        group_dict[style_name_col] = "first"
    if category_col:
        group_dict[category_col] = "first"
    if brand_col:
        group_dict[brand_col] = "first"
    if season_col:
        group_dict[season_col] = "first"

    diagnosis = df.groupby(style_col).agg(group_dict).reset_index()

    diagnosis["총판매율"] = diagnosis.apply(
        lambda x: x["판매"] / (x["판매"] + x["재고"]) * 100
        if (x["판매"] + x["재고"]) > 0 else 0,
        axis=1
    ).round(1)

    if category_col:
        diagnosis["목표판매율"] = diagnosis[category_col].map(category_target).fillna(60)
    else:
        diagnosis["목표판매율"] = 60

    diagnosis["경과개월"] = 7
    diagnosis["기대판매율"] = (diagnosis["목표판매율"] * (diagnosis["경과개월"] / 7)).round(1)
    diagnosis["GAP"] = (diagnosis["총판매율"] - diagnosis["기대판매율"]).round(1)

    diagnosis[["상태", "추천액션"]] = diagnosis.apply(
        lambda x: pd.Series(classify_action(x)),
        axis=1
    )

    diagnosis["문제원인"] = diagnosis.apply(diagnose_reason, axis=1)

    # ======================
    # 필터
    # ======================

    st.sidebar.divider()
    st.sidebar.header("분석 필터")

    filter_df = diagnosis.copy()

    if category_col and category_col in diagnosis.columns:
        category_options = ["전체"] + sorted(diagnosis[category_col].dropna().astype(str).unique().tolist())
        selected_category = st.sidebar.selectbox("카테고리", category_options)

        if selected_category != "전체":
            filter_df = filter_df[filter_df[category_col].astype(str) == selected_category]

    if brand_col and brand_col in diagnosis.columns:
        brand_options = ["전체"] + sorted(filter_df[brand_col].dropna().astype(str).unique().tolist())
        selected_brand = st.sidebar.selectbox("브랜드", brand_options)

        if selected_brand != "전체":
            filter_df = filter_df[filter_df[brand_col].astype(str) == selected_brand]

    # ======================
    # KPI + AI 운영 진단
    # ======================

    risk_count = filter_df[
        filter_df["상태"].astype(str).str.contains("시즌부진|체화위험")
    ].shape[0]

    action_count = filter_df[
        filter_df["추천액션"].astype(str).str.contains("점출|할인|배분")
    ].shape[0]

    stock_bad = filter_df[
        filter_df["상태"].astype(str).str.contains("체화위험|판매부진")
    ].shape[0]

    target_rate = 60
    current_rate = sell_through
    achievement_rate = current_rate / target_rate
    gap_to_target = sell_through - target_rate

    st.subheader("핵심 KPI")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("판매율", f"{sell_through:.1f}%", f"{sell_through - target_rate:.1f}%p")
    c2.metric("관리 필요", f"{action_count:,}")
    c3.metric("최우선 관리", f"{risk_count:,}")
    c4.metric("체화 위험", f"{stock_bad:,}")
    c5.metric("관리 상품", f"{filter_df.shape[0]:,}")

    if gap_to_target >= 0:
        sales_comment = f"현재 판매율은 {sell_through:.1f}%로 목표 판매율 {target_rate}%를 달성했습니다."
    else:
        sales_comment = f"현재 판매율은 {sell_through:.1f}%로 목표 판매율 {target_rate}% 대비 {abs(gap_to_target):.1f}%p 부족합니다."

    if action_count > 0:
        action_comment = f"AI 분석 결과, 우선 점검이 필요한 상품은 {action_count}개입니다."
    else:
        action_comment = "AI 분석 결과, 즉시 조치가 필요한 상품은 없습니다."

    recommended_actions = []

    if action_count > 0:
        recommended_actions.append(f"① 관리 필요 상품 {action_count}개 우선 점검")

    if sell_through < target_rate:
        recommended_actions.append("② 판매 부진 상품 점출/배분 검토")

    if stock_bad > 0:
        recommended_actions.append(f"③ 체화 위험 상품 {stock_bad}개 모니터링")

    if len(recommended_actions) == 0:
        recommended_actions.append("현재 즉시 조치가 필요한 항목은 없습니다.")

    action_text = "\n".join(recommended_actions)

    st.info(
        f"🤖 AI 운영 진단\n\n"
        f"{sales_comment}\n\n"
        f"{action_comment}\n\n"
        f"AI 추천 액션\n"
        f"{action_text}"
    )

    review_reduction = (
        (1 - action_count / filter_df.shape[0]) * 100
        if filter_df.shape[0] > 0 else 0
    )

    st.success(
        f"⏱️ 업무 절감 효과\n\n"
        f"기존 {filter_df.shape[0]}개 상품 전수 검토 → "
        f"TOPS AI가 {action_count}개 관리 필요 상품 자동 선별\n\n"
        f"검토 대상 약 {review_reduction:.0f}% 감소"
    )

    st.progress(min(achievement_rate, 1.0))
    st.caption(
        f"목표 판매율 {target_rate}% 대비 현재 {current_rate:.1f}% 달성"
    )

    st.divider()
    # ======================
    # 상품 진단 TOP + 카테고리
    # ======================

    left, right = st.columns([1.2, 0.8])

    with left:
        st.subheader("AI 우선 조치 대상 상품")
        st.markdown("<div class='small-note'>목표 대비 부족폭이 큰 상품부터 우선 점검</div>", unsafe_allow_html=True)

        view_cols = []
        for col in [
            style_name_col,
            brand_col,
            "총판매율",
            "GAP",
            "상태",
            "추천액션"
        ]:
            if col and col in filter_df.columns and col not in view_cols:
                view_cols.append(col)

        diag_view = filter_df.sort_values("GAP").head(15)[view_cols]

        st.dataframe(
            format_number_cols(diag_view).style.map(
                lambda x: "color: red; font-weight: bold;" if isinstance(x, (int, float)) and x < 0 else "",
                subset=["GAP"]
            ),
            use_container_width=True,
            height=300
        )

    with right:
        st.subheader("카테고리별 운영 현황")
        st.markdown("<div class='small-note'>총판매율과 목표 대비 판단 중심</div>", unsafe_allow_html=True)

        if category_col:
            cat = summary.groupby(category_col).agg({
                sum_sales_col: "sum",
                sum_stock_col: "sum"
            }).reset_index()

            cat["총판매율"] = cat.apply(
                lambda x: x[sum_sales_col] / (x[sum_sales_col] + x[sum_stock_col]) * 100
                if (x[sum_sales_col] + x[sum_stock_col]) > 0 else 0,
                axis=1
            ).round(1)

            cat["목표판매율"] = cat[category_col].map(category_target).fillna(60)
            cat["GAP"] = (cat["총판매율"] - cat["목표판매율"]).round(1)
            cat["판단"] = cat.apply(
                lambda x: "정상" if x["총판매율"] >= x["목표판매율"] else "점검",
                axis=1
            )
            st.caption("카테고리별 실제 판매율과 목표 판매율 비교")
            st.bar_chart(
                cat.set_index(category_col)[["총판매율"]]
            )
            cat_view = cat[[category_col, "총판매율", "목표판매율", "GAP", "판단"]]
            st.dataframe(format_number_cols(cat_view), use_container_width=True, height=180)
#        st.subheader("카테고리별 판매 구성비")
#
#        if category_col:
#            pie_data = cat[[category_col, sum_sales_col]].copy()
#            pie_data.columns = ["카테고리", "판매수량"]
#
#            st.plotly_chart(
#                px.pie(
#                    pie_data,
#                    names="카테고리",
#                    values="판매수량",
#                    hole=0.45
#                ),
#                use_container_width=True
#        )
    st.divider()

    # ======================
    # 실행 추천 탭
    # ======================

    tab1, tab2, tab3 = st.tabs(["점출/점입 추천", "창고 출고배분", "상품 전체 진단"])

    with tab1:
        if inv_style_col and inv_store_col and sales_style_col and sales_store_col and sales_qty_col:

            store_stock = inventory.copy()
            store_sales = sales.copy()

            if inv_type_col:
                store_stock_only = store_stock[
                    ~store_stock[inv_type_col].astype(str).str.contains("창고", na=False)
                ].copy()
            else:
                store_stock_only = store_stock.copy()

            stock_by_store = store_stock_only.groupby(
                [inv_style_col, inv_store_col]
            )[inv_stock_col].sum().reset_index()

            sales_by_store = store_sales.groupby(
                [sales_style_col, sales_store_col]
            )[sales_qty_col].sum().reset_index()

            stock_by_store.columns = ["스타일코드", "점포명", "재고"]
            sales_by_store.columns = ["스타일코드", "점포명", "최근3개월판매"]

            store_perf = pd.merge(
                stock_by_store,
                sales_by_store,
                on=["스타일코드", "점포명"],
                how="left"
            )

            store_perf["최근3개월판매"] = store_perf["최근3개월판매"].fillna(0)

            recommendations = []

            for style in store_perf["스타일코드"].unique():
                temp = store_perf[store_perf["스타일코드"] == style].copy()

                if len(temp) < 2:
                    continue

                source = temp.sort_values(["재고", "최근3개월판매"], ascending=[False, True]).iloc[0]
                dest = temp.sort_values(["최근3개월판매", "재고"], ascending=[False, True]).iloc[0]

                if source["점포명"] == dest["점포명"]:
                    continue

                if source["재고"] >= 5 and dest["최근3개월판매"] > source["최근3개월판매"]:
                    qty = min(int(source["재고"] - 3), 5)

                    if qty > 0:
                        recommendations.append({
                            "스타일코드": style,
                            "재고과다점": source["점포명"],
                            "판매우수점": dest["점포명"],
                            "추천수량": qty,
                            "출발재고": int(source["재고"]),
                            "출발3개월판매": int(source["최근3개월판매"]),
                            "도착재고": int(dest["재고"]),
                            "도착3개월판매": int(dest["최근3개월판매"]),
                            "추천사유": "판매 저조 점포 과재고 → 판매 우수 점포 이동"
                        })

            rec_df = pd.DataFrame(recommendations)

            if not rec_df.empty:
                st.dataframe(rec_df.head(30), use_container_width=True, height=300)
            else:
                st.info("현재 조건에 해당하는 점출/점입 추천 항목이 없습니다.")
        else:
            st.info("점출 추천을 위해 재고/판매 파일의 스타일코드, 점포명, 판매수량 컬럼이 필요합니다.")

    with tab2:
        if inv_type_col and inv_style_col and sales_style_col and sales_store_col and sales_qty_col:

            warehouse = inventory[
                inventory[inv_type_col].astype(str).str.contains("창고", na=False)
            ].copy()

            if not warehouse.empty:
                wh_stock = warehouse.groupby(inv_style_col)[inv_stock_col].sum().reset_index()
                wh_stock.columns = ["스타일코드", "창고재고"]

                sales_rank = sales.groupby(
                    [sales_style_col, sales_store_col]
                )[sales_qty_col].sum().reset_index()

                sales_rank.columns = ["스타일코드", "추천점포", "최근3개월판매"]

                allocation = pd.merge(
                    wh_stock,
                    sales_rank,
                    on="스타일코드",
                    how="left"
                )

                allocation = allocation.sort_values(
                    ["창고재고", "최근3개월판매"],
                    ascending=[False, False]
                )

                allocation["추천수량"] = allocation.apply(
                    lambda x: min(int(x["창고재고"]), 5) if pd.notna(x["최근3개월판매"]) else 0,
                    axis=1
                )

                allocation["추천사유"] = "창고재고 보유 + 최근 판매 우수 점포 우선 배분"
                allocation = allocation[allocation["추천수량"] > 0]

                if not allocation.empty:
                    st.dataframe(allocation.head(30), use_container_width=True, height=300)
                else:
                    st.info("현재 조건에 해당하는 창고 출고배분 추천 항목이 없습니다.")
            else:
                st.info("창고 재고 데이터가 없습니다.")

        else:
            st.info("창고 출고배분을 위해 재고구분, 스타일코드, 점포명, 판매수량 컬럼이 필요합니다.")

    with tab3:
        full_cols = []
        for col in [
            style_col,
            style_name_col,
            category_col,
            brand_col,
            season_col,
            "판매",
            "재고",
            "총판매율",
            "목표판매율",
            "기대판매율",
            "GAP",
            "문제원인",
            "상태",
            "추천액션"
        ]:
            if col and col in filter_df.columns and col not in full_cols:
                full_cols.append(col)

        st.dataframe(
            format_number_cols(filter_df[full_cols].sort_values("GAP")),
            use_container_width=True,
            height=420
        )

else:
    st.info("좌측에서 재고 파일, 총괄장, 판매리스트 3개 파일을 업로드해주세요.")