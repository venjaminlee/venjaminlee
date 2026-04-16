import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from typing import Optional, Dict, List

# ─────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────
st.set_page_config(
    page_title="단품 관리 간소화 툴",
    page_icon="📦",
    layout="wide",
)

# ─────────────────────────────────────
# 스타일
# ─────────────────────────────────────
st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.main-title {font-size: 2rem; font-weight: 700; margin-bottom: 0.4rem;}
.sub-title {color: #666; margin-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
# 샘플 데이터
# ─────────────────────────────────────
@st.cache_data
def generate_sample_inventory() -> pd.DataFrame:
    np.random.seed(42)
    brands = ["Nike", "Adidas", "New Balance", "Puma", "Reebok"]
    categories = ["상의", "하의", "아우터", "신발", "악세서리"]
    stores = ["강남점", "잠실점", "명동점", "신촌점", "홍대점"]

    rows = []
    for i in range(300):
        brand = np.random.choice(brands)
        category = np.random.choice(categories)
        store = np.random.choice(stores)
        stock = np.random.randint(0, 120)

        rows.append({
            "상품코드": f"SKU-{i+1:04d}",
            "상품명": f"{brand} {category} {i+1:04d}",
            "브랜드": brand,
            "카테고리": category,
            "매장코드": store,
            "재고수량": stock,
        })
    return pd.DataFrame(rows)


@st.cache_data
def generate_sample_sales() -> pd.DataFrame:
    np.random.seed(7)
    brands = ["Nike", "Adidas", "New Balance", "Puma", "Reebok"]
    categories = ["상의", "하의", "아우터", "신발", "악세서리"]
    stores = ["강남점", "잠실점", "명동점", "신촌점", "홍대점"]

    rows = []
    for i in range(300):
        brand = np.random.choice(brands)
        category = np.random.choice(categories)
        store = np.random.choice(stores)
        qty = np.random.randint(0, 40)
        price = np.random.randint(30000, 200000)

        rows.append({
            "상품코드": f"SKU-{i+1:04d}",
            "상품명": f"{brand} {category} {i+1:04d}",
            "브랜드": brand,
            "카테고리": category,
            "매장코드": store,
            "판매수량": qty,
            "판매금액": qty * price,
        })
    return pd.DataFrame(rows)

# ─────────────────────────────────────
# 파일 읽기
# ─────────────────────────────────────
def parse_uploaded_file(uploaded_file, kind: str) -> Optional[pd.DataFrame]:
    try:
        file_name = uploaded_file.name.lower()

        if file_name.endswith(".csv"):
            encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]
            seps = [",", "\t", ";", "|"]
            last_error = None

            for enc in encodings:
                for sep in seps:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding=enc, sep=sep)

                        if df is None or df.empty:
                            continue

                        # 구분자 잘못 읽어서 한 컬럼으로 들어오는 경우 방지
                        if len(df.columns) == 1 and sep != seps[-1]:
                            continue

                        return df
                    except Exception as e:
                        last_error = e
                        continue

            st.error(f"{kind} CSV 파일을 읽지 못했습니다. 오류: {last_error}")
            return None

        if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file)

        st.error(f"{kind} 파일 형식이 지원되지 않습니다: {uploaded_file.name}")
        return None

    except Exception as e:
        st.error(f"{kind} 파일 파싱 오류: {e}")
        return None

# ─────────────────────────────────────
# 컬럼 정리
# ─────────────────────────────────────
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().replace("\n", " ").replace("\r", " ") for c in df.columns]
    return df


def coerce_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

# ─────────────────────────────────────
# 컬럼명 매핑
# ─────────────────────────────────────
INVENTORY_COLUMN_CANDIDATES: Dict[str, List[str]] = {
    "상품코드": ["상품코드", "단품코드", "sku", "sku코드"],
    "상품명": ["상품명", "품명", "품번코드(명)", "스타일명", "상품"],
    "브랜드": ["브랜드", "브랜드명"],
    "카테고리": ["카테고리", "품목", "상품군", "분류"],
    "매장코드": ["매장코드", "매장", "점포", "현재위치", "점"],
    "재고수량": ["재고수량", "재고", "현재고", "수량"],
}

