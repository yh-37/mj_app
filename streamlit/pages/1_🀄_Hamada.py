"""Page 1: Hamada's personal mahjong stats from res_input.csv."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from utils import load_res_input

st.set_page_config(page_title="Hamadaの成績", page_icon="🀄", layout="wide")

# ── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; }
    .section-header { font-size: 1.1rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

st.title("🀄 Hamada の成績")

# ── Load data ───────────────────────────────────────────────
df_all = load_res_input()

# ── Sidebar filters ─────────────────────────────────────────
with st.sidebar:
    st.header("フィルター")

    fors_opts = {"全て": ["F", "S"], "フリー (F)": ["F"], "セット (S)": ["S"]}
    fors_label = st.selectbox("対局種別", list(fors_opts.keys()))
    selected_fors = fors_opts[fors_label]

    # Group filter (only relevant for set games)
    members_available = sorted(df_all[df_all["ForS"] == "S"]["member"].dropna().unique())
    if fors_label == "セット (S)":
        selected_members = st.multiselect("グループ", members_available, default=members_available)
    else:
        selected_members = members_available  # ignored for free games

    date_min = df_all["date"].min().date()
    date_max = df_all["date"].max().date()
    date_range = st.date_input("日付範囲", value=(date_min, date_max), min_value=date_min, max_value=date_max)

# ── Apply filters ────────────────────────────────────────────
df = df_all[df_all["ForS"].isin(selected_fors)].copy()

if fors_label == "セット (S)":
    df = df[df["member"].isin(selected_members)]

if len(date_range) == 2:
    df = df[(df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])]

if df.empty:
    st.warning("条件に一致するデータがありません。フィルターを変更してください。")
    st.stop()

# ── KPI metrics ──────────────────────────────────────────────
total_games = len(df)
avg_pm = df["pm"].mean()
win_rate = (df["rank"] == 1).sum() / total_games * 100
avg_rank = df["rank"].mean()
total_score = df["pm"].sum()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("対局数", f"{total_games} 局")
col2.metric("累計スコア", f"{total_score:+.0f} pt")
col3.metric("1局平均スコア", f"{avg_pm:+.1f} pt")
col4.metric("トップ率", f"{win_rate:.1f} %")
col5.metric("平均順位", f"{avg_rank:.2f}")

st.divider()

# ── Cumulative score trend ───────────────────────────────────
st.subheader("📈 累計スコア推移")

# Rebuild cumulative from filter
df_sorted = df.sort_values("num").copy()
df_sorted["cumulative"] = df_sorted["pm"].cumsum()

# Color by ForS
color_map = {"F": "#6366f1", "S": "#f59e0b"}
fig_trend = px.line(
    df_sorted,
    x="num",
    y="cumulative",
    color="ForS",
    color_discrete_map=color_map,
    markers=True,
    labels={"num": "対局通番", "cumulative": "累計スコア (pt)", "ForS": "種別"},
    hover_data={"date": "|%Y/%m/%d", "member": True, "rank": True, "pm": True},
)
fig_trend.update_traces(marker=dict(size=5), line=dict(width=2))
fig_trend.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
fig_trend.update_layout(
    height=380,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor="rgba(100,100,100,0.15)"),
    legend_title_text="種別",
    hovermode="x unified",
)
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ── Rank distribution + Score per game ──────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏆 順位分布")
    rank_counts = df["rank"].value_counts().sort_index()
    rank_labels = {1: "1位", 2: "2位", 3: "3位", 4: "4位"}
    rank_colors = ["#fbbf24", "#94a3b8", "#b45309", "#ef4444"]
    fig_rank = go.Figure(go.Pie(
        labels=[rank_labels.get(r, str(r)) for r in rank_counts.index],
        values=rank_counts.values,
        hole=0.55,
        marker=dict(colors=rank_colors[:len(rank_counts)]),
        textinfo="label+percent",
        hovertemplate="%{label}: %{value} 回<extra></extra>",
    ))
    fig_rank.update_layout(
        height=340,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_rank, use_container_width=True)

with col_b:
    st.subheader("📊 グループ別 平均スコア")
    if fors_label == "セット (S)":
        group_col = "member"
        group_label = "グループ"
    else:
        group_col = "ForS"
        group_label = "種別"

    avg_by_group = (
        df.groupby(group_col)["pm"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "平均スコア", "count": "対局数"})
    )
    avg_by_group["正負"] = avg_by_group["平均スコア"].apply(lambda x: "プラス" if x >= 0 else "マイナス")
    fig_grp = px.bar(
        avg_by_group,
        x=group_col,
        y="平均スコア",
        color="正負",
        color_discrete_map={"プラス": "#22c55e", "マイナス": "#ef4444"},
        text=avg_by_group["平均スコア"].apply(lambda x: f"{x:+.1f}"),
        hover_data={"対局数": True},
        labels={group_col: group_label, "平均スコア": "平均スコア (pt)"},
    )
    fig_grp.update_traces(textposition="outside")
    fig_grp.add_hline(y=0, line_color="gray", line_dash="dash", opacity=0.5)
    fig_grp.update_layout(
        height=340,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(100,100,100,0.15)"),
    )
    st.plotly_chart(fig_grp, use_container_width=True)

st.divider()

# ── Session summary ─────────────────────────────────────────
st.subheader("📅 セッション別成績")
session_df = (
    df.groupby(df["date"].dt.date)
    .agg(
        対局数=("pm", "count"),
        合計スコア=("pm", "sum"),
        平均スコア=("pm", "mean"),
        トップ回数=("rank", lambda x: (x == 1).sum()),
        平均順位=("rank", "mean"),
        種別=("ForS", lambda x: ", ".join(sorted(x.unique()))),
        グループ=("member", lambda x: ", ".join(sorted(x.dropna().unique()))),
    )
    .reset_index()
    .rename(columns={"date": "日付"})
    .sort_values("日付", ascending=False)
)
session_df["合計スコア"] = session_df["合計スコア"].apply(lambda x: f"{x:+.0f}")
session_df["平均スコア"] = session_df["平均スコア"].apply(lambda x: f"{x:+.1f}")
session_df["平均順位"] = session_df["平均順位"].apply(lambda x: f"{x:.2f}")
st.dataframe(session_df, use_container_width=True, hide_index=True)

st.divider()

# ── Raw data ────────────────────────────────────────────────
with st.expander("📋 詳細データ"):
    display_df = df[["num", "date", "ForS", "member", "match", "rank", "score", "pm"]].copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y/%m/%d")
    display_df = display_df.rename(columns={
        "num": "#", "date": "日付", "ForS": "種別", "member": "グループ",
        "match": "局番", "rank": "順位", "score": "生点", "pm": "スコア",
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)
