import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Chess Performance Dashboard",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Premium Look
st.markdown("""
<style>
    /* Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Main Container Glassmorphism */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #ffffff;
    }

    /* KPI Cards Styling */
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #00d2ff;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 16px;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        color: #888;
    }
    .stTabs [aria-selected="true"] {
        color: #00d2ff !important;
        border-bottom-color: #00d2ff !important;
    }
    
    /* Plotly Chart Backgrounds */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    /* Dataframe Styling */
    .stDataFrame {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Constants
DATA_PATH = 'data/processed/processed.csv'

@st.cache_data
def load_data():
    """Load and cache the processed data."""
    if not os.path.exists(DATA_PATH):
        return None
    
    df = pd.read_csv(DATA_PATH)
    
    # Ensure date columns are datetime
    if 'end_date' in df.columns:
        df['end_date'] = pd.to_datetime(df['end_date'])
    if 'end_datetime' in df.columns:
        df['end_datetime'] = pd.to_datetime(df['end_datetime'])
        
    return df

def get_player_data(df, username):
    """Filter data for a specific player perspective."""
    # Filter for games involved
    user_games = df[
        (df['white_username'] == username) | 
        (df['black_username'] == username)
    ].copy()
    
    if user_games.empty:
        return user_games
        
    # Add dynamic player-centric columns
    user_games['player_color'] = user_games.apply(
        lambda x: 'white' if x['white_username'] == username else 'black', axis=1
    )
    user_games['opponent'] = user_games.apply(
        lambda x: x['black_username'] if x['player_color'] == 'white' else x['white_username'], axis=1
    )
    user_games['player_rating'] = user_games.apply(
        lambda x: x['white_rating'] if x['player_color'] == 'white' else x['black_rating'], axis=1
    )
    user_games['result_status'] = user_games.apply(
        lambda x: 'Win' if x['winner'] == username else ('Draw' if x['winner'] == 'draw' else 'Loss'), axis=1
    )
    
    # Ensure rating diff category exists (or recalculate if needed for consistency)
    if 'rating_diff' in user_games.columns:
        def categorize_diff(row):
            # logical flip: imported rating_diff is white-black. 
            # We want player-opponent.
            diff = row['rating_diff'] if row['player_color'] == 'white' else -row['rating_diff']
            if diff >= 100: return 'Higher Rated (+100+)'
            if diff >= 25: return 'Slightly Higher (+25 to +99)'
            if diff > -25: return 'Similar Rated (±25)'
            if diff > -100: return 'Slightly Lower (-25 to -99)'
            return 'Lower Rated (-100+)'
        
        user_games['rating_diff_category'] = user_games.apply(categorize_diff, axis=1)

    return user_games

def main():
    # --- Sidebar ---
    st.sidebar.title("♟️ Chess Analytics")
    
    # Load Data
    df = load_data()
    if df is None:
        st.error(f"Data file not found at {DATA_PATH}. Please run the ETL process first.")
        return

    # User Selection
    all_players = pd.concat([df['white_username'], df['black_username']]).unique()
    # Prioritize known players in list
    default_players = ["MagnusCarlsen", "FabianoCaruana", "hikaru", "GHANDEEVAM2003"]
    valid_defaults = [p for p in default_players if p in all_players]
    
    selected_user = st.sidebar.selectbox(
        "Select Player", 
        options=sorted(all_players),
        index=sorted(all_players).index(valid_defaults[0]) if valid_defaults else 0
    )
    
    # Get Player Data
    player_df = get_player_data(df, selected_user)
    
    if player_df.empty:
        st.warning("No games found for this player.")
        return

    # Filters
    st.sidebar.subheader("Analytics Filters")
    
    # 1. Date Range
    min_date = player_df['end_date'].min().date()
    max_date = player_df['end_date'].max().date()
    date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    # 2. Game Type (Multi-select)
    available_types = sorted(player_df['game_type'].unique()) if 'game_type' in player_df.columns else []
    selected_types = st.sidebar.multiselect("Performance Format", available_types, default=available_types)
    
    # 3. Result Filter (New)
    available_results = sorted(player_df['result_status'].unique())
    selected_results = st.sidebar.multiselect("Game Result", available_results, default=available_results)
    
    # 4. Color Filter (New)
    available_colors = sorted(player_df['player_color'].unique())
    selected_colors = st.sidebar.multiselect("Playing As", available_colors, default=available_colors)
        
    # Apply Filters
    filtered_df = player_df.copy()
    
    # Apply Date filter
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['end_date'].dt.date >= date_range[0]) & 
            (filtered_df['end_date'].dt.date <= date_range[1])
        ]
    
    # Apply Format filter
    if selected_types:
        filtered_df = filtered_df[filtered_df['game_type'].isin(selected_types)]
    
    # Apply Result filter
    if selected_results:
        filtered_df = filtered_df[filtered_df['result_status'].isin(selected_results)]
        
    # Apply Color filter
    if selected_colors:
        filtered_df = filtered_df[filtered_df['player_color'].isin(selected_colors)]

    # --- Dashboard Main Area ---
    st.title(f"Performance Dashboard: {selected_user}")
    
    # 1. KPIs
    st.subheader("Performance Analytics")
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
    
    total_games = len(filtered_df)
    wins = len(filtered_df[filtered_df['result_status'] == 'Win'])
    draws = len(filtered_df[filtered_df['result_status'] == 'Draw'])
    losses = len(filtered_df[filtered_df['result_status'] == 'Loss'])
    
    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    draw_rate = (draws / total_games * 100) if total_games > 0 else 0
    loss_rate = (losses / total_games * 100) if total_games > 0 else 0
    
    avg_rating = int(filtered_df['player_rating'].mean()) if total_games > 0 else 0
    
    # Use end_datetime if available, else end_time
    time_col = 'end_datetime' if 'end_datetime' in filtered_df.columns else 'end_time'
    current_rating = filtered_df.sort_values(time_col, ascending=False).iloc[0]['player_rating'] if not filtered_df.empty else 0
    
    with kpi1:
        st.metric("Total Games", f"{total_games:,}")
    with kpi2:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with kpi3:
        st.metric("Draw Rate", f"{draw_rate:.1f}%")
    with kpi4:
        st.metric("Loss Rate", f"{loss_rate:.1f}%")
    with kpi5:
        st.metric("Avg Rating", f"{avg_rating}")
    with kpi6:
        st.metric("Current Rating", f"{current_rating}")

    st.markdown("---")

    # 2. Trends
    st.subheader("Trend Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        # Rating over time
        # Aggregate by day or take all games? Line chart can handle many points, 
        # but daily/monthly avg usually cleaner. Let's do raw for accuracy first.
        fig_rating = px.line(
            rating_trend, x='end_date', y='player_rating', 
            title='Rating Progression',
            labels={'end_date': 'Date', 'player_rating': 'Rating'},
            template="plotly_dark"
        )
        fig_rating.update_traces(line_color='#00d2ff', line_width=3)
        st.plotly_chart(fig_rating, use_container_width=True)
        
    with col2:
        # Win Rate over time (Monthly)
        # Resample to monthly
        monthly_stats = filtered_df.set_index('end_date').resample('M').apply({
            'result_status': lambda x: (x == 'Win').sum() / len(x) * 100 if len(x) > 0 else 0
        }).reset_index()
        monthly_stats.rename(columns={'result_status': 'Win Rate'}, inplace=True)
        
        fig_winrate = px.area(
            monthly_stats, x='end_date', y='Win Rate',
            title='Monthly Win Rate Trend',
            labels={'end_date': 'Month', 'Win Rate': 'Win %'},
            template="plotly_dark"
        )
        fig_winrate.update_traces(line_color='#27AE60', fillcolor='rgba(39, 174, 96, 0.2)')
        st.plotly_chart(fig_winrate, use_container_width=True)

    # 3. Breakdowns
    st.subheader("Performance Breakdown")
    tab1, tab2, tab3, tab4 = st.tabs(["By Format", "By Color", "By Opening", "By Difficulty"])
    
    with tab1:
        # Format (Game Type)
        if 'game_type' in filtered_df.columns:
            format_stats = filtered_df.groupby('game_type')['result_status'].value_counts(normalize=True).unstack().fillna(0) * 100
            for col in ['Win', 'Draw', 'Loss']:
                if col not in format_stats.columns: format_stats[col] = 0
            
            format_stats = format_stats[['Win', 'Draw', 'Loss']]
            
            fig_format = px.bar(
                format_stats, 
                title="Result Distribution by Game Format",
                labels={'value': 'Percentage', 'game_type': 'Format'},
                color_discrete_map={'Win': '#2ECC71', 'Draw': '#95A5A6', 'Loss': '#E74C3C'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_format, use_container_width=True)
            
    with tab2:
        # Color Performance
        color_stats = filtered_df.groupby('player_color')['result_status'].value_counts(normalize=True).unstack().fillna(0) * 100
        for col in ['Win', 'Draw', 'Loss']:
            if col not in color_stats.columns: color_stats[col] = 0
        color_stats = color_stats[['Win', 'Draw', 'Loss']]
        
        fig_color = px.bar(
            color_stats, barmode='group',
            title="Performance by Color (White vs Black)",
            color_discrete_map={'Win': '#2ECC71', 'Draw': '#95A5A6', 'Loss': '#E74C3C'},
            template="plotly_dark"
        )
        st.plotly_chart(fig_color, use_container_width=True)
        
    with tab3:
        # Top Openings
        if 'opening_name' in filtered_df.columns:
            top_openings = filtered_df['opening_name'].value_counts().head(10).index
            opening_data = filtered_df[filtered_df['opening_name'].isin(top_openings)]
            
            opening_stats = opening_data.groupby('opening_name')['result_status'].apply(
                lambda x: (x == 'Win').sum() / len(x) * 100
            ).sort_values(ascending=True)
            
            fig_opening = px.bar(
                opening_stats, orientation='h',
                title="Win Rate by Top 10 Most Played Openings",
                labels={'value': 'Win %', 'opening_name': 'Opening'},
                template="plotly_dark"
            )
            fig_opening.update_traces(marker_color='#8E44AD')
            st.plotly_chart(fig_opening, use_container_width=True)

    with tab4:
        # Performance by Rating Difference
        if 'rating_diff_category' in filtered_df.columns:
            diff_stats = filtered_df.groupby('rating_diff_category')['result_status'].value_counts(normalize=True).unstack().fillna(0) * 100
            for col in ['Win', 'Draw', 'Loss']:
                if col not in diff_stats.columns: diff_stats[col] = 0
            
            # Sort categories logically
            sort_order = [
                'Higher Rated (+100+)', 
                'Slightly Higher (+25 to +99)', 
                'Similar Rated (±25)', 
                'Slightly Lower (-25 to -99)', 
                'Lower Rated (-100+)'
            ]
            available_order = [c for c in sort_order if c in diff_stats.index]
            diff_stats = diff_stats.loc[available_order][['Win', 'Draw', 'Loss']]
            
            fig_diff = px.bar(
                diff_stats, 
                title="Win Rate by Opponent Strength",
                labels={'value': 'Percentage', 'rating_diff_category': 'Strength'},
                color_discrete_map={'Win': '#2ECC71', 'Draw': '#95A5A6', 'Loss': '#E74C3C'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_diff, use_container_width=True)

    # 4. Detailed Table
    st.subheader("Detailed Games")
    display_cols = ['end_date', 'game_type', 'player_color', 'opponent', 'result_status', 'player_rating', 'rating_diff', 'opening_name', 'url']
    st.dataframe(
        filtered_df[display_cols].sort_values('end_date', ascending=False),
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    main()
