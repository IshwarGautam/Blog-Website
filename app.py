import os
import sqlite3
from dotenv import load_dotenv
from database.models.user import User
from werkzeug.exceptions import abort
from google.oauth2 import service_account
from googleapiclient.discovery import build
from werkzeug.security import check_password_hash
from flask import Flask, render_template, request, url_for, flash, redirect
from utils.helper import upload_image_to_google_drive, extract_base64_images
from flask_login import (
    login_user,
    logout_user,
    current_user,
    LoginManager,
    login_required,
)

# Load the .env file
load_dotenv()

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

# Load Google Drive API credentials
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build("drive", "v3", credentials=credentials)

# Google Drive Folder ID
FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_id(user_id)


def get_db_connection():
    conn = sqlite3.connect("database/database.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post


@app.route("/")
def index():
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts").fetchall()
    conn.close()
    return render_template("index.html", posts=posts)


@app.route("/<int:post_id>")
def post(post_id):
    post = get_post(post_id)
    return render_template("post.html", post=post)


@app.route("/create", methods=("GET", "POST"))
@login_required
def create():
    if not current_user.is_admin:
        flash("Access denied! Admins only.")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            flash("Title is required!")
        else:
            # Extract base64 images and upload them to Google Drive
            images = extract_base64_images(content)
            for image_data in images:
                file_url = upload_image_to_google_drive(
                    image_data["base64"],
                    image_data["format"],
                    drive_service,
                    FOLDER_ID,
                    image_data["filename"],
                )
                content = content.replace(image_data["base64"], file_url)

            # Save the post with the updated content (including Google Drive links)
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO posts (title, content) VALUES (?, ?)", (title, content)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("index"))

    return render_template("create.html")


@app.route("/<int:id>/edit", methods=("GET", "POST"))
@login_required
def edit(id):
    if not current_user.is_admin:
        flash("Access denied! Admins only.")
        return redirect(url_for("index"))

    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            flash("Title is required!")
        else:
            # Extract base64 images and upload them to Google Drive
            images = extract_base64_images(content)
            for image_data in images:
                file_url = upload_image_to_google_drive(
                    image_data["base64"],
                    image_data["format"],
                    drive_service,
                    FOLDER_ID,
                    image_data["filename"],
                )
                content = content.replace(image_data["base64"], file_url)

            # Save the post with the updated content (including Google Drive links)
            conn = get_db_connection()
            conn.execute(
                "UPDATE posts SET title = ?, content = ? WHERE id = ?",
                (title, content, id),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("index"))

    return render_template("edit.html", post=post)


@app.route("/<int:id>/delete", methods=("POST",))
def delete(id):
    post = get_post(id)
    conn = get_db_connection()
    conn.execute("DELETE FROM posts WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(post["title"]))
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.get_user_by_username(username)
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        flash("Invalid credentials")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run()
