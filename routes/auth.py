import os
from random import randint
from utils.sms import send_otp_sms
from database.models.user import User
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login.html", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.get_user_by_username(username)

        if user and check_password_hash(user.password, password):
            # Step 1: Generate OTP
            otp = str(randint(100000, 999999))
            session["otp"] = otp
            session["pending_user_id"] = user.id

            # Step 2: Send OTP via SMS
            send_otp_sms(user.phone_number, f"Your OTP is: {otp}")

            # Step 3: Redirect to verification
            return redirect(url_for("auth.verify_otp"))

        flash("Invalid credentials", "danger")
    return render_template("login.html")


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        user_input = request.form["otp"]

        if user_input == session.get("otp"):
            user = User.get_user_by_id(session.get("pending_user_id"))
            login_user(user)
            session.pop("otp", None)
            session.pop("pending_user_id", None)
            return redirect(url_for("post.index"))
        flash("Incorrect OTP", "danger")
    return render_template("verify_otp.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("post.index"))
