from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple, Any
from flask import Flask, jsonify, render_template, request, redirect, url_for

app = Flask(__name__)

# Game constants
MOVES = ("rock", "paper", "scissors")


@dataclass
class PlayerStats:
    # Stores cumulative statistics for one player
    name: str
    score: int = 0
    wins: int = 0
    losses: int = 0
    ties: int = 0
    games_played: int = 0

    # Convert object to dictionary for JSON responses
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Global leaderboard (persists while server is running)
LEADERBOARD: Dict[str, PlayerStats] = {}

# Current match state (only one match at a time)
CURRENT_MATCH = {
    "active": False,
    "round": 0,
    "max_rounds": 10,
    "p1": None,
    "p2": None,
    "p1_round_wins": 0,
    "p2_round_wins": 0,
    "round_history": [],
    "locked_winner_as_p1": False
}


def normalize_name(name: str) -> str:
    # Remove extra spaces from player names
    return " ".join((name or "").strip().split())


def ensure_player(name: str) -> PlayerStats:
    # Create player in leaderboard if they do not exist
    name = normalize_name(name)
    if not name:
        raise ValueError("Player name cannot be empty.")
    if name not in LEADERBOARD:
        LEADERBOARD[name] = PlayerStats(name=name)
    return LEADERBOARD[name]


def rps_result(move1: str, move2: str) -> int:
    """
    Determine round outcome.
    Returns:
      1  -> Player 1 wins
     -1  -> Player 2 wins
      0  -> Tie
    """
    m1 = (move1 or "").strip().lower()
    m2 = (move2 or "").strip().lower()

    if m1 not in MOVES or m2 not in MOVES:
        raise ValueError("Moves must be rock, paper, or scissors.")

    if m1 == m2:
        return 0

    beats = {
        "rock": "scissors",
        "paper": "rock",
        "scissors": "paper",
    }

    return 1 if beats[m1] == m2 else -1


def current_players() -> Tuple[Optional[str], Optional[str]]:
    # Return current player names
    return CURRENT_MATCH["p1"], CURRENT_MATCH["p2"]


def match_winner() -> Optional[str]:
    # Determine overall winner after all rounds
    if CURRENT_MATCH["round"] < CURRENT_MATCH["max_rounds"]:
        return None

    if CURRENT_MATCH["p1_round_wins"] > CURRENT_MATCH["p2_round_wins"]:
        return CURRENT_MATCH["p1"]
    if CURRENT_MATCH["p2_round_wins"] > CURRENT_MATCH["p1_round_wins"]:
        return CURRENT_MATCH["p2"]

    return None


def match_summary() -> Dict[str, Any]:
    # Return current match state for UI and API
    winner = match_winner()
    return {
        "active": CURRENT_MATCH["active"],
        "round": CURRENT_MATCH["round"],
        "max_rounds": CURRENT_MATCH["max_rounds"],
        "p1": CURRENT_MATCH["p1"],
        "p2": CURRENT_MATCH["p2"],
        "p1_round_wins": CURRENT_MATCH["p1_round_wins"],
        "p2_round_wins": CURRENT_MATCH["p2_round_wins"],
        "winner": winner,
        "overall_tie": (
            CURRENT_MATCH["round"] == CURRENT_MATCH["max_rounds"] and winner is None
        ),
        "locked_winner_as_p1": CURRENT_MATCH["locked_winner_as_p1"],
        "round_history": CURRENT_MATCH["round_history"],
    }


def leaderboard_views() -> Dict[str, Any]:
    # Generate leaderboard sorted two ways
    players = [ps.to_dict() for ps in LEADERBOARD.values()]
    by_name = sorted(players, key=lambda x: x["name"].lower())
    by_score = sorted(players, key=lambda x: (x["score"], x["wins"]), reverse=True)
    return {"by_name": by_name, "by_score": by_score}


@app.get("/")
def home():
    # Render main game page
    return render_template(
        "index.html",
        state=match_summary(),
        leaderboard=leaderboard_views()
    )


