from flask import Blueprint, render_template

game_bp = Blueprint("game", __name__)


@game_bp.route("/game.html")
def game():
    return render_template("game.html")
