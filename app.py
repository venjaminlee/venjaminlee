from __future__ import annotations

import html
import textwrap
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# VERSION: V37 - simplified colors/data + GAP-based single action
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="TOPS Inventory Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DESIGN SYSTEM
# =========================================================

NAVY = "#111827"
BLUE = "#356AE6"
BLUE_DARK = "#1F4EB3"
GREEN = "#2B927F"
AMBER = "#D97706"
RED = "#DC4C64"
PURPLE = "#7C5CE7"
TEXT = "#111827"
MUTED = "#6B7280"
LINE = "#E5E7EB"
BG = "#F4F6FA"
CARD = "#FFFFFF"

st.markdown(
    f"""
    <style>
    :root {{
        --navy: {NAVY};
        --blue: {BLUE};
        --text: {TEXT};
        --muted: {MUTED};
        --line: {LINE};
        --bg: {BG};
        --card: {CARD};
    }}

    html, body, [data-testid="stAppViewContainer"] {{
        background: var(--bg);
        color: var(--text);
    }}

    [data-testid="stHeader"] {{
        background: rgba(244, 246, 250, 0.82);
        backdrop-filter: blur(8px);
    }}

    .block-container {{
        max-width: 100% !important;
        /* Streamlit fixed top toolbar height reserved so the hero is not hidden */
        padding-top: 3.75rem !important;
        padding-bottom: 0.55rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }}

    section[data-testid="stSidebar"] {{
        width: 154px !important;
        background: linear-gradient(180deg, #101827 0%, #17233A 100%) !important;
        border-right: 0 !important;
    }}

    section[data-testid="stSidebar"] * {{
        color: #E5E7EB !important;
        font-size: 10px !important;
    }}

    section[data-testid="stSidebar"] [data-testid="stRadio"] label {{
        padding: 5px 7px !important;
        border-radius: 9px !important;
        margin: 1px 0 !important;
    }}

    section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {{
        background: rgba(255,255,255,0.12) !important;
        box-shadow: inset 3px 0 0 #6EA8FE;
    }}

    h1 {{
        font-size: 21px !important;
        letter-spacing: -0.03em !important;
        margin: 0 !important;
    }}

    h2, h3 {{
        font-size: 13px !important;
        letter-spacing: -0.02em !important;
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
    }}

    p, div, span, label {{
        letter-spacing: -0.01em;
    }}

    hr {{
        margin: 0.45rem 0 !important;
        border-color: #E7EAF0 !important;
    }}

    [data-testid="stExpander"] {{
        background: #FFFFFF;
        border: 1px solid #E7EAF0 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }}

    [data-testid="stFileUploader"] {{
        font-size: 10px !important;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid #E7EAF0;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }}

    div[data-testid="stDataFrame"] * {{
        font-size: 9px !important;
    }}

    [data-testid="stPlotlyChart"] {{
        border-radius: 12px;
        overflow: hidden;
    }}

    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: #FFFFFF;
        border-color: #E7EAF0 !important;
        border-radius: 16px !important;
        box-shadow: 0 7px 20px rgba(15, 23, 42, 0.05);
    }}

    .hero {{
        width: 100%;
        min-height: 68px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: center;
        background: linear-gradient(135deg, #101827 0%, #1C3470 58%, #2D63D8 100%);
        color: white;
        border-radius: 16px;
        padding: 15px 19px;
        margin-top: 2px;
        margin-bottom: 9px;
        box-shadow: 0 9px 22px rgba(17, 24, 39, 0.16);
    }}

    .hero-title {{
        font-size: 24px;
        font-weight: 850;
        letter-spacing: -0.04em;
        line-height: 1.15;
    }}

    .hero-sub {{
        font-size: 11.5px;
        color: #D8E2F5;
        margin-top: 6px;
        line-height: 1.35;
    }}

    .section-label {{
        font-size: 12px;
        font-weight: 850;
        color: #1F2937;
        letter-spacing: -0.02em;
        margin: 3px 0 4px 1px;
    }}

    .kpi-card {{
        background: #FFFFFF;
        border: 1px solid #E6E9EF;
        border-radius: 12px;
        padding: 7px 9px;
        min-height: 60px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.045);
    }}

    .kpi-top {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 3px;
    }}

    .kpi-icon {{
        width: 21px;
        height: 21px;
        border-radius: 7px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
    }}

    .kpi-label {{
        font-size: 10px;
        color: #6B7280;
    }}

    .kpi-value {{
        font-size: 20px;
        line-height: 1.05;
        font-weight: 850;
        color: #111827;
    }}

    .kpi-sub {{
        font-size: 9.2px;
        color: #9CA3AF;
        margin-top: 3px;
    }}

    .insight-card {{
        background: #FFFFFF;
        border-radius: 12px;
        padding: 8px 9px;
        min-height: 72px;
        border: 1px solid #E7EAF0;
        border-top: 3px solid #356AE6;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.045);
    }}

    .insight-title {{
        font-size: 10px;
        font-weight: 800;
        color: #4B5563;
        margin-bottom: 5px;
    }}

    .insight-value {{
        font-size: 18px;
        font-weight: 850;
        color: #111827;
        line-height: 1.1;
    }}

    .insight-desc {{
        font-size: 9.4px;
        color: #6B7280;
        line-height: 1.35;
        margin-top: 4px;
    }}

    .action-card {{
        background: #FFFFFF;
        border: 1px solid #E7EAF0;
        border-radius: 12px;
        padding: 8px 9px;
        min-height: 70px;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.045);
    }}

    .action-line {{
        height: 3px;
        border-radius: 999px;
        margin-bottom: 7px;
    }}

    .action-title {{
        font-size: 10px;
        color: #4B5563;
        font-weight: 800;
    }}

    .action-value {{
        font-size: 18px;
        font-weight: 850;
        color: #111827;
        margin-top: 2px;
        overflow: visible;
    }}

    .action-desc {{
        font-size: 9.4px;
        color: #6B7280;
        line-height: 1.35;
        margin-top: 3px;
    }}

    .muted-box {{
        background: #FFFFFF;
        border: 1px solid #E7EAF0;
        border-radius: 13px;
        padding: 9px 11px;
        font-size: 10px;
        color: #4B5563;
        box-shadow: 0 5px 15px rgba(15, 23, 42, 0.04);
    }}

    .small-note {{
        font-size: 9px;
        color: #8A94A6;
        margin-top: -2px;
        margin-bottom: 5px;
    }}

    .table-card {{
        background: #FFFFFF;
        border: 1px solid #E7EAF0;
        border-radius: 13px;
        padding: 9px 10px 7px 10px;
        box-shadow: 0 5px 15px rgba(15, 23, 42, 0.045);
        margin-top: 2px;
    }}

    .table-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 6px;
    }}

    .table-title {{
        font-size: 12px;
        font-weight: 850;
        color: #1F2937;
    }}

    .table-meta {{
        font-size: 9px;
        color: #8A94A6;
        margin-left: 6px;
    }}

    .table-link {{
        font-size: 9px;
        color: #356AE6;
        font-weight: 700;
    }}

    .compact-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        table-layout: fixed;
        font-size: 9.8px;
        color: #374151;
    }}

    .compact-table th {{
        background: #F6F8FB;
        color: #6B7280;
        font-weight: 800;
        padding: 5px 6px;
        border-top: 1px solid #E7EAF0;
        border-bottom: 1px solid #E7EAF0;
        text-align: left;
        white-space: normal;
        word-break: keep-all;
        overflow-wrap: anywhere;
        line-height: 1.25;
    }}

    .compact-table th:first-child {{
        border-left: 1px solid #E7EAF0;
        border-top-left-radius: 8px;
    }}

    .compact-table th:last-child {{
        border-right: 1px solid #E7EAF0;
        border-top-right-radius: 8px;
    }}

    .compact-table td {{
        min-height: 28px;
        padding: 6px 7px;
        border-bottom: 1px solid #EEF1F5;
        background: #FFFFFF;
        vertical-align: middle;
        white-space: normal;
        word-break: keep-all;
        overflow-wrap: anywhere;
        overflow: visible;
        text-overflow: clip;
        line-height: 1.35;
    }}

    .compact-table tbody tr:hover td {{
        background: #F8FAFD;
    }}

    .compact-table .num {{
        text-align: right;
        font-variant-numeric: tabular-nums;
    }}

    .compact-table .negative {{
        color: #C24158;
        font-weight: 800;
    }}

    .badge {{
        display: inline-block;
        padding: 2px 6px;
        border-radius: 999px;
        font-size: 8.8px;
        font-weight: 800;
        line-height: 1.2;
    }}

    .badge-red {{ background: #FFF0F2; color: #C24158; }}
    .badge-amber {{ background: #FFF7E6; color: #B45309; }}
    .badge-blue {{ background: #EDF4FF; color: #2859B8; }}
    .badge-green {{ background: #ECF8F4; color: #0F766E; }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 5px;
    }}

    .stTabs [data-baseweb="tab"] {{
        height: 30px;
        padding: 0 12px;
        border-radius: 9px;
        background: #EEF1F6;
        font-size: 10.5px;
    }}

    .stTabs [aria-selected="true"] {{
        background: #1F4EB3 !important;
        color: white !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def make_unique_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = []
    seen: dict[str, int] = {}
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


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for candidate in candidates:
        for col in df.columns:
            if candidate == col:
                return col
    for candidate in candidates:
        for col in df.columns:
            if candidate in col:
                return col
    return None


def to_number(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .replace(["", "nan", "None"], "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def format_number_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_numeric_dtype(out[col]):
            if "율" in col or "GAP" in col:
                out[col] = out[col].round(1)
            else:
                out[col] = out[col].round(0).astype(int)
    return out


def render_html_table(
    df: pd.DataFrame,
    title: str,
    note: str = "",
    column_widths: list[int] | None = None,
) -> None:
    """Render a full-width table without its own vertical or horizontal scrollbar."""
    if df is None or df.empty:
        st.info(f"{title} 데이터가 없습니다.")
        return

    view = df.copy()
    columns = [str(col) for col in view.columns]

    if column_widths and len(column_widths) == len(columns):
        colgroup = "<colgroup>" + "".join(
            f'<col style="width:{width}%">' for width in column_widths
        ) + "</colgroup>"
    else:
        colgroup = ""

    def format_cell(col: str, value) -> tuple[str, str]:
        if pd.isna(value):
            return "-", ""

        text = str(value)

        if col == "상태":
            if "판매부진" in text or "위험" in text:
                cls = "badge-red"
            elif "주의" in text:
                cls = "badge-amber"
            else:
                cls = "badge-green"
            return f'<span class="badge {cls}">{html.escape(text)}</span>', ""

        if col == "추천액션":
            if "2차" in text:
                cls = "badge-red"
            elif "1차" in text:
                cls = "badge-amber"
            elif "점 이동" in text:
                cls = "badge-blue"
            else:
                cls = "badge-green"
            return f'<span class="badge {cls}">{html.escape(text)}</span>', ""

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            numeric = float(value)
            if col == "GAP":
                return f"{numeric:.1f}%p", "num negative" if numeric < 0 else "num"
            if "율" in col:
                return f"{numeric:.1f}%", "num"
            if col == "면적당판매":
                return f"{numeric:,.2f}", "num"
            if numeric.is_integer():
                return f"{int(numeric):,}", "num"
            return f"{numeric:,.1f}", "num"

        return html.escape(text), ""

    head_html = "".join(f"<th>{html.escape(col)}</th>" for col in columns)
    rows_html = []

    for _, row in view.iterrows():
        cells = []
        for col in columns:
            cell_html, cell_cls = format_cell(col, row[col])
            class_attr = f' class="{cell_cls}"' if cell_cls else ""
            cells.append(f"<td{class_attr}>{cell_html}</td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    meta_html = f'<span class="table-meta">{html.escape(note)}</span>' if note else ""
    table_html = (
        '<div class="table-card">'
        '<div class="table-head">'
        f'<div><span class="table-title">{html.escape(title)}</span>{meta_html}</div>'
        '</div>'
        '<table class="compact-table">'
        f'{colgroup}<thead><tr>{head_html}</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        '</table></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


def read_excel(uploaded_file, sheet_name=0) -> pd.DataFrame:
    return pd.read_excel(BytesIO(uploaded_file.getvalue()), sheet_name=sheet_name, engine="openpyxl")


def read_inventory_workbook(uploaded_file) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = BytesIO(uploaded_file.getvalue())
    xls = pd.ExcelFile(raw, engine="openpyxl")
    inventory_df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])

    master_df = pd.DataFrame()
    if "점포마스터" in xls.sheet_names:
        master_df = pd.read_excel(xls, sheet_name="점포마스터")

    return make_unique_columns(inventory_df), make_unique_columns(master_df) if not master_df.empty else master_df


def classify_action(row: pd.Series) -> pd.Series:
    """Assign one primary buyer action from the GAP severity only."""
    gap = float(row["GAP"])

    if gap < -30:
        return pd.Series(["🔴 판매부진", "2차 가격 조정 검토"])
    if gap < -20:
        return pd.Series(["🔴 판매부진", "1차 가격 조정 검토"])
    if gap < -10:
        return pd.Series(["🟡 주의", "점 이동 검토"])
    return pd.Series(["🔵 정상", "유지·모니터링"])


def diagnose_reason(row: pd.Series) -> str:
    if row["GAP"] < -10 and row["재고"] > row["판매"] * 2:
        return "목표 미달 + 재고 과다"
    if row["GAP"] < -10:
        return "목표 대비 판매 부진"
    if row["재고"] > row["판매"] * 3:
        return "재고 과다"
    if row["총판매율"] < 30:
        return "판매 저조"
    if row["경과개월"] > 7 and row["총판매율"] < 80:
        return "시즌 경과 체화 우려"
    return "정상 범위"


def kpi_card(icon: str, label: str, value: str, subtext: str, tint: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <div class="kpi-label">{label}</div>
                <div class="kpi-icon" style="background:{tint};">{icon}</div>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title: str, value: str, desc: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card" style="border-top-color:{accent};">
            <div class="insight-title">{title}</div>
            <div class="insight-value">{value}</div>
            <div class="insight-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def action_card(title: str, value: str, desc: str, color: str) -> None:
    st.markdown(
        f"""
        <div class="action-card">
            <div class="action-line" style="background:{color};"></div>
            <div class="action-title">{title}</div>
            <div class="action-value">{value}</div>
            <div class="action-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plot(fig, height: int = 220) -> None:
    fig.update_layout(
        height=height,
        margin=dict(l=5, r=10, t=8, b=5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color="#4B5563"),
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor="#EEF1F5",
            zeroline=False,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="",
            showgrid=False,
            tickfont=dict(size=10),
        ),
        showlegend=False,
    )


