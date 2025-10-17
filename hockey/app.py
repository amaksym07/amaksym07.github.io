import streamlit as st
import pandas as pd
from datetime import datetime

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

st.subheader("Select Active Players (5 Max)")
selected_players = st.multiselect(
    "Choose 5 players currently on the ice:",
    players,
    max_selections=5
)

if len(selected_players) < 5:
    st.warning(f"Please select {5 - len(selected_players)} more player(s).")
elif len(selected_players) == 5:
    st.success("✅ Active players selected!")

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

    # --