SALES_COLUMN_CANDIDATES: Dict[str, List[str]] = {
    "상품코드": ["상품코드", "단품코드", "sku", "sku코드"],
    "상품명": ["상품명", "품명", "품번코드(명)", "스타일명", "상품"],
    "브랜드": ["브랜드", "브랜드명"],
    "카테고리": ["카테고리", "품목", "상품군", "분류"],
    "매장코드": ["매장코드", "매장", "점포", "현재위치", "점"],
    "판매수량": ["판매수량", "수량", "판매량", "총판매"],
    "판매금액": ["판매금액", "매출액", "순매출", "금액", "판매금액합계"],
}

def find_matching_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    col_map = {str(col).strip().lower(): col for col in df.columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in col_map:
            return col_map[key]
    return None


def standardize_inventory_df(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    rename_map = {}

    for standard_col, candidates in INVENTORY_COLUMN_CANDIDATES.items():
        matched = find_matching_column(df, candidates)
        if matched:
            rename_map[matched] = standard_col

    df = df.rename(columns=rename_map)

    # 없는 컬럼 채우기
    for col in ["상품명", "브랜드", "카테고리", "매장코드"]:
        if col not in df.columns:
            df[col] = "미분류"

    if "재고수량" not in df.columns:
        if "재고" in df.columns:
            df["재고수량"] = df["재고"]
        else:
            df["재고수량"] = 0

    if "상품코드" not in df.columns:
        df["상품코드"] = df.index.astype(str)

    df = coerce_numeric(df, ["재고수량"])

    keep_cols = ["상품코드", "상품명", "브랜드", "카테고리", "매장코드", "재고수량"]
    return df[keep_cols].copy()


def standardize_sales_df(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    rename_map = {}

    for standard_col, candidates in SALES_COLUMN_CANDIDATES.items():
        matched = find_matching_column(df, candidates)
        if matched:
            rename_map[matched] = standard_col

    df = df.rename(columns=rename_map)

    for col in ["상품명", "브랜드", "카테고리", "매장코드"]:
        if col not in df.columns:
            df[col] = "미분류"

    if "상품코드" not in df.columns:
        df["상품코드"] = df.index.astype(str)

    if "판매수량" not in df.columns:
        df["판매수량"] = 0

    if "판매금액" not in df.columns:
        df["판매금액"] = 0

    df = coerce_numeric(df, ["판매수량", "판매금액"])

    keep_cols = ["상품코드", "상품명", "브랜드", "카테고리", "매장코드", "판매수량", "판매금액"]
    return df[keep_cols].copy()


def validate_required_columns(df: pd.DataFrame, required_cols: List[str]) -> List[str]:
    return [col for col in required_cols if col not in df.columns]

# ─────────────────────────────────────
# 분석 로직
# ─────────────────────────────────────
def build_summary(inventory_df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    inv = inventory_df.groupby(
        ["상품코드", "상품명", "브랜드", "카테고리"],
        as_index=False
    )["재고수량"].sum()

    sales = sales_df.groupby(
        ["상품코드", "상품명", "브랜드", "카테고리"],
        as_index=False
    ).agg({
        "판매수량": "sum",
        "판매금액": "sum"
    })

    merged = pd.merge(
        inv,
        sales,
        on=["상품코드", "상품명", "브랜드", "카테고리"],
        how="outer"
    )

    for col in ["재고수량", "판매수량", "판매금액"]:
        merged[col] = merged[col].fillna(0)

    merged["총수량"] = merged["재고수량"] + merged["판매수량"]
    merged["판매율"] = np.where(
        merged["총수량"] > 0,
        merged["판매수량"] / merged["총수량"] * 100,
        0
    )

    # 원가 데이터가 없으므로 추정 지표
    # 판매율을 기반으로 간단한 추정 회수율 생성
    merged["원가회수율"] = merged["판매율"] * 1.5

    def recommend(row):
        if row["판매율"] < 20 and row["재고수량"] > 20:
            return "🔥 할인 필요"
        if row["판매율"] < 40 and row["재고수량"] > 10:
            return "📦 점출 필요"
        if row["판매율"] > 70 and row["재고수량"] < 10:
            return "📥 점입 필요"
        return "✅ 정상"

    merged["추천액션"] = merged.apply(recommend, axis=1)
    return merged.sort_values(["판매율", "재고수량"], ascending=[True, False]).reset_index(drop=True)


def build_store_summary(inventory_df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(
        inventory_df,
        sales_df,
        on=["상품코드", "상품명", "브랜드", "카테고리", "매장코드"],
        how="outer"
    )

    for col in ["재고수량", "판매수량", "판매금액"]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)
        else:
            merged[col] = 0

    store_summary = merged.groupby(
        ["상품코드", "상품명", "브랜드", "카테고리", "매장코드"],
        as_index=False
    ).agg({
        "재고수량": "sum",
        "판매수량": "sum",
        "판매금액": "sum"
    })

    store_summary["일판매량"] = store_summary["판매수량"] / 7
    store_summary["재고일수"] = np.where(
        store_summary["일판매량"] > 0,
        store_summary["재고수량"] / store_summary["일판매량"],
        999
    )
    return store_summary


# ─────────────────────────────────────
# 세션 상태
# ─────────────────────────────────────
if "inventory_df" not in st.session_state:
    st.session_state["inventory_df"] = None
if "sales_df" not in st.session_state:
    st.session_state["sales_df"] = None
if "summary_df" not in st.session_state:
    st.session_state["summary_df"] = None
if "store_summary_df" not in st.session_state:
    st.session_state["store_summary_df"] = None

# ─────────────────────────────────────
# 사이드바
# ─────────────────────────────────────
with st.sidebar:
    st.markdown("## 📦 단품 관리 툴")
    st.caption("CSV / XLSX 모두 업로드 가능")
    use_sample = st.toggle("샘플 데이터 사용", value=False)

    page = st.radio(
        "메뉴",
        ["업로드", "대시보드", "문제상품", "액션추천", "재고이동"],
        label_visibility="collapsed"
    )

    if use_sample:
        inv = generate_sample_inventory()
        sales = generate_sample_sales()
        st.session_state["inventory_df"] = inv
        st.session_state["sales_df"] = sales
        st.session_state["summary_df"] = build_summary(inv, sales)
        st.session_state["store_summary_df"] = build_store_summary(inv, sales)

# ─────────────────────────────────────
# 헤더
# ─────────────────────────────────────
st.markdown('<div class="main-title">단품 관리 간소화 툴</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">재고/매출 파일을 업로드하면 자동으로 통합 분석합니다.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────
# 업로드 페이지
# ─────────────────────────────────────
if page == "업로드":
    st.subheader("파일 업로드")

    col1, col2 = st.columns(2)

    with col1:
        inv_file = st.file_uploader(
            "재고 파일 업로드",
            type=["xlsx", "xls", "csv"],
            key="inventory_upload"
        )

        if inv_file is not None:
            raw_inv = parse_uploaded_file(inv_file, "재고")
            if raw_inv is not None:
                inv_df = standardize_inventory_df(raw_inv)
                missing_inv = validate_required_columns(inv_df, ["상품코드", "재고수량"])

                if missing_inv:
                    st.error(f"재고 파일 필수 컬럼 누락: {missing_inv}")
                else:
                    st.session_state["inventory_df"] = inv_df
                    st.success(f"재고 파일 로드 완료: {len(inv_df):,}행")
                    st.dataframe(inv_df.head(10), use_container_width=True)

    with col2:
        sales_file = st.file_uploader(
            "매출 파일 업로드",
            type=["xlsx", "xls", "csv"],
            key="sales_upload"
        )

        if sales_file is not None:
            raw_sales = parse_uploaded_file(sales_file, "매출")
            if raw_sales is not None:
                sales_df = standardize_sales_df(raw_sales)
                missing_sales = validate_required_columns(sales_df, ["상품코드", "판매수량"])

                if missing_sales:
                    st.error(f"매출 파일 필수 컬럼 누락: {missing_sales}")
                else:
                    st.session_state["sales_df"] = sales_df
                    st.success(f"매출 파일 로드 완료: {len(sales_df):,}행")
                    st.dataframe(sales_df.head(10), use_container_width=True)

    st.divider()

    ready = (
        st.session_state["inventory_df"] is not None
        and st.session_state["sales_df"] is not None
    )

    if st.button("🚀 분석 시작", type="primary", use_container_width=True, disabled=not ready):
        inv = st.session_state["inventory_df"]
        sales = st.session_state["sales_df"]

        with st.spinner("분석 중입니다..."):
            st.session_state["summary_df"] = build_summary(inv, sales)
            st.session_state["store_summary_df"] = build_store_summary(inv, sales)

        st.success("분석 완료. 왼쪽 메뉴에서 결과를 확인하세요.")

    if not ready:
        st.info("재고 파일과 매출 파일을 모두 업로드하세요.")

# ─────────────────────────────────────
# 공통: 분석 전 차단
# ─────────────────────────────────────
if page != "업로드":
    if st.session_state["summary_df"] is None:
        st.info("먼저 업로드 메뉴에서 파일을 올리고 분석을 시작하세요.")
        st.stop()

summary_df = st.session_state["summary_df"]
store_summary_df = st.session_state["store_summary_df"]

# ─────────────────────────────────────
# 대시보드
# ─────────────────────────────────────
if page == "대시보드":
    st.subheader("메인 대시보드")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 상품 수", f"{len(summary_df):,}개")
    col2.metric("총 재고", f"{int(summary_df['재고수량'].sum()):,}")
    col3.metric("평균 판매율", f"{summary_df['판매율'].mean():.1f}%")
    col4.metric("평균 원가회수율", f"{summary_df['원가회수율'].mean():.1f}%")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("#### 카테고리별 평균 판매율")
        cat_df = summary_df.groupby("카테고리", as_index=False)["판매율"].mean().sort_values("판매율")
        fig = px.bar(cat_df, x="판매율", y="카테고리", orientation="h", text_auto=".1f")
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("#### 브랜드별 매출")
        brand_df = summary_df.groupby("브랜드", as_index=False)["판매금액"].sum().sort_values("판매금액", ascending=False)
        fig2 = px.bar(brand_df, x="브랜드", y="판매금액", text_auto=".2s")
        fig2.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.markdown("#### 문제 상품 요약")
    problem_df = summary_df[(summary_df["판매율"] < 30) | (summary_df["원가회수율"] < 50)]
    st.dataframe(
        problem_df[["상품코드", "상품명", "브랜드", "카테고리", "재고수량", "판매수량", "판매율", "원가회수율", "추천액션"]],
        use_container_width=True,
        height=350
    )

# ─────────────────────────────────────
# 문제상품
# ─────────────────────────────────────
if page == "문제상품":
    st.subheader("문제 상품 분석")

    c1, c2, c3, c4 = st.columns(4)
    brand_options = ["전체"] + sorted(summary_df["브랜드"].astype(str).unique().tolist())
    cat_options = ["전체"] + sorted(summary_df["카테고리"].astype(str).unique().tolist())

    sel_brand = c1.selectbox("브랜드", brand_options)
    sel_cat = c2.selectbox("카테고리", cat_options)
    sell_thr = c3.slider("판매율 기준", 0, 100, 30)
    cost_thr = c4.slider("원가회수율 기준", 0, 200, 50)

    filtered = summary_df.copy()

    if sel_brand != "전체":
        filtered = filtered[filtered["브랜드"] == sel_brand]
    if sel_cat != "전체":
        filtered = filtered[filtered["카테고리"] == sel_cat]

    problem = filtered[(filtered["판매율"] < sell_thr) | (filtered["원가회수율"] < cost_thr)].copy()

    def status_label(row):
        if row["판매율"] < 20:
            return "긴급"
        if row["판매율"] < sell_thr:
            return "주의"
        return "관찰"

    problem["상태"] = problem.apply(status_label, axis=1)

    m1, m2, m3 = st.columns(3)
    m1.metric("긴급", len(problem[problem["상태"] == "긴급"]))
    m2.metric("주의", len(problem[problem["상태"] == "주의"]))
    m3.metric("전체 문제 상품", len(problem))

    st.dataframe(
        problem[["상태", "상품코드", "상품명", "브랜드", "카테고리", "재고수량", "판매수량", "판매율", "원가회수율", "추천액션"]],
        use_container_width=True,
        height=420
    )

    st.markdown("#### 판매율 vs 원가회수율")
    fig = px.scatter(
        filtered,
        x="판매율",
        y="원가회수율",
        color="카테고리",
        size="재고수량",
        hover_data=["상품명", "브랜드"]
    )
    fig.add_vline(x=sell_thr, line_dash="dash", line_color="red")
    fig.add_hline(y=cost_thr, line_dash="dash", line_color="orange")
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────
# 액션추천
# ─────────────────────────────────────
if page == "액션추천":
    st.subheader("액션 추천")

    discount_df = summary_df[(summary_df["판매율"] < 25) & (summary_df["재고수량"] > 10)].copy()
    transfer_out_df = summary_df[(summary_df["판매율"] < 40) & (summary_df["재고수량"] > 20)].copy()
    transfer_in_df = summary_df[(summary_df["판매율"] > 70) & (summary_df["재고수량"] < 10)].copy()

    discount_df["권장할인율"] = np.where(discount_df["판매율"] < 15, "30%", "15%")
    transfer_out_df["추천점출수량"] = (transfer_out_df["재고수량"] * 0.3).astype(int)
    transfer_in_df["추천점입수량"] = (10 - transfer_in_df["재고수량"]).clip(lower=1)

    t1, t2, t3 = st.tabs(["할인 대상", "점출 대상", "점입 대상"])

    with t1:
        st.write(f"{len(discount_df)}개 상품")
        st.dataframe(
            discount_df[["상품코드", "상품명", "브랜드", "카테고리", "재고수량", "판매율", "권장할인율"]],
            use_container_width=True
        )

    with t2:
        st.write(f"{len(transfer_out_df)}개 상품")
        st.dataframe(
            transfer_out_df[["상품코드", "상품명", "브랜드", "카테고리", "재고수량", "판매율", "추천점출수량"]],
            use_container_width=True
        )

    with t3:
        st.write(f"{len(transfer_in_df)}개 상품")
        st.dataframe(
            transfer_in_df[["상품코드", "상품명", "브랜드", "카테고리", "재고수량", "판매율", "추천점입수량"]],
            use_container_width=True
        )

# ─────────────────────────────────────
# 재고이동
# ─────────────────────────────────────
if page == "재고이동":
    st.subheader("점출 / 점입 추천")

    low_stock = store_summary_df[(store_summary_df["판매수량"] > 5) & (store_summary_df["재고수량"] < 10)].copy()
    high_stock = store_summary_df[(store_summary_df["판매수량"] < 3) & (store_summary_df["재고수량"] > 20)].copy()

    moves = []

    for _, need in low_stock.iterrows():
        donor_candidates = high_stock[
            (high_stock["상품코드"] == need["상품코드"]) &
            (high_stock["매장코드"] != need["매장코드"])
        ]

        if not donor_candidates.empty:
            donor = donor_candidates.iloc[0]
            move_qty = min(max(10 - int(need["재고수량"]), 1), int(donor["재고수량"] * 0.3))

            if move_qty > 0:
                moves.append({
                    "상품코드": need["상품코드"],
                    "상품명": need["상품명"],
                    "브랜드": need["브랜드"],
                    "출발매장": donor["매장코드"],
                    "도착매장": need["매장코드"],
                    "이동수량": move_qty,
                })

    move_df = pd.DataFrame(moves)

    if move_df.empty:
        st.info("현재 데이터 기준 추천 이동 계획이 없습니다.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            out_sum = move_df.groupby("출발매장", as_index=False)["이동수량"].sum()
            fig1 = px.bar(out_sum, x="출발매장", y="이동수량")
            fig1.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            in_sum = move_df.groupby("도착매장", as_index=False)["이동수량"].sum()
            fig2 = px.bar(in_sum, x="도착매장", y="이동수량")
            fig2.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(move_df, use_container_width=True, height=420)

        csv_data = move_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "재고 이동 계획 다운로드",
            data=csv_data,
            file_name="재고이동계획.csv",
            mime="text/csv",
            use_container_width=True
        )
