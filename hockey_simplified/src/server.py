from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__, template_folder="templates")
CORS(app)

# ----------------------------
# Setup
# ----------------------------
players = [
    "Connor McDavid", "Leon Draisaitl", "Auston Matthews", "Sidney Crosby",
    "Nathan MacKinnon", "Cale Makar", "David Pastrnak", "Kirill Kaprizov",
    "Elias Pettersson", "Jack Hughes", "Mitch Marner", "Brady Tkachuk",
    "Nikita Kucherov", "Mikko Rantanen", "Matthew Tkachuk"
]

actions = ["Goal","Assist","+","-","Shot","Good Pass","Bad Pass","No Pass","Takeaway","Giveaway"]

# Generate a new CSV file name each day
def get_csv_file():
    date_str = datetime.now().strftime("%Y%m%d")
    return f"player_stats_{date_str}.csv"

# Load today's stats or initialize
def load_stats():
    csv_file = get_csv_file()
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        return {
            row["Player"]: {a: int(row[a]) for a in actions}
            for _, row in df.iterrows()
        }
    else:
        return {p: {a: 0 for a in actions} for p in players}

player_stats = load_stats()

# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    return render_template("hockey.html", players=players, actions=actions)

@app.route("/record", methods=["POST"])
def record():
    data = request.get_json(force=True)
    player = data.get("player")
    action = data.get("action")
    if not player or not action:
        return jsonify({"status": "error", "message": "Missing player or action"}), 400

    if player in player_stats and action in player_stats[player]:
        player_stats[player][action] += 1
        save_stats()
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Invalid player/action"}), 400

@app.route("/reset", methods=["POST"])
def reset():
    for p in player_stats:
        for a in actions:
            player_stats[p][a] = 0
    save_stats()
    return jsonify({"status": "ok"})

@app.route("/download_csv")
def download_csv():
    df = pd.DataFrame([{"Player": p, **player_stats[p]} for p in players])
    csv_data = df.to_csv(index=False)
    filename = get_csv_file()
    return csv_data, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename="{filename}"'
    }

# ----------------------------
# Helper
# ----------------------------
def save_stats():
    df = pd.DataFrame([{"Player": p, **player_stats[p]} for p in players])
    df.to_csv(get_csv_file(), index=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
