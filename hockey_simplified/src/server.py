from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
from datetime import datetime

app = Flask(__name__, template_folder="templates")
CORS(app)

# -----------------------------
# In-memory data
# -----------------------------
players = []
actions = ["Goal", "Assist", "+", "-", "Shot", "Good Pass", "Bad Pass", "No Pass", "Takeaway", "Giveaway"]
player_stats = {}


# -----------------------------
# Helper
# -----------------------------
def init_player(name):
    player_stats[name] = {a: 0 for a in actions}


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    return render_template("hockey.html", actions=actions, players=players)


@app.route("/team", methods=["GET", "POST", "DELETE"])
def team():
    global players

    if request.method == "GET":
        return jsonify({"players": players})

    data = request.get_json(force=True)
    name = data.get("name", "").strip()

    if request.method == "POST":
        if not name:
            return jsonify({"status": "error", "message": "Player name required"}), 400
        if name in players:
            return jsonify({"status": "error", "message": "Player already exists"}), 400
        players.append(name)
        init_player(name)
        return jsonify({"status": "ok"})

    elif request.method == "DELETE":
        if name not in players:
            return jsonify({"status": "error", "message": "Player not found"}), 404
        players.remove(name)
        player_stats.pop(name, None)
        return jsonify({"status": "ok"})


@app.route("/record", methods=["POST"])
def record():
    data = request.get_json(force=True)
    player = data.get("player")
    action = data.get("action")

    if not player or not action:
        return jsonify({"status": "error", "message": "Missing player or action"}), 400

    if player in player_stats and action in player_stats[player]:
        player_stats[player][action] += 1
        return jsonify({"status": "ok"})

    return jsonify({"status": "error", "message": "Invalid player/action"}), 400


@app.route("/download_csv")
def download_csv():
    df = pd.DataFrame([
        {"Player": p, **player_stats.get(p, {a: 0 for a in actions})}
        for p in players
    ])
    csv_data = df.to_csv(index=False)
    filename = f"player_stats_{datetime.now().strftime('%Y%m%d')}.csv"
    return csv_data, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": f"attachment; filename='{filename}'"
    }



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
