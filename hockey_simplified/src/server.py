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

# --------------------------------------
# Helper: current CSV log file per day
# --------------------------------------
def get_current_log_file():
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(LOGS_FOLDER, f"{today}.csv")

    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=[
            "Timestamp", "Player", "Action", "Goals", "Assists", 
            "Shots", "GoodPasses", "BadPasses", "NoPasses",
            "Takeaways", "Giveaways", "Plus", "Minus"
        ])
        df.to_csv(file_path, index=False)

    return file_path


# --------------------------------------
# Download CSV (for viewing logs)
# --------------------------------------
@app.route("/download_csv", methods=["GET"])
def download_csv():
    file_path = get_current_log_file()
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "No CSV file found"}), 404


# --------------------------------------
# Record an action for a player
# --------------------------------------
@app.route("/record", methods=["POST"])
def record():
    try:
        data = request.get_json(force=True)
        player = data.get("player")
        action = data.get("action")

        if not player or not action:
            return jsonify({"status": "error", "message": "Missing player or action"}), 400

        file_path = get_current_log_file()
        df = pd.read_csv(file_path)

        # Create a blank template for all stat columns
        new_row = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Player": player,
            "Action": action,
            "Goals": 0,
            "Assists": 0,
            "Shots": 0,
            "GoodPasses": 0,
            "BadPasses": 0,
            "NoPasses": 0,
            "Takeaways": 0,
            "Giveaways": 0,
            "Plus": 0,
            "Minus": 0
        }

        # Map Streamlit actions to CSV columns
        action_map = {
            "Goal": "Goals",
            "Assist": "Assists",
            "Shot": "Shots",
            "Good Pass": "GoodPasses",
            "Bad Pass": "BadPasses",
            "No Pass": "NoPasses",
            "Takeaway": "Takeaways",
            "Giveaway": "Giveaways",
            "+": "Plus",
            "-": "Minus"
        }

        if action in action_map:
            new_row[action_map[action]] = 1

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(file_path, index=False)

        print(f"✅ Recorded: {player} - {action}")
        return jsonify({"status": "ok"})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------
# Get aggregated stats across all players
# --------------------------------------
@app.route("/stats", methods=["GET"])
def stats():
    try:
        file_path = get_current_log_file()
        if not os.path.exists(file_path):
            return jsonify([])

        df = pd.read_csv(file_path)
        if df.empty:
            return jsonify([])

        stat_columns = [
            "Goals", "Assists", "Shots", "GoodPasses", "BadPasses",
            "NoPasses", "Takeaways", "Giveaways", "Plus", "Minus"
        ]

        summary = (
            df.groupby("Player")[stat_columns]
            .sum()
            .reset_index()
            .sort_values("Player")
        )

        return jsonify(summary.to_dict(orient="records"))

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
