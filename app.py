import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from typing import Optional, List, Dict

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
.small-note {color: #888; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

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

                        if len(df.columns) == 1 and sep != seps[-1]:
                            continue

                        return df
                    except Exception as e:
                        last_error = e
                        continue

            st.error(f"{kind} CSV 파일을 읽지 못했습니다. 오류: {last_error}")
            return None

        elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            uploaded_file.seek(0)
            return pd.read_excel(uploaded_file)

        else:
            st.error(f"{kind} 파일 형식이 지원되지 않습니다: {uploaded_file.name}")
            return None

    except Exception as e:
        st.error(f"{kind} 파일 파싱 오류: {e}")
        return None


def parse_multiple_files(uploaded_files, kind: str) -> Optional[pd.DataFrame]:
    if not uploaded_files:
        return None

    frames = []
    failed_files = []

    for file in uploaded_files:
        df = parse_uploaded_file(file, kind)
        if df is not None and not df.empty:
            df = df.copy()
            df["원본파일명"] = file.name
            frames.append(df)
        else:
            failed_files.append(file.name)

    if failed_files:
        st.warning(f"{kind} 파일 중 일부를 읽지 못했습니다: {', '.join(failed_files)}")

    if not frames:
        st.error(f"{kind} 파일을 하나도 읽지 못했습니다.")
        return None

    try:
        return pd.concat(frames, ignore_index=True)
    except Exception as e:
        st.error(f"{kind} 파일 병합 오류: {e}")
        return None


# ─────────────────────────────────────
# 공통 정리
# ─────────────────────────────────────
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().replace("\n", " ").replace("\r", " ") for c in df.columns]
    return df


