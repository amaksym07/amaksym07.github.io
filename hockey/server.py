# server.py
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
import traceback

app = Flask(__name__)
CORS(app)

LOGS_FOLDER = "./logs"
os.makedirs(LOGS_FOLDER, exist_ok=True)

def get_current_log_file():
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(LOGS_FOLDER, f"{today}.csv")
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=["Timestamp", "Line", "Player", "Action", "LineDifferential"])
        df.to_csv(file_path, index=False)
    return file_path

@app.route("/download_csv", methods=["GET"])
def download_csv():
    file_path = get_current_log_file()
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "No CSV file found"}), 404


@app.route("/record", methods=["POST"])
def record():
    try:
        data = request.get_json(force=True)
        player = data.get("player")
        action = data.get("action")
        line_id = data.get("line_id")
        line_diff = data.get("line_diff", 0)

        if not action:
            return jsonify({"status": "error", "message": "missing action"}), 400
        if player is None:
            player = ""  # Allow empty player (for line-only actions)
        if line_diff is None:
            line_diff=""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_path = get_current_log_file()

        new_row = pd.DataFrame([[timestamp, line_id, player, action, line_diff]],
                               columns=["Timestamp", "LineID", "Player", "Action", "LineDifferential"])
        new_row.to_csv(file_path, mode="a", header=False, index=False)

        print(f"✅ {timestamp}: {player} - {action} ({line_id}) | LineDiff={line_diff}")
        return jsonify({"status": "ok"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/load_line", methods=["POST"])
def load_line():
    """Return stats for a specific line if it has played before."""
    try:
        data = request.get_json(force=True)
        line_id = data.get("line_id")
        file_path = get_current_log_file()
        if not os.path.exists(file_path):
            return jsonify({"player_stats": {}, "line_diff": 0})

        df = pd.read_csv(file_path)
        df_line = df[df["LineID"] == line_id]
        if df_line.empty:
            return jsonify({"player_stats": {}, "line_diff": 0})

        player_stats = {}
        for player in df_line["Player"].unique():
            df_player = df_line[df_line["Player"] == player]
            goals = (df_player["Action"] == "Goal").sum()
            assists = (df_player["Action"] == "Assist").sum()
            player_stats[player] = {"Goal": int(goals), "Assist": int(assists)}

        last_diff = df_line["LineDifferential"].iloc[-1] if not df_line.empty else 0

        return jsonify({"player_stats": player_stats, "line_diff": int(last_diff)})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

