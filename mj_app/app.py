import streamlit as st
import pandas as pd
import plotly.express as px

# ページ設定
st.set_page_config(
    page_title="麻雀成績可視化アプリ",
    page_icon="🀄",
    layout="wide"
)

# --- データ読み込み関数群 ---

@st.cache_data
def load_set_res():
    """全体成績 (set_res.csv) を読み込む"""
    try:
        df_set = pd.read_csv('set_res.csv')
        
        # 必要な列確認
        required_cols = ['1st_name', '1st_score']
        if not all(col in df_set.columns for col in required_cols):
            return pd.DataFrame()

        if 'date' in df_set.columns:
            df_set['date'] = pd.to_datetime(df_set['date'], errors='coerce')

        # 縦持ち変換
        records = []
        for _, row in df_set.iterrows():
            if pd.isna(row.get('date')): continue

            base_info = {
                'date': row['date'],
                'match': row.get('match', 0),
                'group': row.get('member', 'Unknown'),
                'rule': row.get('rule', '-')
            }

            for rank in range(1, 5):
                suffix = "st" if rank == 1 else "nd" if rank == 2 else "rd" if rank == 3 else "th"
                name_col = f"{rank}{suffix}_name"
                score_col = f"{rank}{suffix}_score"

                p_name = row.get(name_col)
                p_score = row.get(score_col)

                if pd.notna(p_name) and str(p_name).strip() != "":
                    rec = base_info.copy()
                    rec['player'] = str(p_name).strip()
                    rec['rank'] = rank
                    rec['score_pm'] = pd.to_numeric(p_score, errors='coerce') or 0.0
                    records.append(rec)
        
        return pd.DataFrame(records)
    except FileNotFoundError:
        return pd.DataFrame()

@st.cache_data
def load_res_input():
    """個人詳細成績 (res_input.csv) を読み込む"""
    try:
        df = pd.read_csv('res_input.csv')
        
        # データクリーニング
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # 数値変換
        for col in ['score', 'p-m', 'rank', 'match']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 文字列変換
        for col in ['member', 'ForS']:
            if col in df.columns:
                df[col] = df[col].astype(str)

        return df
    except FileNotFoundError:
        return pd.DataFrame()

# --- メインレイアウト ---

st.sidebar.title("🀄 メニュー")
page = st.sidebar.radio("ページ選択", ["全体成績分析 (All)", "個人詳細分析 (Personal)"])

# ==========================================
# ページ1: 全体成績分析 (All)
# ==========================================
if page == "全体成績分析 (All)":
    st.title("📊 全体成績ダッシュボード")
    df_all = load_set_res()

    if df_all.empty:
        st.warning("`set_res.csv` が見つからないか、形式が正しくありません。")
    else:
        # --- フィルタ ---
        st.sidebar.markdown("---")
        st.sidebar.header("検索フィルタ")
        
        players = sorted(df_all['player'].unique())
        
        # === 修正箇所: 初期値を Hamada に設定 ===
        default_index = 0
        target_name = "Hamada"
        if target_name in players:
            default_index = players.index(target_name)
            
        selected_player = st.sidebar.selectbox("選手を選択", players, index=default_index)
        # ======================================
        
        groups = ['All'] + sorted(df_all['group'].unique())
        selected_group = st.sidebar.selectbox("対戦グループ", groups)
        
        # 抽出
        mask = (df_all['player'] == selected_player)
        if selected_group != 'All':
            mask = mask & (df_all['group'] == selected_group)
        
        df_filtered = df_all[mask].copy()

        # --- 表示 ---
        if df_filtered.empty:
            st.info("該当データがありません。")
        else:
            # KPI
            games = len(df_filtered)
            score_sum = df_filtered['score_pm'].sum()
            avg_rank = df_filtered['rank'].mean()
            top_rate = (len(df_filtered[df_filtered['rank']==1]) / games) * 100
            rentai_rate = (len(df_filtered[df_filtered['rank']<=2]) / games) * 100

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("対戦数", f"{games}")
            c2.metric("通算スコア", f"{score_sum:+.1f}")
            c3.metric("平均順位", f"{avg_rank:.2f}")
            c4.metric("トップ率", f"{top_rate:.1f}%")
            c5.metric("連対率", f"{rentai_rate:.1f}%")

            st.markdown("---")

            # グラフ
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("📈 通算スコア推移")
                df_chart = df_filtered.sort_values(['date', 'match'])
                df_chart['cumulative'] = df_chart['score_pm'].cumsum()
                df_chart['game_count'] = range(1, len(df_chart)+1)

                fig = px.line(df_chart, x='game_count', y='cumulative', markers=True,
                              title=f"{selected_player}のスコア推移",
                              labels={'game_count':'対戦数', 'cumulative':'通算スコア'},
                              hover_data={'date': '|%Y-%m-%d'})
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("🍰 順位分布")
                rank_counts = df_filtered['rank'].value_counts().reset_index()
                rank_counts.columns = ['rank', 'count']
                rank_counts['label'] = rank_counts['rank'].astype(int).astype(str) + "着"
                
                fig_pie = px.pie(rank_counts, values='count', names='label',
                                 color='label',
                                 color_discrete_map={'1着':'#FFD700', '2着':'#C0C0C0', '3着':'#CD7F32', '4着':'#808080'})
                st.plotly_chart(fig_pie, use_container_width=True)

            # 履歴
            st.subheader("📝 対局履歴")
            st.dataframe(df_filtered[['date', 'group', 'rank', 'score_pm']].sort_values('date', ascending=False), use_container_width=True)