@app.get("/leaderboard")
def leaderboard_page():
    # Render leaderboard page
    return render_template("leaderboard.html", leaderboard=leaderboard_views())


@app.post("/api/player/register")
def api_register_player():
    # Register a new player
    data = request.get_json(silent=True) or {}
    try:
        player = ensure_player(data.get("name", ""))
        return jsonify({"ok": True, "player": player.to_dict()})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/game/start")
def api_game_start():
    # Start a new match
    data = request.get_json(silent=True) or {}

    p1 = normalize_name(data.get("p1", ""))
    p2 = normalize_name(data.get("p2", ""))

    if CURRENT_MATCH["p1"] and CURRENT_MATCH["locked_winner_as_p1"]:
        p1 = CURRENT_MATCH["p1"]

    if not p1 or not p2 or p1 == p2:
        return jsonify({"ok": False, "error": "Invalid player names."}), 400

    ensure_player(p1)
    ensure_player(p2)

    CURRENT_MATCH.update({
        "active": True,
        "round": 0,
        "p1": p1,
        "p2": p2,
        "p1_round_wins": 0,
        "p2_round_wins": 0,
        "round_history": [],
        "locked_winner_as_p1": False,
    })

    return jsonify({"ok": True, "state": match_summary()})


@app.post("/api/game/play_round")
def api_game_play_round():
    # Play one round of the match
    if not CURRENT_MATCH["active"]:
        return jsonify({"ok": False, "error": "No active match."}), 400

    if CURRENT_MATCH["round"] >= CURRENT_MATCH["max_rounds"]:
        return jsonify({"ok": False, "error": "Match already finished. Start the next match."}), 400

    data = request.get_json(silent=True) or {}
    p1_move = data.get("p1_move", "")
    p2_move = data.get("p2_move", "")

    outcome = rps_result(p1_move, p2_move)

    CURRENT_MATCH["round"] += 1
    round_num = CURRENT_MATCH["round"]

    p1, p2 = current_players()
    ps1 = ensure_player(p1)
    ps2 = ensure_player(p2)

    round_winner = None
    if outcome == 1:
        CURRENT_MATCH["p1_round_wins"] += 1
        ps1.score += 1
        ps1.wins += 1
        ps2.losses += 1
        round_winner = p1
    elif outcome == -1:
        CURRENT_MATCH["p2_round_wins"] += 1
        ps2.score += 1
        ps2.wins += 1
        ps1.losses += 1
        round_winner = p2
    else:
        ps1.ties += 1
        ps2.ties += 1

    CURRENT_MATCH["round_history"].append({
        "round": round_num,
        "p1_move": p1_move,
        "p2_move": p2_move,
        "round_winner": round_winner,
    })

    if round_num == CURRENT_MATCH["max_rounds"]:
        ps1.games_played += 1
        ps2.games_played += 1
        CURRENT_MATCH["active"] = False

        winner = match_winner()
        locked_p1 = p1 if winner is None else winner

        CURRENT_MATCH["p1"] = locked_p1
        CURRENT_MATCH["p2"] = None
        CURRENT_MATCH["locked_winner_as_p1"] = True

    return jsonify({"ok": True, "state": match_summary()})


@app.get("/api/leaderboard")
def api_leaderboard():
    # Return leaderboard data
    return jsonify({"ok": True, "leaderboard": leaderboard_views()})


@app.post("/start")
def web_start():
    # Start match from HTML form
    app.test_client().post(
        "/api/game/start",
        json={
            "p1": request.form.get("p1", ""),
            "p2": request.form.get("p2", "")
        }
    )
    return redirect(url_for("home"))


@app.post("/play")
def web_play():
    # Play round from HTML form
    app.test_client().post(
        "/api/game/play_round",
        json={
            "p1_move": request.form.get("p1_move", ""),
            "p2_move": request.form.get("p2_move", "")
        }
    )
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