# =========================================================
# HEADER / SIDEBAR / UPLOAD
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">TOPS Inventory Intelligence</div>
        <div class="hero-sub">데이터를 보는 것이 아니라, 무엇을 해야 하는지 알려주는 AI 바이어 어시스턴트</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## TOPS AI")
    selected_menu = st.radio(
        "메뉴",
        [
            "대시보드",
            "브랜드 · 점포",
            "AI 인사이트",
            "AI 액션",
            "상세 진단",
        ],
        label_visibility="collapsed",
    )

with st.expander("📂 데이터 업로드", expanded=False):
    up1, up2, up3 = st.columns(3)
    with up1:
        inventory_file = st.file_uploader("재고 파일", type=["xlsx"])
    with up2:
        summary_file = st.file_uploader("총괄장", type=["xlsx"])
    with up3:
        sales_file = st.file_uploader("판매리스트", type=["xlsx"])


# =========================================================
# MAIN DATA PIPELINE
# =========================================================

if not (inventory_file and summary_file and sales_file):
    st.markdown(
        """
        <div class="muted-box">
            상단의 <b>데이터 업로드</b>를 열고 재고 파일, 총괄장, 판매리스트를 업로드해주세요.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

inventory, store_master = read_inventory_workbook(inventory_file)
summary = make_unique_columns(read_excel(summary_file))
sales = make_unique_columns(read_excel(sales_file))

# Column mapping
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

required = {
    "재고 스타일코드": inv_style_col,
    "재고 점포": inv_store_col,
    "재고 수량": inv_stock_col,
    "판매 스타일코드": sales_style_col,
    "판매 점포": sales_store_col,
    "판매 수량": sales_qty_col,
    "총괄 판매": sum_sales_col,
    "총괄 재고": sum_stock_col,
    "총괄 스타일코드": style_col,
}
missing = [name for name, col in required.items() if col is None]
if missing:
    st.error("필수 컬럼을 찾을 수 없습니다: " + ", ".join(missing))
    st.stop()

inventory[inv_stock_col] = to_number(inventory[inv_stock_col])
summary[sum_sales_col] = to_number(summary[sum_sales_col])
summary[sum_stock_col] = to_number(summary[sum_stock_col])
sales[sales_qty_col] = to_number(sales[sales_qty_col])
if sales_amt_col:
    sales[sales_amt_col] = to_number(sales[sales_amt_col])

category_target = {"잡화": 60, "의류": 60, "슈즈": 50}

df = summary.copy()
df["판매"] = to_number(df[sum_sales_col])
df["재고"] = to_number(df[sum_stock_col])

group_dict: dict[str, str] = {"판매": "sum", "재고": "sum"}
for col in [style_name_col, category_col, brand_col, season_col]:
    if col:
        group_dict[col] = "first"

diagnosis = df.groupby(style_col).agg(group_dict).reset_index()
diagnosis["총판매율"] = diagnosis.apply(
    lambda x: x["판매"] / (x["판매"] + x["재고"]) * 100
    if (x["판매"] + x["재고"]) > 0
    else 0,
    axis=1,
).round(1)

diagnosis["목표판매율"] = (
    diagnosis[category_col].map(category_target).fillna(60)
    if category_col
    else 60
)
diagnosis["경과개월"] = 7
diagnosis["기대판매율"] = (
    diagnosis["목표판매율"] * (diagnosis["경과개월"] / 7)
).round(1)
diagnosis["GAP"] = (diagnosis["총판매율"] - diagnosis["기대판매율"]).round(1)
diagnosis[["상태", "추천액션"]] = diagnosis.apply(classify_action, axis=1)
diagnosis["문제원인"] = diagnosis.apply(diagnose_reason, axis=1)

# Sidebar filters
filter_df = diagnosis.copy()
with st.sidebar:
    st.divider()
    st.markdown("### 분석 필터")

    if category_col:
        category_options = ["전체"] + sorted(
            diagnosis[category_col].dropna().astype(str).unique().tolist()
        )
        selected_category = st.selectbox("카테고리", category_options)
        if selected_category != "전체":
            filter_df = filter_df[
                filter_df[category_col].astype(str) == selected_category
            ]

    if brand_col:
        brand_options = ["전체"] + sorted(
            filter_df[brand_col].dropna().astype(str).unique().tolist()
        )
        selected_brand = st.selectbox("브랜드", brand_options)
        if selected_brand != "전체":
            filter_df = filter_df[
                filter_df[brand_col].astype(str) == selected_brand
            ]

# Summary KPI
total_sales = float(summary[sum_sales_col].sum())
total_stock = float(summary[sum_stock_col].sum())
sell_through = (
    total_sales / (total_sales + total_stock) * 100
    if (total_sales + total_stock) > 0
    else 0
)
target_rate = 60
gap_to_target = sell_through - target_rate

action_mask = filter_df["추천액션"].astype(str) != "유지·모니터링"
action_count = int(action_mask.sum())
top_action_df = filter_df[action_mask].copy()

risk_count = int(
    (filter_df["추천액션"].astype(str) == "2차 가격 조정 검토").sum()
)
stock_bad = int((filter_df["재고"] > filter_df["판매"] * 2).sum())
avg_gap = float(top_action_df["GAP"].mean()) if not top_action_df.empty else 0.0
review_reduction = (
    (1 - action_count / len(filter_df)) * 100 if len(filter_df) > 0 else 0
)

# Store analysis & recommendations
rec_df = pd.DataFrame()
allocation = pd.DataFrame()
store_perf_summary = pd.DataFrame()

store_stock_only = inventory.copy()
if inv_type_col:
    store_stock_only = store_stock_only[
        ~store_stock_only[inv_type_col].astype(str).str.contains("창고", na=False)
    ].copy()

stock_by_store_style = (
    store_stock_only.groupby([inv_style_col, inv_store_col])[inv_stock_col]
    .sum()
    .reset_index()
)
sales_by_store_style = (
    sales.groupby([sales_style_col, sales_store_col])[sales_qty_col]
    .sum()
    .reset_index()
)
stock_by_store_style.columns = ["스타일코드", "점포명", "재고"]
sales_by_store_style.columns = ["스타일코드", "점포명", "최근3개월판매"]

store_perf = pd.merge(
    stock_by_store_style,
    sales_by_store_style,
    on=["스타일코드", "점포명"],
    how="left",
)
store_perf["최근3개월판매"] = store_perf["최근3개월판매"].fillna(0)

recommendations: list[dict] = []
for style in store_perf["스타일코드"].dropna().unique():
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
            recommendations.append(
                {
                    "스타일코드": style,
                    "재고과다점": source["점포명"],
                    "판매우수점": dest["점포명"],
                    "추천수량": qty,
                    "출발재고": int(source["재고"]),
                    "출발3개월판매": int(source["최근3개월판매"]),
                    "도착재고": int(dest["재고"]),
                    "도착3개월판매": int(dest["최근3개월판매"]),
                    "추천사유": "판매 저조 점포 과재고 → 판매 우수 점포 이동",
                }
            )

rec_df = pd.DataFrame(recommendations)

stock_store_sum = (
    store_stock_only.groupby(inv_store_col)[inv_stock_col].sum().reset_index()
)
sales_store_sum = sales.groupby(sales_store_col)[sales_qty_col].sum().reset_index()
stock_store_sum.columns = ["점포명", "재고"]
sales_store_sum.columns = ["점포명", "판매"]

store_perf_summary = pd.merge(
    stock_store_sum,
    sales_store_sum,
    on="점포명",
    how="left",
)
store_perf_summary["판매"] = store_perf_summary["판매"].fillna(0)
store_perf_summary["판매율"] = store_perf_summary.apply(
    lambda x: x["판매"] / (x["판매"] + x["재고"]) * 100
    if (x["판매"] + x["재고"]) > 0
    else 0,
    axis=1,
).round(1)

# Store master merge (optional)
if not store_master.empty:
    master_store_col = find_col(store_master, ["점포명", "매장명", "점포"])
    grade_col = find_col(store_master, ["점포등급", "등급"])
    area_col = find_col(store_master, ["매출면적", "실면적", "면적"])

    if master_store_col:
        merge_cols = [master_store_col]
        if grade_col:
            merge_cols.append(grade_col)
        if area_col:
            merge_cols.append(area_col)
            store_master[area_col] = to_number(store_master[area_col])

        master_view = store_master[merge_cols].drop_duplicates().copy()
        master_view = master_view.rename(columns={master_store_col: "점포명"})
        store_perf_summary = store_perf_summary.merge(
            master_view,
            on="점포명",
            how="left",
        )

        if area_col and area_col in store_perf_summary.columns:
            store_perf_summary["면적당판매"] = store_perf_summary.apply(
                lambda x: x["판매"] / x[area_col] if x[area_col] > 0 else 0,
                axis=1,
            ).round(2)

# Warehouse allocation
if inv_type_col:
    warehouse = inventory[
        inventory[inv_type_col].astype(str).str.contains("창고", na=False)
    ].copy()

    if not warehouse.empty:
        wh_stock = warehouse.groupby(inv_style_col)[inv_stock_col].sum().reset_index()
        wh_stock.columns = ["스타일코드", "창고재고"]

        sales_rank = (
            sales.groupby([sales_style_col, sales_store_col])[sales_qty_col]
            .sum()
            .reset_index()
        )
        sales_rank.columns = ["스타일코드", "추천점포", "최근3개월판매"]
        sales_rank = sales_rank.sort_values(
            ["스타일코드", "최근3개월판매"], ascending=[True, False]
        ).groupby("스타일코드", as_index=False).head(1)

        allocation = pd.merge(wh_stock, sales_rank, on="스타일코드", how="left")
        allocation["추천수량"] = allocation.apply(
            lambda x: min(int(x["창고재고"]), 5)
            if pd.notna(x["최근3개월판매"])
            else 0,
            axis=1,
        )
        allocation["추천사유"] = "창고재고 보유 + 최근 판매 우수 점포 우선 배분"
        allocation = allocation[allocation["추천수량"] > 0].sort_values(
            ["창고재고", "최근3개월판매"], ascending=[False, False]
        )

# Brand performance
brand_perf = pd.DataFrame()
if brand_col:
    brand_perf = (
        diagnosis.groupby(brand_col)
        .agg({"판매": "sum", "재고": "sum", style_col: "nunique"})
        .reset_index()
    )
    brand_perf["판매율"] = brand_perf.apply(
        lambda x: x["판매"] / (x["판매"] + x["재고"]) * 100
        if (x["판매"] + x["재고"]) > 0
        else 0,
        axis=1,
    ).round(1)

# Category performance
cat_perf = pd.DataFrame()
if category_col:
    cat_perf = (
        diagnosis.groupby(category_col)
        .agg({"판매": "sum", "재고": "sum", style_col: "nunique"})
        .reset_index()
    )
    cat_perf["판매율"] = cat_perf.apply(
        lambda x: x["판매"] / (x["판매"] + x["재고"]) * 100
        if (x["판매"] + x["재고"]) > 0
        else 0,
        axis=1,
    ).round(1)
    cat_perf["목표판매율"] = cat_perf[category_col].map(category_target).fillna(60)
    cat_perf["GAP"] = (cat_perf["판매율"] - cat_perf["목표판매율"]).round(1)


# =========================================================
# SHARED UI BLOCKS
# =========================================================

def render_kpis() -> None:
    st.markdown('<div class="section-label">Executive Dashboard</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("↗", "판매율", f"{sell_through:.1f}%", "전체 누계 판매 기준", "#E9F0FF")
    with c2:
        kpi_card("±", "목표 대비 GAP", f"{gap_to_target:.1f}%p", f"목표 판매율 {target_rate}%", "#F3F4F6")
    with c3:
        kpi_card("!", "최우선 관리", f"{risk_count:,}", "2차 가격 조정 검토", "#FFF1F2")
    with c4:
        kpi_card("#", "관리 상품", f"{len(filter_df):,}", "분석 대상", "#F1ECFF")


def render_insight_cards() -> None:
    st.markdown('<div class="section-label">AI Insight</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        insight_card(
            "평균 GAP",
            f"{avg_gap:.1f}%p",
            "조치 대상 상품의 평균 목표 대비 부족폭입니다.",
            AMBER,
        )
    with cols[1]:
        insight_card(
            "과재고 의심",
            f"{stock_bad}개",
            "판매수량 대비 재고가 두 배를 초과한 상품입니다.",
            BLUE,
        )
    with cols[2]:
        insight_card(
            "검토 대상 감소",
            f"{review_reduction:.0f}%",
            "전수 검토 대비 우선 점검 대상을 줄였습니다.",
            GREEN,
        )


def render_brand_store_charts() -> None:
    st.markdown('<div class="section-label">Portfolio Snapshot</div>', unsafe_allow_html=True)
    donut_area, brand_area, store_area = st.columns([0.82, 1.18, 1.18])

    with donut_area:
        with st.container(border=True):
            st.subheader("상품 상태 분포")

            status_df = pd.DataFrame(
                {
                    "상태": ["정상", "주의", "판매부진"],
                    "상품수": [
                        int(filter_df["상태"].astype(str).str.contains("정상").sum()),
                        int(filter_df["상태"].astype(str).str.contains("주의").sum()),
                        int(filter_df["상태"].astype(str).str.contains("판매부진").sum()),
                    ],
                }
            )
            status_df = status_df[status_df["상품수"] > 0]

            fig = px.pie(
                status_df,
                names="상태",
                values="상품수",
                hole=0.70,
                color="상태",
                color_discrete_map={
                    "정상": "#356AE6",
                    "주의": "#D9A441",
                    "판매부진": "#D95B70",
                },
            )
            fig.update_traces(
                textinfo="percent",
                textfont_size=9,
                marker=dict(line=dict(color="#FFFFFF", width=2)),
                hovertemplate="%{label}<br>%{value}개 · %{percent}<extra></extra>",
            )
            fig.add_annotation(
                text=f"<b>{len(filter_df):,}</b><br><span style='font-size:9px;color:#8A94A6'>관리상품</span>",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=19, color="#111827"),
            )
            fig.update_layout(
                height=190,
                margin=dict(l=0, r=0, t=2, b=12),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    orientation="h",
                    y=-0.08,
                    x=0.5,
                    xanchor="center",
                    font=dict(size=9, color="#6B7280"),
                    itemwidth=34,
                ),
                showlegend=True,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with brand_area:
        with st.container(border=True):
            st.subheader("브랜드별 판매율 TOP 6")
            if not brand_perf.empty:
                top = brand_perf.sort_values("판매율", ascending=False).head(6)
                fig = px.bar(
                    top,
                    x="판매율",
                    y=brand_col,
                    orientation="h",
                    text="판매율",
                    color_discrete_sequence=[BLUE],
                )
                fig.update_traces(
                    textposition="outside",
                    textfont_size=9,
                    marker_line_width=0,
                    cliponaxis=False,
                )
                fig.update_yaxes(autorange="reversed")
                fig.add_vline(
                    x=target_rate,
                    line_dash="dot",
                    line_color="#C9CFDA",
                    annotation_text="목표",
                    annotation_font_size=8,
                    annotation_font_color="#8A94A6",
                )
                style_plot(fig, 190)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("브랜드 컬럼을 찾을 수 없습니다.")

    with store_area:
        with st.container(border=True):
            st.subheader("점포별 판매율 TOP 6")
            if not store_perf_summary.empty:
                top = store_perf_summary.sort_values("판매율", ascending=False).head(6)
                fig = px.bar(
                    top,
                    x="판매율",
                    y="점포명",
                    orientation="h",
                    text="판매율",
                    color_discrete_sequence=[GREEN],
                )
                fig.update_traces(
                    textposition="outside",
                    textfont_size=9,
                    marker_line_width=0,
                    cliponaxis=False,
                )
                fig.update_yaxes(autorange="reversed")
                fig.add_vline(
                    x=target_rate,
                    line_dash="dot",
                    line_color="#C9CFDA",
                    annotation_text="목표",
                    annotation_font_size=8,
                    annotation_font_color="#8A94A6",
                )
                style_plot(fig, 190)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("점포 분석을 위한 컬럼을 찾을 수 없습니다.")


def render_action_cards() -> None:
    st.markdown('<div class="section-label">AI Action Recommendations</div>', unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)
    with a1:
        action_card("우선 조치 상품", f"{action_count}개", "목표 대비 부족폭이 큰 상품부터 우선 점검", RED)
    with a2:
        action_card("점출 / 점입 추천", f"{len(rec_df)}건", "재고 과다 점포에서 판매 우수 점포로 이동", BLUE)
    with a3:
        action_card("창고 배분 추천", f"{len(allocation)}건", "창고 재고를 판매 우수 점포 중심으로 배분", GREEN)


def render_priority_table(height: int = 225) -> None:
    cols = []
    for col in [
        style_name_col,
        brand_col,
        category_col,
        "총판매율",
        "GAP",
        "재고",
        "문제원인",
        "추천액션",
    ]:
        if col and col in filter_df.columns and col not in cols:
            cols.append(col)

    view = filter_df.sort_values(["GAP", "재고"], ascending=[True, False]).head(18)[cols].copy()
    render_html_table(
        view,
        "AI 우선 발견사항",
        "GAP 기준 상위 18개 · 하나의 우선 액션만 제시",
        [21, 11, 8, 8, 8, 8, 18, 18][:len(cols)],
    )


def render_priority_compact_table(limit: int = 15) -> None:
    product_col = style_name_col if style_name_col and style_name_col in filter_df.columns else style_col
    brand_view_col = brand_col if brand_col and brand_col in filter_df.columns else None

    priority = filter_df.sort_values(
        ["GAP", "재고"],
        ascending=[True, False],
    ).head(limit)

    def esc(value) -> str:
        if pd.isna(value):
            return "-"
        return html.escape(str(value))

    rows = []
    for _, row in priority.iterrows():
        action = str(row.get("추천액션", ""))

        if "2차" in action:
            action_cls = "badge-red"
        elif "1차" in action:
            action_cls = "badge-amber"
        elif "점 이동" in action:
            action_cls = "badge-blue"
        else:
            action_cls = "badge-green"

        sell_rate = float(row.get("총판매율", 0))
        gap = float(row.get("GAP", 0))
        stock = int(round(float(row.get("재고", 0))))
        brand_name = esc(row.get(brand_view_col, "-")) if brand_view_col else "-"

        rows.append(
            textwrap.dedent(
                f"""
                <tr>
                    <td class="product-cell" title="{esc(row.get(product_col, '-'))}">{esc(row.get(product_col, '-'))}</td>
                    <td title="{brand_name}">{brand_name}</td>
                    <td class="num">{sell_rate:.1f}%</td>
                    <td class="num {'negative' if gap < 0 else ''}">{gap:.1f}%p</td>
                    <td class="num">{stock:,}</td>
                    <td class="reason-cell" title="{esc(row.get('문제원인', '-'))}">{esc(row.get('문제원인', '-'))}</td>
                    <td><span class="badge {action_cls}">{esc(action)}</span></td>
                </tr>
                """
            ).strip()
        )

    table_html = textwrap.dedent(
        f"""
        <div class="table-card">
        <div class="table-head">
            <div>
                <span class="table-title">AI 우선 조치 TOP {limit}</span>
                <span class="table-meta">GAP 및 재고 위험도 기준 · 상품별 하나의 우선 액션 제시</span>
            </div>
            <div class="table-link">상세 진단 메뉴에서 전체 보기</div>
        </div>
        <table class="compact-table">
            <colgroup>
                <col style="width:23%">
                <col style="width:11%">
                <col style="width:8%">
                <col style="width:8%">
                <col style="width:8%">
                <col style="width:22%">
                <col style="width:20%">
            </colgroup>
            <thead>
                <tr>
                    <th>상품명</th>
                    <th>브랜드</th>
                    <th style="text-align:right">판매율</th>
                    <th style="text-align:right">GAP</th>
                    <th style="text-align:right">재고</th>
                    <th>문제 원인</th>
                    <th>추천 액션</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
            </table>
        </div>
        """
    ).strip()
    st.markdown(table_html, unsafe_allow_html=True)


def render_full_table(height: int = 330) -> None:
    cols = []
    for col in [
        style_col,
        style_name_col,
        category_col,
        brand_col,
        season_col,
        "판매",
        "재고",
        "총판매율",
        "GAP",
        "문제원인",
        "추천액션",
    ]:
        if col and col in filter_df.columns and col not in cols:
            cols.append(col)

    view = filter_df[cols].sort_values(["GAP", "재고"], ascending=[True, False]).copy()
    widths = [8, 17, 7, 9, 6, 6, 6, 8, 8, 12, 13]
    render_html_table(
        view,
        "상품 전체 진단",
        f"총 {len(view):,}개 상품 · GAP에 따라 단일 우선 액션 제시",
        widths[:len(cols)],
    )


# =========================================================
# PAGE ROUTING
# =========================================================

if selected_menu == "대시보드":
    render_kpis()
    render_insight_cards()
    render_brand_store_charts()
    render_action_cards()
    render_priority_compact_table(15)

elif selected_menu == "브랜드 · 점포":
    render_kpis()
    render_brand_store_charts()

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("브랜드 운영 상세")
            if not brand_perf.empty:
                brand_view = brand_perf.sort_values("판매율", ascending=False).copy()
                brand_view = brand_view.rename(columns={style_col: "스타일수"})
                brand_table = brand_view[[brand_col, "판매율", "판매", "재고", "스타일수"]].copy()
                render_html_table(
                    brand_table,
                    "브랜드 운영 상세",
                    f"총 {len(brand_table):,}개 브랜드",
                    [32, 17, 17, 17, 17],
                )
            else:
                st.info("브랜드 데이터가 없습니다.")

    with right:
        with st.container(border=True):
            st.subheader("점포 운영 상세")
            store_cols = [c for c in ["점포명", "판매율", "판매", "재고", "면적당판매"] if c in store_perf_summary.columns]
            store_table = store_perf_summary.sort_values("판매율", ascending=False)[store_cols].copy()
            store_widths = [34, 18, 16, 16, 16][:len(store_cols)]
            render_html_table(
                store_table,
                "점포 운영 상세",
                f"총 {len(store_table):,}개 점포",
                store_widths,
            )

    if not cat_perf.empty:
        with st.container(border=True):
            st.subheader("카테고리별 판매율")
            fig = px.bar(
                cat_perf,
                x=category_col,
                y=["판매율", "목표판매율"],
                barmode="group",
                color_discrete_sequence=[BLUE, "#CBD5E1"],
            )
            style_plot(fig, 220)
            fig.update_layout(legend=dict(orientation="h", y=1.08, x=0))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

elif selected_menu == "AI 인사이트":
    render_kpis()
    render_insight_cards()

    render_priority_table(300)

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.subheader("최저 판매율 브랜드")
            if not brand_perf.empty:
                low_brand = brand_perf.sort_values("판매율").head(8)
                fig = px.bar(
                    low_brand,
                    x="판매율",
                    y=brand_col,
                    orientation="h",
                    text="판매율",
                    color_discrete_sequence=[RED],
                )
                fig.update_yaxes(autorange="reversed")
                fig.update_traces(textposition="outside")
                style_plot(fig, 220)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with right:
        with st.container(border=True):
            st.subheader("판매율 하위 점포")
            low_store = store_perf_summary.sort_values("판매율").head(8)
            fig = px.bar(
                low_store,
                x="판매율",
                y="점포명",
                orientation="h",
                text="판매율",
                color_discrete_sequence=[AMBER],
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_traces(textposition="outside")
            style_plot(fig, 220)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

elif selected_menu == "AI 액션":
    render_kpis()
    render_action_cards()

    tabs = st.tabs(["점출 / 점입", "창고 배분", "우선 조치"])
    with tabs[0]:
        if not rec_df.empty:
            rec_view = rec_df.head(40).copy()
            rec_view["출발 현황"] = rec_view.apply(
                lambda x: f"재고 {int(x['출발재고'])} / 3개월판매 {int(x['출발3개월판매'])}",
                axis=1,
            )
            rec_view["도착 현황"] = rec_view.apply(
                lambda x: f"재고 {int(x['도착재고'])} / 3개월판매 {int(x['도착3개월판매'])}",
                axis=1,
            )
            rec_view = rec_view[[
                "스타일코드", "재고과다점", "판매우수점", "추천수량",
                "출발 현황", "도착 현황", "추천사유",
            ]]
            render_html_table(
                rec_view,
                "점출 / 점입 추천",
                f"상위 {len(rec_view):,}건",
                [13, 12, 12, 8, 16, 16, 23],
            )
        else:
            st.info("현재 조건에 해당하는 점출/점입 추천 항목이 없습니다.")
    with tabs[1]:
        if not allocation.empty:
            allocation_view = allocation.head(40).copy()
            allocation_cols = [
                c for c in [
                    "스타일코드", "추천점포", "창고재고", "최근3개월판매",
                    "추천수량", "추천사유",
                ] if c in allocation_view.columns
            ]
            allocation_view = allocation_view[allocation_cols]
            allocation_widths = [16, 17, 13, 15, 12, 27][:len(allocation_cols)]
            render_html_table(
                allocation_view,
                "창고 배분 추천",
                f"상위 {len(allocation_view):,}건",
                allocation_widths,
            )
        else:
            st.info("현재 조건에 해당하는 창고 배분 추천 항목이 없습니다.")
    with tabs[2]:
        render_priority_table(360)

else:
    render_kpis()
    render_full_table(520)