def clean_text_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def coerce_numeric(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def find_matching_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in normalized:
            return normalized[key]
    return None


# ─────────────────────────────────────
# 더미 재고 파일 전용 컬럼 매핑
# ─────────────────────────────────────
INVENTORY_CANDIDATES: Dict[str, List[str]] = {
    "브랜드코드": ["브랜드"],
    "브랜드명": ["Unnamed: 1", "Unnamed:1", "브랜드명"],
    "서브브랜드코드": ["서브브랜드"],
    "서브브랜드명": ["Unnamed: 3", "Unnamed:3", "서브브랜드명"],
    "품번코드명": ["품번코드(명)", "품번코드 명"],
    "단품코드": ["단품코드", "상품코드", "sku"],
    "스타일코드": ["스타일", "스타일코드"],
    "스타일명": ["Unnamed: 7", "Unnamed:7", "스타일명"],
    "색상코드": ["색상", "색상코드"],
    "색상명": ["Unnamed: 9", "Unnamed:9", "색상명"],
    "사이즈코드": ["사이즈", "사이즈코드"],
    "사이즈명": ["Unnamed: 11", "Unnamed:11", "사이즈명"],
    "점포": ["현재위치", "점포", "매장", "매장코드"],
    "전월재고": ["전월재고"],
    "판매수량_재고원본": ["판매수량"],
    "출고": ["출고"],
    "판매량_오프라인": ["판매량"],
    "판매량_온라인": ["Unnamed: 17", "Unnamed:17", "온라인판매"],
    "총판매": ["Unnamed: 18", "Unnamed:18", "총판매"],
    "이동": ["이동"],
    "기타출고": ["기타출고"],
    "미확정수량": ["미확정수량"],
    "스타일대체": ["스타일대체"],
    "재고조정": ["재고조정"],
    "재고수량": ["재고", "재고수량"],
}

# ─────────────────────────────────────
# 더미 매출 파일 전용 컬럼 매핑
# ─────────────────────────────────────
SALES_CANDIDATES: Dict[str, List[str]] = {
    "매출일자": ["매출일자", "일자", "판매일자"],
    "점포": ["점포", "매장", "현재위치", "매장코드"],
    "브랜드코드": ["브랜드코드", "브랜드"],
    "브랜드명": ["브랜드명", "Unnamed: 1", "Unnamed:1"],
    "서브브랜드코드": ["서브브랜드코드", "서브브랜드"],
    "서브브랜드명": ["서브브랜드명", "Unnamed: 3", "Unnamed:3"],
    "품번코드명": ["품번코드(명)", "품번코드 명"],
    "단품코드": ["단품코드", "상품코드", "sku"],
    "스타일코드": ["스타일코드", "스타일"],
    "스타일명": ["스타일명", "Unnamed: 7", "Unnamed:7"],
    "색상코드": ["색상코드", "색상"],
    "색상명": ["색상명", "Unnamed: 9", "Unnamed:9"],
    "사이즈코드": ["사이즈코드", "사이즈"],
    "사이즈명": ["사이즈명", "Unnamed: 11", "Unnamed:11"],
    "판매수량": ["판매수량", "수량", "총판매"],
    "정상판매가": ["정상판매가", "판매가"],
    "판매금액": ["판매금액", "매출액"],
    "할인율": ["할인율"],
    "할인금액": ["할인금액"],
    "순매출": ["순매출", "판매금액합계"],
    "판매구분": ["판매구분"],
    "고객구분": ["고객구분"],
}

# ─────────────────────────────────────
# 재고 데이터 표준화
# ─────────────────────────────────────
def standardize_inventory_df(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    rename_map = {}

    for standard_col, candidates in INVENTORY_CANDIDATES.items():
        matched = find_matching_column(df, candidates)
        if matched:
            rename_map[matched] = standard_col

    df = df.rename(columns=rename_map)

    required_defaults = {
        "브랜드코드": "",
        "브랜드명": "미분류",
        "서브브랜드코드": "",
        "서브브랜드명": "미분류",
        "품번코드명": "미분류",
        "단품코드": "",
        "스타일코드": "",
        "스타일명": "미분류",
        "색상코드": "",
        "색상명": "",
        "사이즈코드": "",
        "사이즈명": "",
        "점포": "미분류점포",
        "재고수량": 0,
    }

    for col, default_value in required_defaults.items():
        if col not in df.columns:
            df[col] = default_value

    df = coerce_numeric(df, ["단품코드", "재고수량", "전월재고", "판매수량_재고원본", "출고", "판매량_오프라인",
                             "판매량_온라인", "총판매", "이동", "기타출고", "미확정수량", "스타일대체", "재고조정"])

    for col in ["브랜드명", "서브브랜드명", "품번코드명", "스타일명", "색상명", "사이즈명", "점포"]:
        if col in df.columns:
            df[col] = clean_text_series(df[col])

    if "카테고리" not in df.columns:
        df["카테고리"] = df["브랜드명"]

    # 분석용 표준 컬럼
    result = pd.DataFrame({
        "상품코드": df["단품코드"].astype(str).str.strip(),
        "상품명": df["품번코드명"].astype(str).str.strip(),
        "브랜드": df["브랜드명"].astype(str).str.strip(),
        "서브브랜드": df["서브브랜드명"].astype(str).str.strip(),
        "카테고리": df["카테고리"].astype(str).str.strip(),
        "매장코드": df["점포"].astype(str).str.strip(),
        "스타일코드": df["스타일코드"].astype(str).str.strip(),
        "스타일명": df["스타일명"].astype(str).str.strip(),
        "색상명": df["색상명"].astype(str).str.strip(),
        "사이즈명": df["사이즈명"].astype(str).str.strip(),
        "재고수량": df["재고수량"].fillna(0),
        "원본파일명": df["원본파일명"] if "원본파일명" in df.columns else "",
    })

    return result


# ─────────────────────────────────────
# 매출 데이터 표준화
# ─────────────────────────────────────
def standardize_sales_df(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_columns(df)
    rename_map = {}

    for standard_col, candidates in SALES_CANDIDATES.items():
        matched = find_matching_column(df, candidates)
        if matched:
            rename_map[matched] = standard_col

    df = df.rename(columns=rename_map)

    required_defaults = {
        "매출일자": "",
        "점포": "미분류점포",
        "브랜드코드": "",
        "브랜드명": "미분류",
        "서브브랜드코드": "",
        "서브브랜드명": "미분류",
        "품번코드명": "미분류",
        "단품코드": "",
        "스타일코드": "",
        "스타일명": "미분류",
        "색상명": "",
        "사이즈명": "",
        "판매수량": 0,
        "판매금액": 0,
        "순매출": 0,
    }

    for col, default_value in required_defaults.items():
        if col not in df.columns:
            df[col] = default_value

    df = coerce_numeric(df, ["단품코드", "판매수량", "정상판매가", "판매금액", "할인율", "할인금액", "순매출"])

    for col in ["브랜드명", "서브브랜드명", "품번코드명", "스타일명", "색상명", "사이즈명", "점포"]:
        if col in df.columns:
            df[col] = clean_text_series(df[col])

    if "카테고리" not in df.columns:
        df["카테고리"] = df["브랜드명"]

    result = pd.DataFrame({
        "상품코드": df["단품코드"].astype(str).str.strip(),
        "상품명": df["품번코드명"].astype(str).str.strip(),
        "브랜드": df["브랜드명"].astype(str).str.strip(),
        "서브브랜드": df["서브브랜드명"].astype(str).str.strip(),
        "카테고리": df["카테고리"].astype(str).str.strip(),
        "매장코드": df["점포"].astype(str).str.strip(),
        "스타일코드": df["스타일코드"].astype(str).str.strip(),
        "스타일명": df["스타일명"].astype(str).str.strip(),
        "색상명": df["색상명"].astype(str).str.strip(),
        "사이즈명": df["사이즈명"].astype(str).str.strip(),
        "판매수량": df["판매수량"].fillna(0),
        "판매금액": df["판매금액"].fillna(0),
        "순매출": df["순매출"].fillna(0),
        "원본파일명": df["원본파일명"] if "원본파일명" in df.columns else "",
    })

    return result


# ─────────────────────────────────────
# 검증
# ─────────────────────────────────────
def validate_required_columns(df: pd.DataFrame, required_cols: List[str]) -> List[str]:
    return [col for col in required_cols if col not in df.columns]


# ─────────────────────────────────────
# 분석 로직
# ─────────────────────────────────────
def build_summary(inventory_df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    inv = inventory_df.groupby(
        ["상품코드", "상품명", "브랜드", "서브브랜드", "카테고리", "스타일코드", "스타일명"],
        as_index=False
    ).agg({
        "재고수량": "sum"
    })

    sales = sales_df.groupby(
        ["상품코드", "상품명", "브랜드", "서브브랜드", "카테고리", "스타일코드", "스타일명"],
        as_index=False
    ).agg({
        "판매수량": "sum",
        "판매금액": "sum",
        "순매출": "sum"
    })

    merged = pd.merge(
        inv,
        sales,
        on=["상품코드", "상품명", "브랜드", "서브브랜드", "카테고리", "스타일코드", "스타일명"],
        how="outer"
    )

    for col in ["재고수량", "판매수량", "판매금액", "순매출"]:
        merged[col] = merged[col].fillna(0)

    merged["총수량"] = merged["재고수량"] + merged["판매수량"]
    merged["판매율"] = np.where(
        merged["총수량"] > 0,
        merged["판매수량"] / merged["총수량"] * 100,
        0
    )

    # 원가 데이터가 없으므로 순매출 기반 추정 지표
    merged["원가회수율"] = np.where(
        merged["판매금액"] > 0,
        merged["순매출"] / merged["판매금액"] * 100,
        0
    )

    def recommend(row):
        if row["판매율"] < 20 and row["재고수량"] > 20:
            return "🔥 할인 필요"
        elif row["판매율"] < 40 and row["재고수량"] > 10:
            return "📦 점출 필요"
        elif row["판매율"] > 70 and row["재고수량"] < 10:
            return "📥 점입 필요"
        else:
            return "✅ 정상"

    merged["추천액션"] = merged.apply(recommend, axis=1)

    return merged.sort_values(["판매율", "재고수량"], ascending=[True, False]).reset_index(drop=True)


def build_store_summary(inventory_df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    merged = pd.merge(
        inventory_df,
        sales_df,
        on=["상품코드", "상품명", "브랜드", "서브브랜드", "카테고리", "매장코드", "스타일코드", "스타일명"],
        how="outer"
    )

    for col in ["재고수량", "판매수량", "판매금액", "순매출"]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)
        else:
            merged[col] = 0

    store_summary = merged.groupby(
        ["상품코드", "상품명", "브랜드", "서브브랜드", "카테고리", "매장코드", "스타일코드", "스타일명"],
        as_index=False
    ).agg({
        "재고수량": "sum",
        "판매수량": "sum",
        "판매금액": "sum",
        "순매출": "sum"
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
    st.caption("점포별 재고/매출 CSV 여러 개를 한 번에 업로드해서 분석합니다.")
    page = st.radio(
        "메뉴",
        ["업로드", "대시보드", "문제상품", "액션추천", "재고이동"],
        label_visibility="collapsed"
    )


# ─────────────────────────────────────
# 헤더
# ─────────────────────────────────────
st.markdown('<div class="main-title">단품 관리 간소화 툴</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">점포별 재고 파일 30개 + 매출 파일 30개를 한 번에 올려 통합 분석합니다.</div>',
    unsafe_allow_html=True
)


# ─────────────────────────────────────
# 업로드 페이지
# ─────────────────────────────────────
if page == "업로드":
    st.subheader("파일 업로드")
    st.markdown('<div class="small-note">재고 CSV 여러 개 / 매출 CSV 여러 개를 각각 한 번에 선택하세요.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        inv_files = st.file_uploader(
            "재고 파일 업로드 (여러 개 가능)",
            type=["xlsx", "xls", "csv"],
            accept_multiple_files=True,
            key="inventory_upload"
        )

        if inv_files:
            raw_inv = parse_multiple_files(inv_files, "재고")
            if raw_inv is not None:
                inv_df = standardize_inventory_df(raw_inv)
                missing_inv = validate_required_columns(inv_df, ["상품코드", "재고수량", "매장코드"])

                if missing_inv:
                    st.error(f"재고 파일 필수 컬럼 누락: {missing_inv}")
                else:
                    st.session_state["inventory_df"] = inv_df
                    st.success(f"재고 파일 로드 완료: {len(inv_files)}개 파일 / {len(inv_df):,}행")
                    st.dataframe(inv_df.head(10), use_container_width=True)

    with col2:
        sales_files = st.file_uploader(
            "매출 파일 업로드 (여러 개 가능)",
            type=["xlsx", "xls", "csv"],
            accept_multiple_files=True,
            key="sales_upload"
        )

        if sales_files:
            raw_sales = parse_multiple_files(sales_files, "매출")
            if raw_sales is not None:
                sales_df = standardize_sales_df(raw_sales)
                missing_sales = validate_required_columns(sales_df, ["상품코드", "판매수량", "매장코드"])

                if missing_sales:
                    st.error(f"매출 파일 필수 컬럼 누락: {missing_sales}")
                else:
                    st.session_state["sales_df"] = sales_df
                    st.success(f"매출 파일 로드 완료: {len(sales_files)}개 파일 / {len(sales_df):,}행")
                    st.dataframe(sales_df.head(10), use_container_width=True)

    st.divider()

    ready = (
        st.session_state["inventory_df"] is not None
        and st.session_state["sales_df"] is not None
    )

    if st.button("🚀 분석 시작", type="primary", use_container_width=True, disabled=not ready):
        with st.spinner("재고/매출 데이터를 통합 분석 중입니다..."):
            inv = st.session_state["inventory_df"]
            sales = st.session_state["sales_df"]

            st.session_state["summary_df"] = build_summary(inv, sales)
            st.session_state["store_summary_df"] = build_store_summary(inv, sales)

        st.success("분석 완료. 왼쪽 메뉴에서 결과를 확인하세요.")

    if not ready:
        st.info("재고 파일과 매출 파일을 각각 업로드하세요.")


# ─────────────────────────────────────
# 공통 차단
# ─────────────────────────────────────
if page != "업로드":
    if st.session_state["summary_df"] is None:
        st.info("먼저 업로드 메뉴에서 재고/매출 파일을 올리고 분석을 시작하세요.")
        st.stop()

summary_df = st.session_state["summary_df"]
store_summary_df = st.session_state["store_summary_df"]


# ─────────────────────────────────────
# 대시보드
# ─────────────────────────────────────
if page == "대시보드":
    st.subheader("메인 대시보드")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 SKU 수", f"{len(summary_df):,}개")
    c2.metric("총 재고 수량", f"{int(summary_df['재고수량'].sum()):,}")
    c3.metric("총 판매 수량", f"{int(summary_df['판매수량'].sum()):,}")
    c4.metric("평균 판매율", f"{summary_df['판매율'].mean():.1f}%")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("#### 브랜드별 평균 판매율")
        brand_df = summary_df.groupby("브랜드", as_index=False)["판매율"].mean().sort_values("판매율")
        fig = px.bar(brand_df, x="판매율", y="브랜드", orientation="h", text_auto=".1f")
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("#### 브랜드별 순매출")
        brand_sales_df = summary_df.groupby("브랜드", as_index=False)["순매출"].sum().sort_values("순매출", ascending=False)
        fig2 = px.bar(brand_sales_df, x="브랜드", y="순매출", text_auto=".2s")
        fig2.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.markdown("#### 문제 상품 요약")
    problem_df = summary_df[(summary_df["판매율"] < 30) | (summary_df["원가회수율"] < 80)]
    st.dataframe(
        problem_df[["상품코드", "상품명", "브랜드", "서브브랜드", "재고수량", "판매수량", "판매율", "원가회수율", "추천액션"]],
        use_container_width=True,
        height=360
    )


# ─────────────────────────────────────
# 문제상품
# ─────────────────────────────────────
if page == "문제상품":
    st.subheader("문제 상품 분석")

    f1, f2, f3 = st.columns(3)
    brand_options = ["전체"] + sorted(summary_df["브랜드"].astype(str).unique().tolist())
    subbrand_options = ["전체"] + sorted(summary_df["서브브랜드"].astype(str).unique().tolist())

    selected_brand = f1.selectbox("브랜드", brand_options)
    selected_subbrand = f2.selectbox("서브브랜드", subbrand_options)
    sell_thr = f3.slider("판매율 기준", 0, 100, 30)

    filtered = summary_df.copy()

    if selected_brand != "전체":
        filtered = filtered[filtered["브랜드"] == selected_brand]
    if selected_subbrand != "전체":
        filtered = filtered[filtered["서브브랜드"] == selected_subbrand]

    problem = filtered[filtered["판매율"] < sell_thr].copy()

    def get_status(rate):
        if rate < 15:
            return "긴급"
        elif rate < sell_thr:
            return "주의"
        else:
            return "정상"

    problem["상태"] = problem["판매율"].apply(get_status)

    m1, m2, m3 = st.columns(3)
    m1.metric("긴급", len(problem[problem["상태"] == "긴급"]))
    m2.metric("주의", len(problem[problem["상태"] == "주의"]))
    m3.metric("문제 상품", len(problem))

    st.dataframe(
        problem[["상태", "상품코드", "상품명", "브랜드", "서브브랜드", "재고수량", "판매수량", "판매율", "추천액션"]],
        use_container_width=True,
        height=420
    )

    st.markdown("#### 판매율 vs 재고수량")
    fig = px.scatter(
        filtered,
        x="판매율",
        y="재고수량",
        color="브랜드",
        size="판매수량",
        hover_data=["상품명", "서브브랜드", "스타일명"]
    )
    fig.add_vline(x=sell_thr, line_dash="dash", line_color="red")
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────
# 액션추천
# ─────────────────────────────────────
if page == "액션추천":
    st.subheader("액션 추천")

    discount_df = summary_df[(summary_df["판매율"] < 20) & (summary_df["재고수량"] > 20)].copy()
    transfer_out_df = summary_df[(summary_df["판매율"] < 40) & (summary_df["재고수량"] > 15)].copy()
    transfer_in_df = summary_df[(summary_df["판매율"] > 70) & (summary_df["재고수량"] < 10)].copy()

    discount_df["권장할인율"] = np.where(discount_df["판매율"] < 10, "30%", "15%")
    transfer_out_df["추천점출수량"] = (transfer_out_df["재고수량"] * 0.3).astype(int)
    transfer_in_df["추천점입수량"] = (10 - transfer_in_df["재고수량"]).clip(lower=1)

    t1, t2, t3 = st.tabs(["할인 대상", "점출 대상", "점입 대상"])

    with t1:
        st.write(f"{len(discount_df)}개 상품")
        st.dataframe(
            discount_df[["상품코드", "상품명", "브랜드", "서브브랜드", "재고수량", "판매율", "권장할인율"]],
            use_container_width=True
        )

    with t2:
        st.write(f"{len(transfer_out_df)}개 상품")
        st.dataframe(
            transfer_out_df[["상품코드", "상품명", "브랜드", "서브브랜드", "재고수량", "판매율", "추천점출수량"]],
            use_container_width=True
        )

    with t3:
        st.write(f"{len(transfer_in_df)}개 상품")
        st.dataframe(
            transfer_in_df[["상품코드", "상품명", "브랜드", "서브브랜드", "재고수량", "판매율", "추천점입수량"]],
            use_container_width=True
        )


# ─────────────────────────────────────
# 재고이동
# ─────────────────────────────────────
if page == "재고이동":
    st.subheader("점출 / 점입 추천")

    low_stock = store_summary_df[
        (store_summary_df["판매수량"] > 5) & (store_summary_df["재고수량"] < 10)
    ].copy()

    high_stock = store_summary_df[
        (store_summary_df["판매수량"] < 3) & (store_summary_df["재고수량"] > 20)
    ].copy()

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
                    "서브브랜드": need["서브브랜드"],
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
