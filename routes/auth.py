from database.models.user import User
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required
from flask import Blueprint, render_template, request, redirect, url_for, flash


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.get_user_by_username(username)

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("post.index"))

        flash("Invalid credentials")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("post.index"))
