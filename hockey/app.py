import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import io

API_URL = "https://amaksym07-github-io-1.onrender.com"

st.set_page_config(page_title="Hockey Tracker", layout="wide")

# ----------------------------
# Player data
# ----------------------------
players = [
    "Connor McDavid", "Leon Draisaitl", "Auston Matthews", "Sidney Crosby",
    "Nathan MacKinnon", "Cale Makar", "David Pastrnak", "Kirill Kaprizov",
    "Elias Pettersson", "Jack Hughes", "Mitch Marner", "Brady Tkachuk",
    "Nikita Kucherov", "Mikko Rantanen", "Matthew Tkachuk"
]

st.markdown("""
<style>
button[kind="primary"] {
    border-radius:6px; 
    font-weight:600; 
    padding:6px 0; 
}
button[key*="goal-"] { background-color:#28a745 !important; color:white !important; }
button[key*="assist-"] { background-color:#ffc107 !important; color:black !important; }
button[key="goal-allowed"] { background-color:#dc3545 !important; color:white !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Initialize session state
# ----------------------------
if "lines" not in st.session_state:
    st.session_state.lines = {}  # key = line_id, value = {"player_stats": {...}, "line_diff": 0}

# ----------------------------
# Layout
# ----------------------------
st.title("🏒 Hockey Tracker")

st.subheader("Select Active Players")
selected_players = st.multiselect(
    "Choose players currently on the ice:",
    players,
    max_selections=5
)

if len(selected_players) <= 5 and selected_players:

    line_id = "_".join(sorted(selected_players))

    # ----------------------------
    # Load or initialize line stats
    # ----------------------------
    if line_id not in st.session_state.lines:
        st.session_state.lines[line_id] = {
            "player_stats": {p: {"Goal": 0, "Assist": 0,
                                  "Shot":0,"Good Pass":0,"Bad Pass":0,
                                  "No Pass":0,"Takeaway":0,"Giveaway":0} for p in selected_players},
            "line_diff": 0
        }
    current_line = st.session_state.lines[line_id]

    tab1, tab2 = st.tabs(["🏒 Active Play", "🥅 Goal Log"])

    # ----------------------------
    # TAB 1 - Active Play
    # ----------------------------
    with tab1:
        st.header("Active Play Tracker")
        actions = ["Shot", "Good Pass", "Bad Pass", "No Pass", "Takeaway", "Giveaway"]

        action_emojis = {
            "Shot": "🟩",
            "Good Pass": "🟩",
            "Bad Pass": "🟨",
            "No Pass": "🟥",
            "Takeaway": "🟩",
            "Giveaway": "🟥"
        }

        for player in selected_players:
            cols = st.columns([1] + [1]*len(actions), gap="small")
            cols[0].markdown(f"**{player}**")

            for i, action in enumerate(actions):
                key = f"{player}-{action}"
                label = f"{action_emojis[action]} {action}"

                if cols[i+1].button(label, key=key):
                    current_line["player_stats"][player][action] += 1
                    st.toast(f"{label} for {player}")

        # Build the summary table
        summary_data = [
            [p] + [current_line["player_stats"][p][a] for a in actions]
            for p in selected_players
        ]
        df_summary = pd.DataFrame(summary_data, columns=["Player"] + actions)
        st.table(df_summary)

    # ----------------------------
    # TAB 2 - Goal Log
    # ----------------------------
    with tab2:
        st.header("Goal Log")

        for p in selected_players:
            st.session_state.lines[line_id]["player_stats"].setdefault(p, {"Goal": 0, "Assist": 0})
            cols = st.columns([1,1,1], gap="small")
            cols[0].markdown(f"**{p}**")

            # Goal button
            if cols[1].button("🟩 Goal", key=f"goal-{p}"):
                current_line["player_stats"][p]["Goal"] += 1
                current_line["line_diff"] += 1
                st.toast(f"🥅 Goal for {p} (+1 Line)")

            # Assist button
            if cols[2].button("🟨 Assist", key=f"assist-{p}"):
                current_line["player_stats"][p]["Assist"] += 1
                st.toast(f"🟨 Assist for {p}")

        st.divider()

        # Goal Allowed
        if st.button("🟥 🚫 Goal Allowed (Line)", key="goal-allowed"):
            current_line["line_diff"] -= 1
            st.toast("🚫 Goal Allowed (−1 Line Differential)")

        st.divider()

        # Summary table
        total_goals = sum(current_line["player_stats"][p]["Goal"] for p in selected_players)
        total_assists = sum(current_line["player_stats"][p]["Assist"] for p in selected_players)

        summary_data = [[p, current_line["player_stats"][p]["Goal"], current_line["player_stats"][p]["Assist"]] for p in selected_players]
        summary_data.append(["Line", total_goals, total_assists, int(current_line["line_diff"])])

        df_summary = pd.DataFrame(summary_data, columns=["Player", "Goals", "Assists", "Line +/-"])
        df_summary["Line +/-"] = df_summary["Line +/-"].fillna(0).astype(int)
        st.table(df_summary)

# ----------------------------
# Fetch All Player Stats from Flask
# ----------------------------
st.divider()
st.subheader("📊 All Player Stats")

try:
    response = requests.post(f"{API_URL}/load_line", json={"line_id": "ALL"})
    if response.status_code == 200:
        data = response.json()
        player_stats = data.get("player_stats", {})

        if player_stats:
            # Convert player_stats dict to DataFrame
            stats_df = pd.DataFrame([
                {"Player": player, **stats}
                for player, stats in player_stats.items()
            ])

            st.dataframe(stats_df, use_container_width=True)

            # Convert to CSV for download
            csv_buffer = io.StringIO()
            stats_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Player Stats (CSV)",
                data=csv_buffer.getvalue(),
                file_name="player_stats.csv",
                mime="text/csv"
            )
        else:
            st.info("No player stats recorded yet.")
    else:
        st.error("Failed to load player stats from server.")
except Exception as e:
    st.error(f"Error contacting Flask API: {e}")
