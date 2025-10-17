import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
from streamlit.components.v1 import html
import streamlit.components.v1 as components

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
/* Works sometimes, not guaranteed */
button[key*="goal-"] { background-color:#28a745 !important; color:white !important; }
button[key*="assist-"] { background-color:#ffc107 !important; color:black !important; }
button[key="goal-allowed"] { background-color:#dc3545 !important; color:white !important; }
</style>
""", unsafe_allow_html=True)



# ----------------------------
# Helper functions
# ----------------------------
def load_today_log():
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join("logs", f"{today}.csv")
    os.makedirs("logs", exist_ok=True)
    if os.path.exists(file_path):
        return pd.read_csv(file_path), file_path
    else:
        df = pd.DataFrame(columns=["Timestamp", "Player", "Action"])
        df.to_csv(file_path, index=False)
        return df, file_path

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

FLASK_URL = "https://amaksym07-github-io-1.onrender.com"

def send_to_flask(player, action, line_id, line_diff):
    try:
        requests.post(
            f"{FLASK_URL}/record",
            json={"player": player, "action": action, "line_id": line_id, "line_diff": line_diff}
        )
    except Exception as e:
        st.error(f"⚠️ Could not connect to Flask server: {e}")

def load_line_from_server(line_id):
    try:
        res = requests.post(f"{FLASK_URL}/load_line", json={"line_id": line_id})
        if res.status_code == 200:
            return res.json()
        return {"player_stats": {}, "line_diff": 0}
    except Exception as e:
        st.error(f"⚠️ Could not connect to Flask server: {e}")
        return {"player_stats": {}, "line_diff": 0}

if len(selected_players) < 5:
    st.warning(f"Please select {5 - len(selected_players)} more player(s).")
elif len(selected_players) == 5:
    st.success("✅ Active players selected!")

    line_id = "_".join(sorted(selected_players))

    tab1, tab2 = st.tabs(["🏒 Active Play", "🥅 Goal Log"])

    # ----------------------------
    # TAB 1 - Active Play (with color squares)
    # ----------------------------
    with tab1:
        st.header("Active Play Tracker")
        actions = ["Shot", "Good Pass", "Bad Pass", "No Pass", "Takeaway", "Giveaway"]

        if "player_stats" not in st.session_state:
            st.session_state.player_stats = {}

        # Ensure player stat structure exists
        for p in selected_players:
            if p not in st.session_state.player_stats:
                st.session_state.player_stats[p] = {a: 0 for a in actions}
            else:
                for a in actions:
                    st.session_state.player_stats[p].setdefault(a, 0)

        # Map actions to emojis/colors
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
                    st.session_state.player_stats[player][action] += 1
                    send_to_flask(player, action, line_id, None)
                    st.toast(f"{label} for {player}")

        # Build the summary table
        summary_data = [
            [p] + [st.session_state.player_stats[p][a] for a in actions]
            for p in selected_players
        ]
        df_summary = pd.DataFrame(summary_data, columns=["Player"] + actions)
        st.table(df_summary)



    # ----------------------------
    # TAB 2 - Goal Log (with color squares)
    # ----------------------------
    with tab2:
        st.header("Goal Log")

        # Load previous stats if this line was used before
        if "active_line_id" not in st.session_state or st.session_state.active_line_id != line_id:
            st.session_state.active_line_id = line_id
            prev = load_line_from_server(line_id)
            st.session_state.player_stats = prev["player_stats"] if prev["player_stats"] else {p: {"Goal": 0, "Assist": 0} for p in selected_players}
            st.session_state.line_tracker = prev["line_diff"]

        for p in selected_players:
            st.session_state.player_stats.setdefault(p, {"Goal": 0, "Assist": 0})
            cols = st.columns([1,1,1], gap="small")
            cols[0].markdown(f"**{p}**")

            # Goal button (green square emoji)
            if cols[1].button("🟩 Goal", key=f"goal-{p}"):
                st.session_state.player_stats[p]["Goal"] += 1
                st.session_state.line_tracker += 1
                send_to_flask(p, "Goal", line_id, st.session_state.line_tracker)
                st.toast(f"🥅 Goal for {p} (+1 Line)")

            # Assist button (yellow square emoji)
            if cols[2].button("🟨 Assist", key=f"assist-{p}"):
                st.session_state.player_stats[p]["Assist"] += 1
                send_to_flask(p, "Assist", line_id, st.session_state.line_tracker)
                st.toast(f"🟨 Assist for {p}")

        st.divider()

        # Goal Allowed (red square emoji)
        if st.button("🟥 🚫 Goal Allowed (Line)", key="goal-allowed"):
            st.session_state.line_tracker -= 1
            send_to_flask("", "Goal Allowed", line_id, st.session_state.line_tracker)
            st.toast("🚫 Goal Allowed (−1 Line Differential)")

        st.divider()

        # Summary table
        total_goals = sum(st.session_state.player_stats[p]["Goal"] for p in selected_players)
        total_assists = sum(st.session_state.player_stats[p]["Assist"] for p in selected_players)

        summary_data = [[p, st.session_state.player_stats[p]["Goal"], st.session_state.player_stats[p]["Assist"]] for p in selected_players]
        summary_data.append(["Line", total_goals, total_assists, int(st.session_state.line_tracker)])

        df_summary = pd.DataFrame(summary_data, columns=["Player", "Goals", "Assists", "Line +/-"])
        df_summary["Line +/-"] = df_summary["Line +/-"].fillna(0).astype(int)  # 👈 converts float to int
        st.table(df_summary)

st.markdown(f"""
<a href="{FLASK_URL}/download_csv" target="_blank">
    <button style="background-color:#4CAF50;color:white;padding:10px 20px;border:none;border-radius:6px;cursor:pointer;">
        📥 Download CSV File
    </button>
</a>
""", unsafe_allow_html=True)




