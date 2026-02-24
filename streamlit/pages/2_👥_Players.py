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
last4_rate = (df_player["rank"] == 4).sum() / total_games * 100
avg_rank = df_player["rank"].mean()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("対局数", f"{total_games} 局")
k2.metric("累計スコア", f"{total_score:+.0f} pt")
k3.metric("1局平均", f"{avg_score:+.1f} pt")
k4.metric("トップ率", f"{top_rate:.1f} %")
k5.metric("ラス率", f"{last4_rate:.1f} %")
k6.metric("平均順位", f"{avg_rank:.2f}")

st.divider()

# ══════════════════════════════════════════════════════════════
# 📈 累計スコア推移 + 🏆 順位分布（棒グラフ）
# ══════════════════════════════════════════════════════════════
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
    rank_counts = df_player["rank"].value_counts().sort_index().reset_index()
    rank_counts.columns = ["順位", "回数"]
    rank_counts["順位ラベル"] = rank_counts["順位"].map({1: "1位", 2: "2位", 3: "3位", 4: "4位"})
    rank_counts["率"] = rank_counts["回数"] / total_games * 100
    rank_colors_map = {1: "#fbbf24", 2: "#94a3b8", 3: "#b45309", 4: "#ef4444"}
    rank_counts["color"] = rank_counts["順位"].map(rank_colors_map)

    fig_rank = go.Figure(go.Bar(
        x=rank_counts["順位ラベル"],
        y=rank_counts["回数"],
        text=[f"{r:.0f}回<br>({p:.1f}%)" for r, p in zip(rank_counts["回数"], rank_counts["率"])],
        textposition="outside",
        marker_color=rank_counts["color"].tolist(),
        hovertemplate="%{x}: %{y} 回<extra></extra>",
    ))
    fig_rank.update_layout(
        height=340,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(100,100,100,0.15)", title="回数"),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
    )
    st.plotly_chart(fig_rank, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════
# 📅 月別スコア推移
# ══════════════════════════════════════════════════════════════
st.subheader("📅 月別スコア推移")

df_monthly = df_player.copy()
df_monthly["month"] = df_monthly["date"].dt.to_period("M").astype(str)
monthly_agg = (
    df_monthly.groupby("month")
    .agg(
        合計スコア=("score", "sum"),
        対局数=("score", "count"),
        平均スコア=("score", "mean"),
        トップ率=("rank", lambda x: (x == 1).sum() / len(x) * 100),
    )
    .reset_index()
    .rename(columns={"month": "月"})
)

fig_monthly = go.Figure()
fig_monthly.add_trace(go.Bar(
    x=monthly_agg["月"],
    y=monthly_agg["合計スコア"],
    marker_color=[("#22c55e" if v >= 0 else "#ef4444") for v in monthly_agg["合計スコア"]],
    text=[f"{v:+.0f}" for v in monthly_agg["合計スコア"]],
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>合計: %{y:+.0f} pt<br>対局数: %{customdata[0]}<br>平均: %{customdata[1]:+.1f} pt<extra></extra>",
    customdata=monthly_agg[["対局数", "平均スコア"]].values,
))
fig_monthly.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
fig_monthly.update_layout(
    height=320,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False, title="月"),
    yaxis=dict(gridcolor="rgba(100,100,100,0.15)", title="合計スコア (pt)"),
    showlegend=False,
)
st.plotly_chart(fig_monthly, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════
# 🎲 順位別スコア分布 (Box plot)
# ══════════════════════════════════════════════════════════════
st.subheader("🎲 順位別スコア分布")

rank_label_map = {1: "1位 🥇", 2: "2位 🥈", 3: "3位 🥉", 4: "4位 💀"}
rank_color_list = ["#fbbf24", "#94a3b8", "#b45309", "#ef4444"]

fig_box = go.Figure()
for i, r in enumerate([1, 2, 3, 4]):
    subset = df_player[df_player["rank"] == r]["score"]
    if subset.empty:
        continue
    fig_box.add_trace(go.Box(
        y=subset,
        name=rank_label_map[r],
        marker_color=rank_color_list[i],
        boxmean="sd",
        hovertemplate=f"<b>{rank_label_map[r]}</b><br>スコア: %{{y:+.0f}} pt<extra></extra>",
    ))
fig_box.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
fig_box.update_layout(
    height=340,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor="rgba(100,100,100,0.15)", title="スコア (pt)"),
    showlegend=False,
)
st.plotly_chart(fig_box, use_container_width=True)
st.caption("各順位でのスコア分布。中央線=中央値、×=平均値、ひげ=標準偏差範囲")

st.divider()

# ══════════════════════════════════════════════════════════════
# 🕐 直近20局の順位推移
# ══════════════════════════════════════════════════════════════
st.subheader("🕐 直近20局の順位推移")

df_recent = df_player.sort_values(["date", "match"]).tail(20).copy()
df_recent["game_idx"] = range(1, len(df_recent) + 1)
df_recent["date_str"] = df_recent["date"].dt.strftime("%m/%d")
rank_bar_colors = {1: "#fbbf24", 2: "#94a3b8", 3: "#b45309", 4: "#ef4444"}
df_recent["bar_color"] = df_recent["rank"].map(rank_bar_colors)

col_recent_l, col_recent_r = st.columns([2, 1])

with col_recent_l:
    fig_recent = go.Figure()
    fig_recent.add_trace(go.Bar(
        x=df_recent["game_idx"],
        y=df_recent["rank"],
        marker_color=df_recent["bar_color"].tolist(),
        text=df_recent["rank"].astype(str) + "位",
        textposition="inside",
        insidetextanchor="middle",
        hovertemplate="<b>%{customdata[0]}</b> 局%{customdata[1]}<br>順位: %{y}位<br>スコア: %{customdata[2]:+.0f} pt<extra></extra>",
        customdata=df_recent[["date_str", "match", "score"]].values,
    ))
    fig_recent.add_hline(
        y=df_recent["rank"].mean(),
        line_dash="dot", line_color="#a78bfa",
        annotation_text=f"期間平均 {df_recent['rank'].mean():.2f}",
        annotation_position="top right",
    )
    fig_recent.update_layout(
        height=300,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, title="直近対局 (古→新)", dtick=1),
        yaxis=dict(
            gridcolor="rgba(100,100,100,0.15)",
            title="順位",
            range=[0, 4.8],
            tickvals=[1, 2, 3, 4],
            ticktext=["1位", "2位", "3位", "4位"],
        ),
        showlegend=False,
    )
    st.plotly_chart(fig_recent, use_container_width=True)

with col_recent_r:
    recent_ranks = df_recent["rank"].tolist()
    consecutive_top = 0
    consecutive_last = 0
    for r in reversed(recent_ranks):
        if r == 1:
            consecutive_top += 1
        else:
            break
    for r in reversed(recent_ranks):
        if r == 4:
            consecutive_last += 1
        else:
            break

    st.metric("直近トップ率", f"{(df_recent['rank'] == 1).sum() / len(df_recent) * 100:.1f} %")
    st.metric("直近ラス率", f"{(df_recent['rank'] == 4).sum() / len(df_recent) * 100:.1f} %")
    st.metric("直近平均順位", f"{df_recent['rank'].mean():.2f}")
    st.metric("直近平均スコア", f"{df_recent['score'].mean():+.1f} pt")
    if consecutive_top > 1:
        st.success(f"🔥 連続トップ: {consecutive_top} 連続")
    if consecutive_last > 1:
        st.error(f"💀 連続ラス: {consecutive_last} 連続")

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
