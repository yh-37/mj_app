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

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; }
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

    members_available = sorted(df_all[df_all["ForS"] == "S"]["member"].dropna().unique())
    if fors_label == "セット (S)":
        selected_members = st.multiselect("グループ", members_available, default=members_available)
    else:
        selected_members = members_available

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
last4_rate = (df["rank"] == 4).sum() / total_games * 100

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("対局数", f"{total_games} 局")
col2.metric("累計スコア", f"{total_score:+.0f} pt")
col3.metric("1局平均スコア", f"{avg_pm:+.1f} pt")
col4.metric("トップ率", f"{win_rate:.1f} %")
col5.metric("ラス率", f"{last4_rate:.1f} %")
col6.metric("平均順位", f"{avg_rank:.2f}")

st.divider()

# ══════════════════════════════════════════════════════════════
# 📈 累計スコア推移
# ══════════════════════════════════════════════════════════════
st.subheader("📈 累計スコア推移")

trend_mode = st.radio(
    "表示切替",
    ["全て", "フリー (F)", "セット (S)"],
    horizontal=True,
    key="trend_mode",
)

color_map = {"F": "#6366f1", "S": "#f59e0b"}

# フィルター済み df から日付のみ適用した df_base を作成
if len(date_range) == 2:
    df_base = df_all[
        (df_all["date"].dt.date >= date_range[0]) &
        (df_all["date"].dt.date <= date_range[1])
    ].copy()
else:
    df_base = df_all.copy()

if trend_mode == "全て":
    df_trend = df_base.sort_values("num").copy()
    df_trend["cumulative"] = df_trend["pm"].cumsum()
    df_trend["game_idx"] = range(1, len(df_trend) + 1)
    fig_trend = px.line(
        df_trend,
        x="game_idx",
        y="cumulative",
        markers=True,
        labels={"game_idx": "対局番号", "cumulative": "累計スコア (pt)"},
        hover_data={"date": "|%Y/%m/%d", "ForS": True, "member": True, "rank": True, "pm": True},
        color_discrete_sequence=["#6366f1"],
    )
elif trend_mode == "フリー (F)":
    df_trend = df_base[df_base["ForS"] == "F"].sort_values("num").copy()
    df_trend["cumulative"] = df_trend["pm"].cumsum()
    df_trend["game_idx"] = range(1, len(df_trend) + 1)
    fig_trend = px.line(
        df_trend,
        x="game_idx",
        y="cumulative",
        markers=True,
        labels={"game_idx": "対局番号", "cumulative": "累計スコア (pt)"},
        hover_data={"date": "|%Y/%m/%d", "member": True, "rank": True, "pm": True},
        color_discrete_sequence=[color_map["F"]],
    )
else:  # セット (S)
    df_trend = df_base[df_base["ForS"] == "S"].sort_values("num").copy()
    df_trend["cumulative"] = df_trend["pm"].cumsum()
    df_trend["game_idx"] = range(1, len(df_trend) + 1)
    fig_trend = px.line(
        df_trend,
        x="game_idx",
        y="cumulative",
        markers=True,
        labels={"game_idx": "対局番号", "cumulative": "累計スコア (pt)"},
        hover_data={"date": "|%Y/%m/%d", "member": True, "rank": True, "pm": True},
        color_discrete_sequence=[color_map["S"]],
    )

if df_trend.empty:
    st.info("該当データがありません。")
else:
    fig_trend.update_traces(marker=dict(size=5), line=dict(width=2))
    fig_trend.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig_trend.update_layout(
        height=380,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(100,100,100,0.15)"),
        hovermode="x unified",
        showlegend=False,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════
# 🏆 順位分布 (棒グラフ) + 📊 グループ別平均スコア
# ══════════════════════════════════════════════════════════════
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🏆 順位分布")
    rank_counts = df["rank"].value_counts().sort_index().reset_index()
    rank_counts.columns = ["順位", "回数"]
    rank_counts["順位ラベル"] = rank_counts["順位"].map({1: "1位", 2: "2位", 3: "3位", 4: "4位"})
    rank_counts["率"] = rank_counts["回数"] / total_games * 100
    rank_colors = {1: "#fbbf24", 2: "#94a3b8", 3: "#b45309", 4: "#ef4444"}
    rank_counts["color"] = rank_counts["順位"].map(rank_colors)

    fig_rank = go.Figure(go.Bar(
        x=rank_counts["順位ラベル"],
        y=rank_counts["回数"],
        text=[f"{r:.0f}回<br>({p:.1f}%)" for r, p in zip(rank_counts["回数"], rank_counts["率"])],
        textposition="outside",
        marker_color=rank_counts["color"].tolist(),
        hovertemplate="%{x}: %{y} 回<extra></extra>",
    ))
    fig_rank.update_layout(
        height=320,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(100,100,100,0.15)", title="回数"),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
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
        height=320,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(100,100,100,0.15)"),
    )
    st.plotly_chart(fig_grp, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════
# 🎯 局番ごとの平均順位 & 平均スコア
# ══════════════════════════════════════════════════════════════
st.subheader("🎯 局番ごとの平均順位・平均スコア")

match_agg = (
    df.groupby("match")
    .agg(
        平均順位=("rank", "mean"),
        平均スコア=("pm", "mean"),
        対局数=("pm", "count"),
    )
    .reset_index()
    .rename(columns={"match": "局番"})
)

col_c, col_d = st.columns(2)

with col_c:
    fig_match_rank = px.bar(
        match_agg,
        x="局番",
        y="平均順位",
        text=match_agg["平均順位"].apply(lambda x: f"{x:.2f}"),
        hover_data={"対局数": True},
        color="平均順位",
        color_continuous_scale=["#22c55e", "#fbbf24", "#ef4444"],
        range_color=[1, 4],
        labels={"局番": "局番", "平均順位": "平均順位"},
    )
    fig_match_rank.update_traces(textposition="outside")
    fig_match_rank.add_hline(y=2.5, line_dash="dash", line_color="gray", opacity=0.5,
                              annotation_text="均等値 2.5", annotation_position="top right")
    fig_match_rank.update_layout(
        height=300,
        showlegend=False,
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, dtick=1),
        yaxis=dict(gridcolor="rgba(100,100,100,0.15)", range=[0, 4.5]),
    )
    st.plotly_chart(fig_match_rank, use_container_width=True)
    st.caption("局番ごとの平均順位（緑=良い・赤=悪い）")

with col_d:
    fig_match_score = px.bar(
        match_agg,
        x="局番",
        y="平均スコア",
        text=match_agg["平均スコア"].apply(lambda x: f"{x:+.1f}"),
        hover_data={"対局数": True},
        color="平均スコア",
        color_continuous_scale=["#ef4444", "#fbbf24", "#22c55e"],
        labels={"局番": "局番", "平均スコア": "平均スコア (pt)"},
    )
    fig_match_score.update_traces(textposition="outside")
    fig_match_score.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig_match_score.update_layout(
        height=300,
        showlegend=False,
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, dtick=1),
        yaxis=dict(gridcolor="rgba(100,100,100,0.15)"),
    )
    st.plotly_chart(fig_match_score, use_container_width=True)
    st.caption("局番ごとの平均スコア（緑=プラス・赤=マイナス）")

