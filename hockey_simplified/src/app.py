import streamlit as st
import pandas as pd
import io

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
button[key*="goal-"] { background-color:#28a745 !important; color:white !important; }  /* green */
button[key*="assist-"] { background-color:#ffc107 !important; color:black !important; } /* yellow */
button[key*="plus-"] { background-color:#28a745 !important; color:white !important; }  /* green */
button[key*="minus-"] { background-color:#dc3545 !important; color:white !important; } /* red */
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Initialize session state
# ----------------------------
if "player_stats" not in st.session_state:
    st.session_state.player_stats = {
        p: {
            "Goal": 0,
            "Assist": 0,
            "+": 0,
            "-": 0,
            "Shot": 0,
            "Good Pass": 0,
            "Bad Pass": 0,
            "No Pass": 0,
            "Takeaway": 0,
            "Giveaway": 0
        }
        for p in players
    }

st.title("🏒 Hockey Tracker")

# ----------------------------
# Tabs
# ----------------------------
tab1, tab2 = st.tabs(["🥅 Goal Log", "🏒 Active Play"])

# ----------------------------
# TAB 1 - Goal Log
# ----------------------------
with tab1:
    st.header("Goal & Assist Tracker")

    for p in players:
        cols = st.columns([2, 1, 1, 1, 1], gap="small")
        cols[0].markdown(f"**{p}**")

        if cols[1].button("🟩 Goal", key=f"goal-{p}"):
            st.session_state.player_stats[p]["Goal"] += 1
            st.toast(f"🥅 Goal for {p}")

        if cols[2].button("🟨 Assist", key=f"assist-{p}"):
            st.session_state.player_stats[p]["Assist"] += 1
            st.toast(f"🟨 Assist for {p}")

        if cols[3].button("🟢➕", key=f"plus-{p}"):
            st.session_state.player_stats[p]["+"] += 1
            st.toast(f"✅ +1 for {p}")

        if cols[4].button("🔴➖", key=f"minus-{p}"):
            st.session_state.player_stats[p]["-"] += 1
            st.toast(f"🔴 -1 for {p}")

# ----------------------------
# TAB 2 - Active Play
# ----------------------------
with tab2:
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

    for player in players:
        cols = st.columns([1] + [1]*len(actions), gap="small")
        cols[0].markdown(f"**{player}**")

        for i, action in enumerate(actions):
            key = f"{player}-{action}"
            label = f"{action_emojis[action]} {action}"

            if cols[i+1].button(label, key=key):
                st.session_state.player_stats[player][action] += 1
                st.toast(f"{label} for {player}")

# ----------------------------
# All Player Stats Summary
# ----------------------------
st.divider()
st.subheader("📊 All Player Stats")

df_all = pd.DataFrame([
    {"Player": p, **st.session_state.player_stats[p]} for p in players
])
st.dataframe(df_all, use_container_width=True)

csv_buffer = io.StringIO()
df_all.to_csv(csv_buffer, index=False)
st.download_button(
    label="📥 Download Stats (CSV)",
    data=csv_buffer.getvalue(),
    file_name="all_player_stats.csv",
    mime="text/csv"
)
