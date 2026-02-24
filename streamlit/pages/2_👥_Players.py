"""Page 2: Player/Group stats from set_res.csv."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from utils import load_set_res, set_res_to_long

st.set_page_config(page_title="プレイヤー別成績", page_icon="👥", layout="wide")

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("👥 プレイヤー別成績")

# ── Load data ────────────────────────────────────────────────
df_wide = load_set_res()
df_long = set_res_to_long(df_wide)

# ── Sidebar filters ──────────────────────────────────────────
with st.sidebar:
    st.header("フィルター")

    groups = sorted(df_long["member"].dropna().unique())
    selected_group = st.selectbox("グループ", groups)

    df_group = df_long[df_long["member"] == selected_group]
    players = sorted(df_group["player"].dropna().unique())
    selected_player = st.selectbox("プレイヤー", players)

    date_min = df_group["date"].min().date()
    date_max = df_group["date"].max().date()
    date_range = st.date_input(
        "日付範囲", value=(date_min, date_max), min_value=date_min, max_value=date_max
    )

# ── Filter by date ───────────────────────────────────────────
if len(date_range) == 2:
    df_group = df_group[
        (df_group["date"].dt.date >= date_range[0]) &
        (df_group["date"].dt.date <= date_range[1])
    ]

df_player = df_group[df_group["player"] == selected_player].copy()

if df_player.empty:
    st.warning("条件に一致するデータがありません。")
    st.stop()

# ── Group ranking table ──────────────────────────────────────
st.subheader(f"📊 グループ「{selected_group}」 通算ポイントランキング")

# Date-filtered group stats
group_stats = (
    df_group.groupby("player")
    .agg(
        対局数=("score", "count"),
        合計スコア=("score", "sum"),
        平均スコア=("score", "mean"),
        トップ率=("rank", lambda x: (x == 1).mean() * 100),
        平均順位=("rank", "mean"),
    )
    .reset_index()
    .sort_values("合計スコア", ascending=False)
    .rename(columns={"player": "プレイヤー"})
)

# Highlight selected player
def highlight_player(row):
    if row["プレイヤー"] == selected_player:
        return ["background-color: rgba(99,102,241,0.15)"] * len(row)
    return [""] * len(row)

group_display = group_stats.copy()
group_display["合計スコア"] = group_display["合計スコア"].apply(lambda x: f"{x:+.0f}")
group_display["平均スコア"] = group_display["平均スコア"].apply(lambda x: f"{x:+.1f}")
group_display["トップ率"] = group_display["トップ率"].apply(lambda x: f"{x:.1f}%")
group_display["平均順位"] = group_display["平均順位"].apply(lambda x: f"{x:.2f}")
st.dataframe(
    group_display.style.apply(highlight_player, axis=1),
    use_container_width=True,
    hide_index=True,
)

# Grouped bar for total scores
fig_ranking = px.bar(
    group_stats.sort_values("合計スコア", ascending=True),
    x="合計スコア",
    y="プレイヤー",
    orientation="h",
    color=group_stats.sort_values("合計スコア", ascending=True)["合計スコア"].apply(
        lambda x: "プラス" if x >= 0 else "マイナス"
    ),
    color_discrete_map={"プラス": "#22c55e", "マイナス": "#ef4444"},
    text=group_stats.sort_values("合計スコア", ascending=True)["合計スコア"].apply(lambda x: f"{x:+.0f}"),
    labels={"合計スコア": "通算ポイント (pt)", "プレイヤー": ""},
)
fig_ranking.update_traces(textposition="outside")
fig_ranking.add_vline(x=0, line_color="gray", line_dash="dash", opacity=0.5)
fig_ranking.update_layout(
    height=max(250, len(group_stats) * 45),
    showlegend=False,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor="rgba(100,100,100,0.15)"),
    yaxis=dict(showgrid=False),
)
st.plotly_chart(fig_ranking, use_container_width=True)

st.divider()
st.subheader(f"🔍 {selected_player} の個人成績（グループ: {selected_group}）")

# ── KPIs ─────────────────────────────────────────────────────
total_games = len(df_player)
total_score = df_player["score"].sum()
avg_score = df_player["score"].mean()
top_rate = (df_player["rank"] == 1).sum() / total_games * 100
avg_rank = df_player["rank"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("対局数", f"{total_games} 局")
k2.metric("累計スコア", f"{total_score:+.0f} pt")
k3.metric("1局平均", f"{avg_score:+.1f} pt")
k4.metric("トップ率", f"{top_rate:.1f} %")
k5.metric("平均順位", f"{avg_rank:.2f}")

st.divider()

# ── Cumulative trend + Rank donut ────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📈 累計スコア推移")
    df_player_sorted = df_player.sort_values(["date", "match"]).copy()
    df_player_sorted["cumulative"] = df_player_sorted["score"].cumsum()
    df_player_sorted["game_idx"] = range(1, len(df_player_sorted) + 1)

    fig_trend = px.line(
        df_player_sorted,
        x="game_idx",
        y="cumulative",
        markers=True,
        labels={"game_idx": "対局番号", "cumulative": "累計スコア (pt)"},
        hover_data={"date": "|%Y/%m/%d", "match": True, "score": True, "rank": True},
        color_discrete_sequence=["#6366f1"],
    )
    fig_trend.update_traces(marker=dict(size=6), line=dict(width=2.5))
    fig_trend.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    # Fill area
    fig_trend.add_scatter(
        x=df_player_sorted["game_idx"],
        y=df_player_sorted["cumulative"],
        fill="tozeroy",
        mode="none",
        fillcolor="rgba(99,102,241,0.1)",
        showlegend=False,
    )
    fig_trend.update_layout(
        height=340,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(100,100,100,0.15)"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_right:
    st.subheader("🏆 順位分布")
    rank_counts = df_player["rank"].value_counts().sort_index()
    rank_labels = {1: "1位", 2: "2位", 3: "3位", 4: "4位"}
    rank_colors = ["#fbbf24", "#94a3b8", "#b45309", "#ef4444"]
    fig_rank = go.Figure(go.Pie(
        labels=[rank_labels.get(r, str(r)) for r in rank_counts.index],
        values=rank_counts.values,
        hole=0.55,
        marker=dict(colors=[rank_colors[i - 1] for i in rank_counts.index]),
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

st.divider()

# ── Score distribution ───────────────────────────────────────
st.subheader("📉 スコア分布")
fig_hist = px.histogram(
    df_player,
    x="score",
    nbins=20,
    color_discrete_sequence=["#6366f1"],
    labels={"score": "スコア (pt)", "count": "回数"},
)
fig_hist.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.6)
fig_hist.add_vline(x=avg_score, line_dash="dot", line_color="#f59e0b",
                   annotation_text=f"平均 {avg_score:+.1f}", annotation_position="top right")
fig_hist.update_layout(
    height=280,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor="rgba(100,100,100,0.15)", title="回数"),
    bargap=0.05,
)
st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# ── Session detail table ─────────────────────────────────────
st.subheader("📅 セッション別成績")
session_df = (
    df_player.groupby(df_player["date"].dt.date)
    .agg(
        対局数=("score", "count"),
        合計スコア=("score", "sum"),
        平均スコア=("score", "mean"),
        トップ回数=("rank", lambda x: (x == 1).sum()),
        平均順位=("rank", "mean"),
    )
    .reset_index()
    .rename(columns={"date": "日付"})
    .sort_values("日付", ascending=False)
)
session_df["合計スコア"] = session_df["合計スコア"].apply(lambda x: f"{x:+.0f}")
session_df["平均スコア"] = session_df["平均スコア"].apply(lambda x: f"{x:+.1f}")
session_df["平均順位"] = session_df["平均順位"].apply(lambda x: f"{x:.2f}")
st.dataframe(session_df, use_container_width=True, hide_index=True)

with st.expander("📋 全対局データ"):
    raw = df_player[["date", "match", "score", "rank"]].copy()
    raw["date"] = raw["date"].dt.strftime("%Y/%m/%d")
    raw = raw.rename(columns={"date": "日付", "match": "局番", "score": "スコア", "rank": "順位"})
    raw = raw.sort_values(["日付", "局番"], ascending=[False, True])
    st.dataframe(raw, use_container_width=True, hide_index=True)
