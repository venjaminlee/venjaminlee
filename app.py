import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="단품 관리 간소화 툴",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem; font-weight: 700; color: #1a1a2e;
        border-bottom: 3px solid #4f46e5; padding-bottom: 0.4rem; margin-bottom: 1rem;
    }
    .kpi-card {
        background: #f8f9ff; border: 1px solid #e0e0f0; border-radius: 10px;
        padding: 1rem 1.2rem; text-align: center;
    }
    .kpi-value { font-size: 1.8rem; font-weight: 700; color: #4f46e5; }
    .kpi-label { font-size: 0.85rem; color: #666; margin-top: 0.2rem; }
    .action-badge-red   { background:#fee2e2; color:#b91c1c; padding:3px 10px; border-radius:20px; font-size:0.8rem; font-weight:600; }
    .action-badge-amber { background:#fef3c7; color:#92400e; padding:3px 10px; border-radius:20px; font-size:0.8rem; font-weight:600; }
    .action-badge-green { background:#d1fae5; color:#065f46; padding:3px 10px; border-radius:20px; font-size:0.8rem; font-weight:600; }
    .step-badge {
        display:inline-block; background:#4f46e5; color:white;
        border-radius:50%; width:28px; height:28px; line-height:28px;
        text-align:center; font-weight:700; margin-right:8px;
    }
    div[data-testid="stMetricValue"] { font-size: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

# ── 샘플 데이터 생성 ──────────────────────────────────────────────────────────
@st.cache_data
def generate_sample_data():
    np.random.seed(42)
    brands    = ["Nike", "Adidas", "New Balance", "Puma", "Reebok"]
    cats      = ["상의", "하의", "아우터", "신발", "악세서리"]
    stores    = ["강남점", "홍대점", "잠실점", "신촌점", "명동점"]
    products  = []
    for i in range(80):
        brand   = np.random.choice(brands)
        cat     = np.random.choice(cats)
        stock   = np.random.randint(0, 120)
        sales   = np.random.randint(5, 80)
        cost    = np.random.randint(20000, 150000)
        price   = int(cost * np.random.uniform(1.5, 2.5))
        sold_qty= np.random.randint(0, min(stock + 1, 50))
        products.append({
            "상품코드": f"SKU-{i+1:04d}",
            "상품명":   f"{brand} {cat} {i+1:04d}",
            "브랜드":   brand,
            "카테고리": cat,
            "매장":     np.random.choice(stores),
            "재고수량": stock,
            "판매수량": sold_qty,
            "원가":     cost,
            "판매가":   price,
            "판매율":   round(sold_qty / max(stock, 1) * 100, 1),
            "원가회수율": round(sold_qty * price / max((stock + sold_qty) * cost, 1) * 100, 1),
        })
    return pd.DataFrame(products)


@st.cache_data
def generate_sample_sales():
    np.random.seed(7)
    brands    = ["Nike", "Adidas", "New Balance", "Puma", "Reebok"]
    cats      = ["상의", "하의", "아우터", "신발", "악세서리"]
    dates     = pd.date_range("2024-10-01", "2025-03-31", freq="W")
    rows = []
    for d in dates:
        for brand in brands:
            rows.append({
                "날짜":   d,
                "브랜드": brand,
                "카테고리": np.random.choice(cats),
                "매출액": np.random.randint(500_000, 5_000_000),
            })
    return pd.DataFrame(rows)


# ── 세션 상태 초기화 ──────────────────────────────────────────────────────────
if "inventory_df" not in st.session_state:
    st.session_state["inventory_df"] = None
if "sales_df" not in st.session_state:
    st.session_state["sales_df"] = None
if "analyzed" not in st.session_state:
    st.session_state["analyzed"] = False

# ── 사이드바 네비게이션 ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📦 단품 관리 툴")
    st.caption("데이터를 보는 툴이 아니라,\n**무엇을 해야 하는지** 알려주는 툴")
    st.divider()
    pages = ["① 데이터 업로드", "② 메인 대시보드", "③ 문제 상품", "④ 액션 추천", "⑤ 재고 이동"]
    page  = st.radio("페이지 선택", pages, label_visibility="collapsed")
    st.divider()

    use_sample = st.toggle("샘플 데이터로 체험하기", value=False)
    if use_sample:
        st.session_state["inventory_df"] = generate_sample_data()
        st.session_state["sales_df"]     = generate_sample_sales()
        st.session_state["analyzed"]     = True
        st.success("샘플 데이터 로드 완료!")

    if st.session_state["analyzed"]:
        st.markdown("---")
        st.markdown("**📊 데이터 현황**")
        df = st.session_state["inventory_df"]
        st.metric("총 SKU 수", f"{len(df):,}개")
        st.metric("총 재고 수량", f"{df['재고수량'].sum():,}개")


# ══════════════════════════════════════════════════════════════════════════════
# 1 ▸ 데이터 업로드
# ══════════════════════════════════════════════════════════════════════════════
def parse_uploaded_file(uploaded_file, kind: str) -> pd.DataFrame | None:
    """엑셀 또는 CSV 파일을 DataFrame으로 반환."""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        return df
    except Exception as e:
        st.error(f"{kind} 파일 파싱 오류: {e}")
        return None


if page == "① 데이터 업로드":
    st.markdown('<div class="main-header">① 데이터 업로드</div>', unsafe_allow_html=True)
    st.caption("파일을 업로드하면 자동으로 통합 및 분석이 시작됩니다.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📂 재고 데이터")
        inv_file = st.file_uploader("재고 엑셀/CSV 업로드", type=["xlsx", "xls", "csv"], key="inv")
        if inv_file:
            df_inv = parse_uploaded_file(inv_file, "재고")
            if df_inv is not None:
                st.session_state["inventory_df"] = df_inv
                st.success(f"✅ 재고 데이터 로드 완료 ({len(df_inv):,}행)")
                st.dataframe(df_inv.head(5), use_container_width=True)

    with col2:
        st.markdown("#### 📂 매출 데이터")
        sales_file = st.file_uploader("매출 엑셀/CSV 업로드", type=["xlsx", "xls", "csv"], key="sales")
        if sales_file:
            df_sales = parse_uploaded_file(sales_file, "매출")
            if df_sales is not None:
                st.session_state["sales_df"] = df_sales
                st.success(f"✅ 매출 데이터 로드 완료 ({len(df_sales):,}행)")
                st.dataframe(df_sales.head(5), use_container_width=True)

    st.divider()
    btn_ready = (
        st.session_state["inventory_df"] is not None
        or use_sample
    )
    if st.button("🚀 분석 시작", type="primary", disabled=not btn_ready, use_container_width=True):
        with st.spinner("데이터 통합 및 분석 중..."):
            if use_sample or st.session_state["inventory_df"] is not None:
                if st.session_state["inventory_df"] is None:
                    st.session_state["inventory_df"] = generate_sample_data()
                if st.session_state["sales_df"] is None:
                    st.session_state["sales_df"] = generate_sample_sales()
                st.session_state["analyzed"] = True
                st.success("✅ 분석 완료! 왼쪽 메뉴에서 대시보드를 확인하세요.")
    if not btn_ready:
        st.info("💡 파일을 업로드하거나 왼쪽 토글에서 샘플 데이터를 활성화하세요.")


# ══════════════════════════════════════════════════════════════════════════════
# 헬퍼: 데이터 미준비 경고
# ══════════════════════════════════════════════════════════════════════════════
def require_data():
    if not st.session_state["analyzed"]:
        st.warning("⚠️ 먼저 **① 데이터 업로드** 탭에서 분석을 시작하세요.")
        st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# 2 ▸ 메인 대시보드
# ══════════════════════════════════════════════════════════════════════════════
elif page == "② 메인 대시보드":
    require_data()
    df = st.session_state["inventory_df"]
    st.markdown('<div class="main-header">② 메인 대시보드</div>', unsafe_allow_html=True)
    st.caption("전체 현황과 문제 신호를 한눈에 파악합니다.")

    # KPI
    total_stock   = df["재고수량"].sum()
    avg_sell_rate = df["판매율"].mean()
    avg_cost_rec  = df["원가회수율"].mean()
    problem_cnt   = len(df[(df["판매율"] < 30) | (df["원가회수율"] < 50)])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📦 총 재고 수량",   f"{total_stock:,}개")
    k2.metric("📈 평균 판매율",    f"{avg_sell_rate:.1f}%",
              delta=f"{avg_sell_rate - 50:.1f}%p vs. 기준 50%",
              delta_color="normal")
    k3.metric("💰 평균 원가회수율", f"{avg_cost_rec:.1f}%")
    k4.metric("⚠️ 문제 상품 수",   f"{problem_cnt}개",
              delta=f"전체의 {problem_cnt/len(df)*100:.0f}%",
              delta_color="inverse")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 카테고리별 평균 판매율")
        cat_df = df.groupby("카테고리")["판매율"].mean().reset_index().sort_values("판매율")
        fig = px.bar(
            cat_df, x="판매율", y="카테고리", orientation="h",
            color="판매율", color_continuous_scale="Blues",
            text_auto=".1f",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False, height=280)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### 브랜드 매출 순위 (판매수량 × 판매가)")
        df["매출액"] = df["판매수량"] * df["판매가"]
        brand_df = df.groupby("브랜드")["매출액"].sum().reset_index().sort_values("매출액", ascending=False)
        fig2 = px.bar(
            brand_df, x="브랜드", y="매출액",
            color="매출액", color_continuous_scale="Purples",
            text_auto=".2s",
        )
        fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False, height=280)
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.markdown("##### 문제 상품 요약 (판매율 < 30% 또는 원가회수율 < 50%)")
    problem_df = df[(df["판매율"] < 30) | (df["원가회수율"] < 50)][
        ["상품명", "브랜드", "카테고리", "재고수량", "판매율", "원가회수율"]
    ].sort_values("판매율")
    st.dataframe(
        problem_df.style.background_gradient(subset=["판매율", "원가회수율"], cmap="RdYlGn"),
        use_container_width=True, height=220,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 3 ▸ 문제 상품
# ══════════════════════════════════════════════════════════════════════════════
elif page == "③ 문제 상품":
    require_data()
    df = st.session_state["inventory_df"]
    st.markdown('<div class="main-header">③ 문제 상품</div>', unsafe_allow_html=True)
    st.caption("기준 미달 상품을 자동으로 필터링합니다.")

    # 필터
    fc1, fc2, fc3, fc4 = st.columns(4)
    brand_opt = ["전체"] + sorted(df["브랜드"].unique().tolist())
    cat_opt   = ["전체"] + sorted(df["카테고리"].unique().tolist())
    sel_brand = fc1.selectbox("브랜드", brand_opt)
    sel_cat   = fc2.selectbox("카테고리", cat_opt)
    sell_thr  = fc3.slider("판매율 기준(%)", 0, 100, 30)
    cost_thr  = fc4.slider("원가회수율 기준(%)", 0, 100, 50)

    filtered = df.copy()
    if sel_brand != "전체":
        filtered = filtered[filtered["브랜드"] == sel_brand]
    if sel_cat != "전체":
        filtered = filtered[filtered["카테고리"] == sel_cat]

    problem = filtered[(filtered["판매율"] < sell_thr) | (filtered["원가회수율"] < cost_thr)].copy()

    def status_label(row):
        if row["판매율"] < 20:   return "🔴 긴급"
        if row["판매율"] < sell_thr: return "🟡 주의"
        return "🟢 관찰"

    problem["상태"] = problem.apply(status_label, axis=1)

    st.markdown(f"**{len(problem)}개 상품** 기준 미달 (전체 {len(filtered)}개 중)")

    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 긴급", len(problem[problem["상태"] == "🔴 긴급"]))
    col2.metric("🟡 주의", len(problem[problem["상태"] == "🟡 주의"]))
    col3.metric("🟢 관찰", len(problem[problem["상태"] == "🟢 관찰"]))

    st.dataframe(
        problem[["상태", "상품명", "브랜드", "카테고리", "재고수량", "판매수량", "판매율", "원가회수율"]]
        .sort_values("판매율"),
        use_container_width=True, height=400,
    )

    # 산점도
    st.markdown("##### 판매율 vs 원가회수율 분포")
    fig = px.scatter(
        filtered, x="판매율", y="원가회수율",
        color="카테고리", size="재고수량",
        hover_data=["상품명", "브랜드", "매장"],
        opacity=0.7,
    )
    fig.add_vline(x=sell_thr, line_dash="dash", line_color="red", annotation_text="판매율 기준")
    fig.add_hline(y=cost_thr, line_dash="dash", line_color="orange", annotation_text="원가회수율 기준")
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# 4 ▸ 액션 추천
# ══════════════════════════════════════════════════════════════════════════════
elif page == "④ 액션 추천":
    require_data()
    df = st.session_state["inventory_df"]
    st.markdown('<div class="main-header">④ 액션 추천</div>', unsafe_allow_html=True)
    st.caption("무엇을 해야 하는지 바로 제시합니다.")

    # 로직
    discount_df  = df[(df["판매율"] < 25) & (df["재고수량"] > 10)].copy()
    transfer_out = df[(df["판매율"] < 20) & (df["재고수량"] > 20)].copy()
    transfer_in  = df[(df["판매율"] > 70) & (df["재고수량"] < 10)].copy()

    discount_df["권장할인율"]  = discount_df["판매율"].apply(lambda x: "30%" if x < 15 else "15%")
    transfer_out["추천점출수량"] = (transfer_out["재고수량"] * 0.4).astype(int)
    transfer_in["추천점입수량"]  = (10 - transfer_in["재고수량"]).clip(lower=1)

    t1, t2, t3 = st.tabs(["🏷️ 할인 대상 상품", "📤 점출 필요 상품", "📥 점입 필요 상품"])

    with t1:
        st.markdown(f"**{len(discount_df)}개** 상품 할인 권장")
        if len(discount_df):
            st.dataframe(
                discount_df[["상품명", "브랜드", "카테고리", "재고수량", "판매율", "판매가", "권장할인율"]]
                .sort_values("판매율"),
                use_container_width=True,
            )
            to_dl = discount_df[["상품코드", "상품명", "브랜드", "재고수량", "판매율", "권장할인율"]]
            st.download_button(
                "⬇️ 할인 대상 목록 다운로드",
                data=to_dl.to_csv(index=False, encoding="utf-8-sig"),
                file_name="할인대상상품.csv", mime="text/csv",
            )
        else:
            st.info("할인 권장 상품이 없습니다.")

    with t2:
        st.markdown(f"**{len(transfer_out)}개** 상품 점출 권장")
        if len(transfer_out):
            st.dataframe(
                transfer_out[["상품명", "브랜드", "카테고리", "매장", "재고수량", "판매율", "추천점출수량"]]
                .sort_values("판매율"),
                use_container_width=True,
            )
            to_dl2 = transfer_out[["상품코드", "상품명", "매장", "재고수량", "추천점출수량"]]
            st.download_button(
                "⬇️ 점출 목록 다운로드",
                data=to_dl2.to_csv(index=False, encoding="utf-8-sig"),
                file_name="점출대상상품.csv", mime="text/csv",
            )
        else:
            st.info("점출 권장 상품이 없습니다.")

    with t3:
        st.markdown(f"**{len(transfer_in)}개** 상품 점입 권장")
        if len(transfer_in):
            st.dataframe(
                transfer_in[["상품명", "브랜드", "카테고리", "매장", "재고수량", "판매율", "추천점입수량"]]
                .sort_values("판매율", ascending=False),
                use_container_width=True,
            )
            to_dl3 = transfer_in[["상품코드", "상품명", "매장", "재고수량", "추천점입수량"]]
            st.download_button(
                "⬇️ 점입 목록 다운로드",
                data=to_dl3.to_csv(index=False, encoding="utf-8-sig"),
                file_name="점입대상상품.csv", mime="text/csv",
            )
        else:
            st.info("점입 권장 상품이 없습니다.")


# ══════════════════════════════════════════════════════════════════════════════
# 5 ▸ 재고 이동
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⑤ 재고 이동":
    require_data()
    df = st.session_state["inventory_df"]
    st.markdown('<div class="main-header">⑤ 재고 이동</div>', unsafe_allow_html=True)
    st.caption("매장 간 재고 이동 계획을 자동으로 생성합니다.")

    stores   = df["매장"].unique().tolist()
    low_stk  = df[(df["판매율"] > 60) & (df["재고수량"] < 15)]   # 점입 필요
    high_stk = df[(df["판매율"] < 25) & (df["재고수량"] > 20)]   # 점출 필요

    # 이동 계획 생성
    moves = []
    for _, need in low_stk.iterrows():
        donors = high_stk[
            (high_stk["카테고리"] == need["카테고리"]) &
            (high_stk["매장"] != need["매장"])
        ]
        if not donors.empty:
            donor   = donors.iloc[0]
            qty     = min(int(donor["재고수량"] * 0.3), max(1, 10 - int(need["재고수량"])))
            moves.append({
                "상품명":     need["상품명"],
                "카테고리":  need["카테고리"],
                "출발 매장": donor["매장"],
                "도착 매장": need["매장"],
                "이동 수량": qty,
                "이유":      f"출발({donor['판매율']:.0f}% 판매율) → 도착({need['판매율']:.0f}% 판매율)",
            })

    move_df = pd.DataFrame(moves) if moves else pd.DataFrame(
        columns=["상품명", "카테고리", "출발 매장", "도착 매장", "이동 수량", "이유"]
    )

    st.markdown(f"**{len(move_df)}건** 재고 이동 계획 생성됨")

    # 매장별 요약
    if not move_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            out_cnt = move_df.groupby("출발 매장")["이동 수량"].sum().reset_index()
            out_cnt.columns = ["매장", "점출 수량"]
            fig = px.bar(out_cnt, x="매장", y="점출 수량", color_discrete_sequence=["#f87171"], title="매장별 점출 수량")
            fig.update_layout(height=260, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            in_cnt = move_df.groupby("도착 매장")["이동 수량"].sum().reset_index()
            in_cnt.columns = ["매장", "점입 수량"]
            fig2 = px.bar(in_cnt, x="매장", y="점입 수량", color_discrete_sequence=["#34d399"], title="매장별 점입 수량")
            fig2.update_layout(height=260, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(move_df, use_container_width=True, height=360)

        st.download_button(
            "⬇️ 재고 이동 계획 다운로드 (CSV)",
            data=move_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name="재고이동계획.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True,
        )
    else:
        st.info("현재 데이터 기준으로 생성된 이동 계획이 없습니다.")