# ==========================================
# ページ2: 個人詳細分析 (Personal)
# ==========================================
elif page == "個人詳細分析 (Personal)":
    st.title("👤 個人詳細成績分析")
    
    df_personal = load_res_input()

    if df_personal.empty:
        st.warning("`res_input.csv` が見つからないか、データがありません。")
    else:
        # --- フィルタ ---
        st.sidebar.markdown("---")
        st.sidebar.header("詳細フィルタ")

        if 'member' in df_personal.columns:
            groups = ['All'] + sorted(df_personal['member'].unique())
            sel_group = st.sidebar.selectbox("グループ (member)", groups)
        else:
            sel_group = 'All'
            
        if 'ForS' in df_personal.columns:
            fors_list = ['All'] + sorted(df_personal['ForS'].unique())
            sel_fors = st.sidebar.selectbox("形式 (ForS)", fors_list)
        else:
            sel_fors = 'All'

        min_date = df_personal['date'].min()
        max_date = df_personal['date'].max()
        
        if pd.notnull(min_date):
            date_range = st.sidebar.date_input("期間", [min_date, max_date])
        else:
            date_range = []

        # 抽出実行
        mask = pd.Series([True] * len(df_personal))
        if sel_group != 'All':
            mask &= (df_personal['member'] == sel_group)
        if sel_fors != 'All':
            mask &= (df_personal['ForS'] == sel_fors)
        if len(date_range) == 2:
            mask &= (df_personal['date'].dt.date >= date_range[0]) & (df_personal['date'].dt.date <= date_range[1])
            
        df_p_filtered = df_personal[mask].copy()

        # --- 表示 ---
        if df_p_filtered.empty:
            st.info("条件に一致するデータがありません。")
        else:
            # === 基本KPI ===
            p_games = len(df_p_filtered)
            p_total = df_p_filtered['p-m'].sum()
            p_avg_rank = df_p_filtered['rank'].mean()
            p_avg_score = df_p_filtered['score'].mean()

            st.subheader("📌 成績サマリ")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("対戦数", f"{p_games}")
            col2.metric("通算収支 (p-m)", f"{p_total:+.1f}")
            col3.metric("平均順位", f"{p_avg_rank:.2f}")
            col4.metric("平均素点", f"{p_avg_score:,.0f}")

            st.markdown("---")

            # === 全体グラフエリア ===
            c_chart1, c_chart2 = st.columns([2, 1])

            with c_chart1:
                st.subheader("📈 収支推移 (p-m)")
                df_p_filtered = df_p_filtered.sort_values(['date', 'match'])
                df_p_filtered['cumulative_pm'] = df_p_filtered['p-m'].cumsum()
                df_p_filtered['game_count'] = range(1, len(df_p_filtered) + 1)

                fig_line = px.line(df_p_filtered, x='game_count', y='cumulative_pm',
                                   title="通算収支の推移",
                                   markers=True,
                                   labels={'game_count': '対戦数', 'cumulative_pm': '累積収支'},
                                   hover_data=['date', 'member', 'ForS'])
                st.plotly_chart(fig_line, use_container_width=True)

            with c_chart2:
                st.subheader("📊 素点分布")
                fig_hist = px.histogram(df_p_filtered, x='score', nbins=20,
                                        title="素点の分布 (ヒストグラム)",
                                        labels={'score': '素点'})
                st.plotly_chart(fig_hist, use_container_width=True)

            # === グループ別分析 (All選択時のみ表示) ===
            if sel_group == 'All' and 'member' in df_p_filtered.columns:
                st.markdown("---")
                st.subheader("🏢 グループ別成績比較")
                
                # 集計
                group_stats = df_p_filtered.groupby('member').agg(
                    Games=('match', 'count'),
                    Total_Score=('p-m', 'sum'),
                    Avg_Rank=('rank', 'mean'),
                    Top_Count=('rank', lambda x: (x==1).sum())
                ).reset_index()
                
                group_stats['Top_Rate'] = (group_stats['Top_Count'] / group_stats['Games']) * 100
                
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    fig_g_score = px.bar(group_stats, x='member', y='Total_Score',
                                         title="グループ別通算収支",
                                         labels={'member': 'グループ', 'Total_Score': '通算収支'},
                                         color='Total_Score',
                                         color_continuous_scale=px.colors.diverging.Tealrose)
                    fig_g_score.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(fig_g_score, use_container_width=True)
                    
                with col_g2:
                    fig_g_rank = px.bar(group_stats, x='member', y='Avg_Rank',
                                        title="グループ別平均順位 (低いほど良い)",
                                        labels={'member': 'グループ', 'Avg_Rank': '平均順位'},
                                        text_auto='.2f')
                    fig_g_rank.update_yaxes(autorange="reversed") # 順位なので反転
                    st.plotly_chart(fig_g_rank, use_container_width=True)

                with st.expander("グループ別詳細データを見る"):
                    st.dataframe(
                        group_stats[['member', 'Games', 'Total_Score', 'Avg_Rank', 'Top_Rate']].style.format({
                            'Total_Score': '{:+.1f}',
                            'Avg_Rank': '{:.2f}',
                            'Top_Rate': '{:.1f}%'
                        }),
                        use_container_width=True
                    )

            # === 月別データ分析 ===
            st.markdown("---")
            st.subheader("📅 月別データ分析")
            
            df_monthly_base = df_p_filtered.dropna(subset=['date']).copy()
            df_monthly_base['month'] = df_monthly_base['date'].dt.to_period('M').astype(str)

            col_m1, col_m2 = st.columns(2)

            with col_m1:
                monthly_pm = df_monthly_base.groupby('month')['p-m'].sum().reset_index()
                fig_m_pm = px.bar(
                    monthly_pm, x='month', y='p-m',
                    title="月別収支 (p-m)",
                    labels={'month': '年月', 'p-m': '収支'},
                    text_auto=True,
                    color='p-m',
                    color_continuous_scale=px.colors.diverging.Tealrose
                )
                fig_m_pm.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_m_pm, use_container_width=True)

            with col_m2:
                monthly_rank = df_monthly_base.groupby(['month', 'rank']).size().reset_index(name='count')
                monthly_rank['rank_label'] = monthly_rank['rank'].astype(int).astype(str) + "着"
                
                fig_m_rank = px.bar(
                    monthly_rank, x='month', y='count', color='rank_label',
                    title="月別順位内訳",
                    labels={'month': '年月', 'count': '回数', 'rank_label': '順位'},
                    category_orders={'rank_label': ['1着', '2着', '3着', '4着']},
                    color_discrete_map={'1着': '#FFD700', '2着': '#C0C0C0', '3着': '#CD7F32', '4着': '#808080'}
                )
                st.plotly_chart(fig_m_rank, use_container_width=True)

            # === 詳細テーブル ===
            st.markdown("---")
            st.subheader("📝 詳細データ一覧")
            display_cols = ['date', 'match', 'member', 'ForS', 'rank', 'score', 'p-m']
            existing_cols = [c for c in display_cols if c in df_p_filtered.columns]
            
            st.dataframe(
                df_p_filtered[existing_cols].sort_values(['date', 'match'], ascending=False).style.format({
                    'score': '{:,.0f}',
                    'p-m': '{:+.1f}',
                    'rank': '{:.0f}'
                }),
                use_container_width=True
            )