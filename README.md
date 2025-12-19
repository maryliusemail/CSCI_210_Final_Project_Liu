# # Rock–Paper–Scissors Tournament (CSCI 210 Final Project)
#
# This Flask web application runs a multi-player Rock–Paper–Scissors tournament with a
# persistent leaderboard stored in a Python dictionary.
#
# Each game consists of 10 rounds, and the winner of a completed game is automatically
# retained as Player 1 for the next game.
#
# ---
#
# ## How to Run
#
# ```bash
# python app.py
# ```
#
# Open your browser at:
# http://127.0.0.1:5000
#
# ---
#
# ## Creating Players & Starting a Game
#
# To start a game, send a POST request to /api/game/start with two player names.
#
# ```bash
# curl -X POST http://127.0.0.1:5000/api/game/start \
#   -H "Content-Type: application/json" \
#   -d '{"p1":"Alice","p2":"Bob"}'
# ```
#
# This registers the players (if they do not already exist) and initializes a new
# 10-round game.
#
# ---
#
# ## Playing Rounds
#
# Each round is played by sending the moves for both players.
#
# Valid moves:
# - rock
# - paper
# - scissors
#
# ```bash
# curl -X POST http://127.0.0.1:5000/api/game/play_round \
#   -H "Content-Type: application/json" \
#   -d '{"p1_move":"rock","p2_move":"scissors"}'
# ```
#
# Repeat this command until 10 rounds have been played.
#
# After the 10th round:
# - The game automatically ends
# - The winner is locked as Player 1 for the next game
# - The leaderboard is updated
#
# ---
#
# ## Starting the Next Game (Winner Retention)
#
# After a game ends, Player 1 is automatically retained.
# Only Player 2 needs to be provided.
#
# ```bash
# curl -X POST http://127.0.0.1:5000/api/game/start \
#   -H "Content-Type: application/json" \
#   -d '{"p1":"IGNORED","p2":"Charlie"}'
# ```
#
# The submitted Player 1 value is ignored, and the previous winner remains Player 1.
#
# ---
#
# ## Viewing the Leaderboard
#
# ```bash
# curl http://127.0.0.1:5000/api/leaderboard
# ```
#
# The leaderboard is stored as a dictionary, converted into a list, and sorted
# alphabetically by player name and numerically by total score.
#
# ---
#
# ## Summary
#
# - Central data store: Python dictionary
# - Game length: 10 rounds per match
# - Winner retention: Automatic
# - REST API used for all game actions
# - Leaderboard sorted using Python’s built-in sorting