st.divider()

# ══════════════════════════════════════════════════════════════
# 📅 月別スコア推移
# ══════════════════════════════════════════════════════════════
st.subheader("📅 月別スコア推移")

df_monthly = df.copy()
df_monthly["month"] = df_monthly["date"].dt.to_period("M").astype(str)
monthly_agg = (
    df_monthly.groupby("month")
    .agg(
        合計スコア=("pm", "sum"),
        対局数=("pm", "count"),
        平均スコア=("pm", "mean"),
        トップ率=("rank", lambda x: (x == 1).sum() / len(x) * 100),
    )
    .reset_index()
    .rename(columns={"month": "月"})
)
monthly_agg["正負"] = monthly_agg["合計スコア"].apply(lambda x: "プラス" if x >= 0 else "マイナス")

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

df_box = df.copy()
df_box["順位ラベル"] = df_box["rank"].map(rank_label_map)

fig_box = go.Figure()
for i, r in enumerate([1, 2, 3, 4]):
    subset = df_box[df_box["rank"] == r]["pm"]
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

df_recent = df.sort_values("num").tail(20).copy()
df_recent["game_idx"] = range(1, len(df_recent) + 1)
df_recent["date_str"] = df_recent["date"].dt.strftime("%m/%d")
rank_colors_map = {1: "#fbbf24", 2: "#94a3b8", 3: "#b45309", 4: "#ef4444"}
df_recent["bar_color"] = df_recent["rank"].map(rank_colors_map)

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
        hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>順位: %{y}位<br>スコア: %{customdata[2]:+.0f} pt<extra></extra>",
        customdata=df_recent[["date_str", "ForS", "pm"]].values,
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
    # 直近の連続指標
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
    st.metric("直近平均スコア", f"{df_recent['pm'].mean():+.1f} pt")
    if consecutive_top > 1:
        st.success(f"🔥 連続トップ: {consecutive_top} 連続")
    if consecutive_last > 1:
        st.error(f"💀 連続ラス: {consecutive_last} 連続")

st.divider()

# ══════════════════════════════════════════════════════════════
# 📉 スコア分布
# ══════════════════════════════════════════════════════════════
st.subheader("📉 スコア分布")

fig_hist = px.histogram(
    df,
    x="pm",
    nbins=30,
    color="ForS",
    color_discrete_map={"F": "#6366f1", "S": "#f59e0b"},
    barmode="overlay",
    opacity=0.75,
    labels={"pm": "1局スコア (pt)", "count": "回数", "ForS": "種別"},
)
fig_hist.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.6)
fig_hist.add_vline(
    x=avg_pm, line_dash="dot", line_color="#22c55e" if avg_pm >= 0 else "#ef4444",
    annotation_text=f"平均 {avg_pm:+.1f}", annotation_position="top right",
)
fig_hist.update_layout(
    height=280,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(showgrid=False),
    yaxis=dict(gridcolor="rgba(100,100,100,0.15)", title="回数"),
    bargap=0.05,
    legend_title_text="種別",
)
st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════
# 📅 セッション別成績
# ══════════════════════════════════════════════════════════════
st.subheader("📅 セッション別成績")
session_df = (
    df.groupby(df["date"].dt.date)
    .agg(
        対局数=("pm", "count"),
        合計スコア=("pm", "sum"),
        平均スコア=("pm", "mean"),
        トップ回数=("rank", lambda x: (x == 1).sum()),
        ラス回数=("rank", lambda x: (x == 4).sum()),
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

# ── Raw data ─────────────────────────────────────────────────
with st.expander("📋 詳細データ"):
    display_df = df[["num", "date", "ForS", "member", "match", "rank", "score", "pm"]].copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y/%m/%d")
    display_df = display_df.rename(columns={
        "num": "#", "date": "日付", "ForS": "種別", "member": "グループ",
        "match": "局番", "rank": "順位", "score": "生点", "pm": "スコア",
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)
